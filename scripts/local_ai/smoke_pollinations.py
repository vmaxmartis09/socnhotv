#!/usr/bin/env python3
"""Smoke script: Gọi thật Pollinations.ai sinh ảnh cho S01, S02, S03 của Tập 1 có kèm ảnh DNA tham chiếu."""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "data/projects/soc-nho-tv/content/episodes/ep01-nui-lua-trong-bung-bi/script.json"
SHOTS_DIR = REPO_ROOT / "data/projects/soc-nho-tv/shots"
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

DNA_MAP = {
    "soc_nho": REPO_ROOT / "data/projects/soc-nho-tv/characters/soc_nho/soc_nho_01.png",
    "de_mun": REPO_ROOT / "data/projects/soc-nho-tv/characters/de_mun/de_mun_01.png",
}

_URL_CACHE: dict[str, str] = {}


def upload_temp_reference(img_path: Path) -> str:
    """Tải ảnh tham chiếu lên host tạm (Litterbox Catbox, lưu 1 giờ) để lấy URL công khai truyền vào Pollinations."""
    cache_key = str(img_path)
    if cache_key in _URL_CACHE:
        return _URL_CACHE[cache_key]

    if not img_path.exists():
        raise FileNotFoundError(f"Không tìm thấy ảnh DNA: {img_path}")

    print(f"[*] Đang tải ảnh tham chiếu {img_path.name} ({img_path.stat().st_size} bytes) lên host tạm...")
    data = {"reqtype": "fileupload", "time": "1h"}
    files = {"fileToUpload": (img_path.name, img_path.read_bytes(), "image/png")}
    
    r = httpx.post("https://litterbox.catbox.moe/resources/internals/api.php", data=data, files=files, timeout=30)
    if r.status_code != 200 or not r.text.startswith("http"):
        raise RuntimeError(f"Lỗi tải ảnh lên Litterbox: {r.status_code} - {r.text[:200]}")
    
    url = r.text.strip()
    _URL_CACHE[cache_key] = url
    print(f"    -> URL tham chiếu: {url}")
    return url


def generate_with_pollinations(
    prompt: str,
    ref_url: str | None = None,
    width: int = 1280,
    height: int = 720,
    model: str = "flux",
    seed: int = 42,
    max_retries: int = 5,
) -> bytes:
    """Gọi Pollinations API sinh ảnh, tự động xử lý giới hạn tốc độ 45s."""
    encoded_prompt = urllib.parse.quote(prompt)
    query_parts = [
        f"width={width}",
        f"height={height}",
        f"model={model}",
        "nologo=true",
        f"seed={seed}",
    ]
    if ref_url:
        query_parts.append(f"image={urllib.parse.quote(ref_url)}")

    pollinations_key = os.environ.get("POLLINATIONS_API_KEY", "").strip()
    if pollinations_key:
        query_parts.append(f"key={pollinations_key}")

    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{'&'.join(query_parts)}"

    for attempt in range(1, max_retries + 1):
        t0 = time.time()
        print(f"[*] Gửi request tới Pollinations ({model}, {width}x{height}, lần {attempt})...")
        try:
            r = httpx.get(url, timeout=120, follow_redirects=True)
            elapsed = time.time() - t0
            ct = r.headers.get("content-type", "")
            
            if r.status_code == 200 and "image" in ct:
                print(f"    -> Thành công ({elapsed:.2f}s, {len(r.content)} bytes, {ct})")
                return r.content

            if r.status_code in (402, 429):
                # Giới hạn tốc độ IP
                msg = r.text
                retry_match = re.search(r"Retry after (\d+)s", msg)
                wait_sec = int(retry_match.group(1)) + 2 if retry_match else 46
                print(f"    [!] Chạm hạn mức tốc độ free: {msg[:120]}. Chờ {wait_sec}s...")
                time.sleep(wait_sec)
                continue

            print(f"    [!] HTTP {r.status_code}: {r.text[:200]}")
            time.sleep(5)
        except Exception as exc:
            print(f"    [!] Lỗi kết nối: {exc}. Chờ 5s...")
            time.sleep(5)

    raise RuntimeError(f"Hết lượt thử sinh ảnh từ Pollinations ({max_retries} lần thất bại).")


def main() -> None:
    print("=" * 70)
    print("SMOKE TEST: Sinh ảnh thật cho S01, S02, S03 (Tập 1) qua Pollinations")
    print("=" * 70)

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        script = json.load(f)

    # Tìm S01, S02, S03
    shots_to_run = ["S01", "S02", "S03"]
    found_shots = {}
    for scene in script.get("scenes", []):
        for shot in scene.get("shots", []):
            sid = shot.get("id")
            if sid in shots_to_run:
                found_shots[sid] = shot

    print(f"[*] Tìm thấy {len(found_shots)} shots trong kịch bản: {list(found_shots.keys())}")

    results = []
    for sid in shots_to_run:
        shot = found_shots.get(sid)
        if not shot:
            print(f"[!] Không tìm thấy shot {sid}")
            continue

        print(f"\n--- Tiến hành sinh ảnh cho {sid} ---")
        prompt = shot.get("imagePrompt", "")
        char_ids = shot.get("characterIds", [])
        print(f"  Nhân vật: {char_ids}")
        print(f"  Thoại: {shot.get('dialogue', '')}")

        # Tìm ảnh DNA tham chiếu chính
        primary_char = char_ids[0] if char_ids else "soc_nho"
        dna_path = DNA_MAP.get(primary_char)
        ref_url = None
        if dna_path and dna_path.exists():
            ref_url = upload_temp_reference(dna_path)

        out_file = SHOTS_DIR / f"G1_ep01_{sid}.png"
        img_bytes = generate_with_pollinations(
            prompt=prompt,
            ref_url=ref_url,
            width=1280,
            height=720,
            model="flux",
            seed=1000 + int(sid[-2:]),
        )

        out_file.write_bytes(img_bytes)
        print(f"  -> Đã lưu ảnh: {out_file.relative_to(REPO_ROOT)} ({len(img_bytes)} bytes)")
        results.append({
            "shotId": sid,
            "path": str(out_file),
            "bytes": len(img_bytes),
            "ref": str(dna_path) if dna_path else None,
        })

    print("\n" + "=" * 70)
    print("TỔNG KẾT KẾT QUẢ SINH ẢNH THẬT:")
    for r in results:
        print(f"  - {r['shotId']}: {r['path']} ({r['bytes']:,} bytes)")
    print("=" * 70)


if __name__ == "__main__":
    main()
