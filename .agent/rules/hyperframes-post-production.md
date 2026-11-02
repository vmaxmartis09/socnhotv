# MANDATORY VIDEO POST-PRODUCTION DIRECTIVE: HEYGEN HYPERFRAMES

> [!CRITICAL]
> **MẶC ĐỊNH BẮT BUỘC: HEYGEN HYPERFRAMES LÀ CÔNG CỤ HẬU KỲ & BIÊN TẬP DUY NHẤT**
> Mọi tác vụ liên quan đến dựng video, biên tập hậu kỳ, chèn phụ đề, nhãn giá, sticker giỏ hàng, ghép cảnh hoặc xuất bản video KOC AI trong workspace này BẮT BUỘC phải sử dụng **HeyGen HyperFrames**.

1. **Tuyệt đối không dùng phương pháp cũ:**
   - Cấm viết các script FFmpeg filtergraph ghép nối thủ công phức tạp hoặc script concat binary cũ cho mục đích dựng video chính thức.
   - Toàn bộ pipeline biên tập video sử dụng HyperFrames HTML5, CSS3, Web Animations và timing tracks `data-*`.

2. **Các thành phần cốt lõi:**
   - Service: `src/gobi/services/media/hyperframes_engine.py` (`HyperFramesEngine`).
   - Adapter: `src/gobi/adapters/integrations/hyperframes_adapter.py` (`HyperFramesAdapter`).
   - Standard: `docs/HYPERFRAMES_POST_PRODUCTION_STANDARD.md`.

3. **Tiêu chuẩn TikTok Safe Zone 9:16:**
   - Độ phân giải: 1080x1920 dọc.
   - Top Safe Zone: Tránh 180px trên cùng (header TikTok).
   - Bottom Safe Zone: Tránh 320px dưới cùng (giỏ hàng vàng & controls).
   - Right Safe Zone: Chừa 140px lề phải cho cụm nút tương tác.
   - Phụ đề động (Karaoke / Kinetic) đặt tại `bottom: 380px` - `420px`.

4. **Đa luồng âm thanh & Audio Ducking:**
   - Luồng Voiceover chính mức 1.0 (-14 LUFS).
   - Luồng BGM tự động ducking xuống 0.18 khi có tiếng nói.
