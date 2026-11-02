---
name: flow-auto-video
description: "Biến một ý tưởng kịch bản ngắn thành video hoàn chỉnh trên Google Flow: tự viết kịch bản phân cảnh, Character Bible nhất quán, sinh 3 lớp prompt (Character ref sheet, Storyboard frame, Video prompt có neo style), và tự động hóa thao tác trình duyệt qua Ego Lite hoặc Chrome để tạo nhân vật, storyboard, và render video từng cảnh trên labs.google/flow. Dùng khi user đưa ý tưởng + lưu ý và muốn 'tạo video tự động qua Google Flow'. KHÔNG ghép/edit video cuối — đó là bước CapCut của user."
disable-model-invocation: true
---

# Flow Auto Video (Google Flow × AI Agent)

> Kế thừa kiến trúc sản xuất video tự động đa tầng: Từ ý tưởng ngắn $\rightarrow$ Kịch bản phân cảnh $\rightarrow$ Character Bible $\rightarrow$ 3 lớp Prompt $\rightarrow$ Tự động hóa điều khiển Google Flow (`labs.google/flow`) qua Ego Lite Browser.

---

## 1. NGUYÊN TẮC CỐT LÕI (BẮT BUỘC TUÂN THỦ)

1. **In từng lớp ra chat — Không chạy ngầm:**
   - Mỗi lớp text (Kịch bản, Character Bible, 3 loại prompt) **bắt buộc phải in ra chat ngay khi hoàn thành** để người dùng duyệt.
   - Khi thao tác trên Google Flow, báo tiến độ theo từng hành động cụ thể (*"Đã submit nhân vật A, đang chờ render hoàn tất"*) — tuyệt đối không im lặng tới cuối.
   - Sửa kịch bản ở bước đầu rẻ hơn rất nhiều so với việc sửa sau khi đã đốt hàng chục credit render video.

2. **Một cụm `[STYLE]` nguyên văn xuyên suốt 100%:**
   - Cụm từ phong cách đã chốt (ví dụ: `warm Pixar-style 3D animation` hoặc `hyper-realistic cinematic fashion KOC`) phải xuất hiện **nguyên văn từng chữ** trong Character Reference, Storyboard và Video Prompt.
   - Tuyệt đối không diễn đạt lại hay thay đổi từ ngữ, vì model của Flow sẽ đổi phong cách giữa ảnh tĩnh và video clip.

3. **Một cảnh — Một hành động duy nhất:**
   - Khung hình 8 giây chỉ chứa **đúng 1 hành động chính** rõ ràng. Không gộp 2-3 hành động dồn dập vào 1 cảnh vì model sẽ sinh clip lộn xộn hoặc vỡ hình.

4. **Neo màu sắc và ánh sáng (`CRITICAL: preserve EXACTLY`):**
   - Trong prompt video, câu mở đầu luôn phải chứa chỉ thị giữ phong cách:
     `"CRITICAL: preserve EXACTLY the same [STYLE], lighting, and color palette shown."`

---

## 2. QUY TRÌNH THỰC THI 7 BƯỚC

### BƯỚC 0 — CHỐT THÔNG TIN & DỰ TOÁN CREDIT

1. Nhận ý tưởng và lưu ý từ người dùng (theo mẫu `inputs/idea-brief.md`):
   - Ý tưởng kịch bản (3–6 câu: nhân vật, bối cảnh, xung đột, cái kết).
   - Phong cách hình ảnh (`[STYLE]`).
   - Tỉ lệ khung hình (9:16 dọc hoặc 16:9 ngang).
   - Số cảnh (3–6 cảnh) và thời lượng mỗi cảnh (4s / 6s / 8s).
   - Voiceover (không thoại / lồng tiếng có sẵn / lồng sau).
   - Yếu tố cấm kỵ (không chữ trong hình, không logo, không jump-cut).
2. Hỏi lại nếu thiếu thông tin quan trọng.
3. **Ước lượng Credit:** Báo số lượt generate dự kiến theo công thức:
   $$\text{Credit dự kiến} = (\text{Số nhân vật} + \text{Số cảnh} \times 2) \times 1.3$$
   *(Ví dụ: 2 nhân vật + 4 cảnh = 2 + 8 = 10 lượt cơ bản + 3-5 lượt dự phòng re-gen $\approx$ 13–15 credit).*
4. In bảng chốt thông tin và chờ người dùng gõ xác nhận ("OK" / "Tiến hành").

---

### BƯỚC 1 — KỊCH BẢN PHÂN CẢNH (SCRIPT)

Viết kịch bản chi tiết theo cấu trúc chuẩn 5 trường:
```markdown
**Tên video:** [Tên dự án]
**Phong cách hình ảnh:** [STYLE] (sử dụng nguyên văn trong mọi prompt sau)
**Tỉ lệ · thời lượng/cảnh · số cảnh:** [VD: 9:16 · 8 giây · 3 cảnh]

---

## CẢNH 1
- **BỐI CẢNH:** không gian · thời điểm · ánh sáng và không khí
- **HÀNH ĐỘNG:** nhân vật làm gì, cử động ra sao (1 hành động duy nhất, động từ rõ ràng)
- **DIALOGUE:** `Tên: "..."` — hoặc "không thoại"
- **ÂM THANH:** tiếng động hiện trường (SFX) · nhạc nền gợi ý · tông giọng
- **GHI CHÚ ĐẠO DIỄN:** cảm xúc cần truyền · cách chuyển sang cảnh kế

## CẢNH 2
...

## CẢNH N (KẾT)
...
```
*In toàn bộ kịch bản ra chat $\rightarrow$ Dừng chờ người dùng duyệt.*

---

### BƯỚC 2 — CHARACTER BIBLE (HỒ SƠ NHÂN VẬT NHẤT QUÁN)

Xây dựng hồ sơ nhận diện cố định cho từng nhân vật (kể cả nhân vật phụ xuất hiện 1 cảnh):
```markdown
## [TÊN NHÂN VẬT]
- **Tuổi:** [Số tuổi]
- **Vai trò:** chính / phụ
- **Ngoại hình:** vóc dáng · khuôn mặt · kiểu tóc, màu tóc
- **1–2 ĐẶC ĐIỂM NHẬN DIỆN DỊ BIỆT (BẮT BUỘC):** nốt ruồi má trái, sẹo chân mày, kính gọng tròn, má lúm đồng tiền... (giúp model giữ mặt xuyên suốt các cảnh)
- **Trang phục cố định:** ghi rõ màu sắc cụ thể (VD: "áo bà ba nâu đất, tạp dề xanh rêu", tuyệt đối không ghi chung chung "áo đẹp")
- **Cử chỉ đặc trưng:** 1 câu ngắn để prompt chuyển động nhất quán
```
*In hồ sơ nhân vật ra chat $\rightarrow$ Dừng chờ người dùng duyệt.*

---

### BƯỚC 3 — PROMPT CHARACTER REFERENCE SHEET (IMAGE MODE)

Viết bằng tiếng Anh chuẩn. Tạo sheet nhân vật nhiều góc chụp trên nền trung tính:
```text
CHARACTER REF — [Tên Nhân Vật]:
Character reference sheet for [mô tả nhân vật] named [Tên]: [tuổi], [ngoại hình + đặc điểm nhận diện + trang phục từ Character Bible]. Multiple angles (front, 3/4, side), full body and close-up face, consistent [STYLE], neutral background, consistent soft lighting, no text.
```
*In prompt ra chat.*

---

### BƯỚC 4 — PROMPT STORYBOARD TỪNG CẢNH (IMAGE MODE)

Vẽ khung hình điện ảnh đại diện cho từng cảnh, chỉ định gắn kèm Reference nhân vật:
```text
STORYBOARD — CẢNH [N] (attach: [tên các Character Reference tương ứng]):
Single cinematic frame for [bối cảnh + hành động cảnh N], featuring [Tên nhân vật] exactly as in the attached reference. [Góc máy: wide shot / medium shot / close-up]. Consistent [STYLE], consistent lighting and color palette with the character reference, [tỉ lệ 9:16 / 16:9], no text.
```
*In danh sách prompt storyboard ra chat.*

---

### BƯỚC 5 — PROMPT VIDEO TỪNG CẢNH (VIDEO MODE)

Chuyển đổi ảnh Storyboard thành video clip 4–8 giây:
```text
VIDEO — CẢNH [N]:
Animate this frame into an [8]-second cinematic clip. CRITICAL: preserve EXACTLY the same [STYLE], lighting, and color palette shown. Scene: [mô tả chi tiết chuyển động + ngôn ngữ máy quay: slow push-in / slow pan / tracking shot / rack focus]. [Dialogue nếu có: the character says "..."]. Smooth natural motion, no jump cuts, no text.
```
*In danh sách prompt video ra chat. Tại thời điểm này, người dùng đã thấy trọn vẹn cả 5 lớp text.*

---

### BƯỚC 6 — TỰ ĐỘNG HÓA TRÊN GOOGLE FLOW

Sử dụng **Ego Lite** (`ego-browser` CLI, Node script `src/gobi/adapters/platforms/flow_ai/ego/flow_automation.mjs`) hoặc trình duyệt tự động hóa:

1. **Khởi tạo:**
   - Mở `https://labs.google/flow` (hoặc `labs.google/fx/tools/flow`).
   - Bấm **New project**, đặt tên project theo tên video.
   - Báo trạng thái lên chat.

2. **Chế độ Ảnh (Image Mode) — Tạo Nhân vật:**
   - Chuyển chế độ sang **Image**, chọn đúng tỉ lệ khung hình (9:16 / 16:9). Xác nhận model ảnh (Nano Banana).
   - Với mỗi nhân vật: Nhập prompt Character Ref vào ô soạn thảo (sử dụng DOM injection trên phần tử có `data-slate-editor`), click gửi.
   - Chụp screenshot xác nhận thumbnail đang render. Chờ render hoàn tất 100%.
   - **Đổi tên ảnh reference:** Nhấp đổi tên từ "Untitled" thành đúng tên nhân vật (để tránh nhầm lẫn khi đính kèm ở các cảnh sau).

3. **Chế độ Ảnh (Image Mode) — Tạo Storyboard:**
   - Với mỗi cảnh: Mở khay đính kèm Reference $\rightarrow$ Chọn đúng ảnh nhân vật của cảnh đó $\rightarrow$ Bấm **Add to prompt**.
   - Dán prompt Storyboard $\rightarrow$ Gửi $\rightarrow$ Chờ render xong 100%.
   - Kiểm tra nhanh: Nếu nhân vật bị biến dạng hoặc sai style $\rightarrow$ Bấm regenerate ngay tại cảnh đó.

4. **Chế độ Video (Video Mode) — Render Video:**
   - Đổi chế độ sang **Video**, chọn lại tỉ lệ và thời lượng (8s).
   - Với mỗi cảnh: Bấm nút **+** trên ảnh Storyboard tương ứng để đưa vào làm Start Frame (Frames to Video).
   - (Nếu có thoại) Chọn giọng tại mục Voices.
   - Dán prompt Video $\rightarrow$ Gửi $\rightarrow$ Theo dõi thanh tiến trình cho đến khi hoàn tất.
   - Lặp lại cho tất cả các cảnh.

5. **Luật an toàn & Tự phục hồi:**
   - Không gửi dồn dập prompt mới khi tác vụ trước chưa render xong.
   - Nếu gặp lỗi hoặc selector không phản hồi 3 lần liên tiếp tại cùng một nút: Dừng lại, chụp ảnh lưu vào `shots/`, báo người dùng hỗ trợ, tuyệt đối không thử vô hạn làm mất credit.

---

### BƯỚC 7 — BÀN GIAO & HẬU KỲ

1. Tổng kết danh sách các video cảnh đã render thành công và đường dẫn / link Google Flow project.
2. Hướng dẫn người dùng tải các clip về:
   - Mở **CapCut** (hoặc trình dựng video).
   - Ghép các clip theo thứ tự Cảnh 1 $\rightarrow$ Cảnh N.
   - Thêm nhạc nền (BGM), sound effects (SFX) theo kịch bản.
   - Tạo Auto-caption / phụ đề tiếng Việt.
   - Xuất video hoàn chỉnh.

---

## 3. TÀI NGUYÊN ĐI KÈM TRONG HỆ THỐNG
- Template kịch bản: `templates/flow_auto_video/templates/01-script.md`
- Template hồ sơ nhân vật: `templates/flow_auto_video/templates/02-character-bible.md`
- Template 3 lớp prompt: `templates/flow_auto_video/templates/03-prompts.md`
- Checklist thao tác tay trên Flow: `templates/flow_auto_video/templates/04-flow-manual-checklist.md`
- Mẫu brief đầu vào: `templates/flow_auto_video/inputs/idea-brief.md`
- Ví dụ chạy hoàn chỉnh: `templates/flow_auto_video/example/mot-buoi-sang-o-tiem-pho.md`
- Script điều khiển Ego Lite: `src/gobi/adapters/platforms/flow_ai/ego/open_ai_flow.mjs` & `src/gobi/adapters/platforms/flow_ai/ego/flow_automation.mjs`
