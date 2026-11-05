# SESSION U — TAB TEMPLATE ĐẦY ĐỦ (kế hoạch + prompt giao Ag)
# Mã nhiệm vụ: U-00 … U-12. Ngày lập: 2026-11-05.

## 0. Hiện trạng đã kiểm
- Đã có 8 template trong `data/shared/templates/`: `affiliate-compare-v1, koc-review-v1, localized-reup-v1, shorts-fact-v1, story-cartoon-v1, tiktok-sales-v1, unboxing-v1, yt-animation-episode-v1` (mỗi cái: `template.json`, `composition.html.j2`, `styles.css`, `sample.data.json`, `preview.jpg`) + `publishing_templates.json`. UI có `components/templates/{TemplateCard,SlotField}.tsx`.
- **Cảnh báo từ F0 audit** (`session-F-script-to-video/F0_AUDIT_AND_PLAN.md` mục 1): nút "Tạo video" từ 8 template từng chạy ra **ảnh .jpg mock**; `template_render`/`platform_export` chưa có handler. Template hiện tại là **vỏ chưa chứng minh ra video thật**. Session U **không được coi template là xong** nếu chưa có MP4 thật.
- Toolbox (Session T) đã có: `bg-remove`, `stt-align`, `ffmpeg-bin` (và T-06/T-10/T-11 đang làm). Template phải gọi tool qua `toolbox run`, không import code.

## 1. Mục tiêu
Một tab **Template** trong dashboard: chọn kiểu video → điền ô (slots) → ra graph Studio đúng kiểu → chạy → MP4 thật. Mỗi template khai báo rõ: cần tool nào, cần khoá API nào, cần GPU không, độ tin cậy, và **video mẫu thật** đã render.

## 2. Hợp đồng template v2 (`template.json`)
Giữ tương thích v1, bổ sung:
`kind` (animation|film|koc|replace|review|remotion-style|handdrawn|…), `status` (draft|runnable|verified), `requires{tools[], providers[], gpu, ffmpeg}`, `tier` (A: chạy offline CPU · B: cần khoá API · C: cần GPU/cloud), `recipe` (chuỗi node Studio dùng để dựng graph, tham chiếu node thật đã có handler), `slots[]` (có `type`, `validate`), `outputs{aspect[], duration}`, `sample_output` (đường dẫn MP4 mẫu thật), `verified_on` (ngày + người duyệt), `sources[]` (repo/tài liệu học, kèm giấy phép), `learned_from` (id thẻ trong `data/shared/knowledge/video_craft/techniques/`).
Template `status: verified` chỉ khi `sample_output` tồn tại, ffprobe đo đúng, và người dùng đã duyệt.

## 3. Danh mục template cần có
| Mã | Template | Tier | Công cụ / nguồn học (đã kiểm GitHub 2026-11-05) | Ghi chú trung thực |
|---|---|---|---|---|
| U-A | **Hoạt hình thiếu nhi (series Bi)** | A→B | Phụ thuộc Session F (`episode_script → shot_images → voice_multi → episode_render`) | Đây là template chính; chỉ nối vào, không làm lại lõi F |
| U-B | **Làm phim ngắn / cinematic** (nhiều cảnh, thoại, nhạc) | B | HyperFrames (heygen-com/hyperframes, Apache-2.0, 79k★) + ảnh AI theo shot | Cần khoá Gemini cho ảnh đẹp; Tier A chỉ ra animatic |
| U-C | **TikTok review KOC** | A→B | Template `koc-review-v1`, `tiktok-sales-v1` có sẵn; ý tưởng pipeline từ MoneyPrinterTurbo (MIT, 139k★), openshorts (MIT, 7.5k★) | Chỉ học ý tưởng, tự viết. Không dùng khuôn mặt/giọng người thật khi chưa có đồng ý |
| U-D | **Review sản phẩm / so sánh / unboxing** | A | `affiliate-compare-v1`, `unboxing-v1` có sẵn + `bg-remove` tách nền sản phẩm | Tách nền sản phẩm thật bằng Toolbox thay ảnh mock |
| U-E | **Thay nhân vật, giữ nội dung** (video-to-video) | C | Họ Wan 2.x (Wan-Video/Wan2.2, Apache-2.0), kijai/ComfyUI-WanVideoWrapper (Apache-2.0), LTX-Video (Apache-2.0) | **Cần GPU NVIDIA, máy không có.** Tier A thay thế: *overlay-replace* = tách nền nhân vật mới (`bg-remove`) rồi ghép lên cảnh gốc bằng HyperFrames, không phải AI thay thật. Phải ghi rõ khác biệt trong UI |
| U-F | **Hoạt hình kiểu Remotion (đồ hoạ chuyển động, kinetic text)** | A | Remotion (remotion-dev/remotion, 71k★) giấy phép **NOASSERTION/tuỳ chỉnh, có điều khoản thương mại** → KHÔNG dùng làm engine. Dùng skill `ai/skills/remotion-to-hyperframes`, `motion-graphics`, `hyperframes-animation` để dựng bằng HyperFrames | Học phong cách, không chép mã |
| U-G | **Video vẽ tay (whiteboard)** | A | whiteboard-animator (masihsultani, MIT) CPU, cần ffmpeg; handanim (subroy13, MIT) lập trình; **kiểm lại sao/push trước khi clone** (chưa kiểm số liệu) | Làm thành tool Toolbox `handdraw` rồi template gọi nó; ảnh đầu vào nền trắng nét mực |
| U-H | **Giải thích công thức/toán (manim-style)** | A | 3b1b/manim (MIT, 96k★) hoặc manim-community (kiểm) | Tuỳ chọn |
| U-I | **Shorts kiến thức / facts** | A | `shorts-fact-v1` có sẵn + `stt-align` phụ đề từng từ | Nâng cấp lên karaoke thật |
| U-J | **Cắt Shorts từ tập dài** | A | Toolbox `scene-cut` (PySceneDetect + auto-editor) + reframe 9:16 safe-zone 180/320 | Phụ thuộc T-11 |
| U-K | **Slideshow ảnh + nhạc / music-to-video** | A | Skill `slideshow`, `music-to-video` có sẵn | Nhạc CC0 vì `music_sfx/` đang trống |
| U-L | **Talking-head recut / pr-to-video / product-launch** | A | Skill `talking-head-recut`, `pr-to-video`, `product-launch-video` có sẵn | Gom vào danh mục, kiểm chạy thật |
| U-M | **Reup bản địa hoá** | A | `localized-reup-v1` | Chỉ cho nội dung mình có quyền |

**Thận trọng / không đưa vào mặc định:** Wav2Lip (không giấy phép), SadTalker (NOASSERTION), FujiwaraChoki/MoneyPrinterV2 (**AGPL-3.0** → chỉ đọc ý tưởng, không chép mã), HunyuanVideo-Foley (NOASSERTION), mọi weights non-commercial.

## 4. Vòng "không ngừng học" (bắt buộc, theo `ai/AGENTS.md` mục 8)
- Mỗi template mới/nâng cấp phải kèm ≥ 1 thẻ kỹ thuật trong `data/shared/knowledge/video_craft/techniques/` (đủ front-matter: `status, reproducible_with_our_stack, needs, confidence, last_verified, expires_at`).
- Mỗi tuần (hoặc khi người dùng yêu cầu): quét GitHub theo từ khoá của từng nhóm (whiteboard, kinetic typography, video-to-video, short-form pipeline), **kiểm sao/giấy phép/push bằng GitHub API** như Session T, ghi kết quả vào `data/shared/knowledge/video_craft/repo_watch.md` (bảng: repo, giấy phép, ngày kiểm, đã thử/chưa, kết luận). Không clone repo giấy phép lạ khi chưa hỏi.
- Không tin báo cáo tự sinh; chỉ tin số đo (bài học F0 mục 5).

## 5. UI tab Template (tuân thủ chuẩn dự án)
Đọc trước: `ai/rules/ui-rules.md`, `ai/rules/morphicons.md`, `globals.css`, `components/templates/*`, và **bản sửa middleware `/api` của Session T** (xem 6).
- Theme: chỉ token CSS có sẵn, sáng/tối. Icon: `@/components/ui/icons` + `MorphIcon`, cấm `lucide-react`. Thành phần dùng chung: `Button`, `Card`, `AiLoading`, `confirm()`.
- Animation: framer-motion tween 0.15–0.25s, `enterOnce`, `active:scale`, không spring nảy.
- Bố cục: căn trái; thẻ poster có ảnh preview + huy hiệu `tier` (A/B/C) + trạng thái (draft/runnable/verified) + biểu tượng yêu cầu (khoá API, GPU, tool); template thiếu điều kiện thì **mờ + tooltip nói thiếu gì** (quy tắc 13), không ẩn; trống thì ô nét đứt gợi ý việc (quy tắc 20, 22). Click = xem trước (mở rộng sang trái, quy tắc 2), nhấn đúp = tạo graph vào Studio. Một thẻ dùng chung ở mọi tab (quy tắc 22b).
- Không hai nút cùng chức năng (quy tắc 19). Tooltip cho nút icon. i18n qua `messages/`.
- Tạo file mới trong `components/templates/` và `app/[locale]/templates/`; sửa file có sẵn chỉ khi cần cho tab này và phải ghi rõ trong báo cáo.

## 6. Bài học bắt buộc từ Session T (đã kiểm 2026-11-05)
- Giao diện Toolbox do Ag làm **hiện 0 công cụ** vì `tool/dashboard/middleware.ts` (next-intl) chặn `/api/*` → 404; dự án chưa có route `app/api` nào trước đó (backend là Core qua `/core/*`). Bản sửa: thêm `api` vào matcher loại trừ. **Session U không được lặp lỗi này**: mọi API mới phải gọi thử bằng `curl` vào server đang chạy và thấy JSON thật trước khi báo xong.
- Ag đã báo `READY_FOR_USER_TEST` mà chưa mở UI xem. Quy tắc mới: trước khi báo xong UI phải **mở bằng trình duyệt, chụp ảnh sáng + tối, và đọc console không lỗi**.

## 7. Nhiệm vụ
| Mã | Nhiệm vụ | Cổng nghiệm thu (file thật) |
|---|---|---|
| U-00 | Đọc các tài liệu mục 0, 5, 6; kiểm 8 template hiện có bằng cách chạy thật từng cái; lập bảng `runnable/mock` | `status/U.md` có bảng, kèm lỗi thật |
| U-01 | Hợp đồng v2 + JSON schema + validator (`tool/toolbox/…` hoặc `tool/src` chỉ khi được phép; mặc định tạo trong `data/shared/templates/_schema/`) + migrate 8 template cũ (giữ nguyên hành vi, thêm trường mới) | Validator chạy trên 8 template, báo đúng chỗ thiếu |
| U-02 | API đọc danh mục (đọc `data/shared/templates/*/template.json`) + kiểm điều kiện (tool có cài, khoá có không, GPU) | `curl` ra JSON thật; template thiếu điều kiện hiện lý do |
| U-03 | UI tab Template theo mục 5 | Ảnh chụp sáng/tối đã mở xem; console sạch; `check:icons` sạch; build pass |
| U-04 | U-D review sản phẩm: nối `bg-remove` → ra MP4 thật 9:16 | MP4 + ffprobe + contact sheet; người dùng duyệt |
| U-05 | U-C KOC review: MP4 thật có giọng + phụ đề từ `stt-align` | WER đo; khung hình không đen |
| U-06 | U-G video vẽ tay: tool Toolbox `handdraw` (whiteboard-animator hoặc handanim sau khi kiểm) + template | MP4 vẽ từng nét; giấy phép ghi trong `tool.json` |
| U-07 | U-F kinetic/motion graphics bằng HyperFrames | MP4 16:9 + 9:16 |
| U-08 | U-E thay nhân vật: Tier A overlay-replace + ghi rõ giới hạn; Tier C chỉ khai báo, không giả | MP4 thật Tier A; UI nói đúng "đây là ghép, không phải AI thay" |
| U-09 | U-A/U-B nối vào Session F khi F đã có `episode_render` (nếu chưa: đánh `blocked_by: F`) | Trạng thái trung thực |
| U-10 | U-I, U-J, U-K, U-L, U-M, U-H: nâng/kiểm từng cái | Mỗi cái `runnable` hoặc `draft` kèm lý do |
| U-11 | Vòng học: thẻ kỹ thuật + `repo_watch.md` lần đầu (≥ 10 repo, có số liệu kiểm) | File tồn tại, số liệu có ngày |
| U-12 | Báo cáo cuối `status/U.md` + cập nhật `ai/map/TOOLS.md` | Bảng template: verified/runnable/draft + MP4 mẫu |

**Giao thức báo test:** xong TỪNG template, ghi `data/shared/toolbox/ready/U-XX.md` (cách chạy, đường dẫn MP4, số đo, giới hạn), đặt `READY_FOR_USER_TEST` trong `status/U.md`, báo người dùng một câu rồi DỪNG chờ "OK U-XX". Cấm báo "xong" khi chưa mở file/UI xem.

## 8. Cách ly
Chỉ ghi: `data/shared/templates/**`, `data/shared/knowledge/video_craft/**` (thẻ mới + `repo_watch.md`), `tool/dashboard/components/templates/**`, `tool/dashboard/app/[locale]/templates/**`, `tool/toolbox/tools/handdraw/**` (nếu làm U-06), `ai/plans/2026-11-roadmap/session-U-templates/**`, `status/U.md`. Không sửa `tool/src/socnhotv/**`, session F/K/T khác, `data/projects/**`; cần thì ghi `status/REQUESTS.md`. Nhánh riêng `session-u/templates`.
