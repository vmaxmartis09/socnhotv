---
id: niche-opportunity-index
title: Niche Opportunity Index & Market Gap Discovery
status: knowledge
build: 'no'
reproducible_with_our_stack: partial (Mô hình tính điểm thị trường bằng tay/kịch bản;
  ngoài core video engine)
needs:
- Market Search Data
implemented_in: []
evidence_videos:
- seq_010
confidence: medium
last_verified: '2026-11-04'
expires_at: '2027-11-04'
tags:
- market-research
- niche-index
- strategy
- ecommerce
---

# Kỹ Thuật: Niche Opportunity Index & Series Framing

- **Mã kỹ thuật**: `niche-opportunity-index`
- **Nguồn cảm hứng**: Phân tích từ video `seq_011_2112433349657962` (An Ong - 30-Day YouTube Journey)
- **Tags**: analytics | niche-research | audience-clustering | youtube-algorithm | series-framing | hyperframes

---

## 1. Bản Chất Kỹ Thuật
Khi bắt đầu một kênh hoặc tuyến nội dung mới, sai lầm phổ biến nhất là chọn chủ đề theo cảm tính hoặc nhìn vào tổng lượng view khổng lồ của ngách đó.
Kỹ thuật này đưa ra 2 công cụ định lượng và định hình:

### 1.1. Chỉ Số Cơ Hội Ngách (New Channel Win Rate - NCWR)
$$\text{NCWR} = \frac{\text{Số lượng video }> 50\text{k views từ kênh }< 12\text{ tháng tuổi}}{\text{Tổng số video được đề xuất trong ngách (Top 100)}}$$

- **NCWR < 15% (Vùng Biển Đỏ / Neo Kín Tàu Lớn)**:
  - Khán giả trung thành với nhân vật / thương hiệu cũ. Thuật toán ưu tiên kênh có độ tin cậy lịch sử cao. Kênh mới không nên lao vào trực diện.
- **NCWR > 35% (Vùng Biển Xanh / Đang Khát Nội Dung Mới)**:
  - Khán giả quan tâm tới giải pháp / thông tin / trải nghiệm mới hơn là tên tuổi người đăng. Kênh mới có xác suất bùng nổ đề xuất cao gấp 5-10 lần.

### 1.2. Khung Kịch Bản Chuỗi "Hành Trình N Ngày" (Series Journey Blueprint)
- **Tên chuỗi**: `[Hành trình N ngày] + [Mục tiêu rõ ràng có thể đo đếm] + [Tại nền tảng / Trong lĩnh vực]`.
- **Cấu trúc mỗi tập**:
  - `[0 - 5s]`: Nhắc lại bối cảnh chuỗi: "Hành trình N ngày... Ngày X: [Chủ đề con]".
  - `[5 - 25s]`: Reframing tư duy: Đập tan một hiểu lầm phổ biến bằng một nguyên lý cốt lõi.
  - `[25 - 80%]`: Dữ liệu hoặc hành động thực tế đã làm trong ngày hôm đó (không lý thuyết suông).
  - `[Cuối video]`: Khóa mở vòng lặp (Open Loop) cho ngày tiếp theo.
