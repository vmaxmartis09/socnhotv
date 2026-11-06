from __future__ import annotations

import re
from typing import List, Tuple
from pydantic import BaseModel, Field

PROHIBITED_MEDICAL_CLAIMS = [
    r"chữa khỏi\s*(?:100%|hoàn toàn|triệt để)",
    r"trị dứt điểm",
    r"cam kết khỏi bệnh",
    r"thay thế thuốc chữa bệnh",
    r"thần dược",
    r"thuốc tiên",
    r"chữa ung thư",
    r"chữa bách bệnh",
    r"đặc trị\s+[a-zA-ZÀ-ỹ0-9_]+",
    r"khỏi hẳn\s*(?:ngay|sau)",
    r"vĩnh viễn không tái phát",
]

PROHIBITED_ABSOLUTE_CLAIMS = [
    r"cam kết\s*(?:tuyệt đối|100%|vĩnh viễn)",
    r"hiệu quả tức thì sau\s*(?:1|2|3)\s*giây",
    r"tốt nhất thế giới",
    r"số 1 việt nam",
    r"an toàn tuyệt đối",
    r"cam kết hiệu quả 100%",
    r"hoàn tiền 100% nếu không khỏi",
    r"duy nhất tại việt nam",
]

PROHIBITED_DEFAMATION = [
    r"tẩy chay\s+[a-zA-ZÀ-ỹ0-9_]+",
    r"hàng rác rưởi",
    r"lừa đảo trắng trợn",
    r"đừng mua đồ của\s+[a-zA-ZÀ-ỹ0-9_]+",
]

FAKE_SCARCITY_PATTERNS = [
    r"chỉ còn duy nhất\s*(?:1|2|3)\s*(?:suất|cái|chiếc|đơn)",
    r"hôm nay duy nhất",
    r"cơ hội cuối cùng trong đời",
    r"chỉ dành cho\s*(?:1|2|3)\s*người đầu tiên",
]


class ComplianceViolation(BaseModel):
    category: str
    pattern: str
    severity: str = "CRITICAL"  # CRITICAL, WARNING
    message: str
    suggested_replacement: str = ""


class ComplianceResult(BaseModel):
    passed: bool
    warnings: List[str] = Field(default_factory=list)
    modified_text: str = ""
    violations: List[ComplianceViolation] = Field(default_factory=list)
    disclosure_added: bool = False


def check_and_clean_script(
    text: str,
    is_affiliate: bool = True,
) -> ComplianceResult:
    """Enforce commercial advertisement compliance & affiliate disclosure."""
    warnings: List[str] = []
    violations: List[ComplianceViolation] = []
    clean_text = text
    disclosure_added = False

    # 1. Check medical claims
    for pat in PROHIBITED_MEDICAL_CLAIMS:
        if re.search(pat, clean_text, re.I):
            msg = f"Phát hiện tuyên bố y tế bị cấm theo chính sách quảng cáo: '{pat}'"
            warnings.append(msg)
            violations.append(
                ComplianceViolation(
                    category="medical_claim",
                    pattern=pat,
                    severity="CRITICAL",
                    message=msg,
                    suggested_replacement="hỗ trợ cải thiện",
                )
            )
            clean_text = re.sub(pat, "hỗ trợ cải thiện", clean_text, flags=re.I)

    # 2. Check absolute claims
    for pat in PROHIBITED_ABSOLUTE_CLAIMS:
        if re.search(pat, clean_text, re.I):
            msg = f"Phát hiện cam kết tuyệt đối bị cấm: '{pat}'"
            warnings.append(msg)
            violations.append(
                ComplianceViolation(
                    category="absolute_claim",
                    pattern=pat,
                    severity="CRITICAL",
                    message=msg,
                    suggested_replacement="mang lại trải nghiệm hiệu quả",
                )
            )
            clean_text = re.sub(pat, "mang lại trải nghiệm hiệu quả", clean_text, flags=re.I)

    # 3. Check defamation
    for pat in PROHIBITED_DEFAMATION:
        if re.search(pat, clean_text, re.I):
            msg = f"Phát hiện ngôn từ hạ thấp thương hiệu khác: '{pat}'"
            warnings.append(msg)
            violations.append(
                ComplianceViolation(
                    category="defamation",
                    pattern=pat,
                    severity="CRITICAL",
                    message=msg,
                    suggested_replacement="sản phẩm thông thường khác",
                )
            )
            clean_text = re.sub(pat, "sản phẩm thông thường khác", clean_text, flags=re.I)

    # 4. Check fake scarcity
    for pat in FAKE_SCARCITY_PATTERNS:
        if re.search(pat, clean_text, re.I):
            msg = f"Cảnh báo tính khan hiếm giả tạo: '{pat}'"
            warnings.append(msg)
            violations.append(
                ComplianceViolation(
                    category="fake_scarcity",
                    pattern=pat,
                    severity="WARNING",
                    message=msg,
                    suggested_replacement="số lượng ưu đãi có hạn",
                )
            )
            clean_text = re.sub(pat, "số lượng ưu đãi có hạn", clean_text, flags=re.I)

    # 5. Mandatory affiliate disclosure
    if is_affiliate:
        disclosure_tags = ["#affiliate", "#quangcao", "#tiepthilienket", "#sponsored"]
        has_disclosure = any(tag in clean_text.lower() for tag in disclosure_tags)
        if not has_disclosure:
            clean_text += "\n\n(Video có gắn link tiếp thị liên kết #affiliate #quangcao)"
            warnings.append("Đã tự động bổ sung nhãn tiếp thị liên kết (#affiliate #quangcao).")
            disclosure_added = True

    has_critical = any(v.severity == "CRITICAL" for v in violations)
    passed = not has_critical and len([w for w in warnings if "bị cấm" in w]) == 0

    return ComplianceResult(
        passed=passed,
        warnings=warnings,
        modified_text=clean_text.strip(),
        violations=violations,
        disclosure_added=disclosure_added,
    )
