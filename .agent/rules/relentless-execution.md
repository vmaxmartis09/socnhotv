---
trigger: always_on
description: Quy tắc bắt buộc MẶC ĐỊNH làm việc đến cùng, không bỏ cuộc, không cần gõ /goal
---

# RELENTLESS EXECUTION & NEVER SURRENDER PROTOCOL (DEFAULT / NO /GOAL NEEDED)

> [!CRITICAL]
> **MẶC ĐỊNH TỰ ĐỘNG KÍCH HOẠT: KHÔNG CẦN GÕ /GOAL**
> Mọi yêu cầu trong workspace này mặc định kích hoạt chế độ làm việc đến cùng, kiên trì tuyệt đối, tự sửa lỗi và hoàn thành triệt để mục tiêu mà KHÔNG CẦN người dùng phải gõ `/goal`.

1. **Cam kết hoàn thành mục tiêu đến cùng:**
   - Tuyệt đối không dừng lại, không kết luận "không làm được", không báo lỗi sơ sài khi chưa thử nghiệm ít nhất 3-5 giải pháp thay thế.
   - Luôn chủ động thay đổi selector, chuyển đổi chế độ Headless sang Headed, mô phỏng hành vi tự nhiên (stealth jitter), lắng nghe popup OAuth, và tái sử dụng session từ profile người dùng cung cấp.

2. **Xử lý tình huống nghẽn (Bot Detection / Captcha / 2FA):**
   - Với TikTok / Google / Web tasks: Ưu tiên sử dụng trình duyệt **Ego Lite** (thông qua skill `ego-browser` và CLI `ego-browser`), kết nối trực tiếp với phiên đăng nhập của người dùng.
   - Nếu xuất hiện yêu cầu OTP cá nhân hoặc Captcha trượt: Giữ nguyên trình duyệt mở trên màn hình, lưu ảnh vào `shots/`, thông báo rõ điểm cần người dùng hỗ trợ và ngay lập tức tiếp tục tự động hoàn thành 100% các bước còn lại ngay khi vượt qua.

3. **Xác thực kết quả thực tế:**
   - Luôn kiểm chứng bằng chứng hoàn thành (ảnh chụp màn hình trong `shots/`, URL đích, trạng thái đăng nhập) trước khi kết thúc tác vụ.

4. **Tự học, đúc kết kinh nghiệm & Tinh chỉnh liên tục:**
   - Sau mỗi chu kỳ thực thi, toàn bộ tri thức, công thức viral, dữ liệu chính sách và bài học kinh nghiệm phải được cập nhật vào `configs/koc_ai_knowledge_hub.json` và `configs/koc_learning_memory.json` qua `src/gobi/services/intelligence/continuous_learning_engine.py` để hệ thống tự tối ưu và không bao giờ lặp lại lỗi cũ.

5. **Công cụ Dựng & Biên Tập Video Chính: HeyGen HyperFrames (Mặc định bắt buộc):**
   - Từ nay về sau, **HeyGen HyperFrames** (`integrations/hyperframes/`, adapter: `src/gobi/adapters/integrations/hyperframes_adapter.py`, service: `src/gobi/services/media/hyperframes_engine.py`) là **CÔNG CỤ BIÊN TẬP & DỰNG VIDEO CHÍNH THỨC** của toàn bộ hệ sinh thái Gobi Social.
   - Toàn bộ video KOC AI, affiliate review thời trang và social clips được biên tập bằng composition HTML5/CSS/GSAP HyperFrames tất định, hỗ trợ chuẩn Safe Zone TikTok 9:16, kinetic subtitles, và multi-track audio ducking.

