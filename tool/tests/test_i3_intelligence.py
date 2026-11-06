"""Tests for Stream I3: Channel Intelligence, KOC Script Gen, Compliance, and Studio Integration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient

from socnhotv.core.api.app import app
from socnhotv.intelligence.channel_analyze import analyze_channel
from socnhotv.intelligence.channel_ingest import (
    generate_channel_id,
    ingest_channel,
    ingest_user_channel_data,
    parse_video_item,
)
from socnhotv.intelligence.chat_assistant import handle_intel_chat
from socnhotv.intelligence.compliance import check_and_clean_script
from socnhotv.intelligence.contracts import (
    Beat,
    ChannelBlueprint,
    VideoBlueprint,
    save_video_blueprint,
)
from socnhotv.intelligence.ideas import generate_ideas_batch, list_content_ideas, promote_idea
from socnhotv.intelligence.node_runner import execute_intel_node
from socnhotv.intelligence.patterns import aggregate_patterns
from socnhotv.intelligence.products import Product, list_products, save_product
from socnhotv.intelligence.script_gen import (
    generate_complete_script,
    generate_koc_hook_variants,
    generate_koc_review_script,
    generate_tiktok_sales_script,
)
from socnhotv.intelligence.strategy import generate_channel_strategy
from socnhotv.workspace import project_path


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# (1) Chạy thật với dữ liệu công khai hoặc dữ liệu người dùng đưa
# ---------------------------------------------------------------------------

def test_i3_parse_video_item_real_metrics_no_fabrication():
    """Kiểm tra parse_video_item: giữ nguyên số view thật, không bịa giờ hoặc retention."""
    entry = {
        "id": "vid_real_01",
        "title": "Bí Quyết Chọn Đồ Chơi Cho Bé",
        "view_count": 45200,
        "like_count": 3100,
        "comment_count": 180,
        "duration": 58.5,
        "upload_date": "20261101",
        "timestamp": 1793534400,  # Real epoch timestamp
    }
    parsed = parse_video_item(entry)
    assert parsed["id"] == "vid_real_01"
    assert parsed["view_count"] == 45200
    assert parsed["view_count_source"] == "REAL"
    assert parsed["upload_date"] == "20261101"
    assert parsed["upload_date_source"] == "REAL_TIMESTAMP"
    assert parsed["upload_hour"] is not None
    assert 0 <= parsed["upload_hour"] <= 23


def test_i3_ingest_user_channel_data_and_analyze():
    """Kiểm tra nạp dữ liệu kênh do người dùng cung cấp (manual user data)."""
    pid = "soc-nho-tv"
    user_videos = [
        {
            "id": "u_vid_1",
            "title": "Review Đèn Học Thông Minh Chống Cận Cho Bé",
            "view_count": 85000,
            "duration": 45.0,
            "upload_date": "20261101",
            "upload_hour": 19,
        },
        {
            "id": "u_vid_2",
            "title": "So Sánh 2 Hộp Bút Đa Năng",
            "view_count": 12000,
            "duration": 120.0,
            "upload_date": "20261103",
            "upload_hour": 12,
        },
        {
            "id": "u_vid_3",
            "title": "Mẹo Giữ Vở Sạch Chữ Đẹp",
            "view_count": 34000,
            "duration": 40.0,
            "upload_date": "20261104",
            "upload_hour": 20,
        },
    ]

    meta = ingest_user_channel_data(
        project_id=pid,
        channel_url="https://youtube.com/@KenhMeVaBe",
        channel_name="Kênh Mẹ & Bé Thật",
        raw_videos=user_videos,
    )

    assert meta["data_source"] == "USER_PROVIDED"
    assert meta["data_label"] == "DỮ LIỆU THẬT"
    assert meta["video_count"] == 3

    # Phân tích kênh
    analysis = analyze_channel(pid, meta["id"])
    assert analysis["data_label"] == "DỮ LIỆU THẬT"
    stats = analysis["stats"]
    assert stats["total_videos"] == 3
    assert stats["median_views"] == 34000  # Median of [85000, 34000, 12000]
    assert stats["retention_rate"] is None
    assert "Không bịa số liệu giữ chân" in stats["retention_note"]
    assert analysis["schedule_heatmap_status"] == "DỮ LIỆU THẬT"


# ---------------------------------------------------------------------------
# (2) Sinh ý tưởng, kịch bản KOC từ thông tin sản phẩm & kiểm tuân thủ chính sách
# ---------------------------------------------------------------------------

def test_i3_video_craft_hook_lab_and_koc_script():
    """Kiểm tra Video Craft Hook Lab sinh 3 biến thể A/B/C và chấm điểm hook."""
    prod = Product(
        id="prod_koc_test",
        name="Hộp Cơm Giữ Nhiệt Cắm Điện Sóc Nhỏ",
        brand="Sóc Nhỏ Life",
        price=320000,
        currency="VND",
        usp=["Giữ nóng 8 tiếng", "Khay inox 304 chuẩn an toàn"],
        pain_points=["Cơm trưa văn phòng nguội ngắt và mất ngon"],
    )

    # 1. Hook variants
    hooks = generate_koc_hook_variants(prod, character_name="LyLy")
    assert len(hooks) == 3
    archetypes = {h["archetype"] for h in hooks}
    assert "confession" in archetypes
    assert "paradox_question" in archetypes
    assert "problem_solution" in archetypes
    for h in hooks:
        assert "score" in h
        assert 0 <= h["score"] <= 100

    # 2. Complete script generation
    res = generate_complete_script(
        project_id="soc-nho-tv",
        product=prod,
        generator_type="koc_review",
        character_name="LyLy",
        voice_id="soc-nho",
    )
    assert res["template_id"] == "koc-review-v1"
    assert len(res["lines"]) == 5
    assert res["compliance_passed"]
    # Check honest con included in proof
    proof_line = next(l for l in res["lines"] if l["role"] == "proof")
    assert "điểm trừ" in proof_line["text"].lower() or "chấm em này 9/10" in proof_line["text"]
    # Check disclosure
    assert "#affiliate" in res["full_text"]


def test_i3_compliance_filter_full_enforcement():
    """Kiểm tra bộ lọc tuân thủ: chặn y tế, cam kết tuyệt đối, bôi nhọ, khan hiếm giả tạo."""
    dirty_text = (
        "Sản phẩm này cam kết chữa khỏi 100% bệnh đau khớp, đặc trị mọi loại sẹo. "
        "Đây là sản phẩm số 1 Việt Nam tốt nhất thế giới! "
        "Tẩy chay hãng XYZ vì toàn hàng rác rưởi. "
        "Chỉ còn duy nhất 1 suất ưu đãi hôm nay duy nhất!"
    )
    res = check_and_clean_script(dirty_text, is_affiliate=True)

    assert not res.passed
    assert len(res.violations) >= 4

    categories = {v.category for v in res.violations}
    assert "medical_claim" in categories
    assert "absolute_claim" in categories
    assert "defamation" in categories
    assert "fake_scarcity" in categories

    # Verifications in cleaned text
    assert "chữa khỏi 100%" not in res.modified_text
    assert "số 1 Việt Nam" not in res.modified_text
    assert "hàng rác rưởi" not in res.modified_text
    assert "chỉ còn duy nhất 1 suất" not in res.modified_text
    assert "#affiliate" in res.modified_text


# ---------------------------------------------------------------------------
# (3) Đưa kết quả vào Studio qua node hoặc chat thay vì trang riêng
# ---------------------------------------------------------------------------

def test_i3_studio_chat_assistant():
    """Kiểm tra trợ lý Chat trong Studio xử lý các lệnh nghiên cứu, kịch bản, tuân thủ."""
    pid = "soc-nho-tv"

    # A. Chat: Kiểm tra tuân thủ
    chat_comp = handle_intel_chat(
        project_id=pid,
        prompt="Kiểm tra tuân thủ kịch bản: Sản phẩm kem bôi cam kết khỏi bệnh 100% và là thần dược.",
    )
    assert chat_comp["mode"] == "intel_compliance"
    assert "Kết quả Kiểm tra Tuân thủ" in chat_comp["reply"]
    assert "bệnh đau" not in chat_comp["reply"] or "thần dược" in chat_comp["reply"]

    # B. Chat: Sinh kịch bản KOC
    chat_script = handle_intel_chat(
        project_id=pid,
        prompt="Viết kịch bản KOC review cho sản phẩm Kem Chống Nắng",
    )
    assert chat_script["mode"] == "intel_script"
    assert "Kịch bản KOC" in chat_script["reply"]
    assert len(chat_script["actions"]) > 0
    assert chat_script["actions"][0]["type"] == "add_script"

    # C. Chat: Gợi ý ý tưởng
    chat_ideas = handle_intel_chat(
        project_id=pid,
        prompt="Gợi ý 5 ý tưởng video KOC cho dự án",
    )
    assert chat_ideas["mode"] == "intel_ideas"
    assert "Gợi ý" in chat_ideas["reply"]
    assert len(chat_ideas["ideas"]) >= 5

    # D. Chat: Danh sách sản phẩm
    chat_prod = handle_intel_chat(
        project_id=pid,
        prompt="Xem danh sách sản phẩm",
    )
    assert chat_prod["mode"] == "intel_product"

    # E. Chat: Chiến lược kênh
    chat_strat = handle_intel_chat(
        project_id=pid,
        prompt="Xem chiến lược kênh và định hướng nội dung",
    )
    assert chat_strat["mode"] == "intel_strategy"
    assert "Chiến Lược Kênh" in chat_strat["reply"]


def test_i3_studio_node_runner_execution():
    """Kiểm tra thực thi các node Intelligence trên Studio Canvas."""
    pid = "soc-nho-tv"

    # 1. Node compliance_check
    c_res = execute_intel_node(
        project_id=pid,
        node_type="compliance_check",
        inputs={"text": "Sản phẩm tốt nhất thế giới cam kết khỏi bệnh hoàn toàn"},
    )
    assert not c_res["passed"]
    assert len(c_res["warnings"]) > 0
    assert "#affiliate" in c_res["clean_text"]

    # 2. Node script_from_blueprint
    s_res = execute_intel_node(
        project_id=pid,
        node_type="script_from_blueprint",
        params={"generator_type": "koc_review", "character_name": "LyLy"},
    )
    assert "script" in s_res
    assert "full_text" in s_res
    assert "render_request" in s_res
    assert len(s_res["hook_lab"]) == 3

    # 3. Node channel_insight (với user_videos)
    ch_res = execute_intel_node(
        project_id=pid,
        node_type="channel_insight",
        inputs={
            "channel_name": "Kênh Đồ Chơi Thông Minh",
            "user_videos": [
                {"id": "v1", "title": "Đập hộp đồ chơi xếp hình", "view_count": 50000, "duration": 40.0, "upload_date": "20261102"},
                {"id": "v2", "title": "Bí kíp rèn tính kiên nhẫn", "view_count": 25000, "duration": 50.0, "upload_date": "20261103"},
            ],
        },
    )
    assert "blueprint" in ch_res
    assert "pillars" in ch_res
    assert "summary" in ch_res
    assert "Phân tích Kênh: Kênh Đồ Chơi Thông Minh" in ch_res["summary"]


# ---------------------------------------------------------------------------
# (4) Gắn nhãn "MẪU" cho mọi số liệu giả hoặc thay bằng dữ liệu thật
# ---------------------------------------------------------------------------

def test_i3_sample_labels_and_strict_truthfulness():
    """Kiểm tra các số liệu mẫu đều được gắn nhãn MẪU rõ ràng, không bịa số liệu view."""
    pid = "soc-nho-tv-test-truth"

    # 1. Patterns khi chưa có blueprint: phải có nhãn MẪU
    patterns = aggregate_patterns(pid)
    assert patterns["data_status"] == "MẪU"
    assert "[MẪU]" in patterns["note"]

    # 2. Strategy KPI: phải có nhãn MẪU
    strat = generate_channel_strategy(pid, [])
    assert strat["kpi_30d"]["status"] == "MẪU"
    assert "[MẪU" in strat["kpi_30d"]["note"]

    # 3. Promote idea khi chưa có sản phẩm: sản phẩm fallback phải có nhãn [MẪU]
    ideas = generate_ideas_batch(pid, count=1)
    prom = promote_idea(pid, ideas[0].id)
    assert "[MẪU]" in prom["script_result"]["full_text"] or "[MẪU]" in prom["idea"]["title"] or "[MẪU]" in prom["script_result"]["lines"][0]["text"]


# ---------------------------------------------------------------------------
# API Routes Tests
# ---------------------------------------------------------------------------

def test_i3_api_chat_and_nodes_endpoints(client):
    """Kiểm tra các endpoints HTTP API của intel.py phục vụ Studio."""
    pid = "soc-nho-tv"

    # 1. POST /intel/chat
    r_chat = client.post(
        f"/projects/{pid}/intel/chat",
        json={"prompt": "Kiểm tra tuân thủ: Trị dứt điểm sẹo sau 3 ngày #quangcao"},
    )
    assert r_chat.status_code == 200
    data_chat = r_chat.json()
    assert data_chat["mode"] == "intel_compliance"

    # 2. POST /intel/nodes/execute
    r_node = client.post(
        f"/projects/{pid}/intel/nodes/execute",
        json={
            "node_type": "compliance_check",
            "inputs": {"text": "Trải nghiệm sản phẩm an toàn chuẩn chất lượng #affiliate"},
        },
    )
    assert r_node.status_code == 200
    data_node = r_node.json()
    assert data_node["passed"]

    # 3. POST /intel/compliance/check
    r_comp = client.post(
        f"/projects/{pid}/intel/compliance/check",
        json={"text": "Sản phẩm hỗ trợ cải thiện làn da #affiliate", "is_affiliate": True},
    )
    assert r_comp.status_code == 200
    assert r_comp.json()["passed"]
