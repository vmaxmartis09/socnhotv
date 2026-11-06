# 3 PROMPT DÁN CÙNG LÚC VÀO 3 SESSION ANTIGRAVITY (không ai phải chờ ai)

Cách hoạt động:
- Dán cả 3 prompt cùng lúc. Mỗi prompt giống nhau về "Phase 0", chỉ khác chữ A/B/C.
- Phase 0: tranh khoá nguyên tử `mkdir status/.bootstrap.lock`. Ai thắng thì làm `00_BOOTSTRAP.md` (sửa các file chung đúng 1 lần). Hai người thua KHÔNG chờ: làm ngay phần logic thuần Python trong thư mục riêng (không cần file chung), rồi mới quay lại nối route/node/UI khi `BOOTSTRAP_DONE` xuất hiện.
- Sau Phase 0 không ai được sửa file chung nữa → không đá nhau.

---

## PROMPT SESSION A — Video

```
Bạn là SESSION A (Video) của dự án /Volumes/Data/socnhotv. Có 2 session khác (B, C) đang chạy CÙNG LÚC trên cùng checkout. Chế độ làm đến cùng: không dừng khi gặp lỗi đầu tiên, tự debug, thử tối thiểu 3 hướng trước khi báo bí, không hỏi lại điều có thể tự suy ra, không ngồi chờ.

BƯỚC 0 – Đọc: CLAUDE.md, ai/AGENTS.md, ai/plans/2026-11-roadmap/README.md, ai/plans/2026-11-roadmap/CONTRACTS.md.

PHASE 0 – TRANH KHOÁ BOOTSTRAP (làm ngay, đừng chờ):
Chạy: mkdir /Volumes/Data/socnhotv/ai/plans/2026-11-roadmap/status/.bootstrap.lock  (nếu thư mục status chưa có: mkdir -p ...status trước).
 • Nếu mkdir THÀNH CÔNG → bạn là người bootstrap: đọc và thực hiện ai/plans/2026-11-roadmap/00_BOOTSTRAP.md (gọn, ưu tiên Bước 1–5, xong thì tạo status/BOOTSTRAP_DONE rồi mới làm Bước 6 deps và tạo status/DEPS_DONE). Sau đó chuyển sang PHASE 1.
 • Nếu mkdir THẤT BẠI → session khác đang bootstrap. KHÔNG chờ, KHÔNG sửa file chung (app.py, registry.py, request.ts, nav, store/index.ts, pyproject.toml, package.json, messages/*.json). Sang PHASE 1 ngay.

PHASE 1 – LÀM TUẦN TỰ, mỗi file xong hẳn (test pass, commit, cập nhật status/A.md) mới sang file kế tiếp:
 1) ai/plans/2026-11-roadmap/session-A-video/A1_video_engine_platforms.md
 2) ai/plans/2026-11-roadmap/session-A-video/A2_template_system.md
 3) ai/plans/2026-11-roadmap/session-A-video/A3_template_gallery_render_ui.md
 4) ai/plans/2026-11-roadmap/session-A-video/A4_youtube_animation_pipeline.md
QUY TẮC CHỜ-KHÔNG-CHỜ: trong mỗi file, làm TRƯỚC mọi phần logic thuần Python nằm trong thư mục vùng A (models, engine, queue, template loader, test). Chỉ khi cần nối router/node plugin/nav/i18n/store/trang frontend mới kiểm tra status/BOOTSTRAP_DONE; chưa có thì chuyển sang phần logic của file kế tiếp, rồi quay lại nối sau. Nếu cần cài thư viện mà status/DEPS_DONE chưa có: dùng try/except ImportError + fallback, hoặc ghi vào status/REQUESTS.md, không tự sửa pyproject.toml/package.json.

LUẬT KHÔNG ĐÁ NHAU (chi tiết ở CONTRACTS.md):
- Chỉ sửa file trong "vùng sở hữu của A" (trừ khi bạn đang làm bootstrap). Cần sửa file vùng khác/file chung → ghi 1 dòng vào status/REQUESTS.md.
- Git: không `git add -A`, không stash/reset/checkout/rebase; chỉ `git add <đường dẫn vùng A>` rồi commit. Gặp index.lock thì đợi 5s thử lại. Bootstrap commit riêng bằng đường dẫn các file bootstrap.
- Không tắt/khởi động lại server 3000 và 8000 (trừ người bootstrap được restart uvicorn 8000 đúng 1 lần). Test bằng pytest/TestClient; cần server riêng thì dùng cổng 8101.
- Luôn dùng Morphicons (không lucide-react), HyperFrames, voice soc-nho, Bi 100cm/Koala 150cm.

KẾT THÚC: xong cả 4 file → báo cáo cuối vào status/A.md (đã làm gì, % hoàn thành, lệnh chạy mẫu, nợ còn lại) rồi dừng. Không chạy 99_FINAL_INTEGRATION.md.
```

---

## PROMPT SESSION B — Nguồn & Phân tích

```
Bạn là SESSION B (Sources & Intelligence) của dự án /Volumes/Data/socnhotv. Có 2 session khác (A, C) đang chạy CÙNG LÚC trên cùng checkout. Chế độ làm đến cùng: không dừng khi gặp lỗi đầu tiên, tự debug, thử tối thiểu 3 hướng trước khi báo bí, không hỏi lại điều có thể tự suy ra, không ngồi chờ.

BƯỚC 0 – Đọc: CLAUDE.md, ai/AGENTS.md, ai/plans/2026-11-roadmap/README.md, ai/plans/2026-11-roadmap/CONTRACTS.md.

PHASE 0 – TRANH KHOÁ BOOTSTRAP (làm ngay, đừng chờ):
Chạy: mkdir /Volumes/Data/socnhotv/ai/plans/2026-11-roadmap/status/.bootstrap.lock  (nếu thư mục status chưa có: mkdir -p ...status trước).
 • Nếu mkdir THÀNH CÔNG → bạn là người bootstrap: đọc và thực hiện ai/plans/2026-11-roadmap/00_BOOTSTRAP.md (gọn, ưu tiên Bước 1–5, xong thì tạo status/BOOTSTRAP_DONE rồi mới làm Bước 6 deps và tạo status/DEPS_DONE). Sau đó chuyển sang PHASE 1.
 • Nếu mkdir THẤT BẠI → session khác đang bootstrap. KHÔNG chờ, KHÔNG sửa file chung (app.py, registry.py, request.ts, nav, store/index.ts, pyproject.toml, package.json, messages/*.json). Sang PHASE 1 ngay.

PHASE 1 – LÀM TUẦN TỰ, mỗi file xong hẳn (test pass, commit, cập nhật status/B.md) mới sang file kế tiếp:
 1) ai/plans/2026-11-roadmap/session-B-sources/B1_source_ingestion.md
 2) ai/plans/2026-11-roadmap/session-B-sources/B2_douyin_localization.md
 3) ai/plans/2026-11-roadmap/session-B-sources/B3_video_blueprint_koc_affiliate.md
 4) ai/plans/2026-11-roadmap/session-B-sources/B4_channel_intelligence.md
QUY TẮC CHỜ-KHÔNG-CHỜ: trong mỗi file, làm TRƯỚC mọi phần logic thuần Python nằm trong thư mục vùng B (sources/, intelligence/: models, downloader, asr, translate, analyzer… + test). Chỉ khi cần nối router/node plugin/nav/i18n/store/trang frontend mới kiểm tra status/BOOTSTRAP_DONE; chưa có thì chuyển sang phần logic của file kế tiếp, rồi quay lại nối sau. Cần yt-dlp/scenedetect/rapidfuzz… mà status/DEPS_DONE chưa có: import trong try/except ImportError + fallback, hoặc ghi vào status/REQUESTS.md, không tự sửa pyproject.toml/package.json. Nếu cần hợp đồng của A/C (socnhotv.video.contracts, socnhotv.social.contracts) mà chưa tồn tại: import trong try/except và ghi log "pending", không tự tạo file đó (người bootstrap sẽ tạo).

LUẬT KHÔNG ĐÁ NHAU (chi tiết ở CONTRACTS.md):
- Chỉ sửa file trong "vùng sở hữu của B" (trừ khi bạn đang làm bootstrap). Cần sửa file vùng khác/file chung → ghi 1 dòng vào status/REQUESTS.md. Giao tiếp với A/C chỉ qua contracts, file JSON và API HTTP, không import code nội bộ của họ.
- Git: không `git add -A`, không stash/reset/checkout/rebase; chỉ `git add <đường dẫn vùng B>` rồi commit. Gặp index.lock thì đợi 5s thử lại.
- Không tắt/khởi động lại server 3000 và 8000. Test bằng pytest/TestClient; cần server riêng thì dùng cổng 8102.
- Bản quyền: nguồn mặc định rights=reference_only (chỉ học cấu trúc, không đưa clip gốc vào render); không code né Content-ID; không tự vượt captcha/đăng nhập Douyin — cần cookie thì báo người dùng.
- Luôn dùng Morphicons (không lucide-react).

KẾT THÚC: xong cả 4 file → báo cáo cuối vào status/B.md rồi dừng. Không chạy 99_FINAL_INTEGRATION.md.
```

---

## PROMPT SESSION C — Social Manager

```
Bạn là SESSION C (Social Manager) của dự án /Volumes/Data/socnhotv. Có 2 session khác (A, B) đang chạy CÙNG LÚC trên cùng checkout. Chế độ làm đến cùng: không dừng khi gặp lỗi đầu tiên, tự debug, thử tối thiểu 3 hướng trước khi báo bí, không hỏi lại điều có thể tự suy ra, không ngồi chờ.

BƯỚC 0 – Đọc: CLAUDE.md, ai/AGENTS.md, ai/plans/2026-11-roadmap/README.md, ai/plans/2026-11-roadmap/CONTRACTS.md.

PHASE 0 – TRANH KHOÁ BOOTSTRAP (làm ngay, đừng chờ):
Chạy: mkdir /Volumes/Data/socnhotv/ai/plans/2026-11-roadmap/status/.bootstrap.lock  (nếu thư mục status chưa có: mkdir -p ...status trước).
 • Nếu mkdir THÀNH CÔNG → bạn là người bootstrap: đọc và thực hiện ai/plans/2026-11-roadmap/00_BOOTSTRAP.md (gọn, ưu tiên Bước 1–5, xong thì tạo status/BOOTSTRAP_DONE rồi mới làm Bước 6 deps và tạo status/DEPS_DONE). Sau đó chuyển sang PHASE 1.
 • Nếu mkdir THẤT BẠI → session khác đang bootstrap. KHÔNG chờ, KHÔNG sửa file chung (app.py, registry.py, request.ts, nav, store/index.ts, pyproject.toml, package.json, messages/*.json). Sang PHASE 1 ngay.

PHASE 1 – LÀM TUẦN TỰ, mỗi file xong hẳn (test pass, commit, cập nhật status/C.md) mới sang file kế tiếp:
 1) ai/plans/2026-11-roadmap/session-C-social/C1_social_domain_api.md
 2) ai/plans/2026-11-roadmap/session-C-social/C2_social_manager_ui.md
 3) ai/plans/2026-11-roadmap/session-C-social/C3_publish_adapters_scheduler.md
 4) ai/plans/2026-11-roadmap/session-C-social/C4_analytics_feedback_loop.md
QUY TẮC CHỜ-KHÔNG-CHỜ: trong mỗi file, làm TRƯỚC mọi phần logic thuần Python nằm trong thư mục vùng C (social/: models, store, service, migrate, adapters, scheduler, analytics + test). Chỉ khi cần nối router/node plugin/nav/i18n/store/trang frontend mới kiểm tra status/BOOTSTRAP_DONE; chưa có thì chuyển sang phần logic của file kế tiếp, rồi quay lại nối sau. Cần apscheduler/google-api…/dateutil mà status/DEPS_DONE chưa có: import trong try/except ImportError + fallback, hoặc ghi vào status/REQUESTS.md, không tự sửa pyproject.toml/package.json. Hợp đồng socnhotv.social.contracts do người bootstrap tạo stub; nếu bạn thấy chưa có khi cần ghi đè bằng bản thật thì chờ BOOTSTRAP_DONE (đừng tạo song song).

LUẬT KHÔNG ĐÁ NHAU (chi tiết ở CONTRACTS.md):
- Chỉ sửa file trong "vùng sở hữu của C" (kể cả PublishTab.tsx và app/[locale]/publish/page.tsx; trừ khi bạn đang làm bootstrap). Endpoint cũ /publishing và /channels nằm vùng khác: giữ nguyên, chỉ đọc để di trú. Cần sửa file chung → ghi vào status/REQUESTS.md. Giao tiếp với A/B chỉ qua contracts, file JSON và API HTTP.
- Git: không `git add -A`, không stash/reset/checkout/rebase; chỉ `git add <đường dẫn vùng C>` rồi commit. Gặp index.lock thì đợi 5s thử lại.
- Không tắt/khởi động lại server 3000 và 8000. Test bằng pytest/TestClient; cần server riêng thì dùng cổng 8103.
- An toàn đăng bài: chỉ OAuth chính chủ, token trong key_vault, không lưu mật khẩu, mặc định phải duyệt tay, không tự bấm nút đăng ở chế độ browser_assisted. Đăng thật lên tài khoản người dùng phải hỏi họ trước.
- Luôn dùng Morphicons (không lucide-react); UI gọn, nút thêm = thẻ nét đứt cạnh thẻ cuối.

KẾT THÚC: xong cả 4 file → báo cáo cuối vào status/C.md rồi dừng. Không chạy 99_FINAL_INTEGRATION.md.
```

---

## PROMPT SESSION D — Research Analyst (chạy độc lập, song song cả A/B/C, không chờ ai)

```
Bạn là SESSION D (Research Analyst) của dự án /Volumes/Data/socnhotv. Bạn chạy ĐỘC LẬP song song với A/B/C, không sửa code dự án, không chờ ai. Làm đến cùng, tự debug, thử tối thiểu 3 hướng trước khi báo bí, không bịa nguồn hay số liệu.

Đọc: CLAUDE.md, ai/plans/2026-11-roadmap/CONTRACTS.md (mục 3), rồi thực hiện đầy đủ ai/plans/2026-11-roadmap/session-D-research/D0_video_research_analyst.md.

NHIỆM VỤ HIỆN TẠI = MODE H: người dùng ĐÃ CHO PHÉP bạn dùng Ego Lite (đã đăng nhập Facebook của họ) mở ĐÚNG 1 cuộc trò chuyện Messenger "Stored" (chat với chính họ): https://www.facebook.com/messages/t/100014084354965 để học video. TÔI ĐÃ ỦY QUYỀN TRƯỚC: dùng Ego Lite với Facebook của tôi, xem mọi video/link trong thread, tải video để phân tích nội bộ, dùng mọi skill và công cụ có sẵn. KHÔNG hỏi xin phép/xác nhận lại cho các việc đó, không dừng để hỏi "tiếp tục không" — cứ chạy hết hàng đợi. Chạy CHẾ ĐỘ TỐI ĐA (mục H5 trong D0): nạp và dùng hết skill liên quan, song song hoá được thì song song, model ASR/vision mạnh nhất có sẵn trong hạn mức spend_guard, tái tạo thử kỹ thuật cốt lõi bằng HyperFrames.
Ranh giới còn hiệu lực (không phải xin phép mà là không làm): chỉ-đọc, chỉ đúng thread Stored; không gửi tin/thả cảm xúc/ghim/xoá/đăng/like/bình luận; không nhập mật khẩu/2FA, không giải CAPTCHA, không rút cookie. Gặp đăng nhập/checkpoint/CAPTCHA thì giữ trình duyệt mở, báo tôi, và CHUYỂN NGAY sang mục khác trong hàng đợi trong lúc chờ.
Thứ tự: lập chỉ mục từ MỚI NHẤT → CŨ NHẤT; sàng lọc từng mục; BỎ QUA video lùa gà/không khả dụng, video quá cũ (công cụ/workflow AI >12 tháng, kỹ thuật nền tảng >24 tháng, trừ nguyên lý bền vững), video không liên quan; mục nào đáng học thì học TỚI CÙNG tuần tự theo thứ tự mới→cũ (G1→G6), và lưu docs vào data/shared/knowledge/video_craft/ (harvest/queue.jsonl, triage.csv, skipped.md, accepted.md, notes.md, SUMMARY.md + videos/<id>/REPORT.md + techniques/*.md + playbooks/*). Có checkpoint harvest/state.json để chạy tiếp được. Cứ 10 mục commit 1 lần (chỉ add data/shared/knowledge/video_craft và status/D.md; không git add -A).
Khi xong báo cáo ngắn tiếng Việt: số mục đã duyệt/học/bỏ (kèm lý do), top 5 bài học áp dụng ngay, mẫu lùa gà hay gặp, việc cần tôi làm.
```

---

## PROMPT SESSION D2 — Quét diện rộng kênh TikTok đang follow (Mode T, trong browser Antigravity)

```
Bạn là SESSION D2 (Research Analyst, quét diện rộng) của dự án /Volumes/Data/socnhotv. Chạy ĐỘC LẬP song song với session D (Messenger) và các session khác, không sửa code dự án, không chờ ai. Làm đến cùng, tự debug, thử tối thiểu 3 hướng trước khi báo bí, không bịa nguồn hay số liệu.
Đọc CLAUDE.md, ai/plans/2026-11-roadmap/CONTRACTS.md (mục 3), rồi thực hiện đầy đủ ai/plans/2026-11-roadmap/session-D-research/D0_video_research_analyst.md, TẬP TRUNG MODE T (T0→T6) và dùng G1→G6 + H5 cho phần học sâu.
NHIỆM VỤ: tôi đã đăng nhập TikTok sẵn trong trình duyệt của Antigravity (browser tích hợp). Hãy mở TikTok ở đó, lấy danh sách các kênh tôi ĐANG FOLLOW, chọn ra các kênh liên quan lĩnh vực LÀM VIDEO AI, rồi quét video của các kênh đó từ MỚI NHẤT → CŨ NHẤT (trong 12 tháng gần nhất, tối đa 60 video/kênh), sàng lọc nhanh, BỎ QUA video lùa gà/không khả dụng, quá cũ (mẹo công cụ AI >12 tháng, trừ nguyên lý bền vững), không liên quan; mục nào đáng học thì học TỚI CÙNG và lưu docs vào data/shared/knowledge/video_craft/ (tiktok/*, videos/<id>/REPORT.md, techniques/*, workflows/*, tools_landscape.md, CHANNEL_MAP.md, SUMMARY.md, playbooks/*). Kênh trông như tài khoản cá nhân/bạn bè thì bỏ qua và KHÔNG ghi gì về họ.
TÔI ĐÃ ỦY QUYỀN TRƯỚC: dùng phiên TikTok đã đăng nhập của tôi trong browser Antigravity, đọc danh sách follow của tôi, mở mọi kênh/video công khai, phát video, chụp khung hình, dùng mọi skill và công cụ có sẵn. KHÔNG hỏi xin phép/xác nhận lại, không dừng để hỏi "tiếp tục không", cứ chạy hết hàng đợi. Chạy CHẾ ĐỘ TỐI ĐA (H5): nạp và dùng hết skill liên quan, học sâu song song tối đa 3–4 mục (nhưng chỉ 1 phiên duyệt web TikTok cùng lúc), tái tạo thử kỹ thuật cốt lõi bằng HyperFrames, rút công thức quy trình tái lập được cho Studio.
Ranh giới còn hiệu lực (không phải xin phép mà là không làm): chỉ-đọc; không follow/bỏ follow/like/lưu/bình luận/chia sẻ/nhắn tin; không mở Inbox/Cài đặt/Cửa hàng/thanh toán; không nhập mật khẩu/OTP, không giải CAPTCHA, không rút cookie, không dùng trang tải video lạ, không né phát hiện bot (duyệt như người, nghỉ 1–3s giữa thao tác). Gặp đăng nhập/checkpoint/CAPTCHA/giới hạn tạm thời thì giữ trình duyệt mở, báo tôi, và CHUYỂN NGAY sang việc khác (học sâu mục đã có) rồi quay lại.
Phối hợp với session D: trước khi sửa techniques/, playbooks/, INDEX.md dùng khoá `mkdir video_craft/.lock` (thất bại thì đợi 5s thử lại, xong rmdir), đọc lại file ngay trước khi ghi, ghi tối thiểu. Bỏ trùng với dữ liệu D đã có. Checkpoint tiktok/state.json sau mỗi 5 mục (phiên trước từng bị cắt vì hết quota), commit mỗi 10 mục (chỉ git add data/shared/knowledge/video_craft và status/D2.md; không git add -A).
Khi xong báo cáo ngắn tiếng Việt: số kênh đã quét/chọn/bỏ, số video duyệt/học/bỏ (kèm lý do), top 5 công thức quy trình áp dụng ngay vào Studio, mẫu lùa gà hay gặp, việc cần tôi làm.
```

---

## Khi cả 3 session báo xong
Mở session mới, dán:
```
Đọc và thực hiện đầy đủ ai/plans/2026-11-roadmap/99_FINAL_INTEGRATION.md. Làm đến cùng, không hỏi lại.
```
