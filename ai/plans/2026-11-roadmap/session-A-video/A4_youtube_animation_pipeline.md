# A4 — Pipeline YouTube hoạt hình dài tập + Tự cắt Shorts + Nghiệm thu E2E

Bạn là Session A. Đọc: `CONTRACTS.md`, `status/A.md`, `SCALE_LOCK.md` (tìm trong `data/projects/soc-nho-tv/characters/` hoặc repo), master DNA `characters/soc_nho/`, `core/engine/graph_runner.py` (chỉ đọc), providers `core/providers/*` (image_gen/video_gen), `voice_adapter.py`, `caption_adapter.py`, `components/project/EpisodeDetail.tsx` + `ScriptComposer.tsx` (chỉ đọc để hiểu Episode model), skill `faceless-explainer`, `general-video`.

## Mục tiêu
Từ 1 kịch bản tập (Episode) → video YouTube 16:9 3–10 phút hoạt hình nhân vật Sóc Nhỏ (Bi) & Koala, đúng DNA, đúng tỉ lệ, + 3 Shorts 9:16 tự cắt từ đoạn hay nhất.

## Việc cần làm
1. **`video/episode/planner.py`**: script tập (text) → `ScenePlan[]` (`scene_id, characters[], location, action, dialogue[{speaker, line}], camera, duration_est`). Dùng LLM qua `core/providers/router.py` (provider text đang có), prompt hệ thống bắt buộc: chỉ dùng nhân vật đã có trong `characters/`, khoá tỉ lệ Bi 100cm / Koala 150cm ghi vào mô tả mọi shot.
2. **`video/episode/assets.py`**: mỗi scene → ảnh key-frame bằng `image_gen` với reference ảnh master DNA (không tự vẽ nhân vật mới), tuỳ chọn `video_gen` (image→video 4–6s) nếu provider có & spend guard cho phép; cache theo hash prompt trong `output/<ep>/scenes/`. Dùng `spend_guard` + `/estimate` để hiện chi phí trước khi chạy.
3. **`video/episode/voice.py`**: thoại từng nhân vật: Bi = `soc-nho`, nhân vật khác = voice-id ghi trong character profile; mastering TikTok chain; ghép timeline thoại.
4. **`video/episode/assemble.py`**: dựng `RenderRequest` template `yt-animation-episode-v1` (intro → scenes Ken Burns/keyframes → end-screen 20s), platform `youtube`; captions; BGM ducking. Chương (chapters) YouTube tự sinh từ scene → `output/<ep>/chapters.txt`; mô tả + tag gợi ý → `output/<ep>/youtube_meta.json`.
5. **`video/episode/shorts.py`**: chọn 3 đoạn 20–45s (điểm cao = có hook thoại, nhiều chuyển động, kết thúc trọn câu) → render template `shorts-fact-v1`/`story-cartoon-v1` hoặc `platform_export` blur-pad sang `shorts`,`tiktok`,`reels`.
6. **API** (thêm vào `routes/video.py`): `POST /projects/{pid}/video/episodes/{eid}/plan` (trả ScenePlan + chi phí ước tính), `POST …/build` (chạy full, trả job id), `GET …/status`. Lưu tiến trình từng bước để chạy lại không làm lại phần đã xong.
7. **UI** trong `components/renders/EpisodeBuildPanel.tsx` + route `app/[locale]/renders/episode/[eid]/page.tsx`: xem ScenePlan dạng bảng sửa được, duyệt ảnh key-frame (thay/tạo lại từng scene), chi phí, nút Build. Từ `EpisodeDetail` không sửa được (vùng khác) → thêm link vào REQUESTS cho 99_FINAL.
8. **Nghiệm thu E2E Session A** (`tool/tests/test_video_e2e.py`, dùng mock provider): Episode mẫu "Sóc Nhỏ và Chiếc Răng Sâu" → plan → assets (mock) → voice (mock nếu không có GPU) → render youtube + 3 shorts → `create_draft_post` được gọi 4 lần.
   Chạy thật 1 lần với provider thật ở chế độ 3 scene ngắn (giới hạn chi phí ≤ mức spend guard mặc định).

## Cuối Session A
- Cập nhật `status/A.md`: % hoàn thành từng mảng của A, lệnh chạy mẫu, giới hạn đã biết, đề xuất cho 99_FINAL.
- Ghi chỉ số render (thời gian/1 phút video, chi phí/tập) vào `data/projects/soc-nho-tv/output/_metrics/render_metrics.json` (vùng của A — C chỉ đọc).
- Commit `feat(A4): youtube animation episode pipeline + auto shorts`.
