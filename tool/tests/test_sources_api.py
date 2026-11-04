from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from socnhotv.core.api.app import app
from socnhotv.workspace import project_path

client = TestClient(app)


def test_sources_ping():
    res = client.get("/sources/_ping")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "module": "sources"}


def test_sources_local_upload_and_lifecycle():
    # 1. Create a dummy minimal video file
    dummy_bytes = b"fake video content for testing lifecycle"
    file_payload = {"file": ("test_clip.mp4", io.BytesIO(dummy_bytes), "video/mp4")}

    res = client.post("/projects/soc-nho-tv/sources", files=file_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "file"
    source = data["source"]
    source_id = source["id"]
    assert source["title"] == "test_clip.mp4"
    assert source["rights"] == "owned"

    # 2. Get source details
    res_get = client.get(f"/projects/soc-nho-tv/sources/{source_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == source_id

    # 3. List sources
    res_list = client.get("/projects/soc-nho-tv/sources?platform=local")
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(i["id"] == source_id for i in items)

    # 4. Stream/get file
    res_file = client.get(f"/projects/soc-nho-tv/sources/{source_id}/file/meta.json")
    assert res_file.status_code == 200
    assert "id" in res_file.json()

    # 5. Delete to trash
    res_del = client.get(f"/projects/soc-nho-tv/sources/{source_id}")
    assert res_del.status_code == 200

    res_del_action = client.delete(f"/projects/soc-nho-tv/sources/{source_id}")
    assert res_del_action.status_code == 200

    # Ensure it's no longer in active sources
    res_get_after = client.get(f"/projects/soc-nho-tv/sources/{source_id}")
    assert res_get_after.status_code == 404

    # Verify moved to trash
    trash_path = project_path("soc-nho-tv", "raw", "_trash", source_id)
    assert trash_path.exists()


def test_sources_rights_guard():
    # Test strict rights switching from reference_only
    # Manually create a reference_only source item
    from socnhotv.sources.models import SourceItem
    item = SourceItem(
        id="ref_test_001",
        project_id="soc-nho-tv",
        platform="youtube",
        url="https://youtube.com/watch?v=ref1",
        rights="reference_only",
    )
    meta_p = project_path("soc-nho-tv", "raw", "ref_test_001", "meta.json", ensure=True)
    with open(meta_p, "w", encoding="utf-8") as f:
        f.write(item.model_dump_json())

    # Try changing to owned WITHOUT confirm_rights -> expect HTTP 400
    res_fail = client.patch(
        "/projects/soc-nho-tv/sources/ref_test_001",
        json={"rights": "owned", "confirm_rights": False},
    )
    assert res_fail.status_code == 400
    assert "confirm_rights=true" in res_fail.json()["detail"]

    # Now change WITH confirm_rights=true -> expect HTTP 200
    res_ok = client.patch(
        "/projects/soc-nho-tv/sources/ref_test_001",
        json={"rights": "owned", "confirm_rights": True, "rights_note": "Approved by legal owner"},
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["rights"] == "owned"

    # Cleanup test item
    import shutil
    shutil.rmtree(meta_p.parent)
