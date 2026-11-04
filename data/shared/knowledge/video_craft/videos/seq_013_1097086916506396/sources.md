# Sources & Technical Verification: Seq 013

- **Video URL**: `https://www.facebook.com/share/v/19goEFh3Em/`
- **Canonical ID**: `1097086916506396`
- **Tác giả**: Long Đình
- **Bộ công cụ đề cập**: ViraAI (Video AI generator) + Loha Page (Facebook Fanpage matrix automation).

---

## 1. Bản Chất Kỹ Thuật Đã Xác Thực
1. **Kiến Trúc Tách Rời 2 Tầng (Decoupled 2-Stage Architecture)**:
   - Tầng 1: **Content Engine (ViraAI)**: Đảm nhận việc render video (Text-to-Video, Image-to-Video hoặc Video Inpainting).
   - Tầng 2: **Distribution Engine (Loha Page)**: Đảm nhận việc quản lý hàng chục/hàng trăm tài khoản mạng xã hội, chia lịch đăng bài (staggered publishing), chống checkpoint IP (proxy rotation) và kích hoạt hành vi tương tác sau khi đăng.
2. **Kỹ Thuật Rải Link "First-Comment"**:
   - Facebook thuật toán ngầm bóp tương tác (reach penalty) các bài viết có gắn link ngoài (outbound link) trực tiếp trong caption.
   - Chiến lược hiệu quả nhất là: Bài viết chỉ chứa chữ + video nguyên bản. Ngay sau khi bài lên sóng, hệ thống tự động đăng bình luận đầu tiên (First Comment) chứa link sản phẩm/affiliate và ghim lên đầu.
