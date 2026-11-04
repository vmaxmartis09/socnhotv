# Playbook 10: Vận Hành Hệ Thống Kênh Tự Động Quy Mô Lớn (Faceless Channel Scaling Mastery)

> Áp dụng cho: Mạng lưới 5–20 kênh TikTok / YouTube Shorts vệ tinh, nhà sáng tạo nội dung một người (Solopreneur), studio truyền thông tự động hoá  
> Mục tiêu cốt lõi: Đạt sản lượng 10–20 video chất lượng cao mỗi ngày với chi phí < $0.25/video, giảm 95% thời gian can thiệp thủ công.

---

## 1. Danh Sách Kỹ Thuật Sử Dụng
- [`tiered-channel-automation-engine`](../techniques/tiered-channel-automation-engine.md): Phân tách hệ thống thành 4 tầng sản xuất độc lập.
- [`llm-script-to-timeline-automation`](../techniques/llm-script-to-timeline-automation.md): Lắp ráp video tự động từ structured script JSON sang HyperFrames timeline.
- [`evergreen-shortform-foundations`](../techniques/evergreen-shortform-foundations.md): Xây dựng nội dung thường xanh, tạo giá trị lâu dài không lo hết trend.
- [`pre-publish-hook-retention-prediction`](../techniques/pre-publish-hook-retention-prediction.md): Chấm điểm và lọc hook trước khi bấm render hàng loạt.
- [`7-platform-automated-syndication-and-scope-locked-crm`](../techniques/7-platform-automated-syndication-and-scope-locked-crm.md): Phân phối nội dung đa kênh an toàn.

---

## 2. Quy Trình Vận Hành Hàng Ngày (Daily Operational Routine)

### Bước 1: Thu Hoạch Ý Tưởng Tự Động (08:00 - 08:30)
- Trình thu thập dữ liệu quét qua danh sách kênh tham chiếu trên TikTok / Douyin:
  - Lọc ra top 10% video có chỉ số tương tác vượt trội (Engagement Ratio > 8%).
  - Tự động đẩy dữ liệu thô vào `inbox/` và phân loại theo chủ đề.

### Bước 2: Sinh Kịch Bản Đa Biến Thể (08:30 - 09:30)
- LLM xử lý từng ý tưởng thành 3 biến thể kịch bản với 3 phong cách Hook khác nhau:
  - *Biến thể 1 (Tò mò - Curiosity):* Khơi gợi bí mật chưa ai tiết lộ.
  - *Biến thể 2 (Mất mát - Loss Aversion):* Cảnh báo sai lầm gây tốn kém tiền bạc.
  - *Biến thể 3 (Lợi ích tức thì - Quick Win):* Hướng dẫn 3 bước làm được ngay.

### Bước 3: Đồng Bộ Âm Thanh & Bóc Tách Phụ Đề (09:30 - 10:30)
- Tự động sinh giọng đọc qua OmniVoice SOTA voice-id `soc-nho`.
- Trích xuất word-level timestamps qua `faster-whisper` chạy trên GPU cục bộ (7 giây/file).

### Bước 4: Render Tất Định Hàng Loạt Qua HyperFrames CLI (10:30 - 11:30)
- Khởi chạy render hàng loạt:
  `python -m socnhotv --project soc-nho-tv video render --batch --limit 20`
- Toàn bộ video được xuất trực tiếp vào thư mục xuất bản với định dạng chuẩn 1080x1920 30fps.

### Bước 5: Đăng Tải & Đo Lường Vòng Lặp Phản Hồi (12:00 - Hết ngày)
- Lên lịch đăng trải đều các khung giờ vàng (11:30, 18:00, 20:30).
- Sau 24h, đọc số liệu thực tế nạp ngược vào `CONTINUITY.md` để hệ thống tự tối ưu prompt kịch bản cho ngày hôm sau.

---

## 3. Bản Đồ Phân Bổ Kênh Vệ Tinh (Channel Topology)

```
[Master AI Knowledge Hub]
           │
  ┌────────┼────────┐
  ▼        ▼        ▼
[Kênh A] [Kênh B] [Kênh C]
(Sóc Nhỏ) (Tips AI) (Review)
  │        │        │
  └────────┼────────┘
           ▼
[Hàng Đợi Render HyperFrames]
           │
           ▼
[20 Video / Ngày Hoàn Chỉnh]
```

---

## 4. Bảng Tiêu Chí Giám Sát & Ngưỡng An Toàn (Safety Thresholds)
- **Khoảng cách đăng giữa các video:** Tối thiểu 3 tiếng giữa 2 lần đăng trên cùng 1 kênh để không bị thuật toán coi là spam.
- **Tỷ lệ giữ chân 3s đầu (3s Hook Retention):** Nếu < 60% liên tục 5 video, lập tức dừng kịch bản đó và đổi phong cách mở đầu.
- **Cảnh báo bản quyền âm thanh:** Luôn dùng kho BGM và SFX bản quyền miễn phí hoặc âm thanh do AI sinh ra.
