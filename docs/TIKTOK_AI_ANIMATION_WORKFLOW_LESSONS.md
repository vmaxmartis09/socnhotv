# Kinh nghiệm từ video TikTok: quy trình làm kênh hoạt hình AI bằng Claude

Nguồn: video TikTok của @huandaotaoyoutube (Huan.academy), 2:27, hướng dẫn xây kênh hoạt hình dạy tiếng Anh (kênh mẫu "Family Life English"). Xem ngày 01/11/2026.

Ghi chú: đây là bản diễn giải bằng lời của mình theo cấu trúc prompt trong video, không chép nguyên văn. Video chỉ cho thấy prompt lướt qua màn hình, nhiều đoạn bị che mờ hoặc cuộn nhanh, nên phần chi tiết dưới đây là phần đọc được rõ.

## 1. Quy trình 4 bước trong video

| Bước | Việc | Công cụ | Đầu ra |
|---|---|---|---|
| 1 | Lên ý tưởng bằng AI | Claude (Opus, effort cao) | Danh sách 35 tiêu đề ý tưởng |
| 2 | Viết kịch bản | Claude, cùng cuộc hội thoại | Kịch bản hội thoại 4.500 từ |
| 3 | Tạo prompt ảnh và video | Claude | Bảng prompt nhân vật, rồi prompt từng cảnh |
| 4 | Tạo ảnh và video | Google Flow (công cụ tự tạo "AI Director Foundation") | Ảnh nhân vật, clip từng cảnh |
| 5 | Dựng | CapCut | Video hoàn chỉnh |

Lưu ý hiển thị trong video: ở bước 1, phần ngoặc trống (chủ đề) được thay bằng chủ đề cần chọn; chủ đề đó phải khớp với chủ đề đã chọn ở bước 1 khi sang bước 2.

## 2. Cấu trúc từng prompt (diễn giải)

### Prompt 1 — Lên ý tưởng (planner)
- Vai trò: người lên kế hoạch nội dung cho kênh YouTube truyện nghe tiếng Anh chậm, nhẹ nhàng, trình độ A2.
- Công thức kênh: nhân vật cố định (hai bé, bố mẹ, người lớn phụ), mỗi tập là một tình huống đời thường, có cảm xúc (sợ, tò mò, nhẹ nhõm) và kết có bài học.
- Định dạng đầu ra: chỉ trả về tiêu đề, kiểu gợi tò mò, kèm 1 đến 3 emoji, kết thúc bằng nhãn cấp độ.
- Mục tiêu: sinh hàng loạt (35) ý để chọn.

### Prompt 2 — Viết kịch bản
- Vai trò: biên kịch kênh, cùng dàn nhân vật cố định.
- Đầu vào: "MAIN TOPIC" là tiêu đề đã chọn.
- Luật quan trọng nhất: một video là một **tuyển tập 4 đến 6 truyện ngắn độc lập** nối nhau. Truyện đầu bám chủ đề chính, kết thúc gọn rồi cắt sang truyện mới ở bối cảnh khác với cùng gia đình, và lặp lại cho đủ thời lượng.
- Độ dài: mục tiêu khoảng 4.500 từ thoại; mỗi truyện tự dài ngắn khác nhau, không gộp thành một truyện.
- Phong cách thoại: câu ngắn, từ đơn giản, lặp lại, có người dẫn tự kể ("tôi đang trèo", "tay tôi với tới"), có trấn an.
- Đầu ra: chỉ thoại, mỗi câu một dòng, có nhãn tên người nói. Cấm tiêu đề, đề mục, chỉ dẫn sân khấu, số từ, bình luận.

### Prompt 3 — Biến kịch bản thành bộ prompt hình ảnh (tài liệu có nhiều phần)
Video nhấn mạnh "copy đoạn prompt thứ 3 trong tài liệu", tức tài liệu gồm vài prompt đánh số, mỗi prompt một bước.

Phần A — **Character reference (nền trắng, sinh trước)**:
- Với mỗi nhân vật lặp lại, viết một prompt ảnh tham chiếu: toàn thân, đầu đến chân, đứng thẳng chính diện, tư thế trung tính, nhìn vào camera, **nền trắng thuần #FFFFFF**, ánh sáng studio đều, không đạo cụ, không bối cảnh, không nhân vật khác.
- **Khóa thiết kế** bằng mô tả cố định (tóc, mắt, da, quần áo, giày) và dùng đúng cụm đó ở mọi chỗ sau.
- Dùng chung một "style bible" (3D hoạt hình kiểu Pixar, bóng, mắt biểu cảm).
- Có thêm dòng "consistency keywords" ngắn để dán lại khi cần.
- Giọng nói cũng được khóa: mỗi nhân vật một mô tả giọng (tuổi, âm sắc, tốc độ).

Phần B — **Prompt từng cảnh (beat)**: mỗi beat có
```
Script line(s): "..."          # câu thoại của beat
Characters in frame: ...
Image prompt: ...              # ảnh tĩnh, không có chữ trong ảnh
Video prompt (Veo 3): ...      # chuyển động + thoại trong ngoặc kép gán cho đúng người nói
```
Quy tắc đầu ra của phần B:
1. Phủ toàn bộ kịch bản, không tóm tắt, không bỏ beat.
2. Mỗi prompt ảnh/video tự đứng được (dán thẳng vào model là chạy).
3. Mỗi câu thoại phải xuất hiện nguyên văn trong video prompt của beat đó, ghi rõ ai nói, không bỏ lời.
4. Mỗi beat dài 3 đến 8 giây trên màn hình; thoại dài quá 8 giây thì tách beat.
5. Không nhân vật nào đổi trang phục, kiểu tóc hay giọng giữa các beat.
6. Cuối prompt có chỗ dán nguyên kịch bản.

### Bước 4 — Thao tác trên Google Flow
- Mở công cụ riêng (dựng bằng chức năng tạo công cụ trong Flow), cấu hình model ảnh (Nano Banana Pro), model video (Omni Flash), số lượng đầu ra.
- Tạo nhân vật trước: dán prompt ảnh nhân vật, ra ảnh nền trắng, đặt tên nhân vật (ví dụ "Leo") và lưu vào mục Nhân vật.
- Chuyển sang tab Kịch bản: dán danh sách beat theo định dạng **`[Image Prompt] | [Video Prompt]`** (ngăn cách bằng dấu gạch đứng), nhấn "Phân tích cảnh", công cụ tách thành từng cảnh rồi sinh ảnh và video hàng loạt.
- Kết quả: clip có thoại khớp môi, phụ đề chạy theo, nhân vật nhất quán.

## 3. Điều rút ra cho project SocNhoTV

### Giống những gì project đã có (xác nhận hướng đi đúng)
- Skill `flow-auto-video` đã có cùng kiến trúc: kịch bản, Character Bible, 3 lớp prompt, một cụm `[STYLE]` nguyên văn, mỗi cảnh một hành động.
- Hồ sơ nhân vật Sóc Nhỏ có `prompt_lock`, ảnh chuẩn trong `assets/soc_nho`, đúng tinh thần "character reference nền trơn, khóa mô tả".
- Dựng bằng HyperFrames thay CapCut, đã đúng chuẩn của project.

### Nên bổ sung vào quy trình
1. **Tuyển tập nhiều truyện ngắn thay vì một truyện dài.** Một video dài gồm 4 đến 6 mini-story độc lập cùng dàn nhân vật, mỗi truyện có bối cảnh, sự cố, bài học riêng. Dễ giữ chất lượng, dễ tái sử dụng nhân vật, hợp video dài cho trẻ. Áp dụng khi làm tập dài của Sóc Nhỏ.
2. **Sinh hàng loạt ý tưởng rồi mới chọn.** Yêu cầu 30 đến 35 tiêu đề một lần, chọn một. Prompt ý tưởng nên ép đầu ra chỉ là tiêu đề theo mẫu, không giải thích, để dễ lọc.
3. **Ràng buộc đầu ra "sạch" cho kịch bản.** Chỉ thoại, mỗi câu một dòng, có nhãn người nói, cấm đề mục, chỉ dẫn, đếm từ. Giúp bước sau (TTS, tách beat) chạy được tự động, không phải dọn tay.
4. **Mỗi beat 3 đến 8 giây, thoại dài thì tách beat.** Khớp giới hạn clip của Veo, tránh clip bị cắt giữa câu. Nên thêm vào quy tắc của `flow-auto-video`.
5. **Thoại nguyên văn nằm trong video prompt, gán đúng người nói.** Để model lồng tiếng đúng nhân vật; cấm bỏ lời hay viết lại. Đây là điểm quyết định chuyện khớp môi.
6. **Định dạng cặp prompt `[Image Prompt] | [Video Prompt]` mỗi beat.** Đủ để một công cụ hàng loạt tự tách. Nếu sau này tự động hóa Flow, dùng chính định dạng này làm file đầu vào.
7. **Khóa giọng cùng lúc với khóa hình.** Hồ sơ Sóc Nhỏ hiện khóa ngoại hình; nên thêm mô tả giọng cố định (tuổi, âm sắc, tốc độ) cho từng nhân vật phụ để lồng tiếng nhất quán, liên kết với `vietnamese-voice-clone`.
8. **Nhãn trình độ và nhịp lặp cho nội dung dạy học.** Nếu làm dòng dạy tiếng Anh/tiếng Việt cho bé: câu ngắn, từ lặp, người dẫn tự kể, có câu trấn an.
9. **Dùng đúng ảnh chuẩn có sẵn.** Điểm video làm ở bước nhân vật (sinh ảnh nền trắng) project đã làm xong; theo ghi nhớ, tải ảnh chuẩn `soc_nho_01.png` lên mục Nhân vật của Flow, không sinh nhân vật mới.

### Việc chưa làm (đề xuất, chưa tự ý sửa skill)
- Thêm vào `.agents/skills/flow-auto-video/SKILL.md` mục "mô hình tuyển tập mini-story" và quy tắc beat 3 đến 8 giây.
- Tạo mẫu `inputs/` cho prompt ý tưởng (35 tiêu đề) và prompt kịch bản sạch.
- Thêm trường giọng nói vào `assets/soc_nho/soc_nho_profile.json`.

## 4. Tìm nguồn tool "AI Director Foundation" (kiểm tra 01/11/2026)

Kết luận ngắn: **không có bản công khai**. Đây là một *Google Flow Tool* do Huan.academy tự tạo, phát qua cộng đồng/khóa học của họ.

Bằng chứng:
- Bio TikTok của Huan.academy dẫn tới cộng đồng Skool `faceless-youtube-foundation`; video cuối nhắc "khóa FYF" đóng gói chi tiết các nội dung này.
- Phần bình luận (103) toàn người xin prompt và xin tool, chưa thấy link công khai; tool và tài liệu prompt có vẻ chỉ gửi cho người trong cộng đồng.
- GitHub code search "AI Director Foundation": chỉ ra các repo không liên quan (tên trùng chữ). WebSearch hai lượt: không có link chia sẻ Flow Tool nào.
- Không đi tìm cách vượt qua cổng thành viên: đó là nội dung có thu phí của tác giả.

Về bản chất tool (Flow Tools, theo trang trợ giúp Google Labs):
- Tạo bằng cách mô tả bằng ngôn ngữ tự nhiên ở Tools > Create Tool, Flow tự viết mã và giao diện; cần gói AI Plus/Pro/Ultra.
- Chia sẻ bằng link; ai có link đều xem được mã; có nút Remix để sao chép và sửa.
- Tool chạy sinh ảnh/video sẽ tốn credit Flow.

Hướng tự làm (khả thi, không cần bản gốc):
1. **Flow Tool riêng:** mô tả tool hai giai đoạn như trong video (Nhân vật rồi Kịch bản; chọn model ảnh, model video, thời lượng; dán danh sách `[Image Prompt] | [Video Prompt]`; nút "Phân tích cảnh"), nhân vật mặc định là Sóc Nhỏ (`assets/soc_nho`).
2. **Chạy cục bộ:** repo công khai gần nhất là `ffroliva/gflow-cli` (MIT, alpha, có `gflow character`, `gflow movie` nhiều cảnh, MCP server; rủi ro tài khoản do tự động hóa trình duyệt). Project đã có sẵn `scripts/flow_ai/` và skill `flow-auto-video`, nên nên so sánh trước khi thêm công cụ ngoài.
3. Repo tham khảo quy trình: `schoolwindows/dreamina-story-director` (checkpoint duyệt, lưu `submit_id` để không trả phí hai lần).

## 5. Bổ sung: tài liệu "IMAGE & VIDEO" (prompt thứ 3), đọc thêm lượt 2

Tài liệu Google Docs trong video có ít nhất 3 prompt, mỗi prompt một tab/phần (có đoạn hiển thị trang 7/14). Prompt thứ 3 mở đầu bằng tiêu đề "IMAGE & VIDEO". Cấu trúc (diễn giải):

1. **Vai trò:** vừa là art director vừa là prompt engineer cho kênh truyện thiếu nhi hoạt hình 3D; nhiệm vụ là biến một kịch bản toàn thoại thành gói prompt sẵn sàng sinh: ảnh tham chiếu nhân vật, prompt ảnh từng cảnh, prompt video từng cảnh.
2. **Thứ tự bắt buộc:** làm theo đúng các STEP, không đảo.
3. **STYLE BIBLE (áp vào mọi prompt ảnh và video):** mỗi mục một dòng cố định: chất liệu (3D CGI bóng, điện ảnh, chi tiết cao, mềm mại; không phẳng, không 2D), nhân vật (dễ thương, mắt to bóng, má hồng, mũi nhỏ, tỉ lệ trẻ em 4 đến 7 tuổi), ánh sáng (ấm, mềm, rực rỡ), độ sâu trường ảnh (chủ thể nét, nền mờ nhẹ), màu (rực nhưng cân bằng), môi trường (bán thực tế, đồ vật nhìn thật), khung hình (16:9, độ phân giải cao, không chữ, không watermark, không phụ đề trong ảnh).
4. **Câu "đuôi style":** một đoạn tóm tắt style ngắn nối vào cuối mọi prompt ảnh, cố định nguyên văn.
5. **VOICE BIBLE:** video tạo bằng Veo 3 (có tiếng), nên mỗi nhân vật có mô tả giọng cố định (tuổi, âm sắc, tính cách giọng) và dùng y nguyên ở mọi cảnh.
6. **STEP 1:** ảnh tham chiếu nhân vật nền trắng (xem mục 2 ở trên). **STEP sau:** prompt từng beat (xem mục 2).

Phần chưa đọc được: nội dung ô "Phân tích cảnh" của công cụ và phần giữa/cuối tài liệu bị làm mờ hoặc cuộn quá nhanh. Đoạn đầu prompt chủ đề cũng bị mờ ở khung giữa.

Lý do không chép nguyên văn: các prompt là tài liệu của tác giả trong khóa học/cộng đồng trả phí, nên mình ghi cấu trúc và ý bằng lời của mình, đủ để tự viết lại phiên bản riêng cho Sóc Nhỏ.
