"""Kho giọng (voice vault): liệt kê, tạo giọng từ mp3/mp4, nghe mẫu, gắn vào nhân vật."""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from socnhotv.core.storage.project_store import get_repo_root

router = APIRouter(prefix="/voices", tags=["voices"])

ALLOWED_EXT = {".mp3", ".mp4", ".wav", ".m4a", ".mov", ".webm"}
MAX_UPLOAD = 200 * 1024 * 1024
JOBS: Dict[str, Dict[str, Any]] = {}


def _vault() -> Path:
    return get_repo_root() / "data" / "shared" / "voice_vault"


def _valid_id(voice_id: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,40}", voice_id):
        raise HTTPException(400, "Mã giọng chỉ gồm chữ thường, số, '-' hoặc '_' (2 đến 41 ký tự)")
    return voice_id


def _used_by(voice_id: str) -> list[Dict[str, str]]:
    out = []
    projects = get_repo_root() / "data" / "projects"
    if projects.exists():
        for pj in projects.glob("*/project.json"):
            data = json.loads(pj.read_text(encoding="utf-8"))
            for cid, c in data.get("characters", {}).items():
                if c.get("voice_id") == voice_id:
                    out.append({"projectId": data["id"], "characterId": cid, "name": c.get("name", cid)})
    return out


def _view(d: Path) -> Dict[str, Any]:
    p = json.loads((d / "profile.json").read_text(encoding="utf-8")) if (d / "profile.json").exists() else {}
    sample = p.get("files", {}).get("cloned_sample", "cloned_default_sample.mp3")
    return {
        "id": d.name,
        "name": p.get("speaker_name", d.name),
        "dialect": p.get("dialect", ""),
        "engine": p.get("engine", ""),
        "durationSec": p.get("duration"),
        "transcript": p.get("transcript", ""),
        "createdAt": p.get("created_at", ""),
        "hasSample": (d / sample).exists(),
        "sampleUrl": f"/voices/{d.name}/sample" if (d / sample).exists() else None,
        "usedBy": _used_by(d.name),
    }


@router.get("")
async def list_voices():
    v = _vault()
    if not v.exists():
        return []
    return [_view(d) for d in sorted(v.iterdir()) if d.is_dir() and (d / "profile.json").exists()]


@router.get("/{voice_id}/sample")
async def voice_sample(voice_id: str):
    d = _vault() / _valid_id(voice_id)
    view = _view(d) if (d / "profile.json").exists() else None
    if not view or not view["hasSample"]:
        raise HTTPException(404, "Chưa có mẫu nghe thử")
    sample = json.loads((d / "profile.json").read_text(encoding="utf-8")).get("files", {}).get("cloned_sample", "cloned_default_sample.mp3")
    return FileResponse(d / sample)


async def _run_clone(job_id: str, src: Path, voice_id: str, dialect: str, transcript: str | None) -> None:
    job = JOBS[job_id]
    script = get_repo_root() / "scripts" / "voice" / "voice_studio.py"
    cmd = [sys.executable, str(script), "clone", "--input", str(src), "--name", voice_id, "--dialect", dialect]
    if transcript:
        cmd += ["--text", transcript]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=str(get_repo_root())
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=1800)
        tail = out.decode("utf-8", "ignore")[-600:]
        if proc.returncode == 0 and (_vault() / voice_id / "profile.json").exists():
            job.update(status="done", voice=_view(_vault() / voice_id))
        else:
            job.update(status="failed", error=tail or f"mã thoát {proc.returncode}")
    except Exception as e:  # noqa: BLE001
        job.update(status="failed", error=str(e)[:600])
    finally:
        src.unlink(missing_ok=True)
        job["finishedAt"] = time.time()


async def execute_voice_clone(payload: Dict[str, Any], project_id: Optional[str] = None) -> Dict[str, Any]:
    """Nhân bản giọng nói thật vào Voice Vault toàn cục hoặc theo dự án (OmniVoice + Faster-Whisper + AudioMastering -14 LUFS)."""
    if not payload.get("consentConfirmed"):
        raise HTTPException(
            status_code=400,
            detail="Phải xác nhận quyền sử dụng giọng nói (chỉ giọng của chính bạn hoặc người đã đồng ý).",
        )

    raw_voice_id = str(payload.get("voiceId", "")).strip()
    if not raw_voice_id:
        raise HTTPException(status_code=400, detail="Mã giọng (voiceId) không được để trống.")

    voice_id = re.sub(r"[^a-z0-9_-]+", "-", raw_voice_id.lower()).strip("-")
    if not voice_id or len(voice_id) < 2:
        raise HTTPException(status_code=400, detail="Mã giọng không hợp lệ (tối thiểu 2 ký tự chữ thường, số, dấu gạch).")

    dialect = payload.get("dialect", "south")
    if dialect not in ("north", "south", "central"):
        dialect = "south"

    repo_root = get_repo_root()
    vault_dir = repo_root / "data" / "shared" / "voice_vault"
    uploads_dir = vault_dir / ".uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    source_path: Optional[Path] = None
    clean_up_source = False

    # 1. Tệp âm thanh tải lên dạng base64
    audio_data = payload.get("audioData")
    if audio_data and isinstance(audio_data, str):
        import base64
        filename = payload.get("filename", "sample.mp3")
        ext = Path(filename).suffix.lower()
        if ext not in {".mp3", ".wav", ".m4a", ".mp4", ".mov", ".webm"}:
            ext = ".mp3"
        tmp_file = uploads_dir / f"upload_{uuid.uuid4().hex[:8]}{ext}"
        try:
            tmp_file.write_bytes(base64.b64decode(audio_data))
            source_path = tmp_file
            clean_up_source = True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Dữ liệu âm thanh không hợp lệ: {e}")

    # 2. Tệp âm thanh từ sourceFile được chỉ định
    if not source_path and payload.get("sourceFile"):
        sf_val = str(payload.get("sourceFile"))
        candidates = [
            Path(sf_val),
            repo_root / sf_val.lstrip("/"),
            vault_dir / sf_val.lstrip("/"),
            vault_dir / voice_id / sf_val,
        ]
        if project_id:
            candidates.append(repo_root / "data" / "projects" / project_id / sf_val.lstrip("/"))
        for c in candidates:
            if c.is_file() and c.stat().st_size > 0:
                source_path = c
                break

    # 3. Tìm từ nhân vật nếu có
    character_id = payload.get("characterId")
    if not source_path and character_id and project_id:
        store_path = repo_root / "data" / "projects" / project_id
        char_vault = vault_dir / voice_id
        if char_vault.exists():
            for f in sorted(char_vault.iterdir()):
                if f.is_file() and f.suffix.lower() in {".mp3", ".wav", ".m4a"} and f.name != "cloned_default_sample.mp3":
                    source_path = f
                    break
        p_json = store_path / "project.json"
        if not source_path and p_json.exists():
            try:
                p_data = json.loads(p_json.read_text(encoding="utf-8"))
                char_data = p_data.get("characters", {}).get(character_id, {})
                old_voice_id = char_data.get("voice_id")
                if old_voice_id and (vault_dir / old_voice_id).exists():
                    for f in sorted((vault_dir / old_voice_id).iterdir()):
                        if f.is_file() and f.suffix.lower() in {".mp3", ".wav", ".m4a"} and f.name != "cloned_default_sample.mp3":
                            source_path = f
                            break
            except Exception:
                pass

    if not source_path or not source_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Không tìm thấy tệp âm thanh nguồn để nhân bản giọng. Vui lòng chọn hoặc tải lên tệp âm thanh (.mp3, .wav, .m4a, .mp4).",
        )

    root_src = str(repo_root / "src")
    if root_src not in sys.path:
        sys.path.insert(0, root_src)

    from gobi.services.voice import VoiceCloner

    def _clone_worker():
        cloner = VoiceCloner(profiles_dir=vault_dir)
        return cloner.create_profile(
            media_path=str(source_path),
            profile_id=voice_id,
            dialect=dialect,
            speaker_name=voice_id,
        )

    try:
        meta = await asyncio.to_thread(_clone_worker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi nhân bản giọng OmniVoice: {e}")
    finally:
        if clean_up_source and source_path.exists():
            source_path.unlink(missing_ok=True)

    # Cập nhật hồ sơ nhân vật trong project.json (nếu có project_id và character_id)
    if project_id and character_id:
        store_path = repo_root / "data" / "projects" / project_id
        p_json = store_path / "project.json"
        if p_json.exists():
            try:
                p_data = json.loads(p_json.read_text(encoding="utf-8"))
                if "characters" in p_data and character_id in p_data["characters"]:
                    p_data["characters"][character_id]["voice_id"] = voice_id
                    p_data["characters"][character_id]["sample_audio_url"] = f"/voices/{voice_id}/sample"
                    p_json.write_text(json.dumps(p_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except Exception:
                pass

    return {
        "status": "cloned",
        "voiceId": voice_id,
        "name": meta.get("speaker_name", voice_id),
        "dialect": dialect,
        "durationSec": meta.get("duration"),
        "transcript": meta.get("transcript", ""),
        "sampleUrl": f"/voices/{voice_id}/sample",
        "vaultPath": f"data/shared/voice_vault/{voice_id}/",
        "mastering": "-14 LUFS · 44.1kHz · 192kbps",
    }


@router.post("/clone")
async def clone_voice(
    request: Request,
    name: Optional[str] = None,
    filename: Optional[str] = None,
    consent: bool = False,
    dialect: str = "south",
    transcript: str | None = None,
    overwrite: bool = False,
):
    """Tạo giọng từ tệp mp3/mp4 hoặc JSON payload base64/file reference."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        pid = payload.get("projectId")
        return await execute_voice_clone(payload, project_id=pid)

    if not consent:
        raise HTTPException(400, "Cần xác nhận quyền: chỉ nhân bản giọng của chính bạn hoặc người đã đồng ý (giọng trẻ em cần phụ huynh đồng ý).")
    if not name:
        raise HTTPException(400, "Tên/mã giọng không được để trống")
    if not filename:
        raise HTTPException(400, "Tên tệp không được để trống")
    voice_id = _valid_id(name)
    if dialect not in ("north", "south", "central"):
        raise HTTPException(400, "dialect phải là north, south hoặc central")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Chỉ nhận {sorted(ALLOWED_EXT)}")
    if (_vault() / voice_id).exists() and not overwrite:
        raise HTTPException(409, f"Giọng '{voice_id}' đã có trong kho; dùng tên khác hoặc overwrite=true")
    if voice_id == "soc-nho" and not overwrite:
        raise HTTPException(409, "Không ghi đè giọng chuẩn soc-nho")

    tmp_dir = get_repo_root() / "data" / "shared" / "voice_vault" / ".uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex[:10]
    src = tmp_dir / f"{job_id}{ext}"
    size = 0
    with src.open("wb") as f:
        async for chunk in request.stream():
            size += len(chunk)
            if size > MAX_UPLOAD:
                f.close()
                src.unlink(missing_ok=True)
                raise HTTPException(413, "Tệp quá lớn (tối đa 200 MB)")
            f.write(chunk)
    if size == 0:
        src.unlink(missing_ok=True)
        raise HTTPException(400, "Tệp rỗng")

    JOBS[job_id] = {"id": job_id, "voiceId": voice_id, "status": "running", "startedAt": time.time()}
    asyncio.create_task(_run_clone(job_id, src, voice_id, dialect, transcript))
    return JOBS[job_id]


@router.get("/jobs/{job_id}")
async def clone_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Không có việc này")
    return JOBS[job_id]
