"""Kịch bản tập (Markdown chuẩn Sóc Nhỏ TV) → dữ liệu có cấu trúc.

Định nghĩa kiểu dữ liệu `script` (xem ai/rules/node-card-style.md, mục "Chuẩn dữ liệu đầu vào"):

Script
  id, episodeNumber, title, series, season, durationSec, aspect, style
  leadCharacter, cast[{name, heightCm}], setting{name, code, timeOfDay}
  lesson, mantra, summary, environmentPromptLock
  characters[{name, heightCm, species, profile, promptLock}]
  scenes[Scene]
Scene   : index, title, startSec, endSec, location, purpose, shots[Shot]
Shot    : id, sceneIndex, sceneTitle, startSec, endSec, durationSec, shotSize, camera,
          characters[], action, expression, actingNotes, speaker, dialogue, voiceDelivery,
          sfx, bgm, imagePrompt, videoPrompt, negativePrompt
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

FACETS: List[Dict[str, str]] = [
    {"id": "fulltext", "label": "Toàn văn kịch bản", "type": "text"},
    {"id": "summary", "label": "Tóm tắt nội dung", "type": "text"},
    {"id": "lesson", "label": "Bài học cốt lõi", "type": "text"},
    {"id": "mantra", "label": "Câu thần chú", "type": "text"},
    {"id": "dialogue_all", "label": "Lời thoại toàn tập", "type": "text"},
    {"id": "environment", "label": "Prompt khóa bối cảnh", "type": "text"},
    {"id": "scenes", "label": "Danh sách cảnh / shot (scenes)", "type": "scenes"},
    {"id": "script", "label": "Toàn bộ kịch bản có cấu trúc", "type": "script"},
]

SHOT_FACETS: List[Dict[str, str]] = [
    {"id": "dialogue", "label": "Lời thoại"},
    {"id": "imagePrompt", "label": "Image prompt"},
    {"id": "videoPrompt", "label": "Video prompt"},
    {"id": "action", "label": "Hành động trên hình"},
    {"id": "expression", "label": "Biểu cảm"},
]


def _mmss(s: str) -> int:
    m = re.match(r"\s*(\d+):(\d+)", s or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else 0


def _bullets(block: str) -> Dict[str, str]:
    """Các dòng '- **Khóa**: giá trị' (giá trị có thể kéo dài nhiều dòng thụt lề)."""
    out: Dict[str, str] = {}
    cur: Optional[str] = None
    for line in block.splitlines():
        m = re.match(r"^- \*\*(.+?)\*\*\s*[:：]?\s*(.*)$", line)
        if m:
            cur = m.group(1).strip()
            out[cur] = m.group(2).strip()
        elif cur and line.startswith("  "):
            out[cur] = (out[cur] + "\n" + line.strip()).strip()
        elif not line.strip():
            continue
        else:
            cur = None
    return out


def _get(d: Dict[str, str], *prefixes: str) -> str:
    for k, v in d.items():
        if any(k.startswith(p) for p in prefixes):
            return v
    return ""


def _clean(v: str) -> str:
    return re.sub(r"[`*]", "", v).strip().strip('"“”')


def _code_block(text: str) -> str:
    m = re.search(r"```(?:text)?\n(.*?)```", text, re.S)
    return m.group(1).strip() if m else ""


def _section(md: str, pattern: str, level: str) -> str:
    """Nội dung từ tiêu đề khớp `pattern` tới tiêu đề cùng/cấp cao hơn kế tiếp."""
    m = re.search(rf"^{level} {pattern}.*$", md, re.M)
    if not m:
        return ""
    rest = md[m.end():]
    n = len(level)
    nxt = re.search(rf"^#{{1,{n}}} ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def _parse_shot(head: re.Match, body: str, scene_idx: int, scene_title: str) -> Dict[str, Any]:
    meta = head.group("meta")
    sid = head.group("id")
    times = re.search(r"`(\d+:\d+)\s*-\s*(\d+:\d+)`", meta)
    dur = re.search(r"Thời lượng:\s*`(\d+(?:\.\d+)?)s`", meta)
    size = re.search(r"Cỡ cảnh:\s*`([^`]+)`", meta)
    cam = re.search(r"Góc máy:\s*(.+?)\)?$", meta)
    b = _bullets(body)
    start = _mmss(times.group(1)) if times else 0
    end = _mmss(times.group(2)) if times else start
    dialogue_key = next((k for k in b if k.startswith("Lời thoại")), "")
    speaker = _clean(re.sub(r"^Lời thoại\s*\(?", "", dialogue_key).rstrip(")"))
    sfxbgm = _get(b, "Âm thanh")
    sfx = re.search(r"SFX:\s*(.*?)(?:\s*\|\s*BGM:|$)", sfxbgm, re.S)
    bgm = re.search(r"BGM:\s*(.*)$", sfxbgm, re.S)
    prompts = _code_block(body)

    def pick(label: str) -> str:
        m = re.search(rf"^{label}:\s*(.*?)(?=^(?:Image Prompt|Video Prompt|Negative Prompt):|\Z)", prompts, re.S | re.M)
        return m.group(1).strip() if m else ""

    return {
        "id": sid,
        "sceneIndex": scene_idx,
        "sceneTitle": scene_title,
        "startSec": start,
        "endSec": end,
        "durationSec": float(dur.group(1)) if dur else float(max(0, end - start)),
        "shotSize": size.group(1) if size else "",
        "camera": _clean(cam.group(1)) if cam else "",
        "characters": [c.strip() for c in _clean(_get(b, "Nhân vật xuất hiện")).split(",") if c.strip()],
        "action": _clean(_get(b, "Hành động trên hình")),
        "expression": _clean(_get(b, "Biểu cảm")),
        "actingNotes": _clean(_get(b, "Yêu cầu diễn xuất")),
        "speaker": speaker,
        "dialogue": _clean(b.get(dialogue_key, "")),
        "voiceDelivery": _clean(_get(b, "Giọng điệu")),
        "sfx": _clean(sfx.group(1)) if sfx else "",
        "bgm": _clean(bgm.group(1)) if bgm else "",
        "imagePrompt": pick("Image Prompt"),
        "videoPrompt": pick("Video Prompt"),
        "negativePrompt": pick("Negative Prompt"),
    }


def parse_episode_markdown(md: str, episode_id: str = "") -> Dict[str, Any]:
    md = md.replace("\r\n", "\n")
    title_m = re.search(r"^# (.+)$", md, re.M)
    title_line = title_m.group(1).strip() if title_m else episode_id
    num_m = re.search(r"Tập\s*(\d+)\s*[:：]\s*(.*)$", title_line)
    head_block = md.split("\n---", 1)[0]
    meta = _bullets(head_block)

    duration = _get(meta, "Thời lượng")
    dm = re.search(r"(\d+)\s*phút(?:\s*(\d+)\s*giây)?", duration)
    duration_sec = int(dm.group(1)) * 60 + int(dm.group(2) or 0) if dm else 0
    aspect_style = _clean(_get(meta, "Tỉ lệ"))
    aspect, _, style = (p.strip() for p in aspect_style.partition("|"))
    setting_raw = _get(meta, "Bối cảnh chính")
    code = re.search(r"`(\w+)`", setting_raw)
    tod = re.search(r"Thời gian:\s*\*?([^*(\n]+)", setting_raw)
    cast_raw = _clean(_get(meta, "Dàn nhân vật"))
    cast = [
        {"name": re.sub(r"\s*\(\d+\s*cm\)", "", c).strip(), "heightCm": int(h.group(1)) if (h := re.search(r"(\d+)\s*cm", c)) else None}
        for c in re.split(r",\s*(?![^()]*\))", cast_raw)
        if c.strip()
    ]

    summary = _section(md, r"1\. ", "##").strip()
    env_block = _section(md, r"2\.4\.", "###")
    environment = _code_block(env_block)

    # Nhân vật (mục 3.2)
    characters: List[Dict[str, Any]] = []
    chars_sec = _section(md, r"3\.2\.", "###")
    char_re = re.compile(r"^#### 👤 ([^\n]+?)\s*—\s*Loài:\s*([^\n]*)\n(.*?)(?=^#### |\Z)", re.M | re.S)
    for cm in char_re.finditer(chars_sec):
        name_h = cm.group(1).strip()
        hm = re.search(r"\((\d+)\s*cm\)", name_h)
        cb = _bullets(cm.group(3))
        characters.append(
            {
                "name": re.sub(r"\s*\(\d+\s*cm\)", "", name_h).strip(),
                "heightCm": int(hm.group(1)) if hm else None,
                "species": cm.group(2).strip(),
                "personality": _clean(_get(cb, "Tính cách")),
                "catchphrase": _clean(_get(cb, "Câu cửa miệng")),
                "voiceDirection": _clean(_get(cb, "Chỉ dẫn giọng")),
                "do": _clean(_get(cb, "Yêu cầu diễn xuất")),
                "dont": _clean(_get(cb, "Điều cấm kỵ")),
                "promptLock": _code_block(cm.group(3)),
            }
        )

    # Cảnh + shot (mục 4)
    scenes: List[Dict[str, Any]] = []
    scenes_sec = _section(md, r"4\. ", "##")
    scene_re = re.compile(r"^### 🎬 Cảnh\s*(\d+)\s*\(([^)]*)\)\s*[:：]\s*(.*)$", re.M)
    scene_heads = list(scene_re.finditer(scenes_sec))
    shot_re = re.compile(r"^#### 🔹 Shot `(?P<id>S\d+)` \((?P<meta>.*)\)\s*$", re.M)
    for i, sh in enumerate(scene_heads):
        end = scene_heads[i + 1].start() if i + 1 < len(scene_heads) else len(scenes_sec)
        body = scenes_sec[sh.end():end]
        idx = int(sh.group(1))
        stitle = sh.group(3).strip()
        times = sh.group(2).split("-")
        shot_heads = list(shot_re.finditer(body))
        pre = body[: shot_heads[0].start()] if shot_heads else body
        sb = _bullets(pre)
        shots = []
        for j, hh in enumerate(shot_heads):
            sbody = body[hh.end(): shot_heads[j + 1].start() if j + 1 < len(shot_heads) else len(body)]
            shots.append(_parse_shot(hh, sbody, idx, stitle))
        scenes.append(
            {
                "index": idx,
                "title": stitle,
                "startSec": _mmss(times[0]),
                "endSec": _mmss(times[1]) if len(times) > 1 else 0,
                "location": _clean(_get(sb, "Vị trí bối cảnh")),
                "purpose": _clean(_get(sb, "Mục đích")),
                "shots": shots,
            }
        )

    return {
        "id": episode_id,
        "episodeNumber": int(num_m.group(1)) if num_m else None,
        "title": (num_m.group(2).strip() if num_m else title_line),
        "series": _clean(_get(meta, "Series")),
        "season": _clean(_get(meta, "Mùa phim")),
        "durationSec": duration_sec,
        "aspect": aspect,
        "style": style,
        "leadCharacter": re.sub(r"\s*\(\d+\s*cm\)", "", _clean(_get(meta, "Nhân vật trọng tâm"))).strip(),
        "cast": cast,
        "setting": {
            "name": re.sub(r"\s*—.*$", "", _clean(setting_raw)).strip(),
            "code": code.group(1) if code else "",
            "timeOfDay": tod.group(1).strip() if tod else "",
        },
        "lesson": _clean(_get(meta, "Bài học")),
        "mantra": _clean(_get(meta, "Câu thần chú")),
        "summary": summary,
        "environmentPromptLock": environment,
        "characters": characters,
        "scenes": scenes,
    }


def script_to_scenes(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Mỗi shot → một phần tử `scenes` theo định dạng bộ chạy đang dùng (ParsedScene mở rộng)."""
    out: List[Dict[str, Any]] = []
    n = 0
    for sc in data.get("scenes", []):
        for sh in sc.get("shots", []):
            n += 1
            out.append(
                {
                    "sceneNumber": n,
                    "shotId": sh["id"],
                    "title": f"{sc['title']} · {sh['id']}",
                    "imagePrompt": sh["imagePrompt"],
                    "videoPrompt": sh["videoPrompt"],
                    "dialogue": sh["dialogue"],
                    "speaker": sh["speaker"],
                    "durationSec": sh["durationSec"],
                    "characters": sh["characters"],
                    "shotSize": sh["shotSize"],
                    "camera": sh["camera"],
                    "sfx": sh["sfx"],
                    "bgm": sh["bgm"],
                }
            )
    return out


def resolve_facet(data: Dict[str, Any], facet: str, shot: Optional[str] = None, md: str = "") -> Any:
    """Giá trị của một 'mặt cắt' kịch bản (text / scenes / script)."""
    if shot:
        for sc in data.get("scenes", []):
            for sh in sc.get("shots", []):
                if sh["id"] == shot:
                    return sh.get(facet, "")
        return ""
    if facet == "fulltext":
        return md
    if facet == "summary":
        return data.get("summary", "")
    if facet == "lesson":
        return data.get("lesson", "")
    if facet == "mantra":
        return data.get("mantra", "")
    if facet == "environment":
        return data.get("environmentPromptLock", "")
    if facet == "dialogue_all":
        lines = []
        for sc in data.get("scenes", []):
            for sh in sc.get("shots", []):
                if sh["dialogue"]:
                    lines.append(f"{sh['speaker'] or '—'}: {sh['dialogue']}")
        return "\n".join(lines)
    if facet == "scenes":
        return script_to_scenes(data)
    if facet == "script":
        return data
    return ""
