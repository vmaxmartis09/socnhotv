"""Đọc và ghi dữ liệu dự án thật từ data/projects/<id>/ (nguồn sự thật duy nhất cho giao diện)."""
from __future__ import annotations

import base64
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse

from socnhotv.core.storage.project_store import get_repo_root

router = APIRouter(prefix="/data", tags=["data"])

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def _project_dir(project_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", project_id):
        raise HTTPException(400, "project_id không hợp lệ")
    d = get_repo_root() / "data" / "projects" / project_id
    if not (d / "project.json").exists():
        raise HTTPException(404, f"Không có dự án {project_id}")
    return d


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _project_view(d: Path) -> Dict[str, Any]:
    p = _read_json(d / "project.json", {})
    episodes_dir = d / p.get("paths", {}).get("episodes", "content/episodes")
    episodes = [e for e in episodes_dir.iterdir() if e.is_dir()] if episodes_dir.exists() else []
    f = d / "project.json"
    return {
        "id": p["id"],
        "name": p.get("name", p["id"]),
        "description": p.get("description", ""),
        "language": p.get("language", "vi"),
        "targetPlatforms": p.get("target_platforms", []),
        "defaultAspectRatio": p.get("default_aspect_ratio", "9:16"),
        "defaultCharacterId": p.get("default_character", ""),
        "defaultVoiceId": p.get("default_voice_id", ""),
        "charactersCount": len(p.get("characters", {})),
        "episodesCount": len(episodes),
        "createdAt": _iso(f.stat().st_ctime),
        "updatedAt": _iso(f.stat().st_mtime),
    }


def _first_code_block(path: Path) -> str:
    if not path.exists():
        return ""
    m = re.search(r"```\w*\n(.*?)```", path.read_text(encoding="utf-8"), re.S)
    return m.group(1).strip() if m else ""


def _vault_dir(voice_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", voice_id or ""):
        raise HTTPException(400, "voice id không hợp lệ")
    return get_repo_root() / "data" / "shared" / "voice_vault" / voice_id


AUDIO_EXT = {".mp3", ".wav"}


def _voice_files(voice_id: str) -> List[Dict[str, Any]]:
    try:
        v = _vault_dir(voice_id)
    except HTTPException:
        return []
    if not v.exists():
        return []
    return [
        {"name": f.name, "url": f"/data/voices/{voice_id}/{f.name}", "sizeKb": round(f.stat().st_size / 1024)}
        for f in sorted(v.iterdir())
        if f.is_file() and f.suffix.lower() in AUDIO_EXT
    ]


def _vault_sample_url(voice_id: str) -> str:
    files = _voice_files(voice_id)
    pick = next((f for f in files if f["name"] == "cloned_default_sample.mp3"), files[0] if files else None)
    return pick["url"] if pick else ""


def _decode(payload: Dict[str, Any]) -> bytes:
    try:
        return base64.b64decode(payload["data"], validate=True)
    except Exception:
        raise HTTPException(400, "Dữ liệu tệp (base64) không hợp lệ")


def _safe_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(str(name)).name).strip("._") or "file"
    return name


def _character_view(d: Path, project: Dict[str, Any], cid: str, c: Dict[str, Any]) -> Dict[str, Any]:
    dna = d / c.get("dna_dir", f"characters/{cid}")
    profile: Dict[str, Any] = {}
    prof_path = c.get("profile_path")
    if prof_path and prof_path.endswith(".json"):
        profile = _read_json(d / prof_path, {})
    sidecar = _read_json(dna / "studio.json", {})

    prompt_lock = (
        sidecar.get("promptLock")
        or profile.get("prompt_lock")
        or _first_code_block(dna / "persona.md")
        or ""
    )
    personality = profile.get("identity", {}).get("personality", [])
    memory = {
        "personality": sidecar.get("memory", {}).get("personality")
        or ", ".join(personality)
        or "",
        "catchphrases": sidecar.get("memory", {}).get("catchphrases", []),
        "habits": sidecar.get("memory", {}).get("habits", []),
        "pastEventsSummary": sidecar.get("memory", {}).get("pastEventsSummary", []),
    }
    images: List[str] = []
    ref_library: List[Dict[str, Any]] = list(sidecar.get("referenceLibrary", []))
    primary = sidecar.get("primaryImage")
    if dna.exists():
        files = [f for f in sorted(dna.iterdir()) if f.is_file() and f.suffix.lower() in IMAGE_EXT]
        files.sort(key=lambda f: f.name != primary)  # ảnh chính lên đầu, giữ thứ tự tên cho phần còn lại
        for idx, img in enumerate(files):
            rel = img.relative_to(d).as_posix()
            url = f"/data/projects/{project['id']}/files/{rel}"
            images.append(url)
            if not sidecar.get("referenceLibrary"):
                ref_library.append(
                    {
                        "id": f"ref_{cid}_{idx+1:02d}",
                        "url": url,
                        "angle": img.name,
                        "isPrimary": idx == 0,
                        "sourceType": "master_dna",
                        "createdAt": _iso(img.stat().st_mtime),
                    }
                )
    # Ảnh nhân vật đã tách nền (PNG trong suốt) ở characters/<id>/cutout/, trùng tên với ảnh DNA gốc
    cutout_dir = dna / "cutout"
    cutout_images: List[str] = []
    if cutout_dir.exists():
        cut_by_name = {
            f.name: f"/data/projects/{project['id']}/files/{f.relative_to(d).as_posix()}"
            for f in sorted(cutout_dir.iterdir())
            if f.is_file() and f.suffix.lower() == ".png"
        }
        cutout_images = list(cut_by_name.values())
        for ref in ref_library:
            name = Path(str(ref.get("url", ""))).name
            if name in cut_by_name:
                ref["cutoutUrl"] = cut_by_name[name]
    description = (
        sidecar.get("description")
        or profile.get("body", {}).get("build")
        or profile.get("purpose", "")
    )
    voice_id = c.get("voice_id") or ("soc-nho" if cid == "soc_nho" else "voice-koala")
    default_clips = [
        {
            "id": "clip_ep1_c1",
            "url": f"/data/projects/{project['id']}/files/content/episodes/soc-nho-sau-rang/scenes/canh_01.mp4",
            "thumbnailUrl": f"/data/projects/{project['id']}/files/content/episodes/soc-nho-sau-rang/scenes/canh_01.jpg",
            "episodeId": "soc-nho-sau-rang",
            "episodeTitle": "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
            "sceneIndex": 1,
            "sceneTitle": "Cảnh 1: Sóc Bi ở nhà cây, kệ đầy hũ kẹo",
            "durationSec": 8.0,
            "model": "google-veo-2",
            "createdAt": "2026-11-01T22:41:00.000Z",
        }
    ] if cid == "soc_nho" else []
    default_appearances = [
        {
            "episodeId": "soc-nho-sau-rang",
            "episodeTitle": "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
            "scenes": (
                ["Cảnh 1: Kệ kẹo nhà cây", "Cảnh 2: Ăn kẹo quên đánh răng", "Cảnh 3: Sáng dậy đau răng", "Cảnh 4: Khám Bác sĩ Koala", "Cảnh 5: Học chải răng", "Cảnh 6: Răng sáng bóng"]
                if cid == "soc_nho"
                else ["Cảnh 4: Khám răng tại phòng khám", "Cảnh 5: Hướng dẫn đánh răng đúng cách"]
            ),
        }
    ]
    return {
        "id": cid,
        "projectId": project["id"],
        "name": c.get("name", cid),
        "role": c.get("role", "supporting"),
        "description": description,
        "heightCm": c.get("height_cm", 0),
        "scaleRatio": c.get("scale_ratio", 1.0),
        "voiceId": voice_id,
        "defaultTempo": sidecar.get("defaultTempo", 1.10 if cid == "soc_nho" else 1.0),
        "sampleAudioUrl": sidecar.get("sampleAudioUrl") or _vault_sample_url(voice_id) or "",
        "voiceFiles": _voice_files(voice_id),
        "promptLock": prompt_lock,
        "referenceImages": images,
        "referenceLibrary": ref_library,
        "cutoutImages": cutout_images,
        "generatedClips": sidecar.get("generatedClips", default_clips),
        "appearances": sidecar.get("appearances", default_appearances),
        "memory": memory,
    }


@router.get("/projects")
async def list_data_projects() -> List[Dict[str, Any]]:
    root = get_repo_root() / "data" / "projects"
    if not root.exists():
        return []
    return [_project_view(d) for d in sorted(root.iterdir()) if (d / "project.json").exists()]


@router.post("/projects")
async def create_data_project(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Tạo dự án mới (thư mục data/projects/<id>/ + project.json) và đăng ký vào data/workspace.json."""
    pid = str(payload.get("id") or "").strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", pid):
        raise HTTPException(400, "id dự án chỉ gồm a-z, 0-9, _ và -")
    root = get_repo_root() / "data"
    d = root / "projects" / pid
    if d.exists():
        raise HTTPException(409, "Dự án đã tồn tại")
    for sub in ("characters", "content/episodes", "assets", "library", "output", "publishing"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    project = {
        "id": pid,
        "name": payload.get("name") or pid,
        "description": payload.get("description", ""),
        "version": "1.0.0",
        "language": payload.get("language", "vi"),
        "target_platforms": payload.get("targetPlatforms", ["youtube", "tiktok"]),
        "default_aspect_ratio": payload.get("defaultAspectRatio", "9:16"),
        "default_character": "",
        "default_voice_id": "",
        "characters": {},
    }
    _write_json(d / "project.json", project)
    ws_path = root / "workspace.json"
    ws = _read_json(ws_path, {})
    if isinstance(ws.get("projects"), list):
        ws["projects"].append(
            {"id": pid, "name": project["name"], "description": project["description"],
             "path": f"projects/{pid}", "status": "active", "created_at": dt.date.today().isoformat()}
        )
        _write_json(ws_path, ws)
    return _project_view(d)


@router.get("/projects/{project_id}")
async def get_data_project(project_id: str) -> Dict[str, Any]:
    return _project_view(_project_dir(project_id))


@router.put("/projects/{project_id}")
async def put_data_project(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    d = _project_dir(project_id)
    p = _read_json(d / "project.json", {})
    mapping = {
        "name": "name",
        "description": "description",
        "language": "language",
        "targetPlatforms": "target_platforms",
        "defaultAspectRatio": "default_aspect_ratio",
        "defaultVoiceId": "default_voice_id",
    }
    for src, dst in mapping.items():
        if src in payload:
            p[dst] = payload[src]
    _write_json(d / "project.json", p)
    return _project_view(d)


@router.get("/projects/{project_id}/characters")
async def list_data_characters(project_id: str) -> List[Dict[str, Any]]:
    d = _project_dir(project_id)
    p = _read_json(d / "project.json", {})
    return [_character_view(d, p, cid, c) for cid, c in p.get("characters", {}).items()]


import re as _re

_CHARACTER_SYSTEM = (
    "Bạn là biên kịch nhân vật cho kênh hoạt hình 3D trẻ em Sóc Nhỏ TV (phong cách Pixar). "
    "Từ mô tả của người dùng, trả về JSON hồ sơ nhân vật bằng tiếng Việt. promptLock là mô tả hình dáng "
    "bằng tiếng Anh, ngắn gọn, bất biến, dùng để giữ nhận diện khi sinh ảnh."
)

_CHARACTER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "role": {"type": "STRING", "enum": ["main", "supporting"]},
        "heightCm": {"type": "NUMBER"},
        "description": {"type": "STRING"},
        "personality": {"type": "STRING"},
        "promptLock": {"type": "STRING"},
        "catchphrases": {"type": "ARRAY", "items": {"type": "STRING"}},
        "habits": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["name", "role", "heightCm", "description", "personality", "promptLock"],
}


def _mock_character(prompt: str) -> Dict[str, Any]:
    """Bản nháp theo quy tắc khi chưa có khóa Gemini hoặc đang ở chế độ chạy thử."""
    text = prompt.strip()
    m = _re.search(r"(?:tên(?: là)?|named?|call(?:ed)?)\s+([A-ZÀ-Ỹ][\wÀ-ỹ]*(?:\s+[A-ZÀ-Ỹ][\wÀ-ỹ]*){0,2})", text)
    name = m.group(1) if m else (text.split(",")[0].split(".")[0][:28].strip().title() or "Nhân vật mới")
    h = _re.search(r"(\d{2,3})\s*cm", text)
    height = float(h.group(1)) if h else 120.0
    traits = [w for w in ("vui", "nhút nhát", "thông minh", "tốt bụng", "nghịch ngợm", "hiền", "dũng cảm", "tò mò") if w in text.lower()]
    return {
        "name": name,
        "role": "supporting",
        "heightCm": height,
        "description": text[:240],
        "personality": ", ".join(traits) or "thân thiện, tò mò",
        "promptLock": f"{text[:200]}, cute 3D Pixar-style woodland character, {int(height)}cm tall, soft studio lighting, plain light gray background",
        "catchphrases": [],
        "habits": [],
    }


@router.post("/projects/{project_id}/ai/character")
async def ai_generate_character(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Tạo bản nháp hồ sơ nhân vật từ mô tả: Gemini khi có khóa và không ở chế độ thử, ngược lại theo quy tắc."""
    _project_dir(project_id)
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        raise HTTPException(400, "Thiếu mô tả nhân vật")
    mock = bool(payload.get("mockMode", True))
    if not mock:
        from socnhotv.core.providers import GoogleProvider, KeyVault, SpendGuard
        from socnhotv.core.storage.project_store import ProjectStore

        vault = KeyVault()
        if vault.has_valid_key("gemini"):
            store = ProjectStore(project_id)
            provider = GoogleProvider(store, guard=SpendGuard(store.runs_dir), key=vault.require_key("gemini"))
            res = await provider.text_complete(_CHARACTER_SYSTEM, prompt, schema=_CHARACTER_SCHEMA)
            try:
                return {"mode": "gemini", "draft": json.loads(res.get("text", "{}"))}
            except json.JSONDecodeError:
                raise HTTPException(502, "Mô hình trả về dữ liệu không hợp lệ")
    return {"mode": "mock", "draft": _mock_character(prompt)}


@router.post("/projects/{project_id}/characters")
async def create_data_character(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    d = _project_dir(project_id)
    p = _read_json(d / "project.json", {})
    characters = p.setdefault("characters", {})
    cid = str(payload.get("id") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", cid):
        raise HTTPException(400, "id nhân vật không hợp lệ")
    if cid in characters:
        raise HTTPException(409, "Nhân vật đã tồn tại")
    characters[cid] = {
        "name": payload.get("name") or cid,
        "role": payload.get("role", "supporting"),
        "height_cm": payload.get("heightCm", 100),
        "scale_ratio": payload.get("scaleRatio", 1.0),
        "voice_id": payload.get("voiceId", ""),
        "dna_dir": f"characters/{cid}",
    }
    (d / "characters" / cid).mkdir(parents=True, exist_ok=True)
    _write_json(d / "project.json", p)
    return await put_data_character(project_id, cid, payload)


@router.delete("/projects/{project_id}/characters/{character_id}")
async def delete_data_character(project_id: str, character_id: str) -> Dict[str, Any]:
    """Chỉ gỡ nhân vật khỏi project.json; tệp DNA/ảnh gốc được giữ nguyên trên đĩa."""
    d = _project_dir(project_id)
    p = _read_json(d / "project.json", {})
    if character_id not in p.get("characters", {}):
        raise HTTPException(404, "Không có nhân vật này")
    del p["characters"][character_id]
    if p.get("default_character") == character_id:
        p["default_character"] = next(iter(p["characters"]), "")
    _write_json(d / "project.json", p)
    return {"deleted": character_id}


@router.put("/projects/{project_id}/characters/{character_id}")
async def put_data_character(
    project_id: str, character_id: str, payload: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    d = _project_dir(project_id)
    p = _read_json(d / "project.json", {})
    if character_id not in p.get("characters", {}):
        raise HTTPException(404, "Không có nhân vật này")
    c = p["characters"][character_id]
    for src, dst in {"name": "name", "role": "role", "heightCm": "height_cm", "scaleRatio": "scale_ratio", "voiceId": "voice_id"}.items():
        if src in payload:
            c[dst] = payload[src]
    _write_json(d / "project.json", p)
    # Phần mô tả mở rộng lưu cạnh hồ sơ gốc, không ghi đè tệp hồ sơ chuẩn
    dna = d / c.get("dna_dir", f"characters/{character_id}")
    sidecar = _read_json(dna / "studio.json", {})
    for key in ("description", "promptLock", "memory", "referenceLibrary", "generatedClips", "appearances", "defaultTempo", "primaryImage", "sampleAudioUrl"):
        if key in payload:
            sidecar[key] = payload[key]
    _write_json(dna / "studio.json", sidecar)
    return _character_view(d, p, character_id, c)


@router.post("/projects/{project_id}/characters/{character_id}/images")
async def upload_character_image(
    project_id: str, character_id: str, payload: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Thêm ảnh DNA cho nhân vật. Body: {name, data(base64)}; không ghi đè tệp đã có."""
    d = _project_dir(project_id)
    p = _read_json(d / "project.json", {})
    c = p.get("characters", {}).get(character_id)
    if c is None:
        raise HTTPException(404, "Không có nhân vật này")
    name = _safe_name(payload.get("name", "image.png"))
    if Path(name).suffix.lower() not in IMAGE_EXT:
        raise HTTPException(400, "Chỉ nhận ảnh png/jpg/webp")
    dna = d / c.get("dna_dir", f"characters/{character_id}")
    dna.mkdir(parents=True, exist_ok=True)
    target, n = dna / name, 1
    while target.exists():
        target = dna / f"{Path(name).stem}_{n}{Path(name).suffix}"
        n += 1
    target.write_bytes(_decode(payload))
    return _character_view(d, p, character_id, c)


@router.delete("/projects/{project_id}/characters/{character_id}/images/{filename}")
async def delete_character_image(project_id: str, character_id: str, filename: str) -> Dict[str, Any]:
    """Không xóa hẳn: chuyển ảnh vào _removed/ cạnh thư mục DNA để có thể khôi phục."""
    d = _project_dir(project_id)
    p = _read_json(d / "project.json", {})
    c = p.get("characters", {}).get(character_id)
    if c is None:
        raise HTTPException(404, "Không có nhân vật này")
    dna = d / c.get("dna_dir", f"characters/{character_id}")
    src = dna / _safe_name(filename)
    if not src.is_file() or src.suffix.lower() not in IMAGE_EXT:
        raise HTTPException(404, "Không có ảnh này")
    trash = dna / "_removed"
    trash.mkdir(exist_ok=True)
    src.rename(trash / src.name)
    sidecar = _read_json(dna / "studio.json", {})
    if sidecar.get("primaryImage") == src.name:
        sidecar.pop("primaryImage")
        _write_json(dna / "studio.json", sidecar)
    return _character_view(d, p, character_id, c)


@router.post("/voices/{voice_id}/samples")
async def upload_voice_sample(voice_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Thêm mẫu giọng (mp3/wav) vào voice vault; không ghi đè tệp đã có."""
    v = _vault_dir(voice_id)
    name = _safe_name(payload.get("name", "sample.mp3"))
    if Path(name).suffix.lower() not in AUDIO_EXT:
        raise HTTPException(400, "Chỉ nhận mp3/wav")
    v.mkdir(parents=True, exist_ok=True)
    target, n = v / name, 1
    while target.exists():
        target = v / f"{Path(name).stem}_{n}{Path(name).suffix}"
        n += 1
    target.write_bytes(_decode(payload))
    return {"files": _voice_files(voice_id)}


@router.get("/voices/{voice_id}/{filename}")
async def get_voice_file(voice_id: str, filename: str):
    f = _vault_dir(voice_id) / _safe_name(filename)
    if not f.is_file() or f.suffix.lower() not in AUDIO_EXT | {".json"}:
        raise HTTPException(404, "Không có tệp")
    return FileResponse(f)


VIDEO_EXT = {".mp4", ".webm", ".mov"}


def _file_url(project_id: str, d: Path, f: Path) -> str:
    return f"/data/projects/{project_id}/files/{f.relative_to(d).as_posix()}"


@router.get("/projects/{project_id}/library")
async def get_project_library(project_id: str) -> Dict[str, Any]:
    """Kho tư liệu của dự án: video, hình ảnh, kịch bản và tập phim (đọc từ assets/ và content/episodes/)."""
    d = _project_dir(project_id)
    videos: List[Dict[str, Any]] = []
    images: List[Dict[str, Any]] = []
    audios: List[Dict[str, Any]] = []

    # Kho artifact có băm nội dung: assets/<hash>.<ext> kèm <hash>.meta.json
    assets = d / "assets"
    if assets.exists():
        for meta_f in sorted(assets.glob("*.meta.json")):
            m = _read_json(meta_f, {})
            uri = m.get("uri")
            f = d / uri if uri else None
            if not f or not f.is_file():
                continue
            prov, meta = m.get("provenance", {}), m.get("meta", {})
            item = {
                "id": m.get("id", f.stem),
                "name": f.name[:12],
                "url": _file_url(project_id, d, f),
                "source": "artifact",
                "aspect": meta.get("aspect"),
                "durationSec": meta.get("duration"),
                "provider": prov.get("provider"),
                "model": prov.get("model"),
                "createdAt": prov.get("createdAt") or _iso(f.stat().st_mtime),
            }
            if m.get("kind") == "video":
                videos.append(item)
            elif m.get("kind") == "image":
                images.append(item)
            elif m.get("kind") == "audio":
                audios.append(item)

    # Tập phim và kịch bản
    episodes: List[Dict[str, Any]] = []
    scripts: List[Dict[str, Any]] = []
    ep_root = d / "content" / "episodes"
    if ep_root.exists():
        for ep in sorted(x for x in ep_root.iterdir() if x.is_dir()):
            ep_videos = [f for f in ep.rglob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXT]
            ep_images = [f for f in ep.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXT]
            title = ep.name
            for md in sorted(ep.glob("*.md")):
                text = md.read_text(encoding="utf-8", errors="replace")
                heading = re.search(r"^#\s+(.+)$", text, re.M)
                if md.name.upper().startswith("KICH") and heading:
                    title = heading.group(1).strip()
                scripts.append(
                    {
                        "id": f"{ep.name}/{md.name}",
                        "name": md.name,
                        "episodeId": ep.name,
                        "url": _file_url(project_id, d, md),
                        "preview": text[:320],
                        "updatedAt": _iso(md.stat().st_mtime),
                    }
                )
            for f in ep_videos:
                videos.append(
                    {"id": f"{ep.name}/{f.relative_to(ep).as_posix()}", "name": f.relative_to(ep).as_posix(), "url": _file_url(project_id, d, f),
                     "source": "episode", "episodeId": ep.name, "createdAt": _iso(f.stat().st_mtime)}
                )
            for f in ep_images:
                images.append(
                    {"id": f"{ep.name}/{f.relative_to(ep).as_posix()}", "name": f.relative_to(ep).as_posix(), "url": _file_url(project_id, d, f),
                     "source": "episode", "episodeId": ep.name, "createdAt": _iso(f.stat().st_mtime)}
                )
            episodes.append(
                {"id": ep.name, "title": title, "videoCount": len(ep_videos), "imageCount": len(ep_images),
                 "scriptCount": len(list(ep.glob("*.md"))), "updatedAt": _iso(ep.stat().st_mtime)}
            )

    return {"videos": videos, "images": images, "audios": audios, "scripts": scripts, "episodes": episodes}


def _slug(text: str, default: str = "muc") -> str:
    import unicodedata

    t = unicodedata.normalize("NFD", text.strip().lower().replace("đ", "d"))
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = _re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or default


def _unique_dir(root: Path, base: str) -> Path:
    d, n = root / base, 2
    while d.exists():
        d = root / f"{base}-{n}"
        n += 1
    return d


@router.post("/projects/{project_id}/episodes")
async def create_episode(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Tạo thư mục tập mới trong content/episodes/. Body: {title}."""
    d = _project_dir(project_id)
    title = str(payload.get("title", "")).strip()
    if not title:
        raise HTTPException(400, "Thiếu tên tập")
    ep = _unique_dir(d / "content" / "episodes", _slug(title, "tap"))
    ep.mkdir(parents=True)
    (ep / "KICH-BAN.md").write_text(f"# {title}\n\n", encoding="utf-8")
    return {"id": ep.name, "title": title}


_SCRIPT_SYSTEM = (
    "Bạn là biên kịch video hoạt hình ngắn cho trẻ em. Viết kịch bản bằng Markdown tiếng Việt gồm: tiêu đề (#), "
    "mục tiêu, bảng cảnh (| # | Giây | Cảnh | Lời thoại |) khoảng 6 cảnh, và lời thoại. Ngắn gọn, đúng thông điệp."
)


def _mock_script(prompt: str) -> str:
    topic = prompt.strip().split("\n")[0][:80] or "Câu chuyện mới"
    rows = "\n".join(
        f"| {i} | {(i - 1) * 7}-{i * 7} | Cảnh {i}: {step} | (lời thoại cảnh {i}) |"
        for i, step in enumerate(["Mở đầu giới thiệu nhân vật", "Vấn đề xuất hiện", "Nhân vật gặp khó khăn", "Người giúp đỡ xuất hiện", "Cách giải quyết", "Kết thúc và bài học"], 1)
    )
    return (
        f"# {topic}\n\nMục tiêu: {prompt.strip()[:200]}\n\n## Kịch bản (lời thoại + hình)\n\n"
        f"| # | Giây | Cảnh | Lời thoại |\n|---|------|------|-----------|\n{rows}\n"
    )


@router.post("/projects/{project_id}/ai/script")
async def ai_generate_script(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Viết nháp kịch bản Markdown từ ý tưởng: Gemini khi có khóa và không ở chế độ thử, ngược lại theo mẫu."""
    _project_dir(project_id)
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        raise HTTPException(400, "Thiếu ý tưởng")
    if not bool(payload.get("mockMode", True)):
        from socnhotv.core.providers import GoogleProvider, KeyVault, SpendGuard
        from socnhotv.core.storage.project_store import ProjectStore

        vault = KeyVault()
        if vault.has_valid_key("gemini"):
            store = ProjectStore(project_id)
            provider = GoogleProvider(store, guard=SpendGuard(store.runs_dir), key=vault.require_key("gemini"))
            res = await provider.text_complete(_SCRIPT_SYSTEM, prompt)
            return {"mode": "gemini", "markdown": res.get("text", "")}
    return {"mode": "mock", "markdown": _mock_script(prompt)}


@router.post("/projects/{project_id}/scripts")
async def create_script(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Lưu kịch bản Markdown vào tập. Body: {title, content, episodeId?}; chưa có tập thì tạo tập mới theo tiêu đề."""
    d = _project_dir(project_id)
    title = str(payload.get("title", "")).strip()
    content = str(payload.get("content", ""))
    if not title:
        raise HTTPException(400, "Thiếu tiêu đề")
    eps = d / "content" / "episodes"
    ep_id = str(payload.get("episodeId") or "")
    if ep_id:
        ep = eps / _safe_name(ep_id)
        if not ep.is_dir():
            raise HTTPException(404, "Không có tập này")
    else:
        ep = _unique_dir(eps, _slug(title, "tap"))
        ep.mkdir(parents=True)
    name = _slug(title, "kich-ban").upper() + ".md"
    target, n = ep / name, 2
    while target.exists():
        target = ep / f"{Path(name).stem}-{n}.md"
        n += 1
    target.write_text(content, encoding="utf-8")
    return {"episodeId": ep.name, "name": target.name}


def _episode_script_file(project_id: str, episode_id: str) -> Path:
    ep = _project_dir(project_id) / "content" / "episodes" / episode_id
    files = sorted(ep.glob("KICH*.md")) if ep.is_dir() else []
    if not files:
        raise HTTPException(404, f"Không tìm thấy kịch bản của tập '{episode_id}'")
    return files[0]


def load_episode_script(project_id: str, episode_id: str) -> Dict[str, Any]:
    """Đọc + phân tích kịch bản tập thành dữ liệu có cấu trúc (kiểu `script`)."""
    from socnhotv.core.engine.character_profile import load_profiles
    from socnhotv.core.engine.episode_script import load_script

    f = _episode_script_file(project_id, episode_id)
    md = f.read_text(encoding="utf-8", errors="replace")
    data = load_script(f.parent, episode_id, load_profiles(_project_dir(project_id) / "characters"))
    return {"data": data, "markdown": md, "file": f.name}


@router.post("/projects/{project_id}/script-data/compile-all")
async def compile_all_scripts(project_id: str, payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """Biên dịch kịch bản của mọi tập thành script.json (có id nhân vật). force=true: ghi đè cả tập đã khoá."""
    from socnhotv.core.engine.character_profile import load_profiles
    from socnhotv.core.engine.episode_script import SCRIPT_JSON, compile_script
    import json as _json

    root = _project_dir(project_id)
    profiles = load_profiles(root / "characters")
    force = bool(payload.get("force"))
    done: List[Dict[str, Any]] = []
    for ep in sorted((root / "content" / "episodes").glob("*")):
        files = sorted(ep.glob("KICH*.md"))
        if not ep.is_dir() or not files:
            continue
        sj = ep / SCRIPT_JSON
        if sj.is_file() and not force:
            try:
                if _json.loads(sj.read_text(encoding="utf-8")).get("locked"):
                    done.append({"episode": ep.name, "skipped": "locked"})
                    continue
            except Exception:
                pass
        data = compile_script(files[0].read_text(encoding="utf-8", errors="replace"), ep.name, profiles, files[0].name)
        sj.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        done.append({"episode": ep.name, "cast": data["castIds"], "unmatched": data["unmatched"]})
    return {"compiled": [d for d in done if "cast" in d], "skipped": [d for d in done if "skipped" in d]}


@router.get("/projects/{project_id}/script-data/{episode_id}")
async def get_script_data(project_id: str, episode_id: str) -> Dict[str, Any]:
    """Kịch bản tập có cấu trúc + danh mục các 'mặt cắt' (facet) để chọn làm đầu vào node."""
    from socnhotv.core.engine.episode_script import FACETS, SHOT_FACETS

    from socnhotv.core.engine.character_profile import load_profiles, match_speaker

    loaded = load_episode_script(project_id, episode_id)
    data = loaded["data"]
    # Ghép người nói với nhân vật của dự án (giống cổng 'lines' của node Kịch bản) để giao diện báo câu lạc người nói
    profiles = load_profiles(_project_dir(project_id) / "characters")
    matched: Dict[str, Any] = {}

    def _cid(speaker: str):
        if speaker not in matched:
            matched[speaker] = match_speaker(speaker, profiles) if (speaker and profiles) else None
        return matched[speaker]

    shots = [
        {
            "id": sh["id"],
            "scene": sc["index"],
            "sceneTitle": sc["title"],
            "dialogue": sh["dialogue"][:80],
            "speaker": sh["speaker"],
            "characterId": _cid(sh["speaker"]) if sh.get("dialogue") else None,
        }
        for sc in data["scenes"]
        for sh in sc["shots"]
    ]
    return {"script": data, "facets": FACETS, "shotFacets": SHOT_FACETS, "shots": shots}


@router.get("/projects/{project_id}/policy")
async def get_project_policy(project_id: str) -> Dict[str, Any]:
    """Chính sách nội dung xuyên suốt của dự án (tự tạo mặc định nếu chưa có)."""
    from socnhotv.core.engine import content_policy

    _project_dir(project_id)
    return content_policy.load_policy(get_repo_root(), project_id)


@router.put("/projects/{project_id}/policy")
async def put_project_policy(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    from socnhotv.core.engine import content_policy

    _project_dir(project_id)
    return content_policy.save_policy(get_repo_root(), project_id, payload)


@router.get("/policy-packs")
async def get_policy_packs() -> List[Dict[str, Any]]:
    """Các gói chính sách chuẩn của nền tảng (YouTube, TikTok, Meta…)."""
    from socnhotv.core.engine import content_policy

    return content_policy.list_packs(get_repo_root())


@router.post("/projects/{project_id}/policy/import-pack")
async def import_policy_pack(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    from socnhotv.core.engine import content_policy

    _project_dir(project_id)
    root = get_repo_root()
    pack = content_policy.load_pack(root, str(payload.get("packId", "")))
    if not pack:
        raise HTTPException(404, "Không tìm thấy gói chính sách")
    pol = content_policy.import_pack(content_policy.load_policy(root, project_id), pack)
    return content_policy.save_policy(root, project_id, pol)


@router.post("/projects/{project_id}/policy/import")
async def import_policy_file(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Nhập chính sách từ tệp tải lên (.json / .txt / .md / .csv). Body: {name, text}."""
    from socnhotv.core.engine import content_policy

    _project_dir(project_id)
    name = str(payload.get("name") or "upload.txt")
    text_in = str(payload.get("text") or "")
    # Tệp chính sách dạng văn xuôi (vd. chính sách YouTube): lưu thành tài liệu của dự án, KHÔNG tách thành "từ cấm"
    if not name.lower().endswith(".json") and content_policy.looks_like_prose(text_in):
        doc = content_policy.add_document(get_repo_root(), project_id, name, text_in)
        return {
            "policy": content_policy.load_policy(get_repo_root(), project_id),
            "document": doc,
            "added": 0,
            "terms": 0,
            "message": f"Đã lưu '{doc['name']}' làm tài liệu chính sách của dự án ({len(doc['sections'])} mục). Mọi video phải qua kiểm định theo tài liệu này.",
        }
    try:
        rules = content_policy.parse_policy_text(name, text_in)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"Không đọc được tệp: {e}") from e
    if not rules:
        raise HTTPException(400, "Tệp không có từ/quy tắc nào")
    root = get_repo_root()
    source = "upload-" + _slug(Path(name).stem, "tep")
    pol = content_policy.merge_rules(content_policy.load_policy(root, project_id), rules, source)
    saved = content_policy.save_policy(root, project_id, pol)
    return {"policy": saved, "added": len(rules), "terms": sum(len(r["terms"]) for r in rules)}


@router.post("/projects/{project_id}/policy/fetch-url")
async def fetch_policy_url(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Lấy trang chính sách công khai từ nền tảng và lưu làm tài liệu tham chiếu của chính sách dự án."""
    import time as _time

    from socnhotv.core.engine import content_policy

    _project_dir(project_id)
    url = str(payload.get("url") or "").strip()
    try:
        page = content_policy.fetch_policy_page(url)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"Không lấy được trang: {e}") from e
    root = get_repo_root()
    ref = {
        "url": url,
        "title": page["title"],
        "kind": "url",
        "fetchedAt": _time.strftime("%Y-%m-%d %H:%M"),
        "excerpt": page["text"][:600],
    }
    saved = content_policy.save_policy(root, project_id, content_policy.add_reference(content_policy.load_policy(root, project_id), ref))
    return {"policy": saved, "page": {"title": page["title"], "chars": page["chars"], "text": page["text"]}}


@router.post("/projects/{project_id}/policy/check")
async def check_project_policy(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Kiểm nhanh văn bản theo chính sách dự án: {texts: {nguồn: văn bản}} hoặc {text}."""
    from socnhotv.core.engine import content_policy

    _project_dir(project_id)
    texts = payload.get("texts") or ({"text": payload.get("text", "")} if payload.get("text") else {})
    pol = content_policy.load_policy(get_repo_root(), project_id)
    return content_policy.check_texts({str(k): str(v) for k, v in texts.items()}, pol)


@router.post("/projects/{project_id}/library/upload")
async def upload_library_file(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Tải ảnh/video lên kho (assets/ + meta.json). Body: {name, data(base64)}."""
    import hashlib

    d = _project_dir(project_id)
    name = _safe_name(payload.get("name", "file"))
    ext = Path(name).suffix.lower()
    if ext in IMAGE_EXT:
        kind = "image"
    elif ext in VIDEO_EXT:
        kind = "video"
    elif ext in AUDIO_EXT:
        kind = "audio"
    else:
        raise HTTPException(400, "Chỉ nhận ảnh (png/jpg/webp), video (mp4/webm/mov) hoặc âm thanh (mp3/wav)")
    raw = _decode(payload)
    digest = hashlib.sha256(raw).hexdigest()
    assets = d / "assets"
    assets.mkdir(exist_ok=True)
    target = assets / f"{digest}{ext}"
    target.write_bytes(raw)
    _write_json(
        assets / f"{digest}.meta.json",
        {
            "id": f"art_{digest[:12]}",
            "kind": kind,
            "uri": f"assets/{target.name}",
            "mime": "video/mp4" if kind == "video" else ("audio/mpeg" if ext == ".mp3" else "audio/wav") if kind == "audio" else f"image/{ext.lstrip('.')}",
            "size": len(raw),
            "hash": f"sha256:{digest}",
            "meta": {},
            "provenance": {"provider": "upload", "model": name, "createdAt": dt.datetime.now(dt.timezone.utc).isoformat()},
        },
    )
    return {
        "id": f"art_{digest[:12]}",
        "kind": kind,
        "url": _file_url(project_id, d, target),
        "uri": f"assets/{target.name}",
        "name": target.name,
    }


@router.get("/projects/{project_id}/channels")
async def list_data_channels(project_id: str) -> List[Dict[str, Any]]:
    d = _project_dir(project_id)
    return _read_json(d / "publishing" / "channels.json", [])


@router.put("/projects/{project_id}/channels")
async def put_data_channels(project_id: str, payload: List[Dict[str, Any]] = Body(...)) -> List[Dict[str, Any]]:
    d = _project_dir(project_id)
    _write_json(d / "publishing" / "channels.json", payload)
    return payload


@router.get("/projects/{project_id}/files/{file_path:path}")
async def get_data_file(project_id: str, file_path: str):
    d = _project_dir(project_id).resolve()
    target = (d / file_path).resolve()
    if d not in target.parents or not target.is_file():
        raise HTTPException(404, "Không có tệp")
    if target.suffix.lower() not in IMAGE_EXT | {".mp3", ".mp4", ".wav", ".json", ".md"}:
        raise HTTPException(403, "Loại tệp không được phép")
    return FileResponse(target)


# ------------------------------------------------------------------ gói shot để làm clip tay (C5, G4)
_SHOT_ID = re.compile(r"^S\d{1,3}$")


def _latest_keyframes(root: Path) -> Dict[str, Path]:
    """shotId -> ảnh keyframe mới nhất từ snapshot cổng ra của mọi node image_gen trong graph.json."""
    out: Dict[str, Path] = {}
    graph = _read_json(root / "graph.json", {})
    gid = graph.get("id") or f"graph_{root.name}"
    snap_dir = root / "runs" / "_node_outputs" / gid
    for n in graph.get("nodes", []):
        if n.get("type") != "image_gen":
            continue
        snap = _read_json(snap_dir / f"{n.get('id')}.json", {})
        for sc in (snap.get("outputs") or {}).get("scenes") or []:
            if not isinstance(sc, dict):
                continue
            sid, uri = sc.get("shotId"), sc.get("imageUri")
            if sid and uri and (root / uri).is_file():
                out[str(sid)] = root / uri
    return out


@router.get("/projects/{project_id}/episodes/{episode_id}/shot-pack")
async def get_shot_pack(project_id: str, episode_id: str, shots: str = "", all: bool = False):
    """ZIP để làm clip AI bằng tay trên web có credit miễn phí rồi thả lại vào clips/ (hợp đồng C5).

    Mỗi shot: `S07.png` (keyframe đã sinh, chưa có thì ảnh DNA của nhân vật nói), `S07.txt` (videoPrompt,
    thời lượng clip, lời thoại, camera), kèm `README.txt` hướng dẫn đặt tên `clips/S07.mp4`.
    Mặc định lấy các shot `priority = 1`; `shots=S01,S07` chọn tay; `all=true` lấy cả 30 shot.
    """
    import io
    import zipfile

    from fastapi.responses import Response

    from socnhotv.core.engine.character_profile import dna_reference_files, load_profile

    root = _project_dir(project_id)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", episode_id):
        raise HTTPException(400, "episode_id không hợp lệ")
    data = load_episode_script(project_id, episode_id)["data"]
    all_shots = [sh for sc in data.get("scenes", []) for sh in sc.get("shots", [])]
    want = [s.strip().upper() for s in shots.split(",") if s.strip()]
    if any(not _SHOT_ID.match(s) for s in want):
        raise HTTPException(400, "shots chỉ nhận dạng S01,S07,...")
    if want:
        picked = [sh for sh in all_shots if sh["id"] in want]
    elif all:
        picked = all_shots
    else:
        picked = [sh for sh in all_shots if sh.get("priority") == 1] or all_shots[:5]
    if not picked:
        raise HTTPException(404, "Không có shot nào khớp")
    keyframes = _latest_keyframes(root)
    chars_dir = root / "characters"
    clips_dir = f"data/projects/{project_id}/content/episodes/{episode_id}/clips"
    buf = io.BytesIO()
    manifest = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for sh in picked:
            sid = sh["id"]
            img = keyframes.get(sid)
            img_src = "keyframe"
            if img is None:
                cid = sh.get("speakerId") or ((sh.get("characterIds") or [None])[0])
                refs = dna_reference_files(chars_dir, cid, load_profile(chars_dir, cid)) if cid else []
                img, img_src = (refs[0], f"dna:{cid}") if refs else (None, "none")
            if img is not None:
                z.write(img, f"{sid}{img.suffix.lower()}")
            clip_sec = sh.get("clipDurationSec") or 5
            z.writestr(
                f"{sid}.txt",
                "\n".join([
                    f"Shot {sid} · {data.get('title', episode_id)}",
                    f"Khung giờ trong tập: {sh.get('startSec')}s → {sh.get('endSec')}s (shot {sh.get('durationSec')}s)",
                    f"Clip cần làm: {clip_sec} giây, 16:9, KHÔNG cần âm thanh (giọng OmniVoice ghép sau)",
                    f"Ảnh khung đầu: {sid}{img.suffix.lower() if img else ''} ({img_src})",
                    f"Camera: {sh.get('camera', '')} · cỡ cảnh {sh.get('shotSize', '')}",
                    "",
                    "PROMPT (dán vào web làm video):",
                    sh.get("videoPrompt", ""),
                    "",
                    "NEGATIVE:",
                    sh.get("negativePrompt", ""),
                    "",
                    f"Lời thoại (để canh khẩu hình): {sh.get('speaker', '')}: {sh.get('dialogue', '')}",
                ]),
            )
            manifest.append({"shotId": sid, "image": img_src, "clipDurationSec": clip_sec, "priority": sh.get("priority")})
        z.writestr(
            "README.txt",
            "\n".join([
                f"GÓI SHOT — {data.get('title', episode_id)} ({episode_id})",
                "",
                "1. Mở web làm video có credit miễn phí (danh sách: ai/knowledge/free_ai_sources.md).",
                "2. Với mỗi shot: tải ảnh SXX.png làm khung đầu (image-to-video), dán prompt trong SXX.txt.",
                "3. Tắt âm thanh của clip nếu web cho chọn (giọng nhân vật do OmniVoice đọc, ghép sau).",
                "4. Tải clip về, đổi tên ĐÚNG theo shot: S07.mp4 (chữ S hoa, 2 chữ số).",
                f"5. Thả vào: {clips_dir}/",
                "6. Chạy lại flow trong Studio: bộ dựng tự dùng clip có sẵn, shot không có clip thì giữ ảnh.",
                "",
                "Shot trong gói: " + ", ".join(m["shotId"] for m in manifest),
            ]),
        )
        z.writestr("manifest.json", json.dumps({"episodeId": episode_id, "shots": manifest}, ensure_ascii=False, indent=2))
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{episode_id}_shot-pack.zip"'},
    )
