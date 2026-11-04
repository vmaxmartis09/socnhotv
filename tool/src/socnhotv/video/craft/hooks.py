"""Hook Lab: Generation and Heuristic Scoring for Video Opening Hooks.

Generates A/B/C hook variants based on proven retention archetypes (Confession, Paradox, Numbers/Proof)
and scores them using measurable heuristic rules (word count, reading speed, greeting penalties,
visual keywords).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import List, Dict, Any, Optional

GREETING_PATTERNS = [
    r"^(xin\s+)?chào(\s+cả\s+nhà|\s+mọi\s+người|\s+các\s+bạn)?",
    r"^(hello|hi)(\s+everyone|\s+các\s+bạn)?",
    r"^hôm\s+nay\s+(mình|em|tôi|chúng\s+mình)(\s+sẽ|\s+chia\s+sẻ|\s+muốn|\s+làm)?",
    r"^ngày\s+mới\s+chúc",
]

SURPRISE_KEYWORDS = [
    "thật ra", "sự thật", "bí mật", "đừng tin", "không phải", "đố bạn",
    "nghịch lý", "ai ngờ", "chưa từng", "bất ngờ", "tại sao", "vì sao",
    "chỉ mất", "tiết lộ", "lần đầu", "cảnh báo", "sai lầm"
]

VISUAL_KEYWORDS = [
    "nhìn", "xem", "thấy", "màu", "cầu vồng", "lung linh", "nét", "đẹp",
    "ảnh", "vải", "mặt", "trời mưa", "ánh sáng", "chiếc đầm", "áo", "da"
]

@dataclass
class HookScore:
    total_score: float  # 0 to 100
    word_count: int
    estimated_duration_sec: float
    has_greeting_penalty: bool
    has_surprise_element: bool
    has_visual_element: bool
    penalties: List[str] = field(default_factory=list)
    bonuses: List[str] = field(default_factory=list)

@dataclass
class HookVariant:
    variant_id: str  # "A", "B", "C"
    archetype: str   # "confession", "paradox_question", "numbers_proof"
    text: str
    score: HookScore
    reasoning: str

@dataclass
class HookLabResult:
    topic: str
    variants: List[HookVariant]
    best_variant_id: str
    selected_hook: str

def score_hook(text: str) -> HookScore:
    """Scores a hook text using transparent, deterministic heuristic rules."""
    text_clean = text.strip()
    words = re.findall(r"\w+", text_clean.lower())
    word_count = len(words)
    # Average speaking rate in Vietnamese short videos: ~3.8 words/sec
    duration_sec = round(word_count / 3.8, 2)

    base_score = 60.0
    penalties = []
    bonuses = []
    has_greeting = False
    has_surprise = False
    has_visual = False

    # Check for greeting penalty
    text_lower = text_clean.lower()
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, text_lower):
            has_greeting = True
            base_score -= 35.0
            penalties.append("Trừ điểm: Mở đầu bằng lời chào xã giao làm giảm tỷ lệ giữ chân 3s")
            break

    # Length / word count evaluation
    if word_count == 0:
        return HookScore(0.0, 0, 0.0, False, False, False, ["Hook rỗng"], [])

    if word_count <= 12:
        base_score += 15.0
        bonuses.append(f"Cộng điểm: Độ dài lý tưởng (≤12 từ: {word_count} từ, ~{duration_sec}s)")
    elif word_count <= 16:
        base_score += 5.0
        bonuses.append(f"Chấp nhận được: {word_count} từ (~{duration_sec}s)")
    else:
        over = word_count - 16
        penalty_val = min(30.0, over * 4.0)
        base_score -= penalty_val
        penalties.append(f"Trừ điểm: Hook quá dài ({word_count} từ, ~{duration_sec}s > 3.5s)")

    # Surprise element
    for kw in SURPRISE_KEYWORDS:
        if kw in text_lower:
            has_surprise = True
            base_score += 15.0
            bonuses.append(f"Cộng điểm: Chứa yếu tố bất ngờ/kích thích trí tò mò ('{kw}')")
            break

    # Visual element
    for kw in VISUAL_KEYWORDS:
        if kw in text_lower:
            has_visual = True
            base_score += 10.0
            bonuses.append(f"Cộng điểm: Có từ ngữ gợi hình/thị giác ('{kw}')")
            break

    # Punctuation check (exclamation or question mark adds engagement)
    if any(p in text_clean for p in ["?", "!"]):
        base_score += 5.0
        bonuses.append("Cộng điểm: Có dấu câu biểu cảm (! hoặc ?)")

    total_score = max(0.0, min(100.0, base_score))
    return HookScore(
        total_score=round(total_score, 1),
        word_count=word_count,
        estimated_duration_sec=duration_sec,
        has_greeting_penalty=has_greeting,
        has_surprise_element=has_surprise,
        has_visual_element=has_visual,
        penalties=penalties,
        bonuses=bonuses,
    )

def generate_hook_variants(topic: str, context: str = "", character: str = "soc-nho") -> HookLabResult:
    """Generates 3 distinct hook variants (A/B/C) based on proven craft archetypes."""
    topic_clean = topic.strip()
    
    if character == "soc-nho":
        # Kid-science cartoon tone
        var_a_text = f"Đố các bạn biết, bí mật đằng sau {topic_clean} thật ra là gì?"
        var_b_text = f"Đừng tin những gì bạn thấy! Sự thật về {topic_clean} sẽ làm bạn bất ngờ!"
        var_c_text = f"Bi vừa phát hiện ra {topic_clean} kỳ diệu lắm nè, xem ngay nhé!"
    else:
        # KOC / e-commerce tone
        var_a_text = f"Thú thật là lúc đầu mình không tin {topic_clean} lại xịn thế này!"
        var_b_text = f"Đừng vội mua nếu bạn chưa biết bí mật này về {topic_clean}!"
        var_c_text = f"90% mọi người hiểu sai về {topic_clean}, xem ngay để không hối hận!"

    # Score each variant
    score_a = score_hook(var_a_text)
    score_b = score_hook(var_b_text)
    score_c = score_hook(var_c_text)

    variants = [
        HookVariant(
            variant_id="A",
            archetype="paradox_question",
            text=var_a_text,
            score=score_a,
            reasoning="Khai thác tính tò mò và câu đố tương tác trực tiếp",
        ),
        HookVariant(
            variant_id="B",
            archetype="confession_warning",
            text=var_b_text,
            score=score_b,
            reasoning="Cảnh báo đảo ngược định kiến (Pattern Interrupt)",
        ),
        HookVariant(
            variant_id="C",
            archetype="first_person_discovery",
            text=var_c_text,
            score=score_c,
            reasoning="Trải nghiệm khám phá chân thực tự nhiên",
        ),
    ]

    # Select best variant by score
    best_variant = max(variants, key=lambda v: v.score.total_score)

    return HookLabResult(
        topic=topic_clean,
        variants=variants,
        best_variant_id=best_variant.variant_id,
        selected_hook=best_variant.text,
    )
