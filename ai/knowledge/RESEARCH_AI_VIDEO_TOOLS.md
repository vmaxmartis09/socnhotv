# Khảo sát cách người ta làm tool tạo video AI dạng canvas node (02-03/11/2026)

Nguồn: Agent Reach 1.6.1 (kênh GitHub, YouTube, Bilibili, web; chỉ đọc công khai, không đăng nhập). Mình chỉ đọc README và tài liệu, **chưa đọc mã nguồn và chưa chạy thử** tool nào. Số sao lấy từ GitHub ngày 03/11/2026; hầu hết dự án còn rất mới và nhỏ, nên xem là nguồn ý tưởng chứ chưa phải tiêu chuẩn đã kiểm chứng.

## 1. Dự án mã nguồn mở gần với yêu cầu của mình
| Dự án | Sao | Giấy phép | Điểm đáng học |
|---|---|---|---|
| [nodaroai/app.nodaro.ai](https://github.com/nodaroai/app.nodaro.ai) | 12 | Sustainable Use + Apache-2.0 (fair-code) | Backend REST là chính, giao diện canvas chỉ là một client. Chạy đồ thị phía máy chủ bằng hàng đợi BullMQ, không cần mở tab trình duyệt. 100+ loại node, 100+ model qua nhiều provider (KIE.ai, Replicate, fal, ElevenLabs, HeyGen...). Workflow là JSON mang đi được; đăng một workflow thành ứng dụng có giao diện, API, webhook và công cụ MCP (150+ tool). "Entity studio": nhân vật, địa điểm, đồ vật, giọng nói có bộ ảnh tham chiếu giữ nhất quán. Dựng phụ đề, lớp phủ bằng Remotion. Tự host bằng `docker compose up`. |
| [JustinPerea/nebula-nodes](https://github.com/JustinPerea/nebula-nodes) | 22 | AGPL-3.0 | Python (FastAPI) + React Flow + Zustand, chạy local, tự mang khóa API. Cổng có kiểu (ảnh, video, âm thanh, văn bản, 3D). Chạy một phần đồ thị, cache đồ thị con, xem trước dạng stream. Lưu dự án, đầu ra và lịch sử chạy ở local. Hạn mức chi tiêu cho agent: trần mỗi lần chạy, mỗi phiên chat, mỗi 24 giờ. Có CLI và MCP để Claude Code, Codex, Cursor điều khiển canvas. Có nút "quyết định" (hỏi một câu có/không hoặc chấm điểm về ảnh/văn bản) đặt giữa các node tạo, và đánh dấu kết quả "hết hạn" khi nguồn đổi chứ không tự chạy lại. |
| [SankaiAI/TwitCanva-Video-Workflow](https://github.com/SankaiAI/TwitCanva-Video-Workflow) | 291 | Apache-2.0 | Canvas vô hạn tạo video, TypeScript. Dự án nhiều sao nhất trong nhóm; chưa đọc kỹ. |
| [Mr-banananana/Banana_canvas](https://github.com/Mr-banananana/Banana_canvas) | 9 | MIT | Canvas vô hạn chạy local cho quy trình đa phương thức. |
| [doomL/OpenRouter-Studio](https://github.com/doomL/OpenRouter-Studio) | 5 | không rõ | Next.js tự host, nối LLM, ảnh, video qua một cổng OpenRouter. |
| [liaorunqing/FrameFlow](https://github.com/liaorunqing/FrameFlow) | 0 | MIT | Studio quảng cáo video theo kịch bản: chọn kịch bản, kiểm tra nhất quán hình ảnh, rồi tạo video. |
Ngoài ra có `ym1100/huobao-canvas`, `MiaoMint/vision-flow`, `YusufAlper17/Nexa-Canvas`, `veritasian/Ai-Canvas` (cùng ý tưởng, rất nhỏ).

## 2. Sản phẩm thương mại (đọc tài liệu công khai)
FLORA, Krea (Nodes), Figma Weave, Artlist Flows, Topview Canvas, PicLumen Canvas, và các canvas Trung Quốc như LibTV, Pavo, bản canvas chạy local trên Bilibili. Cách FLORA chạy node (docs.flora.ai):
- Chạy một node, hoặc chọn nhiều node rồi "Run all"; tối đa 50 node một lần; chạy theo thứ tự phụ thuộc.
- Đưa chuột lên nút chạy thấy giá credit; chọn nhiều node thấy tổng giá.
- Chạy một node **không** tự chạy các node phía trên; thiếu đầu vào thì báo "Can't run yet".
- Node phía dưới **không** tự chạy lại khi node phía trên đổi; mỗi lần chạy sinh ra một "generation" mới, không dùng cache; mỗi node giữ lịch sử các generation để chọn lại.
- Node văn bản nối vào node ảnh/video **thay thế** ô prompt của node đó.

## 3. Kết luận và điều áp dụng cho dự án
1. **Cách làm chung của nhóm tool này:** đồ thị có kiểu, các node gọi model qua API của bên thứ ba (fal, Replicate, KIE.ai, OpenRouter, Google...), người dùng mang khóa riêng hoặc dùng credit của nền tảng. Đúng hướng mình đã vạch trong Core.
2. **Chạy phía máy chủ, canvas chỉ là một client** (Nodaro, Nebula): đã có trong Core; thêm "đăng workflow thành API/MCP" làm mục tiêu về sau.
3. **Kết quả sinh ra không nên tự ghi đè.** FLORA giữ lịch sử generation theo node; Nebula đánh dấu "hết hạn" thay vì tự chạy lại. Vì model AI cho kết quả khác nhau mỗi lần và tốn tiền, nên: mỗi node có danh sách các lần sinh, người dùng "ghim" một lần làm đầu ra; đổi đầu vào chỉ đánh dấu hạ nguồn là cũ, không tự tạo lại. Bộ nhớ đệm theo mã băm vẫn dùng cho các bước xác định (ghép, dựng, đo), không dùng để chặn tạo lại ảnh/video khi người dùng bấm tạo lại.
4. **Cổng chấm điểm đặt giữa các bước tốn tiền** (Nebula "Jev"): hỏi model nhìn một câu như "nhân vật có đúng áo vàng quần đen không", pass thì mới chạy bước video đắt. Rất hợp với yêu cầu giữ nhân vật Sóc Nhỏ nhất quán.
5. **Hạn mức chi tiêu cho agent:** trần mỗi lần chạy và mỗi 24 giờ, áp dụng cả khi AI điều khiển studio qua MCP.
6. **Một khóa tổng hợp giảm số adapter:** các tool trên dùng KIE.ai, Replicate, fal, OpenRouter. Mình đã có logic fal.ai trong `video_gen_backends.py`; nên đi từ đó, rồi thêm Gemini/Veo.
7. **"Entity studio" (nhân vật, địa điểm, giọng) = Character trong dự án**, mở rộng thêm địa điểm và đồ vật có bộ ảnh tham chiếu.
8. **Giấy phép:** Nebula là AGPL-3.0 nên không chép mã vào dự án; Nodaro là fair-code, có giới hạn thương mại hóa; TwitCanva (Apache-2.0) và Banana_canvas (MIT) có thể tham khảo mã, giữ ghi công. Chỉ học ý tưởng, tự viết mã.

## 4. Chưa làm / chưa chắc
- Chưa đọc mã nguồn và chưa chạy thử dự án nào; chất lượng thực tế và độ bền chưa biết.
- Video Bilibili và YouTube chỉ lấy tiêu đề, chưa lấy phụ đề hay xem nội dung.
- Chưa so giá API của các nhà cung cấp.

## 5. Đã cài trên máy
Agent Reach 1.6.1 qua `uv tool install` (chỉ từ GitHub, không từ PyPI), dữ liệu ở `~/.agent-reach/`. Setup đã liên kết skill `agent-reach` vào thư mục skill của Claude Code, Cursor, Gemini CLI, OpenClaw (`~/.claude/skills`, `~/.cursor/skills`, `~/.gemini/skills`, `~/.openclaw/skills`). Các kênh đăng nhập (Twitter, Reddit, Instagram, ...) chưa bật. Gỡ: `agent-reach uninstall --dry-run` rồi `agent-reach uninstall`.
