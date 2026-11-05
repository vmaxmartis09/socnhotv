"""Chính sách nội dung xuyên suốt dự án + bộ kiểm định lời nói / caption / kịch bản.

Policy (lưu ở data/projects/<id>/policy.json):
  name, mode: "strict" (mọi vi phạm đều chặn) | "standard" (chỉ vi phạm mức 'block' chặn)
  scopes: {dialogue, caption, script, prompt}  — nơi được kiểm
  rules[{id, category, label, severity: "block"|"warn", enabled, terms[], note}]
  allowlist[]  — cụm từ được phép dù khớp một quy tắc

Khớp không phân biệt hoa/thường, GIỮ dấu tiếng Việt (nhập thêm biến thể không dấu nếu cần), theo ranh giới từ.
"""

from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_POLICY: Dict[str, Any] = {
    "name": "Chính sách nội dung trẻ em (Made for Kids)",
    "mode": "standard",
    "scopes": {"dialogue": True, "caption": True, "script": True, "prompt": True},
    "allowlist": [],
    "rules": [
        {
            "id": "violence",
            "category": "Bạo lực",
            "label": "Bạo lực, gây thương tích",
            "severity": "block",
            "enabled": True,
            "terms": ["giết", "đánh nhau", "đấm", "đá vào mặt", "máu me", "đổ máu", "tra tấn", "dao găm", "súng", "bắn chết", "kill", "gore", "blood"],
            "note": "Nội dung dành cho trẻ 3–7 tuổi: không mô tả hoặc cổ xuý bạo lực.",
        },
        {
            "id": "scary",
            "category": "Gây sợ hãi",
            "label": "Kinh dị, đáng sợ",
            "severity": "warn",
            "enabled": True,
            "terms": ["ma quỷ", "kinh dị", "xác chết", "rùng rợn", "ác mộng kinh hoàng", "horror"],
            "note": "Tránh gây ám ảnh; nếu cần (vd. bài học sợ bóng tối) phải xử lý nhẹ nhàng.",
        },
        {
            "id": "adult",
            "category": "Người lớn",
            "label": "Nội dung người lớn",
            "severity": "block",
            "enabled": True,
            "terms": ["khiêu dâm", "sex", "làm tình", "nude", "khỏa thân", "18+"],
            "note": "",
        },
        {
            "id": "profanity",
            "category": "Thô tục",
            "label": "Chửi thề, lăng mạ",
            "severity": "block",
            "enabled": True,
            "terms": ["đồ ngu", "ngu ngốc", "đm", "đ.m", "chết tiệt", "khốn nạn", "đồ điên", "stupid", "idiot", "damn"],
            "note": "Tránh lời lẽ xúc phạm; dùng cách nói ôn hòa.",
        },
        {
            "id": "hate",
            "category": "Phân biệt đối xử",
            "label": "Kỳ thị, miệt thị",
            "severity": "block",
            "enabled": True,
            "terms": ["kỳ thị", "miệt thị", "đồ béo", "đồ lùn", "đồ xấu xí", "dân tộc thấp kém"],
            "note": "",
        },
        {
            "id": "danger",
            "category": "Hành vi nguy hiểm",
            "label": "Hành vi trẻ có thể bắt chước gây nguy hiểm",
            "severity": "warn",
            "enabled": True,
            "terms": ["nhảy từ trên cao", "chơi với lửa", "uống thuốc một mình", "đi một mình ra đường", "đùa với điện", "leo lên mái nhà"],
            "note": "",
        },
        {
            "id": "commercial",
            "category": "Quảng cáo",
            "label": "Quảng cáo, mua bán, thương hiệu",
            "severity": "warn",
            "enabled": True,
            "terms": ["mua ngay", "đặt hàng", "giảm giá", "khuyến mãi", "link bio", "đăng ký kênh ngay"],
            "note": "Made for Kids hạn chế kêu gọi hành động thương mại.",
        },
        {
            "id": "personal",
            "category": "Thông tin cá nhân",
            "label": "Thông tin cá nhân / liên hệ",
            "severity": "block",
            "enabled": True,
            "terms": ["số điện thoại", "địa chỉ nhà", "zalo", "facebook của bé", "gmail.com"],
            "note": "",
        },
    ],
}


def _normalize_with_map(text: str) -> Tuple[str, List[int]]:
    """Chuẩn hoá NFC + hạ chữ thường (GIỮ dấu tiếng Việt để 'tạo' không khớp nhầm 'tao'); ánh xạ vị trí về chuỗi gốc."""
    out: List[str] = []
    idx: List[int] = []
    for i, ch in enumerate(text):
        n = unicodedata.normalize("NFC", ch).lower()
        for c in n:
            out.append(c)
            idx.append(i)
    return "".join(out), idx


def _norm(s: str) -> str:
    return _normalize_with_map(s)[0]


def policy_path(repo_root: Path, project_id: str) -> Path:
    return repo_root / "data" / "projects" / project_id / "policy.json"


def load_policy(repo_root: Path, project_id: str) -> Dict[str, Any]:
    p = policy_path(repo_root, project_id)
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("rules"), list):
                merged = deepcopy(DEFAULT_POLICY)
                merged.update({k: v for k, v in data.items() if k != "scopes"})
                merged["scopes"] = {**DEFAULT_POLICY["scopes"], **(data.get("scopes") or {})}
                return merged
        except Exception:
            pass
    return deepcopy(DEFAULT_POLICY)


def save_policy(repo_root: Path, project_id: str, policy: Dict[str, Any]) -> Dict[str, Any]:
    clean = {
        "name": str(policy.get("name") or DEFAULT_POLICY["name"]),
        "mode": "strict" if policy.get("mode") == "strict" else "standard",
        "scopes": {k: bool((policy.get("scopes") or {}).get(k, True)) for k in DEFAULT_POLICY["scopes"]},
        "allowlist": [str(t).strip() for t in policy.get("allowlist", []) if str(t).strip()],
        "rules": [],
    }
    for r in policy.get("rules", []):
        terms = [str(t).strip() for t in r.get("terms", []) if str(t).strip()]
        clean["rules"].append(
            {
                "id": str(r.get("id") or f"rule_{len(clean['rules']) + 1}"),
                "category": str(r.get("category") or "Khác"),
                "label": str(r.get("label") or r.get("category") or "Quy tắc"),
                "severity": "warn" if r.get("severity") == "warn" else "block",
                "enabled": bool(r.get("enabled", True)),
                "terms": terms,
                "note": str(r.get("note") or ""),
            }
        )
    p = policy_path(repo_root, project_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    return clean


def merge_extra_terms(policy: Dict[str, Any], extra_terms: List[str], severity: str = "block") -> Dict[str, Any]:
    """Thêm quy tắc riêng của node (cục bộ) lên chính sách dự án."""
    terms = [t.strip() for t in extra_terms if t and t.strip()]
    if not terms:
        return policy
    out = deepcopy(policy)
    out["rules"].append(
        {
            "id": "node_extra",
            "category": "Riêng node",
            "label": "Từ khoá bổ sung của node",
            "severity": "warn" if severity == "warn" else "block",
            "enabled": True,
            "terms": terms,
            "note": "",
        }
    )
    return out


def check_texts(texts: Dict[str, str], policy: Dict[str, Any]) -> Dict[str, Any]:
    """Kiểm định các đoạn văn bản (khoá = nguồn, vd. 'dialogue', 'S03.dialogue'). Trả báo cáo vi phạm."""
    allow = [_norm(a) for a in policy.get("allowlist", []) if a]
    violations: List[Dict[str, Any]] = []
    for source, raw in texts.items():
        if not raw:
            continue
        norm, idx = _normalize_with_map(raw)
        for rule in policy.get("rules", []):
            if not rule.get("enabled", True):
                continue
            for term in rule.get("terms", []):
                nt = _norm(term).strip()
                if not nt:
                    continue
                for m in re.finditer(rf"(?<!\w){re.escape(nt)}(?!\w)", norm):
                    # cụm trong allowlist bao trùm vị trí khớp → bỏ qua
                    if any(a and a in norm[max(0, m.start() - 40): m.end() + 40] and nt in a for a in allow):
                        continue
                    s, e = idx[m.start()], idx[m.end() - 1] + 1
                    ctx_s, ctx_e = max(0, s - 24), min(len(raw), e + 24)
                    violations.append(
                        {
                            "source": source,
                            "ruleId": rule.get("id"),
                            "category": rule.get("category"),
                            "label": rule.get("label"),
                            "severity": rule.get("severity", "block"),
                            "term": raw[s:e],
                            "snippet": raw[ctx_s:ctx_e].replace("\n", " "),
                            "note": rule.get("note", ""),
                        }
                    )
    strict = policy.get("mode") == "strict"
    blocking = [v for v in violations if strict or v["severity"] == "block"]
    return {
        "passed": len(blocking) == 0,
        "violations": violations,
        "blockCount": len(blocking),
        "warnCount": len(violations) - len(blocking),
        "checkedSources": list(texts.keys()),
    }


def format_report(report: Dict[str, Any], limit: int = 12) -> str:
    v = report["violations"]
    if not v:
        return "Chính sách: ĐẠT — không có từ ngữ vi phạm."
    head = f"Chính sách: {'KHÔNG ĐẠT' if not report['passed'] else 'CẢNH BÁO'} — {report['blockCount']} vi phạm chặn, {report['warnCount']} cảnh báo."
    lines = [
        f"- [{x['severity'].upper()}] {x['category']}: “{x['term']}” trong {x['source']} …{x['snippet']}…"
        for x in v[:limit]
    ]
    if len(v) > limit:
        lines.append(f"… và {len(v) - limit} mục khác.")
    return head + "\n" + "\n".join(lines)
