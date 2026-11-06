"""Studio Chat Assistant for Intelligence stream.

Handles natural language requests from Studio Chat tab for channel research,
KOC script generation, idea brainstorming, compliance checks, and strategy.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from socnhotv.intelligence.channel_analyze import analyze_channel
from socnhotv.intelligence.channel_ingest import ingest_channel, ingest_user_channel_data
from socnhotv.intelligence.compliance import check_and_clean_script
from socnhotv.intelligence.ideas import generate_ideas_batch, list_content_ideas, promote_idea
from socnhotv.intelligence.products import (
    Product,
    get_product,
    import_product_from_url,
    list_products,
    save_product,
)
from socnhotv.intelligence.script_gen import GeneratorType, generate_complete_script
from socnhotv.intelligence.strategy import generate_channel_strategy, load_channel_strategy


def handle_intel_chat(
    project_id: str,
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Process an intelligence chat command and return reply text and Studio actions."""
    p_strip = prompt.strip()
    p_lower = p_strip.lower()
    ctx = context or {}

    actions: List[Dict[str, Any]] = []

    # 1. URL pattern detection
    url_match = re.search(r"https?://[^\s]+", p_strip)
    found_url = url_match.group(0).rstrip(".,)") if url_match else None

    # --- A. Kiểm tra tuân thủ chính sách (Compliance) ---
    if any(k in p_lower for k in ["tuân thủ", "compliance", "từ cấm", "vi phạm", "kiểm tra kịch bản"]):
        # Extract text to check
        text_to_check = p_strip
        m_quote = re.search(r'["“\'](.*?)["”\']', p_strip, re.DOTALL)
        if m_quote:
            text_to_check = m_quote.group(1).strip()
        else:
            # Strip preamble
            text_to_check = re.sub(
                r"^(kiểm tra\s+)?(tuân thủ|compliance|từ cấm|chính sách)(\s+kịch bản)?[:\s\-]*",
                "",
                p_strip,
                flags=re.IGNORECASE,
            ).strip()

        if not text_to_check or len(text_to_check) < 5:
            return {
                "reply": (
                    "**[Kiểm tra Tuân thủ Chính sách Quảng cáo]**\n\n"
                    "Vui lòng cung cấp đoạn văn hoặc kịch bản cần kiểm tra. Ví dụ:\n"
                    "> *Kiểm tra tuân thủ: \"Sản phẩm này cam kết chữa khỏi 100% bệnh đau lưng và tốt nhất Việt Nam.\"*"
                ),
                "mode": "intel_compliance",
                "actions": [],
                "data_label": "DỮ LIỆU THẬT",
            }

        res = check_and_clean_script(text_to_check, is_affiliate=True)
        status_badge = "✅ HỢP LỆ" if res.passed else "⚠️ PHÁT HIỆN VI PHẠM"

        details = []
        for v in res.violations:
            details.append(f"- **{v.severity} ({v.category})**: {v.message}")
            if v.suggested_replacement:
                details.append(f"  *Thay thế đề xuất*: `{v.suggested_replacement}`")

        reply_md = (
            f"### Kết quả Kiểm tra Tuân thủ: {status_badge}\n\n"
            f"- **Trạng thái**: {'Không có vi phạm chính sách' if res.passed else f'Có {len(res.violations)} cảnh báo'}\n"
            f"- **Nhãn Tiếp thị (#affiliate)**: {'Đã tự động bổ sung' if res.disclosure_added else 'Đã có sẵn'}\n\n"
        )
        if details:
            reply_md += "#### Chi tiết vi phạm phát hiện:\n" + "\n".join(details) + "\n\n"

        reply_md += (
            "#### Bản văn bản đã được làm sạch và chuẩn hoá:\n"
            f"```text\n{res.modified_text}\n```"
        )

        return {
            "reply": reply_md,
            "mode": "intel_compliance",
            "actions": [],
            "data_label": "DỮ LIỆU THẬT",
            "compliance_result": res.model_dump(),
        }

    # --- B. Phân tích Kênh YouTube / TikTok (Channel Research) ---
    if any(k in p_lower for k in ["kênh", "channel", "đối thủ", "nghiên cứu kênh"]) and (
        found_url or "phân tích" in p_lower or "ingest" in p_lower or "học" in p_lower
    ):
        target_url = found_url
        if not target_url:
            return {
                "reply": (
                    "**[Nghiên cứu Kênh Đối thủ]**\n\n"
                    "Hãy dán đường dẫn kênh YouTube hoặc TikTok công khai bạn muốn nghiên cứu. Ví dụ:\n"
                    "> *Phân tích kênh https://www.youtube.com/@SocNhoTV*\n\n"
                    "Hệ thống sẽ bóc tách: lượt xem trung vị thực tế, tỷ lệ Shorts/Longs, lịch đăng, cụm chủ đề (Pillars) và công thức tiêu đề viral."
                ),
                "mode": "intel_channel",
                "actions": [],
                "data_label": "DỮ LIỆU THẬT",
            }

        try:
            meta = ingest_channel(project_id, target_url, max_videos=30, download_top_n=0)
            analysis = analyze_channel(project_id, meta["id"])
            stats = analysis.get("stats", {})
            pillars = analysis.get("pillars", [])
            patterns = analysis.get("title_patterns", [])

            reply_md = (
                f"### 📊 Phân tích Kênh: {meta.get('name', meta['id'])}\n\n"
                f"- **Nguồn dữ liệu**: {meta.get('data_label', 'DỮ LIỆU THẬT')} (Trích xuất công khai qua yt-dlp)\n"
                f"- **Tổng video phân tích**: {stats.get('total_videos', 0)}\n"
                f"- **Lượt xem trung vị (Median Views)**: {stats.get('median_views', 0):,} view\n"
                f"- **Lượt xem trung bình**: {stats.get('avg_views', 0):,} view\n"
                f"- **Phân bổ định dạng**: {stats.get('shorts_ratio', 0)*100:.0f}% Shorts / {stats.get('longs_ratio', 0)*100:.0f}% Video dài\n"
                f"- **Lịch đăng**: {stats.get('upload_cadence', 'N/A')} (Giờ hiển thị: {analysis.get('schedule_heatmap_status', 'N/A')})\n"
                f"- **Tỷ lệ giữ chân**: {stats.get('retention_note', 'Không có số liệu bịa đặt')}\n\n"
                f"#### 🎯 Các Pillars nội dung chủ đạo:\n"
            )
            for pi in pillars[:4]:
                reply_md += f"- **{pi['name']}**: {pi.get('video_pct', 0)}% số video ({pi.get('view_pct', 0)}% tổng lượt xem)\n"

            reply_md += "\n#### 📝 Mẫu tiêu đề viral phổ biến:\n"
            for tmpl in patterns[:3]:
                reply_md += f"- `{tmpl}`\n"

            actions.append({
                "type": "add_node",
                "nodeType": "channel_insight",
                "params": {"channel_url": target_url},
                "summaryVi": f"Thêm node Phân tích Kênh ({meta.get('name', 'Đối thủ')}) vào canvas",
            })

            return {
                "reply": reply_md,
                "mode": "intel_channel",
                "actions": actions,
                "data_label": "DỮ LIỆU THẬT",
                "channel_id": meta["id"],
                "analysis": analysis,
            }
        except Exception as e:
            return {
                "reply": f"❌ Lỗi khi tải dữ liệu kênh '{target_url}': {e}. Bạn có thể cung cấp danh sách video thủ công qua API user-data.",
                "mode": "intel_channel",
                "actions": [],
                "data_label": "MẪU",
            }

    # --- C. Sinh ý tưởng nội dung (Ideas Brainstorming) ---
    if any(k in p_lower for k in ["ý tưởng", "idea", "chủ đề", "gợi ý", "nội dung mới"]) and not any(
        k in p_lower for k in ["viết kịch bản", "tạo kịch bản", "kịch bản chi tiết"]
    ):
        count = 10
        m_num = re.search(r"\b(\d+)\s*(ý tưởng|chủ đề|video)\b", p_lower)
        if m_num:
            count = min(int(m_num.group(1)), 30)

        ideas = generate_ideas_batch(project_id, count=count)
        reply_md = (
            f"### 💡 Gợi ý {len(ideas)} Ý Tưởng Video KOC & Hoạt Hình Sóc Nhỏ\n"
            f"- **Bảo vệ chống sao chép**: Đã lọc qua RapidFuzz guardrail (< 70% trùng lặp đối thủ)\n"
            f"- **Trạng thái**: Đã ghi vào `content/ideas/` sẵn sàng lên lịch đăng\n\n"
        )
        for idx, ide in enumerate(ideas[:count], 1):
            reply_md += f"{idx}. **{ide.title}** (Độ ưu tiên: ⭐{ide.priority} | Template: `{ide.template_id}`)\n"

        actions.append({
            "type": "open_tab",
            "tab": "ideas",
            "summaryVi": "Mở danh sách ý tưởng nội dung",
        })

        return {
            "reply": reply_md,
            "mode": "intel_ideas",
            "actions": actions,
            "data_label": "DỮ LIỆU THẬT",
            "ideas": [i.model_dump() for i in ideas[:count]],
        }

    # --- D. Sinh kịch bản KOC / Review / Sales ---
    if any(k in p_lower for k in ["kịch bản", "script", "viết review", "bán hàng"]) or (
        "koc" in p_lower and any(v in p_lower for v in ["viết", "tạo", "soạn", "làm", "review", "chạy"])
    ):
        gen_type: GeneratorType = "koc_review"
        if "bán hàng" in p_lower or "sales" in p_lower or "tiktok shop" in p_lower:
            gen_type = "tiktok_sales"
        elif "so sánh" in p_lower or "compare" in p_lower:
            gen_type = "affiliate_compare"

        char_name = "LyLy"
        if "neau" in p_lower:
            char_name = "Neau"
        elif "sóc nhỏ" in p_lower or "soc nho" in p_lower or "bi" in p_lower:
            char_name = "Sóc Nhỏ"

        prods = list_products(project_id)
        matched_prod = None

        for pr in prods:
            if pr.name.lower() in p_lower:
                matched_prod = pr
                break

        if not matched_prod and prods:
            matched_prod = prods[0]

        if not matched_prod:
            matched_prod = save_product(
                project_id,
                Product(
                    id=f"prod_demo_{project_id}",
                    name="[MẪU] Kem Chống Nắng Quang Phổ Rộng Sóc Nhỏ",
                    brand="Sóc Nhỏ Lab",
                    price=289000,
                    usp=["Kháng nước 80 phút", "Kiềm dầu 12 tiếng"],
                    pain_points=["Kem bết dính và chảy vệt trắng"],
                    compliance_notes="[MẪU] Dữ liệu sản phẩm mẫu",
                ),
            )

        script_res = generate_complete_script(
            project_id=project_id,
            product=matched_prod,
            generator_type=gen_type,
            character_name=char_name,
            voice_id="soc-nho",
        )

        lines = script_res["lines"]
        hooks = script_res.get("hook_lab", [])

        reply_md = (
            f"### 🎬 Kịch bản KOC: {matched_prod.name}\n"
            f"- **Định dạng**: `{gen_type}` | **Nhân vật**: {char_name} | **Giọng đọc**: `soc-nho` (-14 LUFS)\n"
            f"- **Template gắn kết**: `{script_res['template_id']}`\n"
            f"- **Tuân thủ chính sách**: {'✅ Đã kiểm duyệt' if script_res['compliance_passed'] else '⚠️ Cần lưu ý'}\n\n"
            f"#### 🎯 Thử nghiệm Hook Lab (Video Craft A/B):\n"
        )
        for h in hooks:
            score_text = f"⭐ {h.get('score', 0):.0f}/100" if "score" in h else ""
            reply_md += f"- **Phương án {h.get('variant_id', 'A')}** ({h.get('archetype', '')}) {score_text}: \"{h.get('text', '')}\"\n"

        reply_md += "\n#### 📜 Kịch bản chi tiết theo phân cảnh:\n"
        for idx, l in enumerate(lines, 1):
            reply_md += f"{idx}. **[{l['role'].upper()}]** ({l['duration_s']}s): \"{l['text']}\"\n"

        actions.append({
            "type": "add_script",
            "scriptId": script_res["script_id"],
            "title": f"Review {matched_prod.name}",
            "templateId": script_res["template_id"],
            "summaryVi": f"Lưu kịch bản {matched_prod.name} vào danh sách kịch bản dự án",
        })

        return {
            "reply": reply_md,
            "mode": "intel_script",
            "actions": actions,
            "data_label": "DỮ LIỆU THẬT",
            "script_result": script_res,
        }

    # --- E. Quản lý sản phẩm (Products) ---
    if any(k in p_lower for k in ["sản phẩm", "product", "hàng hóa", "giỏ hàng"]):
        if found_url and ("nhập" in p_lower or "import" in p_lower or "thêm" in p_lower):
            extracted = import_product_from_url(found_url)
            p_id = f"prod_{re.sub(r'[^a-zA-Z0-9]+', '_', extracted.get('title', 'item'))[:16].lower()}"
            new_p = Product(
                id=p_id,
                name=extracted.get("title") or "Sản phẩm mới",
                price=float(extracted.get("price") or 0.0),
                usp=[extracted.get("description", "")] if extracted.get("description") else [],
                affiliate_links={"other": found_url},
                compliance_notes="Nhập từ OpenGraph công khai",
            )
            saved = save_product(project_id, new_p)
            return {
                "reply": (
                    f"✅ Đã nhập sản phẩm từ URL công khai:\n"
                    f"- **Tên**: {saved.name}\n"
                    f"- **Giá**: {saved.price:,.0f} {saved.currency}\n"
                    f"- **Mã ID**: `{saved.id}`\n\n"
                    f"Bạn có thể yêu cầu: *“Viết kịch bản KOC review cho sản phẩm {saved.name}”*."
                ),
                "mode": "intel_product",
                "actions": [],
                "data_label": "DỮ LIỆU THẬT",
                "product": saved.model_dump(),
            }

        prods = list_products(project_id)
        if not prods:
            return {
                "reply": "Hiện tại chưa có sản phẩm nào trong dự án. Bạn có thể dán đường dẫn sản phẩm công khai hoặc nhập thông tin sản phẩm mới.",
                "mode": "intel_product",
                "actions": [],
                "data_label": "DỮ LIỆU THẬT",
            }

        reply_md = f"### 🛍️ Danh sách Sản phẩm KOC ({len(prods)} sản phẩm):\n"
        for p in prods:
            reply_md += f"- **{p.name}** (`{p.id}`): {p.price:,.0f} {p.currency} | USP: {', '.join(p.usp[:2]) or 'N/A'}\n"

        return {
            "reply": reply_md,
            "mode": "intel_product",
            "actions": [],
            "data_label": "DỮ LIỆU THẬT",
            "products": [p.model_dump() for p in prods],
        }

    # --- F. Chiến lược kênh (Strategy) ---
    if any(k in p_lower for k in ["chiến lược", "strategy", "định hướng", "kpi"]):
        strat = load_channel_strategy(project_id)
        if not strat:
            strat = generate_channel_strategy(project_id, [])

        reply_md = (
            f"### 🎯 Chiến Lược Kênh & Định Vị Nội Dung Sóc Nhỏ TV\n\n"
            f"**Điểm khác biệt độc quyền**:\n{strat.get('differentiation', '')}\n\n"
            f"#### 📌 Phân bổ 4 Pillars Nội Dung:\n"
        )
        for pi in strat.get("our_pillars", []):
            reply_md += f"- **{pi['name']}** ({pi.get('target_ratio', 0)}%): {pi.get('description', '')}\n"

        kpis = strat.get("kpi_30d", {})
        reply_md += (
            f"\n#### 📈 Mục tiêu Kế hoạch 30 Ngày ({kpis.get('note', '[MẪU]')})\n"
            f"- Lượt xem mục tiêu: {kpis.get('target_total_views', 0):,}\n"
            f"- Người đăng ký mới: {kpis.get('target_subscribers', 0):,}\n"
            f"- Lượt click affiliate: {kpis.get('target_affiliate_clicks', 0):,}\n"
        )

        return {
            "reply": reply_md,
            "mode": "intel_strategy",
            "actions": [],
            "data_label": "DỮ LIỆU THẬT",
            "strategy": strat,
        }

    # --- Fallback hướng dẫn trợ lý Intelligence ---
    return {
        "reply": (
            "**[Trợ Lý Nghiên Cứu Kênh & Kịch Bản KOC SocNhoTV]**\n\n"
            "Tôi có thể hỗ trợ bạn trực tiếp các tác vụ sau:\n"
            "1. **Phân tích Kênh Đối Thủ**: *“Phân tích kênh https://youtube.com/@...”*\n"
            "2. **Sinh Kịch Bản KOC**: *“Viết kịch bản KOC review cho sản phẩm Kem Chống Nắng”*\n"
            "3. **Kiểm Tra Tuân Thủ**: *“Kiểm tra tuân thủ: Sản phẩm này cam kết chữa khỏi 100%...”*\n"
            "4. **Gợi Ý Ý Tưởng**: *“Gợi ý 10 ý tưởng video KOC mới”*\n"
            "5. **Quản Lý Sản Phẩm**: *“Danh sách sản phẩm”* hoặc *“Nhập sản phẩm từ https://...”*\n"
            "6. **Chiến Lược Kênh**: *“Xem chiến lược kênh và định hướng nội dung”*"
        ),
        "mode": "intel_help",
        "actions": [],
        "data_label": "DỮ LIỆU THẬT",
    }
