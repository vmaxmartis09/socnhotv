# Session H: Hoàn thiện hệ thống (7 luồng độc lập)

> Viết 2026-11-06. Session G làm 2 tập đầu chạy được. Session H xây các phần còn thiếu để tool thành hệ thống làm **nhiều loại video**, không chỉ 2 tập.
> Đọc trước: `status/THUC_TRANG_2026-11-06.md`, `ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md` (hợp đồng C1–C6 vẫn áp dụng), `status/G*.md` (xem G đã xong gì).
> Mỗi luồng H độc lập: không luồng nào chờ luồng khác để bắt đầu. Mỗi luồng ghi báo cáo `status/H<số>.md`.

## Luật chung (bắt buộc)
- **Git:** làm trên `main`, commit **kèm đường dẫn** (`git commit -m "..." -- <tệp>`), không `git add -A`, `git pull --rebase` trước khi push, không reformat cả tệp. Không commit `data/`.
- **Quyền sở hữu tệp:** chỉ sửa tệp ở cột "Sở hữu". Sửa chung `core/api/app.py` hoặc `core/api/routes/__init__.py`: **chỉ được thêm 1 dòng `include_router`**, không sửa gì khác. Cần sửa tệp luồng khác: ghi "Yêu cầu gửi H#/G#" vào `status/H<số của mình>.md`.
- **Tiền:** mọi lệnh gọi trả phí đi qua `SpendGuard` + `confirmPaidRun`. **Hỏi người dùng và nêu chi phí trước khi gọi tiền thật.** Không nhập thông tin thanh toán, không tạo tài khoản thay người dùng, không tạo hàng loạt tài khoản, không vượt CAPTCHA. Không in key ra log/chat. Không tải ảnh nhân vật lên host ngoài chưa được người dùng cho phép.
- **Trung thực:** báo cáo ghi lệnh đã chạy, số đo thật và mục **CHƯA** làm được. Không ghi "xong 100%" nếu chưa kiểm bằng mắt hoặc số đo. Ảnh/clip sinh ra phải **đặt cạnh ảnh DNA gốc** để so, không nhận xét theo prompt.
- **Test:** dùng thư mục tạm, không ghi vào `data/projects/soc-nho-tv/` thật.
- Tuân thủ `ai/AGENTS.md`: HyperFrames, voice `soc-nho`, Morphicons (không `lucide-react`), i18n vi/en, đọc skill `video-craft` trước khi sửa phần dựng.

## Bảng luồng

| Luồng | Tên | Giải quyết | Sở hữu chính |
|---|---|---|---|
| **H1** | Video ngắn 30–90s từ 1 prompt | "Chức năng tạo video đơn giản" chưa chạy | `video/short_form/**` (mới), `lib/short-video-preset.ts` (mới), `components/studio/ShortVideoModal.tsx` (mới), `tests/test_h1_*` |
| **H2** | Nguồn video trả phí + đo thật | Chưa có clip AI nào; so Veo/Kling/Seedance | `core/providers/fal_provider.py`, `google_provider.py`, `models_registry/models.yaml`, `scripts/bench/**`, `ai/knowledge/video_models_bench.md`, `tests/test_h2_*` |
| **H3** | Chạy nhiều tập một lần | 51 tập, hiện chạy từng tập | `core/engine/batch_runner.py` (mới), `core/api/routes/batch.py` (mới), `components/studio/BatchRunModal.tsx` (mới), `tests/test_h3_*` |
| **H4** | Trình chỉnh sửa (timeline) trong Studio | Chưa có chỗ chỉnh tay | `components/editor/**` (mới), `core/api/routes/editor.py` (mới), `core/engine/edit_decisions.py` (mới), `tests/test_h4_*` |
| **H5** | Khẩu hình + chất lượng chuyển động | Clip AI nói không khớp giọng OmniVoice | `video/lipsync/**` (mới), `scripts/lipsync/**` (mới), `ai/knowledge/lipsync_options.md`, `tests/test_h5_*` |
| **H6** | Đăng bài + số liệu phản hồi | Chưa đăng thật, chưa có số liệu | `social/**`, `core/api/routes/social.py`, `components/studio/tabs/PublishTab.tsx`, `tests/test_h6_*` |
| **H7** | Vệ sinh dữ liệu + hạ tầng | 695 thư mục `runs/`, chính sách `data/`, bảo vệ voice vault | `.gitignore`, `scripts/maintenance/**` (mới), `tool/tests/conftest.py` (chỉ thêm), `ai/map/DATA.md`, `status/H7.md` |

Khuyến nghị thứ tự ưu tiên: **H2** (cần để biết nguồn video nào dùng được) → **H1** và **H4** → **H3** → **H5** → **H6**. **H7** làm bất cứ lúc nào. Không có luồng nào phụ thuộc cứng.

---

## H1 — Video ngắn 30–90 giây từ 1 prompt
**Mục tiêu:** nhập 1 ý tưởng, ra video 9:16 (hoặc 16:9) 30–90 giây, chạy trong Studio. Đây là "video đơn giản" bạn cần và là loại video hợp với chuyển động AI thật (rẻ hơn tập 10 phút).
**Việc:** (1) sinh kịch bản ngắn 4–10 shot từ 1 prompt (dùng `intelligence/script_gen.py`, không sửa, chỉ gọi); (2) preset graph "Video ngắn": Kịch bản → Cast → Ảnh/Clip theo shot → Dựng → Xuất, có chế độ **ảnh tĩnh** (miễn phí) và **clip AI** (trả phí, qua `video_gen perShot` của G3); (3) modal "Tạo video ngắn" (chủ đề, nhân vật, độ dài, tỉ lệ, ước tính chi phí); (4) chạy thử 1 video 30 giây ở chế độ ảnh tĩnh, đo thời gian dựng.
**Done khi:** 1 video ngắn xuất `output/<slug>/` có tiếng, phụ đề, đúng safe-zone TikTok, xem được trong Studio; `status/H1.md` có số đo và ảnh chụp.

## H2 — Nguồn video trả phí + đo thật
**Mục tiêu:** biết model video nào dùng được thật, giá thật, độ phân giải thật, độ giống nhân vật.
**Việc:** (1) rà soát `fal_provider.py`, `google_provider.py`: đúng đường gọi image-to-video của Veo 3.1 / Veo 3.1 Fast / Kling v3 Pro / Kling 2.5 Turbo Pro / Seedance 1.0 Pro / Hailuo 02 Pro / Wan 2.2; thêm model vào `models.yaml` với giá/độ phân giải/độ dài clip đã kiểm; (2) `scripts/bench/video_bench.py`: cùng 1 shot (ảnh DNA khung đầu + `videoPrompt` S01 Tập 1), chạy nhiều model, lưu clip + đo độ phân giải thật/thời gian/chi phí hoá đơn; (3) ghi `ai/knowledge/video_models_bench.md`: bảng kết quả, link trang giá chính thức, ngày kiểm, ảnh so sánh với DNA.
**Điều kiện:** cần `FAL_KEY` (hoặc billing Google) do người dùng cung cấp. **Chưa có key thì dừng, chỉ làm phần test giả (mock) và chờ.** Tổng chi phí thử ≤ $5, hỏi người dùng trước.
**Done khi:** bảng so sánh ≥3 model với clip thật, người dùng chọn được model mặc định.

## H3 — Chạy nhiều tập một lần
**Mục tiêu:** chọn N tập, chạy lần lượt cùng 1 flow mẫu, báo cáo từng tập (thiết kế đã có ở `ai/plans/2026-11-roadmap/session-E-studio-consolidation/E6_reusable_episode_flow.md` mục 4).
**Việc:** `POST /projects/{id}/run-episodes {graph, episodeIds[], runPolicy, concurrency}`; nhân bản graph mẫu cho từng tập (không sửa graph gốc), cache theo `(graphId, episodeId, nodeId)`, ước tính tổng chi phí trước khi chạy (SpendGuard), tập lỗi không làm hỏng tập khác, báo cáo đạt/bị chặn/lỗi; modal "Chạy cho các tập" trong Studio dùng lại thanh tiến trình.
**Done khi:** chạy thử 3 tập ở chế độ rẻ nhất (mock/ảnh tĩnh), báo cáo từng tập đúng, hủy giữa chừng được; test pass.

## H4 — Trình chỉnh sửa (timeline) trong Studio
**Mục tiêu:** sau khi flow sinh xong, người dùng **chỉnh tay** mà không cần chạy lại cả flow.
**Việc (MVP, làm từng bước nhỏ):** (1) timeline chỉ-đọc: các shot theo thời gian, ảnh/clip đại diện, thoại, nhạc; (2) thao tác: đổi thứ tự shot, đổi thời lượng, thay ảnh/clip bằng tệp khác, tắt/bật shot, sửa phụ đề; (3) lưu quyết định vào `edit_decisions.json` (không sửa `script.json`), render lại **chỉ phần bị đổi**; (4) xem trước tua được.
**Việc nghiên cứu trước:** đọc skill `hyperframes-studio`, `hyperframes-core` (creator-editing-recipes) và xem HyperFrames Studio có thể nhúng/dùng lại không trước khi tự viết.
**Done khi:** đổi 1 shot và 1 thời lượng trong Studio, render lại dưới X phút (ghi số đo), video đúng; test pass.

## H5 — Khẩu hình + chuyển động
**Mục tiêu:** clip AI có miệng nói nhưng dùng giọng OmniVoice, miệng không khớp. Tìm hướng sửa.
**Việc:** nghiên cứu và đo thật các lựa chọn: (a) tắt âm thanh gốc và để miệng không nói; (b) công cụ lip-sync chạy trên máy hoặc API (liệt kê, kiểm giá/điều khoản/độ phù hợp nhân vật hoạt hình 3D, **kiểm bằng clip thật**); (c) sinh clip có thoại đúng lời ngay từ model (nếu model hỗ trợ). Prototype 1 phương án khả thi nhất cho 1 shot.
**Done khi:** `ai/knowledge/lipsync_options.md` có bảng so sánh kèm link chính thức và clip thử; 1 shot demo khớp khẩu hình hoặc kết luận trung thực "chưa khả thi".

## H6 — Đăng bài + số liệu phản hồi
**Mục tiêu:** từ video thành phẩm đến đăng và có số liệu để rút kinh nghiệm.
**Việc:** rà soát `social/**`, `PublishTab.tsx` đang chạy thật tới đâu (nhiều phần là demo); làm đường **thủ công trước** (gói đăng: video + caption + hashtag + nút "Tôi đã đăng") chạy đúng; kiểm khả thi API chính thức YouTube/TikTok (OAuth, giới hạn, duyệt app) và chỉ viết adapter khi người dùng đồng ý; nhập số liệu (view, giữ chân) bằng tay hoặc CSV vào `analytics/`, sinh gợi ý cho tập sau.
**Không làm:** đăng bài thật hoặc dùng tài khoản thật khi chưa được người dùng xác nhận từng lần. Không dùng dữ liệu giả để báo cáo.
**Done khi:** 1 video thành phẩm có gói đăng đầy đủ, số liệu nhập tay hiện trên Studio.

## H7 — Vệ sinh dữ liệu + hạ tầng
**Việc:** (1) liệt kê `runs/` (695 thư mục) và đề xuất xoá, **hỏi người dùng trước khi xoá**; (2) chốt chính sách `data/` lên Git: cái nào lưu (ảnh nhân vật, kịch bản), cái nào bỏ qua (assets mã băm, `raw/`, `runs/`, **voice_vault: mẫu giọng clone là tài sản riêng, đề xuất không đưa lên repo công khai**), cập nhật `.gitignore` tương ứng; (3) kiểm repo `vmaxmartis09/socnhotv` đang công khai hay riêng tư và báo người dùng; (4) script dọn `scripts/maintenance/clean_runs.py` có `--dry-run`; (5) cập nhật `ai/map/DATA.md`.
**Không làm:** viết lại lịch sử Git, xoá tệp, hay đổi quyền repo khi chưa được người dùng đồng ý.
**Done khi:** `status/H7.md` có số liệu trước/sau, người dùng đã duyệt các thay đổi.
