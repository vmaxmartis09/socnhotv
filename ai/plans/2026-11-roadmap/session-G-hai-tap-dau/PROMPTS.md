# 5 prompt gửi cho 5 AI (Session G)

> Cập nhật 2026-11-06: G1 đã đổi (có nguồn trả phí Google Omni có kiểm soát), thêm G5 (nhân vật). **Các prompt G1 và G5 dán trực tiếp từ mục "Prompt mới" ở cuối tệp này.**

Mỗi prompt dán nguyên khối vào một AI riêng. Các AI cùng làm trên repo `/Volumes/Data/socnhotv`, nhánh `main`.
Gợi ý chọn AI: **G1** cần duyệt web (Gemini / Antigravity / Claude có web). **G2** mạnh frontend (Cursor / Claude). **G3** mạnh Python (Codex / Claude). **G4** có trình duyệt để test Studio (Claude Code).

---

## Prompt 1: G1 Nguồn AI miễn phí

```text
Bạn là AI phụ trách luồng G1 của dự án SocNhoTV, repo /Volumes/Data/socnhotv (nhánh main).
Mục tiêu chung của 4 AI: Tập 1 và Tập 2 hoạt hình (mỗi tập 10 phút, 30 shot) chạy ra từ flow Studio và xem được trong Studio, ở mức "animatic thật", chi phí API $0.
Hiện chưa có nguồn sinh ảnh/video nào dùng được: key Gemini trong .env bị Google báo không hợp lệ, không có fal/replicate, chưa tích hợp nguồn free nào.

Đọc theo thứ tự:
1) ai/AGENTS.md
2) status/THUC_TRANG_2026-11-06.md
3) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md (mục 3 quyền sở hữu tệp, mục 4 hợp đồng C1 và C2, mục 6 luật chung)
4) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/G1_nguon_ai_mien_phi.md (plan của bạn)

Việc của bạn: lùng sục trên mạng các nguồn AI MIỄN PHÍ hợp lệ (API có free tier, model chạy được trên Mac M4 16GB, web có credit hằng ngày để người dùng làm tay). GỌI THỬ THẬT từng nguồn và ghi số đo (hạn mức, giây/ảnh, có nhận ảnh tham chiếu nhân vật không, giấy phép). Sau đó viết provider cho nguồn ảnh free tốt nhất (ưu tiên nguồn có ảnh tham chiếu), kèm 1 nguồn dự phòng, đúng hợp đồng C1/C2.
Ưu tiên số 1: sinh được ảnh thật cho shot S01–S03 của Tập 1 (prompt trong data/projects/soc-nho-tv/content/episodes/ep01-nui-lua-trong-bung-bi/script.json), dùng ảnh DNA nhân vật trong data/projects/soc-nho-tv/characters/<id>/.

Luật cứng:
- Chỉ sửa tệp G1 sở hữu (README mục 3). Không sửa router.py, graph_runner.py.
- Không tạo hàng loạt tài khoản hay email ảo để cày credit, không vượt CAPTCHA, không xoay vòng key. Cần key thì dừng lại, hướng dẫn người dùng tự tạo trên trang chính chủ rồi đặt vào .env. Không in key ra log hay chat.
- Commit chỉ tệp của bạn, kèm đường dẫn: git commit -m "..." -- <tệp>. Không git add -A. Không commit data/. Chạy git pull --rebase trước khi push.
- Báo cáo trung thực ở status/G1.md: lệnh đã chạy, số đo, cái gì CHƯA làm được. Ghi "Yêu cầu gửi G2" nếu cần UI hoặc key mới.
Làm đến khi đạt mục "Done khi" trong plan G1.
```

---

## Prompt 2: G2 Chế độ chạy lai + chọn model

```text
Bạn là AI phụ trách luồng G2 của dự án SocNhoTV, repo /Volumes/Data/socnhotv (nhánh main). Backend: FastAPI (tool/src/socnhotv). Studio: Next.js (tool/dashboard).
Mục tiêu chung của 4 AI: Tập 1 và Tập 2 hoạt hình (10 phút/tập) chạy ra từ flow Studio và xem được trong Studio, chi phí $0.
Hai điểm nghẽn của bạn:
(N2) "Mock" là công tắc chung: bật Mock thì giọng OmniVoice chạy trên máy (miễn phí, đang chạy tốt) bị thay bằng WAV im lặng; tắt Mock thì node ảnh lỗi vì thiếu key. Không có chế độ "ảnh tạm + giọng thật".
(N3) Không có chỗ chọn model và nguồn cung cấp đúng nghĩa: UI không dùng GET /models và /providers, dropdown viết cứng, card image_gen không có chỗ chọn model, không hiện miễn phí hay trả phí, trạng thái key, có nhận ảnh tham chiếu không.

Đọc theo thứ tự:
1) ai/AGENTS.md
2) status/THUC_TRANG_2026-11-06.md
3) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md (mục 3, mục 4 hợp đồng C1 C2 C3 C4, mục 6)
4) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/G2_che_do_lai_chon_model.md (plan của bạn)

Làm PHA 1 (backend runPolicy, giọng luôn chạy local, router tra factories của G1, chuỗi dự phòng chỉ trong nguồn free/local, /models trả thêm available/tier) TRƯỚC và commit sớm, vì luồng G4 cần nó cho mốc M1. Sau đó mới làm PHA 2: menu chế độ chạy, ModelPicker dùng chung, gắn vào card image_gen/video_gen, ô key trong Cài đặt.

Luật cứng:
- Chỉ sửa tệp G2 sở hữu (README mục 3). Trong graph_runner.py chỉ sửa vùng chạy/kế hoạch đã liệt kê. Commit nhỏ, git pull --rebase trước khi commit, không reformat cả tệp.
- Icon dùng Morphicons (@/components/ui/icons), không dùng lucide-react. i18n vi/en. Build kiểm bằng: NEXT_DIST_DIR=.next-build npx next build (không build vào .next khi dev server cổng 3000 đang chạy).
- Không bao giờ để router tự rơi sang nguồn trả phí. Nguồn trả phí phải qua confirmPaidRun và SpendGuard.
- Commit kèm đường dẫn: git commit -m "..." -- <tệp>. Không git add -A, không commit data/.
- Báo cáo trung thực ở status/G2.md, kèm ảnh chụp UI (sáng/tối) trong data/projects/soc-nho-tv/shots/G2_*.png.
Làm đến khi đạt mục "Done khi" trong plan G2.
```

---

## Prompt 3: G3 Engine dựng theo shot

```text
Bạn là AI phụ trách luồng G3 của dự án SocNhoTV, repo /Volumes/Data/socnhotv (nhánh main). Engine Python ở tool/src/socnhotv. Bộ dựng là HeyGen HyperFrames (composition HTML/GSAP, render qua CLI).
Mục tiêu chung của 4 AI: Tập 1 và Tập 2 hoạt hình (10 phút, 30 shot × 20 giây) chạy ra từ flow Studio và xem được trong Studio, chi phí $0.
Điểm nghẽn của bạn:
- video_gen chỉ làm 1 clip, không lặp theo shot; flow Tập không có bước video; shot 20 giây nhưng clip AI chỉ 4–10 giây.
- Bộ dựng thô: mỗi shot 1 ảnh tĩnh zoom nhẹ suốt 20 giây; không dùng trường camera của kịch bản; không nhạc nền/SFX; module video/craft không được gọi.
- Đường tốn tiền ngầm: khi hyperframes_render lỗi, code tự gọi provider.generate_video 45 giây. HyperFrames lỗi thì lặng lẽ chuyển sang FFmpeg. "npx -y hyperframes" có thể tải bản khác bản đã ghim 0.9.12.

Đọc theo thứ tự:
1) ai/AGENTS.md
2) status/THUC_TRANG_2026-11-06.md
3) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md (mục 3, mục 4 hợp đồng C4 C5 C6, mục 6)
4) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/G3_engine_dung_theo_shot.md (plan của bạn)
5) skill ai/skills/video-craft, data/shared/knowledge/video_craft/techniques/STATUS.md, các skill hyperframes-core và hyperframes-animation

Làm PHA 1 trước và commit sớm: bỏ fallback generate_video, báo rõ khi dùng FFmpeg dự phòng, ghim binary HyperFrames, camera theo kịch bản. Luồng G4 cần phần này cho mốc M1. Sau đó làm PHA 2: video_gen lặp theo shot trong core/engine/shot_video.py (có maxClips, cache theo shot, clipSource auto/manual/ai, AI lỗi thì giữ ảnh), nhận clip làm tay ở content/episodes/<ep>/clips/<shotId>.mp4, BGM có ducking, SFX, tên tệp xuất theo tập.

Luật cứng:
- Chỉ sửa tệp G3 sở hữu (README mục 3). Trong graph_runner.py chỉ sửa _render_dialogue và các nhánh video_gen/hyperframes_render/export; logic nặng đặt ở module mới. Commit nhỏ, git pull --rebase trước khi commit, không reformat cả tệp.
- Không thêm đường nào tự gọi model trả phí khi đang có lỗi. Test dùng provider giả và tmp_path, không gọi mạng, không ghi vào data/ thật.
- Commit kèm đường dẫn: git commit -m "..." -- <tệp>. Không git add -A, không commit data/.
- Báo cáo trung thực ở status/G3.md (thời gian render 10 phút đo thật, engine đã dùng, cái gì CHƯA làm được).
Làm đến khi đạt mục "Done khi" trong plan G3.
```

---

## Prompt 4: G4 Dữ liệu tập, Studio, nghiệm thu (tích hợp)

```text
Bạn là AI phụ trách luồng G4 (tích hợp và nghiệm thu) của dự án SocNhoTV, repo /Volumes/Data/socnhotv (nhánh main). Studio: http://localhost:3000/vi/studio, Core API: http://localhost:8000.
Mục tiêu chung của 4 AI: Tập 1 (ep01-nui-lua-trong-bung-bi) và Tập 2 (ep02-mun-so-bong-toi), mỗi tập 10 phút, chạy ra từ flow Studio và xem/tua được trong Studio, mức "animatic thật", chi phí $0. Ba AI khác đang làm song song: G1 nguồn AI free, G2 chế độ chạy lai + chọn model, G3 engine dựng theo shot.
Sự thật hiện tại: chưa có video thật nào. Mọi output của flow đều mock (ảnh giả 1 tấm lặp lại, giọng im lặng). Báo cáo cũ ghi "100%" là không đúng. 844 tệp data/ đang nằm sẵn trong staging. Test ghi thẳng vào runs/ của dự án thật (695 thư mục).

Đọc theo thứ tự:
1) ai/AGENTS.md
2) status/THUC_TRANG_2026-11-06.md
3) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md (đọc hết, nhất là mục 5 "Định nghĩa Done")
4) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/G4_tap1_tap2_studio_nghiem_thu.md (plan của bạn)

Pha 1 (không cần chờ ai):
- tách test khỏi dữ liệu thật (conftest.py)
- kiểm DNA và giọng của 5 nhân vật trong 2 tập
- dựng sẵn giọng thật cho 60 câu thoại
- gắn priority cho shot, sửa videoPrompt
- kiểm video trả 206 khi tua, PreviewPane phát và tua được
- viết scripts/video/verify_episode.py
Sau đó chạy các mốc M1 → M4 khi các luồng kia đã đưa phần cần thiết vào main (đọc status/G1.md, G2.md, G3.md). Kiểm thật trong Studio bằng trình duyệt, chụp ảnh làm bằng chứng.

Luật cứng:
- Chỉ sửa tệp G4 sở hữu (README mục 3). Cần luồng khác sửa gì thì ghi "Yêu cầu gửi G#" trong status/G4.md.
- Không xoá dữ liệu cũ, không tự chạy git restore --staged data/: liệt kê ra và hỏi người dùng.
- Một tập chỉ được báo "xong" khi verify_episode.py ĐẠT các mục 1–5 VÀ người dùng đã xem contact sheet và xác nhận (mục 6). Báo cáo trung thực; mục nào chưa đạt ghi CHƯA kèm lý do.
- Commit kèm đường dẫn: git commit -m "..." -- <tệp>. Không git add -A, không commit data/. Chạy git pull --rebase trước khi push.
- Cuối cùng viết status/G.md, cập nhật ai/map/TOOLS.md và ai/memory/CONTINUITY.md cho đúng sự thật.
Làm đến khi đạt mục "Done khi" trong plan G4.
```


---

## Prompt mới: G1 Nguồn ảnh/video (thay cho Prompt 1 ở trên)

```text
Bạn là AI phụ trách luồng G1 của dự án SocNhoTV, repo /Volumes/Data/socnhotv (nhánh main).
Mục tiêu chung của các AI: Tập 1 và Tập 2 hoạt hình (mỗi tập 10 phút, 30 shot × 20 giây) chạy ra từ flow Studio và xem được trong Studio. Đây là hệ thống dùng lâu dài cho nhiều loại video (YouTube, TikTok KOC), nên làm provider đúng chuẩn, không làm tạm.

Sự thật đã xác nhận từ docs chính thức (đọc lại để chắc):
- Gemini API gói Free KHÔNG có sinh ảnh (https://ai.google.dev/gemini-api/docs/pricing). Key mới của người dùng trong .env hợp lệ nhưng sinh ảnh trả 429.
- Model video của Google hiện là Gemini Omni Flash (gemini-omni-1.2-flash): clip 3–15 giây, có âm thanh gốc, nhận ảnh tham chiếu (https://ai.google.dev/gemini-api/docs/video). Code hiện gọi veo-3.1-fast-generate-preview, cần kiểm và cập nhật.
- Google Cloud tặng $300 credit khách mới (https://cloud.google.com/free), chưa rõ có trừ được cho Gemini API hay chỉ Vertex AI.
- Chưa biết: độ phân giải clip, giá video thật, hạn mức.

Đọc theo thứ tự:
1) ai/AGENTS.md
2) status/THUC_TRANG_2026-11-06.md
3) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md (mục 3, 4 hợp đồng C1 C2, mục 6)
4) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/G1_nguon_ai_mien_phi.md (đọc cả mục "Cập nhật 2026-11-06")

Việc của bạn:
- Tích hợp nguồn TRẢ PHÍ được kiểm soát: Google (ảnh Nano Banana + video Omni Flash), đúng hợp đồng C1/C2, tier "paid", qua SpendGuard + confirmPaidRun. fal.ai Kling là phương án thay.
- Trước khi gọi bất cứ thứ gì tốn tiền thật, HỎI người dùng và nêu chi phí ước tính (tổng thử ≤ $2). Người dùng tự bật billing; bạn không nhập thông tin thanh toán hay tạo tài khoản thay họ.
- Đo và ghi lại thật: độ phân giải clip, giá trên hoá đơn, thời gian, số ảnh tham chiếu nhận được. Ghi vào ai/knowledge/free_ai_sources.md kèm LINK trang chính thức và ngày kiểm. Không dùng blog làm bằng chứng duy nhất.
- Vẫn tìm nguồn miễn phí/dự phòng như plan (API free, model chạy trên máy, web có credit hằng ngày), gọi thử thật.
- Đặt has_audio=false mặc định khi sinh clip (dùng giọng OmniVoice); ghi vào tài liệu giới hạn khẩu hình không khớp.
- Ưu tiên số 1: sinh được ảnh thật cho shot S01–S03 của Tập 1 (script.json trong data/projects/soc-nho-tv/content/episodes/ep01-nui-lua-trong-bung-bi/) với ảnh DNA nhân vật làm tham chiếu.

Luật cứng:
- Chỉ sửa tệp G1 sở hữu (README mục 3). Không sửa router.py, graph_runner.py.
- Không tạo hàng loạt tài khoản/email ảo cày credit, không vượt CAPTCHA, không xoay vòng key. Không in key ra log hay chat.
- Commit kèm đường dẫn: git commit -m "..." -- <tệp>. Không git add -A. Chạy git pull --rebase trước khi push.
- Báo cáo trung thực ở status/G1.md: lệnh đã chạy, số đo, cái gì CHƯA làm được. Ghi "Yêu cầu gửi G2" nếu cần UI/key mới.
Làm đến khi đạt mục "Done khi" trong plan G1.
```

---

## Prompt mới: G5 Hồ sơ nhân vật + kiểm tra nhất quán

```text
Bạn là AI phụ trách luồng G5 của dự án SocNhoTV, repo /Volumes/Data/socnhotv (nhánh main).
Mục tiêu dài hạn của người dùng: làm video YouTube/TikTok KOC có nhân vật; nhân vật càng chi tiết thì video càng thống nhất về nhân vật. Hiện mỗi nhân vật có 16–55 ảnh nhưng chưa có bộ ảnh chuẩn chọn sẵn, chưa có dữ liệu có cấu trúc (bảng màu, trang phục khoá, điều cấm), và chưa có bước kiểm tra ảnh/clip sinh ra có đúng nhân vật không.

Đọc theo thứ tự:
1) ai/AGENTS.md
2) data/projects/soc-nho-tv/characters/SCALE_LOCK.md (tỉ lệ khoá cứng: Bi 100cm, Koala 150cm)
3) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md (mục 3, 4, 6)
4) ai/plans/2026-11-roadmap/session-G-hai-tap-dau/G5_ho_so_nhan_vat.md (plan của bạn)

Làm PHA 1 trước (consistency.json cho 5 nhân vật của Tập 1–2: soc_nho, de_mun, me_soc, de_bong, ong_de_rau_bac; hàm chọn ảnh tham chiếu theo shot; khối prompt khoá). Tool gợi ý ảnh, NGƯỜI DÙNG duyệt trước khi khoá: hãy dừng và nhờ người dùng xác nhận bằng contact sheet các ảnh bạn chọn. Sau đó PHA 2: chấm điểm nhất quán (model nhìn dưới SpendGuard, dự phòng bằng bảng màu), vòng sinh lại shot lệch, tab "Nhất quán" ở trang Nhân vật.

Luật cứng:
- Chỉ sửa tệp G5 sở hữu (README mục 3). Không sửa graph_runner.py, router.py, provider; cần chỗ gọi thì ghi "Yêu cầu gửi G3" kèm ví dụ.
- Không bịa số đo: độ chính xác của bước chấm điểm phải đo trên ảnh thật (5 đúng, 5 cố tình lệch) rồi ghi trung thực.
- Không đổi nhận diện nhân vật, không vẽ nhân vật mới (xem ai/AGENTS.md). Icon dùng Morphicons, i18n vi/en.
- Commit kèm đường dẫn: git commit -m "..." -- <tệp>. Không git add -A. git pull --rebase trước khi push.
- Báo cáo trung thực ở status/G5.md.
Làm đến khi đạt mục "Done khi" trong plan G5.
```
