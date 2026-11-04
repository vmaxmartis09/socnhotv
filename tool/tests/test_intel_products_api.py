from __future__ import annotations

from fastapi.testclient import TestClient
from socnhotv.core.api.app import app

client = TestClient(app)


def test_intel_ping():
    res = client.get("/intel/_ping")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "module": "intel"}


def test_products_crud_api():
    pid = "prod_api_test_99"
    product_payload = {
        "id": pid,
        "name": "Bình Nước Hoạt Hình Sóc Nhỏ",
        "brand": "SocNhoTV",
        "category": "kids",
        "price": 120000,
        "sale_price": 99000,
        "currency": "VND",
        "usp": ["giữ nhiệt 12h", "inox 316 an toàn"],
        "pain_points": ["bình dễ đổ vỡ"],
        "affiliate_links": {
            "tiktok_shop": "https://tiktok.com/@socnhotv/live",
            "shopee": "https://shopee.vn/socnhotv",
        },
    }

    # 1. Create
    res_create = client.post("/projects/soc-nho-tv/products", json=product_payload)
    assert res_create.status_code == 200
    assert res_create.json()["id"] == pid

    # 2. Get
    res_get = client.get(f"/projects/soc-nho-tv/products/{pid}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Bình Nước Hoạt Hình Sóc Nhỏ"

    # 3. List
    res_list = client.get("/projects/soc-nho-tv/products")
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(i["id"] == pid for i in items)

    # 4. Update
    product_payload["price"] = 135000
    res_update = client.put(f"/projects/soc-nho-tv/products/{pid}", json=product_payload)
    assert res_update.status_code == 200
    assert res_update.json()["price"] == 135000

    # 5. Delete to trash
    res_del = client.delete(f"/projects/soc-nho-tv/products/{pid}")
    assert res_del.status_code == 200
    assert "thùng rác" in res_del.json()["message"]

    # Verify 404 after delete
    res_after = client.get(f"/projects/soc-nho-tv/products/{pid}")
    assert res_after.status_code == 404
