# Session I: Các chức năng còn thiếu / chưa hoàn thiện (7 luồng độc lập)

> Viết 2026-11-06, bổ sung cho Session G (2 tập đầu) và Session H (hệ thống).
> Luật chung, cách commit, quyền sở hữu tệp, luật tiền và trung thực: **dùng đúng `ai/plans/2026-11-roadmap/session-H-he-thong/README.md` mục "Luật chung"**.
> Mỗi luồng ghi báo cáo `status/I<số>.md`: lệnh đã chạy, số đo, mục **CHƯA** làm.

## Kết quả kiểm tra thực tế khi viết plan này
| Điều đã kiểm | Kết quả |
|---|---|
| **G2 (chế độ chạy lai + chọn model) chưa làm** | `ai/map/TOOLS.md` (do G4 ghi) xác nhận: router chưa dùng `factories.py`, chưa có `runPolicy` → từ Studio chưa chạy được ảnh thật. Không có commit G2 nào. **Đây vẫn là điểm chặn lớn nhất.** |
| Chạy toàn bộ test | **5 test hỏng, 290 pass, 1 skip**: `test_content_policy::test_import_text_and_merge_rules`, `test_craft_index` (2 test), `test_custom_ports` (2 test) |
| Trang `/sources`, `/products`, `/intel`, `/social`, `/publish`, `/renders`, `/templates` | Chỉ còn **redirect về `/studio`** (cắt ở Session E). Code backend các phần này vẫn còn. |
| Kho nhạc/SFX `data/shared/music_sfx/`, `data/shared/library/` | **Rỗng** |
| Toolbox: `bg-remove`, `depth-layers`, `ffmpeg-bin`, `handdraw`, `scene-cut`, `stt-align`, `voice-clone` | Công cụ có, **chưa kiểm đã nối vào node Studio chưa** |
| Templates: 10 mẫu (koc-review, unboxing, affiliate-compare, tiktok-sales, localized-reup, shorts-fact, story-cartoon, yt-animation-episode, handdraw-whiteboard, character-overlay-replace) | Có thư mục; các báo cáo cũ nói đã render, nhưng khi chạy từ Studio mọi thứ vẫn là mock → **chưa chứng minh chạy thật từ Studio** |
| Dữ liệu phân tích | Dữ liệu mẫu (`analytics/_demo/`), **không phải số liệu thật** |
| Chưa kiểm | Trợ lý AI trong tab Chat có làm được việc thật không; mỗi nút trong Studio có hoạt động không |

## Bảng luồng
| Luồng | Tên | Sở hữu chính |
|---|---|---|
| **I0** | **Làm lại G2** (không phải luồng mới) | xem G2 plan |
| **I1** | Sửa 5 test hỏng + chạy test tự động | `tool/tests/test_content_policy.py`, `test_craft_index.py`, `test_custom_ports.py`, `core/engine/content_policy.py`, `core/engine/validator.py`, `tool/scripts/video_craft_*.py`, `.github/workflows/**` (mới) |
| **I2** | Nhập nguồn video + Việt hoá (sources) | `tool/src/socnhotv/sources/**`, `core/api/routes/sources.py`, `core/nodes/plugins/sources.py`, `tests/test_i2_*` |
| **I3** | Nghiên cứu kênh, ý tưởng, sản phẩm KOC (intelligence) | `tool/src/socnhotv/intelligence/**`, `core/api/routes/intel.py`, `tests/test_i3_*` |
| **I4** | Templates chạy thật từ Studio | `data/shared/templates/**`, `video/templates/**`, `lib/template-graphs.ts`, `tests/test_i4_*` |
| **I5** | Toolbox nối vào Studio (node) | `tool/toolbox/**`, `core/nodes/plugins/toolbox.py` (mới), `tests/test_i5_*` |
| **I6** | Kiểm toàn bộ Studio: nút chết + trợ lý AI | chỉ **đọc và ghi báo cáo** `status/I6.md`; sửa lỗi nhỏ ở tệp không thuộc luồng khác đang làm; lỗi lớn thì ghi yêu cầu |
| **I7** | Kho nhạc nền + SFX hợp lệ bản quyền | `data/shared/music_sfx/**`, `scripts/audio/**` (mới), `ai/knowledge/audio_sources.md` |

Thứ tự ưu tiên: **I0** → **I1**, **I6** (không rủi ro, cho thấy sự thật) → **I7**, **I4** → **I2**, **I3**, **I5**. Các luồng không phụ thuộc cứng nhau.

---

## I0 — Làm lại G2
Đọc `ai/plans/2026-11-roadmap/session-G-hai-tap-dau/G2_che_do_lai_chon_model.md`. Làm đúng như plan (pha 1 backend `runPolicy`, giọng luôn local, router dùng `factories.py`; pha 2 UI). Lưu ý bổ sung: **ảnh đầu ra phải được so với ảnh DNA gốc**; không thêm Pollinations làm nguồn chính (G1 đã thử: sai nhân vật, có watermark).

## I1 — Sửa 5 test hỏng
Chạy `pytest tool/tests -q`. Với từng test hỏng, tìm nguyên nhân gốc (đừng sửa test cho pass nếu code sai): `test_content_policy` (KeyError ở dòng ~34, liên quan tệp chính sách văn xuôi nhập vào), `test_craft_index` (frontmatter thẻ kỹ thuật hợp lệ, sinh registry), `test_custom_ports` (cổng tuỳ chỉnh, giá trị mặc định thoả cổng bắt buộc). Báo cáo từng test: nguyên nhân, sửa code hay test, vì sao. Thêm workflow GitHub Actions chạy `pytest` cho các test không cần mạng. Mục tiêu: **0 test hỏng, không đụng dữ liệu thật** (conftest đã có sandbox).

## I2 — Nhập nguồn video + Việt hoá
Backend `sources/` (downloader, asr, translate, revoice, localize_pipeline, scenes) và node `source_video`, `localize` hiện bị ẩn khỏi Studio. Việc: (1) chạy thật 1 đường: nhập 1 video nguồn **do người dùng cung cấp, có quyền dùng**, cắt cảnh, nhận dạng lời, dịch, đọc lại bằng giọng Việt, dựng; (2) báo thẳng phần nào chạy, phần nào hỏng; (3) quyết định cùng người dùng có đưa node lại vào menu Studio không. **Lưu ý bản quyền:** tải và đăng lại video của người khác (re-up) có rủi ro vi phạm bản quyền và chính sách nền tảng; ghi rõ cảnh báo này trong tài liệu và UI, không tự động hoá việc re-up nội dung không có quyền. Không dùng tài khoản mạng xã hội thật khi chưa được xác nhận.

## I3 — Nghiên cứu kênh, ý tưởng, sản phẩm KOC
Backend `intelligence/` (channel_analyze, ideas, products, script_gen, strategy, compliance). Việc: (1) chạy thật với dữ liệu công khai hoặc dữ liệu người dùng đưa; (2) kiểm sinh ý tưởng, kịch bản KOC từ thông tin sản phẩm, kiểm tuân thủ chính sách (`compliance`); (3) đưa kết quả vào Studio qua node/chat thay vì trang riêng; (4) thay toàn bộ dữ liệu mẫu bằng dữ liệu thật hoặc gắn nhãn "MẪU". Không bịa số liệu view/giữ chân.

## I4 — Templates chạy thật từ Studio
10 template trong `data/shared/templates/`. Với từng template: chạy từ Studio ở chế độ thật rẻ nhất, xuất MP4, kiểm bằng mắt, ghi **Tier trung thực** (chạy thật / chạy một phần / chỉ mock) và lý do. Sửa template nào hỏng được trong phạm vi sở hữu; template nào cần nguồn video/ảnh trả phí thì ghi rõ chi phí ước tính. Ưu tiên: `shorts-fact-v1`, `koc-review-v1`, `tiktok-sales-v1`, `yt-animation-episode-v1`. Kết quả: bảng "template → trạng thái thật" trong `status/I4.md`.

## I5 — Toolbox nối vào Studio
7 công cụ trong `tool/toolbox/tools/`. Việc: kiểm từng công cụ chạy thật được (lệnh mẫu, thời gian); tạo node plugin để dùng trong flow: tách nền ảnh (`bg-remove`), phụ đề từng từ (`stt-align`), cắt cảnh (`scene-cut`), tách lớp chiều sâu (`depth-layers`), vẽ tay bảng trắng (`handdraw`), clone giọng (`voice-clone`). Mỗi node có test, có tham số mặc định hợp lý, hiện đúng trong menu Thêm node. Thêm node tách nền cho **ảnh nhân vật** sẽ giúp tạo ảnh nhân vật cắt sẵn (hỗ trợ nhân vật nhất quán).

## I6 — Kiểm toàn bộ Studio (nút chết + trợ lý AI)
Mở Studio (cổng 3000) bằng trình duyệt, đi qua **từng nút, tab, menu**: Dự án, Nhân vật, Chat, Đăng, Jobs, Node, Phím tắt, thanh công cụ, modal Tạo video, Cài đặt, trang Nhân vật, Jobs. Với mỗi cái ghi: hoạt động / không phản hồi / lỗi console / dữ liệu giả. Kiểm riêng **trợ lý AI trong tab Chat**: nó làm được việc thật (sinh kịch bản, sửa node, chạy flow) hay chỉ là giao diện. Kết quả: bảng "chức năng → trạng thái thật → có ảnh chụp/lỗi console" trong `status/I6.md`, xếp theo mức nghiêm trọng. Đây là bước làm rõ **sự thật** về UI, không phải để sửa hết.

## I7 — Kho nhạc nền + SFX hợp lệ bản quyền
`data/shared/music_sfx/` đang rỗng nên bộ dựng (G3) không có nhạc. Việc: tìm nguồn nhạc/SFX **có giấy phép dùng cho video YouTube thiếu nhi và TikTok** (nhạc nền, tiếng động như bước chân, mở cửa, tiếng thú; ưu tiên nguồn không cần tài khoản, ví dụ skill `media-use` tìm SFX qua Openverse); ghi giấy phép và link nguồn **từng tệp** vào một `index.json`; tải về `data/shared/music_sfx/`; 20–30 bản nhạc phù hợp phim hoạt hình thiếu nhi (vui, nhẹ, kể chuyện) và 40–60 SFX phổ biến. Không tải thứ giấy phép không rõ. Báo cáo cho người dùng danh sách trước khi tải số lượng lớn.
