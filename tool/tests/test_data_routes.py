from fastapi.testclient import TestClient

from socnhotv.core.api.app import app

client = TestClient(app)


def test_projects_come_from_project_json():
    r = client.get("/data/projects")
    assert r.status_code == 200
    p = next(x for x in r.json() if x["id"] == "soc-nho-tv")
    assert p["name"] == "Sóc Nhỏ TV" and p["defaultVoiceId"] == "soc-nho"
    assert p["charactersCount"] == 2


def test_characters_have_real_profile_and_images():
    chars = {c["id"]: c for c in client.get("/data/projects/soc-nho-tv/characters").json()}
    assert chars["soc_nho"]["heightCm"] == 100 and chars["koala"]["heightCm"] == 150
    assert "squirrel" in chars["soc_nho"]["promptLock"]
    imgs = chars["soc_nho"]["referenceImages"]
    assert imgs and client.get(imgs[0]).status_code == 200


def test_channels_empty_not_invented():
    assert client.get("/data/projects/soc-nho-tv/channels").json() == []


def test_file_route_blocks_traversal_and_bad_types():
    assert client.get("/data/projects/soc-nho-tv/files/..%2F..%2Fworkspace.json").status_code in (403, 404)
    assert client.get("/data/projects/soc-nho-tv/files/project.json").status_code == 200
    assert client.get("/data/projects/nope/characters").status_code == 404


def test_character_create_and_delete_do_not_touch_real_data(tmp_path, monkeypatch):
    import json

    from socnhotv.core.api import data_routes

    proj = tmp_path / "data" / "projects" / "demo"
    proj.mkdir(parents=True)
    (proj / "project.json").write_text(
        json.dumps({"id": "demo", "name": "Demo", "default_character": "a", "characters": {"a": {"name": "A"}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(data_routes, "get_repo_root", lambda: tmp_path)

    body = {"id": "b", "name": "B", "role": "supporting", "heightCm": 120, "voiceId": "v", "promptLock": "pl",
            "memory": {"personality": "vui", "catchphrases": ["hi"]}}
    r = client.post("/data/projects/demo/characters", json=body)
    assert r.status_code == 200 and r.json()["heightCm"] == 120 and r.json()["promptLock"] == "pl"
    assert client.post("/data/projects/demo/characters", json=body).status_code == 409
    assert client.post("/data/projects/demo/characters", json={**body, "id": "../x"}).status_code == 400

    assert client.delete("/data/projects/demo/characters/a").status_code == 200
    ids = [c["id"] for c in client.get("/data/projects/demo/characters").json()]
    assert ids == ["b"]
    assert client.delete("/data/projects/demo/characters/a").status_code == 404


def test_image_and_voice_upload_use_temp_root(tmp_path, monkeypatch):
    import base64
    import json

    from socnhotv.core.api import data_routes

    proj = tmp_path / "data" / "projects" / "demo"
    proj.mkdir(parents=True)
    (proj / "project.json").write_text(
        json.dumps({"id": "demo", "characters": {"a": {"name": "A", "voice_id": "va"}}}), encoding="utf-8"
    )
    monkeypatch.setattr(data_routes, "get_repo_root", lambda: tmp_path)
    b64 = base64.b64encode(b"x").decode()

    r = client.post("/data/projects/demo/characters/a/images", json={"name": "p.png", "data": b64})
    assert r.status_code == 200 and len(r.json()["referenceImages"]) == 1
    assert client.post("/data/projects/demo/characters/a/images", json={"name": "p.txt", "data": b64}).status_code == 400
    r = client.delete("/data/projects/demo/characters/a/images/p.png")
    assert r.json()["referenceImages"] == [] and (proj / "characters/a/_removed/p.png").exists()

    r = client.post("/data/voices/va/samples", json={"name": "s.mp3", "data": b64})
    assert r.json()["files"][0]["name"] == "s.mp3"
    assert client.get("/data/voices/va/s.mp3").status_code == 200
    assert client.post("/data/voices/../samples", json={"name": "s.mp3", "data": b64}).status_code in (400, 404)
