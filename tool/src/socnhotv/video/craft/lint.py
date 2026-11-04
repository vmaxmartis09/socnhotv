"""Creative QA / Video Craft Lint Engine.

Performs deterministic rule-based checks on video scripts, compositions, and social captions
to ensure maximum viewer retention and strict compliance with platform standards.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import List, Dict, Any, Optional

@dataclass
class Issue:
    level: str  # "error", "warning", "info"
    rule_id: str
    message_vi: str
    technique_ref: str
    suggestion_vi: Optional[str] = None

@dataclass
class LintReport:
    total_checks: int
    error_count: int
    warning_count: int
    info_count: int
    passed: bool
    issues: List[Issue] = field(default_factory=list)

def lint_script(
    script_text: str,
    duration_sec: Optional[float] = None,
    platform: str = "tiktok"
) -> LintReport:
    """Lints script content against retention rules, hook length, and CTA presence."""
    issues: List[Issue] = []
    lines = [line.strip() for line in script_text.splitlines() if line.strip()]
    
    if not lines:
        issues.append(Issue(
            level="error",
            rule_id="RULE_EMPTY_SCRIPT",
            message_vi="Kịch bản trống không có nội dung.",
            technique_ref="evergreen-shortform-foundations"
        ))
        return LintReport(1, 1, 0, 0, False, issues)

    # 1. Hook check (First line)
    hook_text = lines[0]
    words_in_hook = re.findall(r"\w+", hook_text.lower())
    hook_word_count = len(words_in_hook)
    est_hook_duration = round(hook_word_count / 3.8, 2)

    # Greeting check
    greeting_match = re.search(r"^(chào|hello|hi\b|hôm nay mình|xin chào)", hook_text.lower())
    if greeting_match:
        issues.append(Issue(
            level="error",
            rule_id="RULE_NO_GREETINGS",
            message_vi=f"Hook mở đầu bằng lời chào xã giao ('{greeting_match.group(0)}'). Người xem sẽ lướt qua trong 1 giây.",
            technique_ref="confession-hook",
            suggestion_vi="Vào thẳng vấn đề hoặc bí mật bất ngờ, bỏ hoàn toàn lời chào ở đầu video."
        ))

    if hook_word_count > 16 or est_hook_duration > 3.5:
        issues.append(Issue(
            level="warning",
            rule_id="RULE_HOOK_DURATION",
            message_vi=f"Hook quá dài ({hook_word_count} từ, ~{est_hook_duration}s > 3.0s chuẩn).",
            technique_ref="pre-publish-hook-retention-prediction",
            suggestion_vi="Gọt giũa hook xuống dưới 12 từ để truyền tải thông điệp trong 3 giây đầu."
        ))

    # 2. CTA check (Call to Action in concluding portion of text)
    # Take the last 3 lines or last 40% of text
    concluding_lines = lines[-2:] if len(lines) >= 2 else lines
    concluding_text = " ".join(concluding_lines).lower()
    
    cta_patterns = [
        r"(hãy|nhớ|đừng quên)\s+chia sẻ", r"bình luận", r"comment",
        r"bấm theo dõi", r"follow", r"đón xem", r"đăng ký", r"link",
        r"ghim", r"xem ngay", r"bạn nghĩ sao", r"để lại ý kiến"
    ]
    has_cta = any(re.search(pat, concluding_text) for pat in cta_patterns)
    if not has_cta:
        issues.append(Issue(
            level="warning",
            rule_id="RULE_HAS_CTA",
            message_vi="Kịch bản chưa có lời kêu gọi hành động (CTA) rõ ràng ở phần kết.",
            technique_ref="3-layer-knowledge-retention",
            suggestion_vi="Thêm câu hỏi kích thích tương tác hoặc điều hướng vào bình luận đầu tiên."
        ))

    # 3. Duration check
    if duration_sec is not None:
        if platform in {"tiktok", "shorts", "reels"}:
            if duration_sec > 60.0:
                issues.append(Issue(
                    level="warning",
                    rule_id="RULE_PLATFORM_DURATION",
                    message_vi=f"Thời lượng video ({duration_sec}s) vượt quá mức tối ưu của video ngắn (15s - 50s).",
                    technique_ref="evergreen-shortform-foundations",
                    suggestion_vi="Cân nhắc cô đọng nội dung hoặc cắt thành series tập."
                ))
            elif duration_sec < 5.0:
                issues.append(Issue(
                    level="error",
                    rule_id="RULE_TOO_SHORT",
                    message_vi=f"Thời lượng video quá ngắn ({duration_sec}s < 5s).",
                    technique_ref="evergreen-shortform-foundations"
                ))

    err_count = sum(1 for i in issues if i.level == "error")
    warn_count = sum(1 for i in issues if i.level == "warning")
    info_count = sum(1 for i in issues if i.level == "info")

    return LintReport(
        total_checks=5,
        error_count=err_count,
        warning_count=warn_count,
        info_count=info_count,
        passed=(err_count == 0),
        issues=issues
    )

def lint_caption(caption_text: str, has_affiliate: bool = False) -> LintReport:
    """Lints social post caption for link hygiene and affiliate disclosure."""
    issues: List[Issue] = []

    # Check for raw external URLs in caption
    url_pattern = r"(https?://\S+|bit\.ly/\S+|shopee\.vn/\S+)"
    raw_urls = re.findall(url_pattern, caption_text)
    if raw_urls:
        issues.append(Issue(
            level="error",
            rule_id="RULE_NO_LINK_IN_CAPTION",
            message_vi=f"Phát hiện liên kết trực tiếp trong caption ({raw_urls[0]}). Thuật toán sẽ bóp lượt tiếp cận tự nhiên.",
            technique_ref="first-comment-link-routing",
            suggestion_vi="Chuyển liên kết vào bình luận đầu tiên ghim (Pinned First Comment), caption chỉ ghi 'xem link ở bình luận ghim'."
        ))

    # Check for affiliate disclosure
    if has_affiliate:
        disclosure_pattern = r"(affiliate|tiếp thị liên kết|tài trợ|sponsored|quảng cáo)"
        if not re.search(disclosure_pattern, caption_text.lower()):
            issues.append(Issue(
                level="warning",
                rule_id="RULE_AFFILIATE_DISCLOSURE",
                message_vi="Bài viết tiếp thị chưa có câu thông báo minh bạch tài trợ / affiliate.",
                technique_ref="first-comment-link-routing",
                suggestion_vi="Thêm ghi chú: '*(Bài viết có chứa liên kết tiếp thị - Affiliate link)*'."
            ))

    err_count = sum(1 for i in issues if i.level == "error")
    warn_count = sum(1 for i in issues if i.level == "warning")
    info_count = sum(1 for i in issues if i.level == "info")

    return LintReport(
        total_checks=3,
        error_count=err_count,
        warning_count=warn_count,
        info_count=info_count,
        passed=(err_count == 0),
        issues=issues
    )

def lint_composition(composition_meta: Dict[str, Any]) -> LintReport:
    """Lints HyperFrames composition structure, cut rhythm, and safe-zones."""
    issues: List[Issue] = []
    scenes = composition_meta.get("scenes", [])

    # Check cut rhythm
    for idx, sc in enumerate(scenes):
        dur = sc.get("duration", 0)
        if dur > 5.5:
            issues.append(Issue(
                level="warning",
                rule_id="RULE_SCENE_TOO_LONG",
                message_vi=f"Cảnh {idx+1} quá dài ({dur}s > 5.0s) mà không có chuyển động camera hoặc b-roll bổ trợ.",
                technique_ref="evergreen-shortform-foundations",
                suggestion_vi="Chia nhỏ cảnh thành các góc máy khác nhau hoặc bổ sung hiệu ứng push-in."
            ))

    # Check safe zone compliance
    elements = composition_meta.get("elements", [])
    for el in elements:
        y_pos = el.get("y", 0)
        el_type = el.get("type", "")
        # TikTok Safe Zone: Top 180px, Bottom 320px in 1920 height
        if el_type in {"text", "subtitle", "button"}:
            if y_pos < 180:
                issues.append(Issue(
                    level="warning",
                    rule_id="RULE_SAFE_ZONE_TOP",
                    message_vi=f"Phần tử '{el_type}' nằm quá sát đỉnh (y={y_pos} < 180px), có nguy cơ bị thanh tìm kiếm che mất.",
                    technique_ref="evergreen-shortform-foundations"
                ))
            elif y_pos > (1920 - 320):
                issues.append(Issue(
                    level="warning",
                    rule_id="RULE_SAFE_ZONE_BOTTOM",
                    message_vi=f"Phần tử '{el_type}' nằm quá sát đáy (y={y_pos} > 1600px), có nguy cơ bị icon giỏ hàng và caption che mất.",
                    technique_ref="evergreen-shortform-foundations"
                ))

    err_count = sum(1 for i in issues if i.level == "error")
    warn_count = sum(1 for i in issues if i.level == "warning")
    info_count = sum(1 for i in issues if i.level == "info")

    return LintReport(
        total_checks=len(scenes) + len(elements),
        error_count=err_count,
        warning_count=warn_count,
        info_count=info_count,
        passed=(err_count == 0),
        issues=issues
    )
