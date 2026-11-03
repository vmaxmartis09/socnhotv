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
