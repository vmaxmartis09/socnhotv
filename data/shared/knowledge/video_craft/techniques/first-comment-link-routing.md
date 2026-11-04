---
id: first-comment-link-routing
title: First-Comment Link Routing & Zero-Penalty Affiliate Funnel
status: in-studio
build: 'yes'
reproducible_with_our_stack: 'yes'
needs:
- Social Publishing Engine
- Caption Templates
implemented_in:
- tool/src/socnhotv/social/publishing_templates.py
- data/shared/knowledge/video_craft/playbooks/affiliate-links-and-first-comment.md
evidence_videos:
- seq_013
confidence: high
last_verified: '2026-11-04'
expires_at: never
tags:
- affiliate
- first-comment
- social-reach
- cta
- link-in-bio
---

# Kỹ Thuật: First-Comment Link Routing & Outbound Penalty Bypass

- **Mã kỹ thuật**: `first-comment-link-routing`
- **Nguồn cảm hứng**: Phân tích từ video `seq_013_1097086916506396` (Long Đình - Auto Traffic Pipeline)
- **Tags**: social-distribution | facebook-algorithm | publishing | affiliate | anti-penalty | session-c

---

## 1. Vấn Đề
- Cả Facebook, TikTok lẫn Instagram đều áp dụng hình phạt ngầm (Shadow Reach Penalty) đối với các bài đăng chứa đường dẫn bên ngoài (outbound links) trong nội dung chính (caption/post body). Thuật toán muốn giữ chân người dùng trong ứng dụng.
- Nếu gắn link mua hàng trực tiếp trong caption bài đăng, lượng người xem tự nhiên (organic reach) có thể tụt từ 50% đến 80%.

---

## 2. Giải Pháp Chuẩn Hóa Cho Dự Án `socnhotv`

### 2.1. Quy Trình Xuất Bản 2 Bước (2-Phase Publishing)
1. **Bước 1 (Clean Post Publishing)**:
   - Đăng video kèm caption thuần chữ, hashtag và lời kêu gọi: `"Link chi tiết sản phẩm / thông tin đầy đủ mình để ngay dưới bình luận đầu tiên nhé!"`.
2. **Bước 2 (Delayed First Comment Injection)**:
   - Đợi 5s - 15s sau khi post được tạo thành công trên Facebook Graph API / Browser Automation.
   - Gọi API tạo bình luận từ chính tài khoản vừa đăng bài với nội dung:
     `"👉 Xem chi tiết và săn ưu đãi tại đây: <link_affiliate_hoặc_landing_page>"`
   - Kích hoạt thao tác Ghim bình luận (Pin Comment) nếu nền tảng hỗ trợ.

### 2.2. Quy Chuẩn Cấu Hình Trong Metadata Xuất Bản
Trong file `package.json` của Session C:
```json
{
  "post_body": "Outfit dạo phố cực xinh cùng LyLy hôm nay ✨ Cả nhà thích mẫu nào nhất? Bình luận bên dưới nhé!",
  "first_comment": {
    "enabled": true,
    "delay_seconds": 10,
    "content": "✨ Link săn đầm NuNu ưu đãi độc quyền 30% hôm nay: https://socnhotv.vn/deal/nunu-dress",
    "pin": true
  }
}
```
