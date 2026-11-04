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
    r"chữa ung thư",
    r"chữa bách bệnh",
]

PROHIBITED_ABSOLUTE_CLAIMS = [
    r"cam kết\s*(?:tuyệt đối|100%|vĩnh viễn)",
    r"hiệu quả tức thì sau\s*(?:1|2|3)\s*giây",
    r"tốt nhất thế giới",
    r"số 1 việt nam",
]

PROHIBITED_DEFAMATION = [
    r"tẩy chay\s+[a-zA-Z0-9_]+",
    r"hàng rác rưởi",
    r"lừa đảo trắng trợn",
]

FAKE_SCARCITY_PATTERNS = [
    r"chỉ còn duy nhất\s*(?:1|2|3)\s*(?:suất|cái|chiếc)",
    r"hôm nay duy nhất",
]


class ComplianceResult(BaseModel):
    passed: bool
    warnings: List[str] = Field(default_factory=list)
    modified_text: str = ""


def check_and_clean_script(
    text: str,
    is_affiliate: bool = True,
) -> ComplianceResult:
    """Enforce commercial advertisement compliance & affiliate disclosure."""
    warnings: List[str] = []
    clean_text = text

    # 1. Check medical claims
    for pat in PROHIBITED_MEDICAL_CLAIMS:
        if re.search(pat, clean_text, re.I):
            warnings.append(f"Phát hiện tuyên bố y tế bị cấm theo chính sách quảng cáo: '{pat}'")
            clean_text = re.sub(pat, "hỗ trợ cải thiện", clean_text, flags=re.I)

    # 2. Check absolute claims
    for pat in PROHIBITED_ABSOLUTE_CLAIMS:
        if re.search(pat, clean_text, re.I):
            warnings.append(f"Phát hiện cam kết tuyệt đối bị cấm: '{pat}'")
            clean_text = re.sub(pat, "mang lại trải nghiệm hiệu quả", clean_text, flags=re.I)

    # 3. Check defamation
    for pat in PROHIBITED_DEFAMATION:
        if re.search(pat, clean_text, re.I):
            warnings.append(f"Phát hiện ngôn từ hạ thấp thương hiệu khác: '{pat}'")
            clean_text = re.sub(pat, "sản phẩm thông thường khác", clean_text, flags=re.I)

    # 4. Check fake scarcity
    for pat in FAKE_SCARCITY_PATTERNS:
        if re.search(pat, clean_text, re.I):
            warnings.append(f"Cảnh báo tính khan hiếm giả tạo: '{pat}'")

    # 5. Mandatory affiliate disclosure
    if is_affiliate:
        disclosure_tags = ["#affiliate", "#quangcao", "#tiepthilienket"]
        has_disclosure = any(tag in clean_text.lower() for tag in disclosure_tags)
        if not has_disclosure:
            clean_text += "\n\n(Video có gắn link tiếp thị liên kết #affiliate #quangcao)"
            warnings.append("Đã tự động bổ sung nhãn tiếp thị liên kết (#affiliate #quangcao).")

    return ComplianceResult(
        passed=len([w for w in warnings if "bị cấm" in w]) == 0,
        warnings=warnings,
        modified_text=clean_text.strip(),
    )
