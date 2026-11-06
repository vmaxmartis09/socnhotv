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
        "references": [
            {k: str(v) for k, v in r.items() if k in ("url", "title", "kind", "fetchedAt", "excerpt")}
            for r in policy.get("references", [])
            if isinstance(r, dict) and r.get("url")
        ],
        "documents": [
            {k: v for k, v in d.items() if k in ("id", "name", "file", "chars", "sha", "sections", "importedAt")}
            for d in policy.get("documents", [])
            if isinstance(d, dict) and d.get("file")
        ],
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
                **({"source": str(r["source"])} if r.get("source") else {}),
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


# ---------------------------------------------------------------------------
# Gói chính sách chuẩn của nền tảng, nhập từ tệp, lấy từ URL
# ---------------------------------------------------------------------------

def packs_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "shared" / "policy_packs"


def list_packs(repo_root: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    d = packs_dir(repo_root)
    for f in sorted(d.glob("*.json")) if d.is_dir() else []:
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append(
            {
                "id": p.get("id", f.stem),
                "name": p.get("name", f.stem),
                "platform": p.get("platform", ""),
                "sourceUrl": p.get("sourceUrl", ""),
                "description": p.get("description", ""),
                "ruleCount": len(p.get("rules", [])),
            }
        )
    return out


def load_pack(repo_root: Path, pack_id: str) -> Optional[Dict[str, Any]]:
    if not re.fullmatch(r"[a-z0-9_-]+", pack_id or ""):
        return None
    f = packs_dir(repo_root) / f"{pack_id}.json"
    if not f.is_file():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def merge_rules(policy: Dict[str, Any], rules: List[Dict[str, Any]], source: str) -> Dict[str, Any]:
    """Gộp quy tắc vào chính sách: cùng id thì ghi đè, đánh dấu nguồn (pack:/upload:)."""
    out = deepcopy(policy)
    by_id = {r.get("id"): i for i, r in enumerate(out["rules"])}
    for r in rules:
        rid = f"{source}:{r.get('id')}"
        item = {**r, "id": rid, "source": source}
        if rid in by_id:
            out["rules"][by_id[rid]] = item
        else:
            out["rules"].append(item)
            by_id[rid] = len(out["rules"]) - 1
    return out


def import_pack(policy: Dict[str, Any], pack: Dict[str, Any]) -> Dict[str, Any]:
    out = merge_rules(policy, pack.get("rules", []), f"pack-{pack.get('id', 'x')}")
    refs = [r for r in out.get("references", []) if r.get("url") != pack.get("sourceUrl")]
    if pack.get("sourceUrl"):
        refs.append({"url": pack["sourceUrl"], "title": pack.get("name", ""), "kind": "pack", "fetchedAt": ""})
    out["references"] = refs
    return out


def parse_policy_text(filename: str, text: str) -> List[Dict[str, Any]]:
    """Đọc tệp chính sách tải lên → danh sách quy tắc.

    Hỗ trợ: .json (policy đầy đủ {rules:[...]}, hoặc mảng chuỗi / mảng quy tắc),
    văn bản (.txt/.md/.csv): mỗi dòng một từ; '# Nhóm' hoặc 'Nhóm: từ1, từ2' để đặt nhóm.
    """
    name = (filename or "").lower()
    rules: List[Dict[str, Any]] = []

    def mk(category: str, terms: List[str], severity: str = "block") -> None:
        terms = [t.strip() for t in terms if t.strip()]
        if not terms:
            return
        rid = re.sub(r"[^a-z0-9]+", "_", _norm(category)).strip("_") or f"nhom_{len(rules) + 1}"
        for r in rules:
            if r["id"] == rid:
                r["terms"].extend(terms)
                return
        rules.append(
            {"id": rid, "category": category, "label": category, "severity": severity, "enabled": True, "terms": terms, "note": ""}
        )

    if name.endswith(".json"):
        data = json.loads(text)
        if isinstance(data, dict) and isinstance(data.get("rules"), list):
            for r in data["rules"]:
                mk_terms = [str(t) for t in r.get("terms", [])]
                mk(str(r.get("category") or r.get("label") or "Tải lên"), mk_terms, "warn" if r.get("severity") == "warn" else "block")
                if rules:
                    rules[-1]["label"] = str(r.get("label") or rules[-1]["label"])
                    rules[-1]["note"] = str(r.get("note") or "")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    mk("Tải lên", [item])
                elif isinstance(item, dict):
                    mk(str(item.get("category") or "Tải lên"), [str(t) for t in item.get("terms", [])], "warn" if item.get("severity") == "warn" else "block")
        return rules

    cat = "Tải lên"
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip().lstrip("\ufeff")
        if not line:
            continue
        if line.startswith("#"):
            cat = line.lstrip("#").strip() or cat
            continue
        if ":" in line and not line.startswith(("http://", "https://")):
            head, _, tail = line.partition(":")
            if 0 < len(head) <= 40:
                mk(head.strip(), re.split(r"[,;|]", tail))
                continue
        mk(cat, re.split(r"[,;|]" if "," in line or ";" in line or "|" in line else r"\n", line.lstrip("-*• ").strip()))
    return rules


def _is_public_host(host: str) -> bool:
    import ipaddress
    import socket

    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


def fetch_policy_page(url: str, max_bytes: int = 1_500_000, timeout: float = 12.0) -> Dict[str, Any]:
    """Tải trang chính sách công khai (https), trả về tiêu đề + văn bản thuần. Chặn địa chỉ nội bộ (SSRF)."""
    import html as _html
    import urllib.request
    from urllib.parse import urlparse

    u = urlparse(url)
    if u.scheme != "https" or not u.hostname:
        raise ValueError("Chỉ hỗ trợ đường dẫn https.")
    if not _is_public_host(u.hostname):
        raise ValueError("Không truy cập được địa chỉ này (nội bộ hoặc không phân giải được).")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; PolicyFetcher/1.0)", "Accept-Language": "vi,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - https + host đã kiểm tra
        raw = resp.read(max_bytes)
        charset = resp.headers.get_content_charset() or "utf-8"
    page = raw.decode(charset, errors="replace")
    title_m = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
    body = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", page)
    body = re.sub(r"(?s)<br\s*/?>|</p>|</li>|</h\d>|</div>", "\n", body)
    text = _html.unescape(re.sub(r"<[^>]+>", " ", body))
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return {
        "url": url,
        "title": _html.unescape(title_m.group(1)).strip() if title_m else u.hostname,
        "text": text[:60000],
        "chars": len(text),
    }


def looks_like_prose(text: str) -> bool:
    """Tệp là văn bản chính sách dạng văn xuôi (như trang chính sách YouTube), không phải danh sách từ cấm.

    Danh sách từ: nhiều dòng ngắn. Văn xuôi: dòng dài, nhiều câu. Nhập văn xuôi như danh sách từ sẽ sinh hàng
    nghìn 'từ cấm' vô nghĩa và chặn mọi nội dung, nên phải tách riêng thành tài liệu."""
    lines = [l.strip() for l in text.replace("\r\n", "\n").split("\n") if l.strip()]
    if not lines:
        return False
    # Danh sách từ cấm: dòng ngắn (vài từ). Văn xuôi: phần lớn dòng có từ 8 từ trở lên.
    wordy = sum(1 for l in lines if len(l.split()) >= 8)
    return len(text) > 4000 and wordy / len(lines) > 0.4


def extract_sections(text: str, limit: int = 60) -> List[str]:
    """Các mục (tiêu đề markdown) của tài liệu chính sách, bỏ ký tự thoát."""
    out: List[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip().replace("\\", "")
        m = re.match(r"^(#{1,4})\s+(.+)$", line)
        if not m:
            continue
        title = re.sub(r"[*_`]+", "", m.group(2)).strip(" -=#")
        if title and title not in out and not title.lower().startswith(("source", "thu thap", "ngay thu")):
            out.append(title[:120])
        if len(out) >= limit:
            break
    return out


def document_dir(repo_root: Path, project_id: str) -> Path:
    return repo_root / "data" / "projects" / project_id / "policy"


def add_document(repo_root: Path, project_id: str, name: str, text: str) -> Dict[str, Any]:
    """Lưu tệp chính sách văn xuôi vào policy/<tên>.md của dự án và ghi vào policy.json (documents)."""
    import hashlib
    import time as _time

    stem = re.sub(r"[^a-z0-9]+", "-", _norm(Path(name).stem)).strip("-") or "chinh-sach"
    d = document_dir(repo_root, project_id)
    d.mkdir(parents=True, exist_ok=True)
    fn = f"{stem}.md"
    (d / fn).write_text(text, encoding="utf-8")
    doc = {
        "id": stem,
        "name": Path(name).stem,
        "file": f"policy/{fn}",
        "chars": len(text),
        "sha": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
        "sections": extract_sections(text),
        "importedAt": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
    }
    pol = load_policy(repo_root, project_id)
    docs = [x for x in pol.get("documents", []) if x.get("id") != stem] + [doc]
    pol["documents"] = docs
    save_policy(repo_root, project_id, pol)
    return doc


def read_documents(repo_root: Path, project_id: str, policy: Dict[str, Any], max_chars: int = 24000) -> str:
    """Nội dung các tệp chính sách văn xuôi (cắt gọn) để đưa cho model kiểm định."""
    parts: List[str] = []
    for d in policy.get("documents", []):
        f = repo_root / "data" / "projects" / project_id / str(d.get("file", ""))
        try:
            parts.append(f"## {d.get('name')}\n" + f.read_text(encoding="utf-8", errors="replace").replace("\\", ""))
        except OSError:
            continue
    return "\n\n".join(parts)[:max_chars]


def add_reference(policy: Dict[str, Any], ref: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(policy)
    refs = [r for r in out.get("references", []) if r.get("url") != ref.get("url")]
    refs.append(ref)
    out["references"] = refs
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
    # Bỏ trùng (cùng nguồn + cùng từ + cùng ngữ cảnh) khi nhiều quy tắc/gói cùng chứa một từ; giữ mức nặng nhất
    best: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for v in violations:
        key = (v["source"], v["term"].lower(), v["snippet"])
        if key not in best or (v["severity"] == "block" and best[key]["severity"] != "block"):
            best[key] = v
    violations = list(best.values())
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
