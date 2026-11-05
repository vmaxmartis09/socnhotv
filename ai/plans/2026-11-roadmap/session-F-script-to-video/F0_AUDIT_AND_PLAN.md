# F0 — Kiểm toán thực tế & Kế hoạch "Studio: Kịch bản → Video" (v2 — 2026-11-05)

> Đích: trong Studio, nạp hoặc sinh **kịch bản tập theo schema series "Bi và Những Người Bạn"** (scene → shot 8s) → bấm Chạy → ra **video 16:9 đúng kịch bản** (mỗi shot có hình đúng DNA, đúng camera/chuyển cảnh, mỗi nhân vật đúng giọng, phụ đề khớp lời), lưu đúng chỗ, xem được ngay trong Studio; cắt thêm Shorts 9:16.

---

## 1. Kiểm chứng thực tế (không dựa vào báo cáo `status/*.md`)

Cách kiểm: đọc code + chạy thật 2 đồ thị qua core API với kịch bản 3 cảnh "Vì sao lá cây màu xanh?" (Sóc Nhỏ + Koala).

| # | Hạng mục | Báo cáo nói | Thực tế đã kiểm |
|---|---|---|---|
| 1 | Video mẫu `output/cau-vong/final_45s.mp4` | "Hoàn thành xuất sắc, 5/5 nhân vật" | 44,5s nhưng **toàn bộ 12 khung là nền đen + chữ phụ đề**. Cả 7 cảnh trong composition `src=""`. Không có nhân vật, không có hình. |
| 2 | Cổng nghiệm thu `video/verify.py` | pass_all | Điểm **hard-code**: `character_consistency: 5.0` cố định, `voice_clarity` chỉ dựa vào âm lượng. WER đo bằng `whisper-tiny` (0,6–0,7) — vô nghĩa với tiếng Việt. Video đen vẫn pass. |
| 3 | Nút "Tạo video" 3 bước (8 template) | 6/6 node chạy thành công | Chạy thật: `isSuccess: true` nhưng **thành phẩm là ảnh .jpg mock**. `template_render` và `platform_export` **không có handler** trong `graph_runner.py` → rơi vào nhánh `else` sinh ảnh giả. Preset không truyền kịch bản người dùng vào node script (không `mode: paste`/`rawScript`), không nối `scenes` vào render. Job báo `outputUrl = output/final_render.mp4` (file không tồn tại). |
| 4 | Đường thủ công `script → voice_tts → captions → hyperframes_render → export` | — | **Ra MP4 thật** (13,6s, HyperFrames CLI). Nhưng: cảnh rỗng (đen), giọng **đọc luôn nhãn "Sóc Nhỏ:", "Koala:"**, 1 giọng cho mọi nhân vật, thời lượng cảnh không khớp từng câu. |
| 5 | Node `export` | — | **Hard-code cho video cầu vồng**: tiêu đề mặc định "Vì sao cầu vồng…", slug `cau-vong`, phụ đề dự phòng, `final_45s.mp4`, `expect_duration=45`, `providers_per_scene="local_dna_pixar"`. Video "lá cây" bị lưu vào `output/v-sao-c-u-v-ng-c-nhi-u-m-u/` (slug hỏng dấu, sai chủ đề). |
| 6 | Kịch bản AI | "Tự viết kịch bản" | Chưa có provider thật (chỉ `mock`). Chế độ `ai` khi không có provider chỉ **cắt câu chủ đề thành 1 cảnh**. Trên máy đã có sẵn **Ollama `qwen2.5:7b`**, `claude` CLI, `gemini` CLI → chưa dùng. |
| 7 | Giọng OmniVoice `soc-nho` | -14 LUFS | **Tốt**: whisper-small nhận đúng ~90% lời. Có thêm `koala-voice` trong voice_vault nhưng runner không dùng. |
| 8 | Nhân vật | Bi + Koala + 4 nhân vật mới | Chỉ `soc_nho/` có 18 ảnh DNA (nền trắng, chưa tách nền). **Koala, cho_lu, de_bong, de_mun, meo_mimi: 0 ảnh**. Node `character` trả ảnh mock. |
| 9 | Render HyperFrames | đa nền tảng | `hyperframes_render` cứng 1080×1920; **artifact captions không được truyền vào bundle** (chữ lấy từ dialogue cảnh, không karaoke word-level); GSAP tải từ CDN (render offline/tất định dễ gãy); tiến độ 30%/60% phát giả trước khi render. |
| 10 | Fallback | "ghi FALLBACK_USED" | `hyperframes_render` lỗi → **âm thầm** gọi `provider.generate_video` (mock) và vẫn báo thành công. Node lạ → âm thầm mock. |
| 11 | Test backend | "142 pass" | `pytest`: **182 pass, 2 fail** (`test_craft_index.py`). Test xanh trong khi sản phẩm ra video đen → test đang kiểm sai thứ (chỉ kiểm `isSuccess`, không kiểm nội dung khung hình). |
| 12 | Khác | — | Plugin `sources` nạp lỗi (`register()` sai chữ ký). `POST /run` trả 500 khi graph sai schema (nên 422). `data/shared/music_sfx/` rỗng → không có BGM. |

**Kết luận:** Hạ tầng tốt (graph runner, canvas, OmniVoice, HyperFrames CLI 0.9.12, run_manager/SSE, ffmpeg, whisper). Cái **thiếu là cả "lõi kịch bản → cảnh → hình"**: chưa có hợp đồng dữ liệu cảnh đúng nghĩa, chưa có bước tạo hình cho từng cảnh, giọng chưa đa nhân vật, và đường "Tạo video" trong Studio đang trả kết quả giả. Ước lượng thật so với đích: **~35%**.

---

## 1B. Đối chiếu với kịch bản series thật (bổ sung v2 — 2026-11-05 chiều)

Đã `git fetch`: `origin/main` **không có commit mới** (local `main` đi trước remote 1 commit `3320c23`, chưa push). "Kịch bản" thật nằm ở commit `ee2da10`:
`data/projects/soc-nho-tv/content/series/bi-va-nhung-nguoi-ban/` → `series_bible.json`, `PROMPT_MASTER_50_TAP.md`, `MASTER_DNA_PROMPTS.md`, 4 hồ sơ nhân vật mới, `SCALE_LOCK.md`.

| Điều kịch bản yêu cầu | Plan v1 giả định | Thực tế code/dữ liệu |
|---|---|---|
| Tập **~10 phút, 16:9 1920×1080**, 12–16 scene, **70–78 shot × 8s**, + 3 Shorts 9:16 cắt ra | Short 45s 9:16 | `hyperframes_render` **cứng 1080×1920**. Không có khái niệm *shot* trong runner. |
| Định dạng kịch bản = **episode JSON** (`scenes[].shots[]` có `dialogue[{char,line,emotion,delivery}]`, `image_prompt`, `video_prompt`, `camera_move`, `transition_out`, `sfx`, `bgm_cue`, `interactive_pause`, `on_screen_text`) | Tự đặt `SceneSpec` mới | **Không file code nào đọc schema này**. `episodes/` **trống** — chưa có tập nào được viết. `script_parser` chỉ hiểu dạng `Cảnh N:` + `Tên: lời`. |
| Hình: nhân vật 3D Pixar giữ DNA + bối cảnh *photoreal-stylized*, sinh ảnh từng shot rồi **image-to-video 8s** | Tier 0 = DNA cắt nền + nền HTML/SVG | Provider Google (Gemini image, Veo, text) **đã viết thật** (`google_provider.py` 593 dòng, httpx) nhưng **chưa có khoá**. Nền HTML chỉ đủ làm *animatic nháp*, không đạt phong cách series. |
| 5 nhân vật chính + Bác sĩ Koala + 4 người lớn | Bi + Koala | Ảnh DNA: **chỉ Bi** (18 ảnh). Bông/Mun/Lu/Mimi/Koala: **0 ảnh** (chỉ có prompt lock + MASTER_DNA_PROMPTS). |
| `voice_map`: bi→soc-nho, bong→de-bong, mun→de-mun, lu→cho-lu, mimi→meo-mimi, koala→voice-koala | 2 giọng | Vault có `soc-nho`, `koala-voice`, `be-an-voice`. **4 giọng trẻ + 4 người lớn = TODO_CLONE**. **Lệch tên**: bible & `studio_characters.json` ghi `voice-koala`, thư mục vault là `koala-voice` → runner sẽ không tìm thấy. |
| Viết kịch bản tập theo PROMPT_MASTER (JSON ~75 shot rất chi tiết, kèm `qa_self_check`) | Ollama qwen2.5:7b | Model 7B **không đủ** để sinh JSON 75 shot đúng ràng buộc. PROMPT_MASTER được thiết kế cho Claude/Gemini (có ghi "chạy trong Claude Code tại repo này"). |
| Camera move & chuyển cảnh trong danh sách cho phép | — | Có sẵn module `video/craft/{camera,transitions,depth,hooks,lint}` (Session K) — **chưa nối vào render**. |
| Chi phí | — | Theo `models.yaml`: Veo 3.1 fast **0,15 $/giây** → 600s ≈ **90 $/tập** nếu toàn bộ shot là video AI (≈4.500 $ cho 50 tập). Gemini image ≈ vài xu/ảnh → 75 ảnh ≈ **3–5 $/tập**. ⇒ Cần chế độ lai: ảnh + chuyển động camera HyperFrames cho đa số shot, Veo chỉ cho shot "hero". |

**Kết luận v2:** Phase 0 (trung thực) giữ nguyên. Còn lại phải **lấy episode JSON của series làm hợp đồng trung tâm**, render **16:9 theo shot**, coi ảnh AI theo shot là đường chính (không phải nền HTML), và quản lý chi phí/tiếp tục chạy theo từng shot. Đích đo được được chia thành mốc tăng dần, không nhảy thẳng tới tập 10 phút.

---

## 2. Danh sách thiếu (v2, ưu tiên)

### P0 — Chặn đích "Studio dựng video theo kịch bản series"
1. **Trung thực**: node không có handler → lỗi; bỏ fallback mock âm thầm; gỡ hard-code cầu vồng ở `export`; `verify` đo thật (khung đen, media mỗi shot, WER whisper-small, đọc nhãn tên). *(như v1)*
2. **Hợp đồng `Episode` = schema epNN của PROMPT_MASTER** (`core/contracts/episode.py`, Pydantic): nạp, kiểm (`qa_self_check` tính lại bằng code: tổng 570–630s, 70–78 shot, t_start/t_end liền mạch, ≤15 từ/câu, ≤18 từ/shot, câu tỉ lệ trong mọi prompt nhiều nhân vật, voice_map hợp lệ).
3. **Node `episode_script`**: 3 chế độ — *import* file `episodes/epNN_*.json`; *paste* (giữ `script_parser` cho kịch bản ngắn → chuyển thành Episode 1 scene); *generate* (gọi LLM mạnh theo PROMPT_MASTER + bible: `claude -p` CLI hoặc Gemini; Ollama chỉ để sửa JSON nhỏ). Sinh theo từng scene để không vượt độ dài, ghép và kiểm schema.
4. **Viết thật tập 01** "Núi lửa trong bụng Bi" → `episodes/ep01_nui-lua-trong-bung-bi.json`, qua validator. Không có tập thật thì không có gì để dựng.
5. **Giọng đa nhân vật theo shot**: mỗi `dialogue` line → OmniVoice theo `voice_map`, áp `emotion/delivery` (tempo/pitch nhẹ), mastering; đặt line vào trong khung 8s của shot (cảnh báo nếu lời > 8s); trả `timings`. Sửa lệch `voice-koala`/`koala-voice` (alias trong vault).
6. **Hình theo shot (`shot_images`, batch)**: Tier A — Gemini image với ảnh tham chiếu DNA + `image_prompt`, cache theo hash prompt, chạy lại từng shot; Tier 0 (không khoá) — *animatic*: DNA cắt nền + nền theo `location_id` (ảnh tĩnh/HTML) để kiểm đường ống, ghi rõ "animatic".
7. **Render tập 16:9 theo shot (`episode_render`)**: HyperFrames composition = chuỗi shot 8s, `camera_move` → keyframes (dùng `craft/camera`), `transition_out` → `craft/transitions`, karaoke phụ đề, `on_screen_text`, `interactive_pause`, BGM ducking -12dB, title sequence 15s + end screen 20s; platform-aware (16:9 chính, 9:16 cho shorts). Render từng scene rồi ghép (10 phút một composition sẽ chậm/treo).
8. **Studio**: canvas gọn cho tập dài: `episode_script → shot_images → [shot_videos] → voice_multi → captions → episode_render → export (+ shorts_cut)`. Thêm **bảng Storyboard** (scene → shot: ảnh, lời, camera, trạng thái, chi phí, chạy lại 1 shot). Nút "Tạo video" dùng chuỗi này; job lấy kết quả thật từ run state.

### P1 — Cần để ra đúng chất lượng series
9. **Ảnh DNA cho Bông, Mun, Lu, Mimi, Koala** (master chính diện nền xám + lineup chiều cao 0–150cm) từ `MASTER_DNA_PROMPTS.md` — cần provider ảnh; người dùng duyệt từng nhân vật trước khi khoá vào `characters/<id>/`.
10. **Clone 4 giọng trẻ + người lớn** (skill `vietnamese-voice-clone`) — cần mẫu giọng nguồn. Tạm thời: map giọng thay thế có gắn nhãn `voice_fallback`, không âm thầm.
11. **Spend guard theo tập**: ước tính trước ($ ảnh + $ video), người dùng xác nhận 1 lần, dừng khi vượt hạn mức, chạy tiếp từ shot dở (resume).
12. **Shot video AI (`shot_videos`)**: Veo image-to-video 8s cho shot được đánh dấu `hero` (mặc định ≤10 shot/tập), còn lại ảnh + camera move.
13. BGM/SFX: thư viện `music_sfx/` (đang trống) + map `bgm_cue`/`sfx`; bài hát gốc của tập (TTS hát hoặc nhạc nền + lời karaoke).
14. Vendor GSAP, tiến độ render thật, `/run` trả 422, sửa plugin `sources`.

### P2
15. `shorts_cutdowns` → 3 Shorts 9:16 reframe theo safe-zone 180/320.
16. Xuất YouTube metadata (title/description/chapters/tags/thumbnail) sang Social Hub.
17. Sinh hàng loạt 50 tập + lịch sản xuất.

---

## 3. Kế hoạch thực thi v2 (mốc tăng dần, mỗi mốc có cổng bằng file thật)

| Mốc | Nội dung | Cần khoá? | Cổng nghiệm thu |
|---|---|---|---|
| **M0 — Trung thực** (0,5 ngày) | P0-1 | Không | Video cầu vồng cũ bị verify **FAIL**; node lạ báo lỗi; export không còn chữ "cầu vồng". |
| **M1 — Kịch bản tập 01** (1 ngày) | P0-2, P0-3, P0-4 | Không (Claude Code viết) | `ep01_*.json` qua validator: 570–630s, 70–78 shot, mọi ràng buộc sư phạm đạt; node `episode_script` import được và hiện danh sách scene/shot. |
| **M2 — Animatic 1 scene từ Studio** (1,5 ngày) | P0-5, P0-6 (Tier 0), P0-7, P0-8 tối thiểu | Không | Từ Studio chạy **sc01 (cold open, 3–4 shot ≈ 24–32s)** → MP4 **16:9**: mỗi shot có hình (không khung đen), Bi đúng DNA, đúng camera move/transition, giọng không đọc nhãn tên, WER ≤ 25%, phụ đề khớp. Contact sheet được mở xem và nhận xét. |
| **M3 — Tier A ảnh AI 1 scene** (1 ngày) | P0-6 Tier A, P1-9 (DNA nhân vật có mặt), P1-11 | **Gemini** | Cùng sc01 nhưng ảnh sinh theo `image_prompt` + DNA; chi phí thật ghi trong `video.json`; chạy lại 1 shot không chạy lại cả scene. |
| **M4 — Tập 01 đầy đủ ~10 phút** (2 ngày) | Render theo scene + ghép, title/end screen, BGM, Storyboard UI, resume | Gemini (+ giọng clone nếu có) | `final.mp4` 570–630s 16:9, 70–78 shot đều có media, verify pass bằng số đo, thời gian render & chi phí ghi lại; xem được trong Studio. |
| **M5 — Nâng chất** (tuỳ chọn) | P1-12 Veo hero shots, P1-10 giọng clone, P2-15 Shorts | Gemini/Veo | ≤10 shot hero là video AI; 3 Shorts 9:16 hợp lệ. |
| **M6 — Nghiệm thu & nhân bản** | Test E2E tự động (1 scene), tập 02 chỉ bằng đổi file kịch bản, cập nhật CONTINUITY | — | Tập 02 animatic ra file hợp lệ không sửa code. |

Ước tính: M0–M2 ≈ **3 ngày, không cần khoá** (chứng minh Studio dựng được video theo đúng kịch bản series). M3–M4 ≈ 3 ngày nữa, phụ thuộc khoá Gemini và ảnh DNA được duyệt.

---

## 4. Cần người dùng quyết/cung cấp
1. **Khoá Gemini API** (Cài đặt → key_vault): mở ảnh AI theo shot (M3+) và Veo. Không có khoá thì dừng ở animatic M2.
2. **Ngân sách/tập**: gợi ý *ảnh AI cho mọi shot + Veo ≤10 shot hero* ≈ 15–20 $/tập (theo đơn giá trong `models.yaml`, cần xác nhận lại giá Google hiện hành) thay vì ≈ 90 $/tập khi toàn bộ là video AI.
3. **Mẫu giọng** cho Bông, Mun, Lu, Mimi (và người lớn) để clone; chưa có thì dùng giọng thay thế có gắn nhãn.
4. **Duyệt ảnh DNA** 5 nhân vật sau khi sinh (một lần, rồi khoá).
5. Có push commit `3320c23` lên GitHub không (hiện local đi trước remote).

---

## 5. Bài học dựng video từ nghiên cứu FB/TikTok (2026-11-04) → áp vào plan

Nguồn: `data/shared/knowledge/video_craft/` (Session D: ~23 video Facebook phân tích riêng từng video; Session D2: 6 video TikTok phân tích sâu, 282 video chỉ sàng lọc theo tiêu đề trong 35 phút).
**Độ tin cậy:** số đo `edit_metrics.json` là thật (ffprobe). REPORT của 6 video TikTok là **văn mẫu lặp lại** (giống nhau từng câu, tự mâu thuẫn số liệu) → chỉ lấy số đo. Trạng thái `in-studio` của thẻ craft bị thổi phồng: `craft/{camera,transitions,depth}` **chưa được gọi khi render** (chỉ 2 API gợi ý hook / lint kịch bản dùng tới).

| # | Bài học (nguồn) | Áp vào mốc |
|---|---|---|
| 1 | **Phân rã theo shot ngắn + ghép tất định**: model AI chỉ ổn định 4–8s/clip; chữ, phụ đề, thời gian do engine HTML quản lý, không để AI vẽ chữ (FB `seq_n03`, TikTok SUMMARY) | Khẳng định hợp đồng shot 8s của series. `on_screen_text`, phụ đề, title card luôn là lớp HTML — M2/M4 |
| 2 | **Neo nhân vật 3 góc** (chính diện / 3/4 / nghiêng) truyền làm ảnh tham chiếu cho mọi lần sinh hình (FB `seq_n01`) | M3: mỗi nhân vật sinh 3 anchor + lineup chiều cao; Bi hiện chỉ có góc chính diện |
| 3 | **Image-to-video khoá khung đầu/cuối, không text-to-video; biên độ chuyển động vừa phải; nối shot liền mạch bằng khung cuối shot trước** (`ai-video-realism`, `dual-node-stitching`, FB `seq_007`) | M5 Veo: start frame = ảnh shot; shot liên tiếp cùng cảnh lấy tail-frame shot trước |
| 4 | **Transition foresight**: hướng chuyển cảnh nối tiếp vector chuyển động 0,5s cuối shot trước, tránh "đụng trục" (FB `seq_n01`) | M2: nối `craft/transitions.py` vào `episode_render`; validator M1 báo lỗi khi `transition_out` ngược hướng `camera_move` |
| 5 | **Ngữ pháp camera có tham số**: push-in 1.0→1.08 suốt shot; punch-in 1.25 trong 0,15s đúng điểm nhấn âm; dolly-out 1.1→1.0; pan parallax; whip kèm blur. Zoom chỉ 5–10% mỗi 3–5s để không chóng mặt (playbook camera, FB `seq_006`, `seq_n10`) | M2: map `camera_move` → preset GSAP qua `craft/camera.py`. Đây là thứ làm shot ảnh tĩnh 8s "sống" |
| 6 | **Chiều sâu 3 lớp**: prompt tiền/trung/hậu cảnh (bible đã có); khi dựng từ ảnh thì parallax 0.2x / 1.0x / 1.8x; tiền cảnh chỉ 5–15% mép khung; luôn có bóng tiếp xúc dưới chân (FB `seq_n08`, playbook depth) | M2 Tier 0 dựng 3 lớp; M3 thêm lớp hạt/bokeh tiền cảnh phủ trên ảnh AI |
| 7 | **Chống "rác AI" ở hậu kỳ**: hạt film 6–8% overlay, grade màu thống nhất (ấm), bóng tiếp xúc (`ai-video-realism-anti-artifact`) | M3/M4: thêm 1 pass grade + grain chung cho mọi shot → các ảnh sinh độc lập trông như cùng một phim |
| 8 | **Prompt chỉ ~10% chất lượng; 90% là ảnh điều kiện, camera và nhịp dựng** (TikTok SUMMARY) | Ưu tiên đầu tư anchor DNA + dựng, không kéo dài prompt |
| 9 | **Nhịp đo thật**: clip quảng cáo/KOC 3,75–5,65 cắt/10s (shot ~1,8–2,7s); video kiến thức/nói chuyện 0,1–0,4 cắt/10s; tốc độ nói 2,6–3,4 từ/s. Series dùng ≤18 từ/8s ≈ 2,25 từ/s (chậm, hợp trẻ 3–7) | Shot 8s là **đơn vị sinh hình**, không bắt buộc là đơn vị cắt: cho phép reframe/punch-in bên trong 1 shot khi có đổi người nói. Shorts cắt ra (M5) cần nhịp nhanh hơn hẳn bản 16:9 |
| 10 | **Hook**: hình/chữ xuất hiện trong ≤0,5s, không chào hỏi, 3 biến thể chấm điểm (playbook hook, `craft/hooks.py`) | M1: validator chấm `hooks[A/B/C]` bằng `hooks.py`; cold open không mở bằng lời chào |
| 11 | **Âm thanh**: -14 LUFS, ducking khi có thoại, SFX nhấn ở điểm lật, cắt đúng phách nhạc | M4: ducking -12dB theo bible; đặt SFX theo `sfx[]` của shot; punch-in trùng SFX |
| 12 | **Render song song theo đoạn rồi ghép** (FB `seq_n03`) | M4: render từng scene song song → concat, thay vì 1 composition 10 phút |
| 13 | **Ra nhanh rồi sửa theo đường giữ chân** (FB `seq_014`) | Củng cố thứ tự mốc: animatic trước, chất lượng sau; P2 nối analytics retention về kịch bản tập sau |

**Không áp dụng / cần thận trọng:** thẻ VTON, lookbook, affiliate, KOC (lệch mục tiêu series thiếu nhi); Kling/Runway/ComfyUI (stack hiện chỉ có provider Google; ComfyUI cần GPU NVIDIA); playbook `yt-animation-episode.md` đã lỗi thời (45–90s, chỉ Bi + Koala, ghi DNA "RGBA trong suốt" nhưng thực tế ảnh nền trắng); vài thẻ trỏ tới file không tồn tại (`outfit-scan-pedestal.md`, `beat-matched-camera.md`); thông số Kling motion 3–5 và "60% xem tắt tiếng" chưa có nguồn kiểm chứng.
