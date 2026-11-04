from fastapi.testclient import TestClient

from socnhotv.core.api.app import app

client = TestClient(app)


def test_list_has_soc_nho_with_sample_and_usage():
    v = {x["id"]: x for x in client.get("/voices").json()}
    assert "soc-nho" in v and v["soc-nho"]["hasSample"]
    assert any(u["characterId"] == "soc_nho" for u in v["soc-nho"]["usedBy"])
    assert client.get(v["soc-nho"]["sampleUrl"]).status_code == 200


def test_clone_requires_consent_valid_name_and_type():
    body = b"x" * 10
    r = client.post("/voices/clone?name=be-test&filename=a.mp3", content=body)
    assert r.status_code == 400 and "đồng ý" in r.json()["detail"]
    assert client.post("/voices/clone?name=BAD NAME&filename=a.mp3&consent=true", content=body).status_code == 400
    assert client.post("/voices/clone?name=be-test&filename=a.exe&consent=true", content=body).status_code == 400
    assert client.post("/voices/clone?name=soc-nho&filename=a.mp3&consent=true", content=body).status_code == 409
    assert client.post("/voices/clone?name=be-test&filename=a.mp3&consent=true", content=b"").status_code == 400


def test_project_voice_clone_validation():
    # 1. Thiếu consent
    r = client.post("/projects/soc-nho-tv/voice/clone", json={"voiceId": "test-v"})
    assert r.status_code == 400 and "đồng ý" in r.json()["detail"]

    # 2. Thiếu tệp âm thanh nguồn
    r = client.post("/projects/soc-nho-tv/voice/clone", json={"voiceId": "test-v", "consentConfirmed": True})
    assert r.status_code == 400 and "âm thanh nguồn" in r.json()["detail"]


def test_global_voice_clone_validation():
    # Kiểm tra endpoint toàn cục /voices/clone có thể gọi bất cứ đâu không cần projectId
    r = client.post("/voices/clone", json={"voiceId": "test-global"})
    assert r.status_code == 400 and "đồng ý" in r.json()["detail"]

    r = client.post("/voices/clone", json={"voiceId": "test-global", "consentConfirmed": True})
    assert r.status_code == 400 and "âm thanh nguồn" in r.json()["detail"]


