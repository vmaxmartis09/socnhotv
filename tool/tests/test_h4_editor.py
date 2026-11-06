from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from socnhotv.core.api.app import app
from socnhotv.core.engine.edit_decisions import EditDecisionsManager
from socnhotv.core.storage.project_store import ProjectStore


def _file_sha(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture
def test_setup(tmp_path):
    """Thiết lập môi trường test độc lập trong tmp_path."""
    project_id = "test-h4-proj"
    store = ProjectStore(project_id)
    # Trỏ store sang tmp_path
    store.project_dir = tmp_path / "data" / "projects" / project_id

    ep_dir = store.project_dir / "content" / "episodes" / "ep01-test"
    ep_dir.mkdir(parents=True, exist_ok=True)

    # Tạo kịch bản mẫu script.json
    script_data = {
        "id": "ep01-test",
        "title": "Tập thử nghiệm H4",
        "durationSec": 60,
        "aspect": "16:9 Widescreen",
        "scenes": [
            {
                "index": 1,
                "title": "Cảnh 1",
                "shots": [
                    {
                        "id": "S01",
                        "sceneIndex": 1,
                        "durationSec": 10.0,
                        "shotSize": "WS",
                        "camera": "push-in",
                        "speaker": "Sóc Bi",
                        "speakerId": "soc_nho",
                        "characters": ["Sóc Bi"],
                        "dialogue": "Chào các bạn nhỏ!",
                        "imagePrompt": "Bi waving",
                        "videoPrompt": "Bi waving 5s",
                        "priority": 1,
                        "sfx": "chim hót",
                        "bgm": "nhạc vui",
                    },
                    {
                        "id": "S02",
                        "sceneIndex": 1,
                        "durationSec": 10.0,
                        "shotSize": "CU",
                        "camera": "pan-left",
                        "speaker": "Dê Mun",
                        "speakerId": "de_mun",
                        "characters": ["Dê Mun"],
                        "dialogue": "Mun cũng muốn chơi!",
                        "imagePrompt": "Mun smiling",
                        "videoPrompt": "Mun running 5s",
                        "priority": 2,
                        "sfx": "bước chân",
                        "bgm": "nhạc vui",
                    },
                    {
                        "id": "S03",
                        "sceneIndex": 1,
                        "durationSec": 10.0,
                        "shotSize": "MCU",
                        "camera": "static",
                        "speaker": "Sóc Bi",
                        "speakerId": "soc_nho",
                        "characters": ["Sóc Bi"],
                        "dialogue": "Cùng hít thở nào!",
                        "imagePrompt": "Bi breathing",
                        "videoPrompt": "Bi breathing 5s",
                        "priority": 3,
                        "sfx": "chuông reo",
                        "bgm": "nhạc vui",
                    },
                ],
            }
        ],
    }

    script_path = ep_dir / "script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)

    manager = EditDecisionsManager(store)
    return {
        "project_id": project_id,
        "episode_id": "ep01-test",
        "store": store,
        "manager": manager,
        "script_path": script_path,
    }


def test_script_json_never_mutated(test_setup):
    """Kiểm tra: script.json không bao giờ bị sửa đổi trong suốt quá trình chỉnh sửa."""
    manager = test_setup["manager"]
    ep_id = test_setup["episode_id"]
    script_path = test_setup["script_path"]

    sha_before = _file_sha(script_path)

    # Thực hiện một chuỗi thao tác chỉnh sửa
    manager.apply_decision(ep_id, "reorder", params={"order": ["S02", "S01", "S03"]})
    manager.apply_decision(ep_id, "update_duration", shot_id="S01", params={"durationSec": 15.5})
    manager.apply_decision(ep_id, "replace_media", shot_id="S02", params={"mediaSrc": "custom.mp4"})
    manager.apply_decision(ep_id, "toggle_shot", shot_id="S03", params={"enabled": False})
    manager.apply_decision(ep_id, "update_subtitle", shot_id="S01", params={"subtitle": "Lời thoại mới"})

    sha_after = _file_sha(script_path)
    assert sha_before == sha_after, "LỖI BẢO MẬT: script.json đã bị sửa đổi trực tiếp!"


def test_reorder_shots(test_setup):
    """Kiểm tra đổi thứ tự shot và tự động tính lại mốc thời gian startSec / endSec."""
    manager = test_setup["manager"]
    ep_id = test_setup["episode_id"]

    res = manager.apply_decision(ep_id, "reorder", params={"order": ["S03", "S01", "S02"]})
    shots = res["effectiveShots"]

    assert [s["shotId"] for s in shots] == ["S03", "S01", "S02"]
    # Kiểm tra tính toán timeline nối tiếp
    assert shots[0]["startSec"] == 0.0
    assert shots[0]["endSec"] == 10.0
    assert shots[1]["startSec"] == 10.0
    assert shots[1]["endSec"] == 20.0
    assert shots[2]["startSec"] == 20.0
    assert shots[2]["endSec"] == 30.0


def test_update_shot_duration(test_setup):
    """Kiểm tra đổi thời lượng shot: thời lượng cập nhật và timeline co giãn chuẩn xác."""
    manager = test_setup["manager"]
    ep_id = test_setup["episode_id"]

    manager.apply_decision(ep_id, "update_duration", shot_id="S01", params={"durationSec": 25.0})
    shots = manager.get_effective_shots(ep_id)

    s01 = next(s for s in shots if s["shotId"] == "S01")
    s02 = next(s for s in shots if s["shotId"] == "S02")
    assert s01["durationSec"] == 25.0
    assert s01["endSec"] == 25.0
    assert s02["startSec"] == 25.0
    assert s02["endSec"] == 35.0


def test_replace_media_and_subtitle(test_setup):
    """Kiểm tra thay thế hình ảnh/clip và sửa phụ đề."""
    manager = test_setup["manager"]
    ep_id = test_setup["episode_id"]

    manager.apply_decision(ep_id, "replace_media", shot_id="S01", params={"mediaSrc": "content/episodes/ep01-test/clips/S01_new.mp4"})
    manager.apply_decision(ep_id, "update_subtitle", shot_id="S01", params={"subtitle": "Câu chào mới"})

    shots = manager.get_effective_shots(ep_id)
    s01 = next(s for s in shots if s["shotId"] == "S01")
    assert s01["mediaSrc"] == "content/episodes/ep01-test/clips/S01_new.mp4"
    assert s01["subtitle"] == "Câu chào mới"
    assert s01["isModified"] is True


def test_toggle_shot(test_setup):
    """Kiểm tra tắt/bật shot: shot tắt thì không chiếm thời lượng trong timeline hữu dụng."""
    manager = test_setup["manager"]
    ep_id = test_setup["episode_id"]

    manager.apply_decision(ep_id, "toggle_shot", shot_id="S02", params={"enabled": False})
    shots = manager.get_effective_shots(ep_id)

    s02 = next(s for s in shots if s["shotId"] == "S02")
    s03 = next(s for s in shots if s["shotId"] == "S03")
    assert s02["enabled"] is False
    # S01 (10s) -> S02 tắt -> S03 bắt đầu ngay tại 10s
    assert s03["startSec"] == 10.0


def test_selective_rerender_caching_and_benchmark(test_setup):
    """Kiểm tra RENDER VI SAI:
    - Lượt 1: Render 3 shot lần đầu (chưa có cache).
    - Lượt 2: Chỉ sửa 1 shot -> kiểm tra CHỈ RENDER 1 SHOT, 2 shot kia trúng cache.
    - Đo thời gian render lại (dưới ngưỡng yêu cầu).
    """
    manager = test_setup["manager"]
    ep_id = test_setup["episode_id"]

    # Đặt thời lượng ngắn cho test chạy siêu nhanh (mỗi shot 1.0s)
    manager.apply_decision(ep_id, "update_duration", shot_id="S01", params={"durationSec": 1.0})
    manager.apply_decision(ep_id, "update_duration", shot_id="S02", params={"durationSec": 1.0})
    manager.apply_decision(ep_id, "update_duration", shot_id="S03", params={"durationSec": 1.0})

    # Lượt 1: Render ban đầu
    t0 = time.time()
    res1 = manager.selective_rerender(ep_id)
    dur1 = time.time() - t0

    assert res1["status"] == "success"
    assert res1["renderedShotsCount"] == 3
    assert res1["cachedShotsCount"] == 0
    assert Path(res1["outputFullPath"]).is_file()
    assert os.path.getsize(res1["outputFullPath"]) > 1000

    # Lượt 2: Chỉ sửa DUY NHẤT shot S02 (đổi subtitle/lời thoại)
    manager.apply_decision(ep_id, "update_subtitle", shot_id="S02", params={"subtitle": "Phụ đề S02 đã đổi"})

    t1 = time.time()
    res2 = manager.selective_rerender(ep_id)
    dur2 = time.time() - t1

    assert res2["status"] == "success"
    # CHỈ render lại đúng 1 shot S02!
    assert res2["renderedShotsCount"] == 1
    # 2 shot S01 và S03 được tái sử dụng từ cache!
    assert res2["cachedShotsCount"] == 2
    # Đo thời gian render lại: cực nhanh (thường dưới 2.0s trên Mac M4)
    assert dur2 < dur1 or dur2 < 5.0
    print(f"\n[BENCHMARK] Lần đầu (3 shot): {dur1:.3f}s | Lần 2 (chỉ 1 shot đổi): {dur2:.3f}s (nhanh hơn {dur1/max(0.01, dur2):.1f}x)")


def test_api_routes(test_setup, monkeypatch):
    """Kiểm tra các endpoint REST API của editor."""
    manager = test_setup["manager"]
    store = test_setup["store"]
    project_id = test_setup["project_id"]
    ep_id = test_setup["episode_id"]

    # Vá _get_manager để dùng store test
    from socnhotv.core.api.routes import editor as editor_module
    monkeypatch.setattr(editor_module, "_get_manager", lambda pid: manager)

    client = TestClient(app)

    # 1. GET /projects/{id}/editor/{ep}
    res = client.get(f"/projects/{project_id}/editor/{ep_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["episodeId"] == ep_id
    assert len(data["shots"]) == 3

    # 2. POST /projects/{id}/editor/{ep}/decisions
    body = {
        "action": "update_duration",
        "shotId": "S01",
        "params": {"durationSec": 18.0},
    }
    res_dec = client.post(f"/projects/{project_id}/editor/{ep_id}/decisions", json=body)
    assert res_dec.status_code == 200
    data_dec = res_dec.json()
    assert data_dec["status"] == "success"
    s01 = next(s for s in data_dec["effectiveShots"] if s["shotId"] == "S01")
    assert s01["durationSec"] == 18.0

    # 3. POST /projects/{id}/editor/{ep}/render
    # Set duration 1.0s để test render chạy siêu tốc
    client.post(
        f"/projects/{project_id}/editor/{ep_id}/decisions",
        json={"action": "update_duration", "shotId": "S01", "params": {"durationSec": 1.0}},
    )
    client.post(
        f"/projects/{project_id}/editor/{ep_id}/decisions",
        json={"action": "update_duration", "shotId": "S02", "params": {"durationSec": 1.0}},
    )
    client.post(
        f"/projects/{project_id}/editor/{ep_id}/decisions",
        json={"action": "update_duration", "shotId": "S03", "params": {"durationSec": 1.0}},
    )

    res_render = client.post(f"/projects/{project_id}/editor/{ep_id}/render", json={"forceAll": False})
    assert res_render.status_code == 200
    render_data = res_render.json()
    assert render_data["status"] == "success"
    assert "videoUrl" in render_data


def test_real_episode_ep01_editing():
    """Kiểm tra trực tiếp trên kịch bản thực tế của Tập 1 (30 shots)."""
    project_id = "soc-nho-tv"
    ep_id = "ep01-nui-lua-trong-bung-bi"
    store = ProjectStore(project_id)
    manager = EditDecisionsManager(store)

    script_path = manager.get_script_path(ep_id)
    if not script_path.is_file():
        pytest.skip(f"Không có kịch bản thực tế {script_path}")

    sha_orig = _file_sha(script_path)

    # 1. Đọc danh sách shot ban đầu
    shots = manager.get_effective_shots(ep_id)
    assert len(shots) == 30, f"Mong đợi 30 shots cho Tập 1, thực tế: {len(shots)}"

    # 2. Đổi thời lượng shot S07 từ 20s thành 15s
    res_dur = manager.apply_decision(ep_id, "update_duration", shot_id="S07", params={"durationSec": 15.0})
    s07 = next(s for s in res_dur["effectiveShots"] if s["shotId"] == "S07")
    assert s07["durationSec"] == 15.0
    assert s07["isModified"] is True

    # 3. Sửa phụ đề của S10
    res_sub = manager.apply_decision(ep_id, "update_subtitle", shot_id="S10", params={"subtitle": "Bi hít thở thật sâu nào!"})
    s10 = next(s for s in res_sub["effectiveShots"] if s["shotId"] == "S10")
    assert s10["subtitle"] == "Bi hít thở thật sâu nào!"

    # 4. Tắt shot S15
    res_tog = manager.apply_decision(ep_id, "toggle_shot", shot_id="S15", params={"enabled": False})
    s15 = next(s for s in res_tog["effectiveShots"] if s["shotId"] == "S15")
    assert s15["enabled"] is False

    # 5. Kiểm tra script.json KHÔNG BỊ CHẠM ĐẾN
    assert _file_sha(script_path) == sha_orig, "script.json của ep01 đã bị thay đổi!"

    # 6. Đặt lại toàn bộ (reset_all) để hoàn trả trạng thái sạch
    manager.apply_decision(ep_id, "reset_all")
    clean_shots = manager.get_effective_shots(ep_id)
    assert all(not s["isModified"] for s in clean_shots)
    assert all(s["enabled"] for s in clean_shots)
