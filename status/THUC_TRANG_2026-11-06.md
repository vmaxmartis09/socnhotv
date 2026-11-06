# THỰC TRẠNG DỰ ÁN SOCNHOTV — 2026-11-06

> Viết sau khi kiểm trực tiếp code, dữ liệu, server đang chạy và gọi thử từng thành phần.
> Không dựa vào các báo cáo cũ (`status/V.md`, `status/E.md`, `ai/memory/CONTINUITY.md`), vì các báo cáo đó ghi "HOÀN THÀNH 100%" trong khi thực tế không khớp (xem N7).
> Người dùng xác nhận: **hiện chưa có video nào làm ra được.** Các file `output/tap01_*.mp4`, `tap02_*.mp4` là dữ liệu cũ chạy Mock, bỏ qua.

---

## 0. Trả lời thẳng

| Câu hỏi | Trả lời |
|---|---|
| Flow Studio đã làm ra video chưa? | **Chưa.** Chưa có video nào có hình AI thật và giọng thật đi ra từ flow Studio. |
| Sinh được ảnh chưa? | **Chưa, ở chế độ thật.** Chỉ có Mock: một ảnh mẫu dùng lại cho cả 30 shot. |
| Sinh được video (clip AI chuyển động) chưa? | **Chưa.** Flow Tập không có node sinh video. Node `video_gen` mỗi lần chỉ làm được 1 clip và chưa từng chạy thật. |
| Có chỗ chọn model và nguồn cung cấp chưa? | **Chưa đúng nghĩa.** Backend có sổ 16 model và API `/models`, `/providers`, nhưng giao diện không dùng tới. Dropdown viết cứng 2 lựa chọn. Không có chỗ nào cho biết model nào có key, miễn phí hay trả phí, có nhận ảnh nhân vật tham chiếu không. |
| Công cụ edit video hoạt động thế nào? | Không có trình edit tay (không có timeline). "Dựng" là máy tự sinh 1 trang HTML: mỗi shot là 1 ảnh hoặc clip phủ kín khung, zoom nhẹ, có phụ đề và 1 track giọng, rồi gọi `hyperframes render` ra MP4. **Riêng phần dựng này chạy được.** |
| Flow Studio có chạy không? | **Ở Mock thì chạy hết** (Kịch bản → Dàn diễn viên → Ảnh → Kiểm định → Dựng → Xuất), nhưng sản phẩm vô dụng (ảnh giả, tiếng im lặng). **Ở chế độ thật thì dừng ngay ở node Ảnh**, vì không có nguồn sinh ảnh nào dùng được. |

---

## 1. Những gì chạy được thật (đã tự kiểm hôm nay)

| Thành phần | Trạng thái | Bằng chứng |
|---|---|---|
| Kịch bản đã biên dịch | ✅ Tốt | 51 tập `.md` → `script.json`. Tập 1 và Tập 2 mỗi tập có 10 cảnh, 30 shot, 600 giây. Shot nào cũng có `imagePrompt`, `videoPrompt`, thoại, `speakerId`, `camera`, `sfx`, `bgm`. |
| Hồ sơ nhân vật + ảnh DNA | ✅ Có | 10 nhân vật, mỗi nhân vật 16–55 ảnh. Tập 1: `soc_nho`, `de_mun`, `me_soc`. Tập 2: `de_mun`, `de_bong`, `ong_de_rau_bac`. Đã gán giọng trong `characters/studio_characters.json`. |
| Giọng OmniVoice (chạy trên máy, $0) | ✅ Chạy | `scripts/voice/voice_studio.py speak --voice soc-nho` cho ra MP3 có tiếng (-17.8 dB), mất khoảng 15 giây mỗi câu. |
| HyperFrames CLI | ✅ Có | `tool/dashboard/node_modules/.bin/hyperframes` 0.9.12. `hyperframes doctor`: Chrome headless và FFmpeg 8.1.1 OK. |
| Core API `:8000`, Studio `:3000` | ✅ Đang chạy | `/health` healthy. Có tiến trình SSE, cache kết quả từng node, cổng kiểm định chính sách. |
| Đường ống Mock từ đầu đến cuối | ✅ Chạy | Toàn bộ output node trong `runs/_node_outputs/graph_soc-nho-tv/*.json` đều có `"mock": true`. |

---

## 2. Điểm tối & điểm nghẽn (xếp theo mức chặn)

### N1 — Không có nguồn sinh ảnh/video thật nào dùng được · **CHẶN TẤT CẢ**
- `GEMINI_API_KEY` trong `.env`: Google trả về **`400 API key not valid`** (đã thử bằng lệnh liệt kê model, không tốn phí).
- Không có `FAL_KEY`, không có `REPLICATE_API_TOKEN`. `GET /providers` trả về: google=false, fal=false, replicate=false.
- Chưa tích hợp nguồn miễn phí nào: không có API free (Pollinations, Cloudflare Workers AI, Hugging Face…), cũng không có model chạy trên máy (Mac M4, 16 GB RAM).
- → **Giải pháp: G1.**

### N2 — "Mock" là một công tắc chung cho mọi thứ, tắt luôn cả phần miễn phí · **CHẶN**
- `core/providers/router.py::speak_voice`: hễ bật Mock là trả về **WAV im lặng**, dù OmniVoice trên máy miễn phí và đang chạy tốt.
- Tắt Mock thì node ảnh (đang đặt `model: mock-image`) bị tự chuyển sang google, gặp `MissingApiKey` và báo lỗi.
- Mặc định giao diện `isMockMode: true` (`store/slices/canvasSlice.ts`); API cũng mặc định `mockMode: True`.
- → Không có chế độ lai kiểu "ảnh tạm + giọng thật" để làm ra ngay một bản animatic nghe được.
- → **Giải pháp: G2**: đặt chế độ chạy riêng cho từng loại. Ảnh, video, text: mock hoặc thật. Giọng, phụ đề, dựng: luôn chạy thật trên máy.

### N3 — Chọn model & nguồn cung cấp chưa được định nghĩa · **CHẶN TRẢI NGHIỆM**
- Backend có `core/models_registry/models.yaml` (16 model) và API `/models`, `/providers`. **Giao diện không gọi tới.**
- `components/studio/tabs/NodeTab.tsx` viết cứng dropdown. Video: `google-veo-2 | fal-ltx-video`. Ảnh: `gemini-2.5-flash-image | imagen-3.0-generate` (riêng `imagen-3.0-generate` không có trong sổ). Card `image_gen` bị loại khỏi dropdown nên **không có chỗ chọn model**. Graph hiện tại để `n_keyframes.model = "mock-image"`.
- Không hiển thị: nguồn đã có key chưa, miễn phí hay trả phí, giá, có nhận ảnh nhân vật tham chiếu không, hạn mức còn bao nhiêu.
- Không có chuỗi dự phòng (nguồn A hết hạn mức thì tự chuyển sang nguồn B).
- → **Giải pháp: G1** (sổ model + các nguồn) **và G2** (bộ chọn model `ModelPicker`).

### N4 — Flow Tập không có bước sinh video, `video_gen` chưa dùng được · **CHẶN PHẦN "CHUYỂN ĐỘNG"**
- Flow hiện có 6 node: Kịch bản → Dàn diễn viên → Keyframe (`image_gen`) → Kiểm định → Dựng → Xuất. **Không có `video_gen`.**
- `video_gen` chỉ sinh 1 clip, không lặp qua từng shot như `image_gen`.
- Lệch thời lượng: mỗi shot dài **20 giây**, `videoPrompt` lại ghi "8-second clip", còn model chỉ cho clip 4–10 giây.
- Khối lượng: 2 tập × 600 giây = 1200 giây, tức khoảng **150–240 clip AI**. Nguồn miễn phí không gánh nổi trong ngắn hạn.
- → **Giải pháp: G3** (lặp theo shot, giới hạn số clip, cho phép nhập clip làm tay) và chia mục tiêu theo **mức A/B/C** (mục 3).

### N5 — Bộ dựng quá thô cho video 10 phút
- Mỗi shot là 1 ảnh tĩnh đứng suốt 20 giây, chỉ zoom 1.05→1.03, không dùng trường `camera` của kịch bản.
- Các module craft `tool/src/socnhotv/video/craft/` (`hooks`, `depth`, `transitions`, `camera`, `lint`) **không được gọi ở đâu cả**: grep trong `graph_runner.py` và `hyperframes_engine.py` không ra kết quả nào.
- **Không có nhạc nền**: bộ chạy không truyền `bgm` (grep "bgm" trong `graph_runner.py` không ra kết quả nào) và `data/shared/music_sfx/` trống. **Không có SFX**, dù kịch bản có trường `sfx`/`bgm`.
- Không có trình chỉnh tay (timeline) trong Studio. Muốn sửa chỉ có cách sửa kịch bản hoặc sửa HTML.
- `npx -y hyperframes render` chạy trong thư mục bundle, nên có thể tải bản mới nhất trên npm thay vì dùng bản 0.9.12 đã ghim.
- → **Giải pháp: G3.**

### N6 — Rủi ro mất tiền ngầm & lỗi bị nuốt im lặng
- Trong `graph_runner.py`, nhánh `hyperframes_render`: nếu dựng lỗi, code **tự gọi `provider.generate_video(prompt="Final rendered video composition", duration 45s)`**. Ở chế độ thật mà có key Veo thì vừa tốn tiền vừa ra một video không liên quan. Chỗ này phải đổi thành báo lỗi rõ ràng.
- HyperFrames lỗi thì lặng lẽ chuyển sang FFmpeg, chỉ ghi vào log, người dùng không được báo.
- → **Giải pháp: G3.**

### N7 — Báo cáo cũ nói quá
- `status/V.md`, `status/E.md`, `CONTINUITY.md` ghi "HOÀN THÀNH 100%", "video đầu tiên xuất sắc". Thực tế `output/cau-vong/final_45s.mp4` không còn, và mọi output của flow Tập đều `mock: true`.
- Nghiệm thu chỉ dựa vào pytest và ảnh chụp UI. Không kiểm âm lượng, không kiểm ảnh có bị trùng không, không kiểm provenance (nguồn sinh thật hay mock).
- → **Giải pháp:** "Định nghĩa Done" mới ở `ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md`. Bắt buộc có ffprobe, volumedetect, số ảnh khác nhau, provenance `mock=false`, và người dùng xem bằng mắt.

### N8 — Vệ sinh repo (nguy hiểm khi nhiều AI cùng làm)
- **844 tệp trong `data/` đang nằm sẵn trong staging** (`git diff --cached --stat`). AI nào gõ `git commit` không kèm đường dẫn sẽ commit cả đống mp3/asset, trái quy tắc "không commit data/".
  - Đề xuất (người dùng tự quyết): `git restore --staged data/`. Lệnh này chỉ bỏ khỏi staging, không xoá tệp.
- `runs/` có **695 thư mục**, phần lớn do test ghi thẳng vào dữ liệu dự án thật (mỗi run 0 giây, 2 node).
- → Quy tắc bắt buộc cho mọi AI: commit **kèm đường dẫn** (`git commit -- <tệp của mình>`) và test phải dùng thư mục tạm (giao cho G4).

---

## 3. Giải pháp tổng: chia mục tiêu thành 3 mức Done

| Mức | Nội dung | Khả thi miễn phí? |
|---|---|---|
| **A — Animatic thật** (mục tiêu đầu tiên) | Mỗi shot có ≥1 ảnh AI thật, đúng nhân vật theo DNA; giọng thật cho từng nhân vật; phụ đề; nhạc nền; chuyển động camera theo trường `camera`. Tập 1 và Tập 2 (10 phút) **phát được và tua được trong Studio**. | **Có.** Cần 60 ảnh cho 2 tập: model chạy trên máy hoặc API free gánh được. |
| **B — Clip AI cho shot chính** | 5–10 shot mỗi tập (mở đầu, cao trào, bài hát, kết) thay ảnh bằng clip AI 5–8 giây, lấy từ credit miễn phí hằng ngày hoặc người dùng làm tay rồi nhập vào. | **Một phần**, phải làm dần qua nhiều ngày. |
| **C — Chuyển động toàn bộ** | Thay dần mọi shot bằng clip. | **Không**, trừ khi có ngân sách hoặc chấp nhận model trên máy chạy rất chậm. |

Đi theo thứ tự **A → B → C**. Không chờ có video AI rồi mới làm ra tập đầu tiên.

---

## 4. Bản đồ điểm nghẽn → plan

| Điểm nghẽn | Plan | AI phụ trách gợi ý |
|---|---|---|
| N1 không có nguồn | `G1_nguon_ai_mien_phi.md` | AI có duyệt web (Gemini / Antigravity / Claude có web) |
| N2 Mock chung, N3 chọn model | `G2_che_do_lai_chon_model.md` | AI mạnh frontend + FastAPI (Cursor / Claude) |
| N4 video theo shot, N5 bộ dựng, N6 rủi ro tiền | `G3_engine_dung_theo_shot.md` | AI mạnh Python (Codex / Claude) |
| N7 nghiệm thu, N8 vệ sinh repo, dữ liệu tập, xem trong Studio | `G4_tap1_tap2_studio_nghiem_thu.md` | AI có trình duyệt để test Studio (Claude Code) |

Thứ tự chạy, quyền sở hữu tệp và hợp đồng chung: `ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md`.
4 prompt để gửi cho các AI: `ai/plans/2026-11-roadmap/session-G-hai-tap-dau/PROMPTS.md`.

---

## 5. Cách tự kiểm lại các khẳng định trên

```bash
# N1: key Gemini có hợp lệ không (không tốn phí)
set -a; source .env; set +a; curl -s "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1" -H "x-goog-api-key: $GEMINI_API_KEY" | head -c 300
# N1: nguồn nào đã cấu hình
curl -s localhost:8000/providers | python3 -m json.tool | grep -E '"id"|configured'
# N2: output các node của flow đều là mock
grep -l '"mock": true' data/projects/soc-nho-tv/runs/_node_outputs/graph_soc-nho-tv/*.json
# N2: giọng thật chạy được
.venv/bin/python scripts/voice/voice_studio.py speak --voice soc-nho --script "Chào các bạn nhỏ" --output /tmp/bi.mp3 --no-master
# N5: các module craft không được dùng
grep -n "craft" tool/src/socnhotv/core/engine/graph_runner.py tool/src/socnhotv/video/hyperframes_engine.py
# N8: số tệp data đang nằm trong staging
git diff --cached --name-only | grep -c '^data/'
```
