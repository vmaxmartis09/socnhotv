# Session G: Hai tập đầu chạy được, xem được trong Studio

> Viết 2026-11-06. Đọc trước: `status/THUC_TRANG_2026-11-06.md`.
> **Mục tiêu duy nhất:** Tập 1 (`ep01-nui-lua-trong-bung-bi`) và Tập 2 (`ep02-mun-so-bong-toi`) đi ra từ **flow Studio**, đạt **Mức A (animatic thật)**, phát và tua được ngay trong Studio, chi phí API **$0**.
> Sau Mức A mới làm Mức B (clip AI cho shot chính).

---

## 1. Bốn luồng song song

| Luồng | Tên | Giải quyết | Ra sản phẩm gì |
|---|---|---|---|
| **G1** | Nguồn AI miễn phí | N1 | Báo cáo nguồn free đã gọi thử thật. ≥1 nguồn ảnh free **có ảnh tham chiếu nhân vật** chạy được. ≥1 đường làm clip video free. Provider mới + sổ model. |
| **G2** | Chế độ lai + chọn model | N2, N3 | `runPolicy` theo từng loại (giọng luôn thật). `ModelPicker` lấy dữ liệu từ `/models`. Trang Cài đặt có key cho các nguồn mới. |
| **G3** | Engine dựng theo shot | N4, N5, N6 | Bỏ fallback tốn tiền. `video_gen` lặp theo shot (có trần số clip). Nhập clip làm tay. Camera theo kịch bản. BGM/SFX. |
| **G5** | Hồ sơ nhân vật + kiểm tra nhất quán | Nhân vật đồng nhất qua ảnh/clip | Bộ ảnh chuẩn nhiều góc, khoá màu/trang phục, ảnh tham chiếu tốt nhất theo shot, bước chấm điểm giống DNA và sinh lại shot lệch. |
| **G4** | Dữ liệu tập + Studio + nghiệm thu | N7, N8 | Giọng 2 tập dựng sẵn vào cache. Kiểm DNA. Đổi tập bằng 1 tham số. Xem/tua video trong Studio. Test không ghi vào dữ liệu thật. **Chạy nghiệm thu cuối.** |

---

> **Cập nhật:** G1 nay gồm cả 1 nguồn trả phí được kiểm soát (Google Nano Banana + Gemini Omni Flash). G5 là luồng thứ 5 (xem `G5_ho_so_nhan_vat.md`); G5 tạo `characters/<id>/consistency.json`, G3 và G1 chỉ đọc.

## 2. Thứ tự (tuần tự theo pha, song song trong pha)

```
Pha 0 (mọi AI): đọc THUC_TRANG + README này + plan của mình. Không sửa gì ngoài tệp mình sở hữu.

Pha 1 — song song, không ai chờ ai
  G1: kiểm thật các nguồn free → báo cáo ai/knowledge/free_ai_sources.md + provider ảnh free đầu tiên
  G2: runPolicy ở backend (router + run API), giọng luôn local; /models trả thêm tier/available
  G3: bỏ fallback generate_video 45s; ghim HyperFrames local; camera theo trường `camera`
  G4: tách test khỏi dữ liệu thật; dựng sẵn giọng 60 câu (2 tập); kiểm DNA 5 nhân vật; kiểm Range/tua video

Mốc M1 (G4 kiểm, cần G2-pha1 + G3-pha1):
  Tập 1 chạy ở chế độ lai: ảnh mock + GIỌNG THẬT → MP4 10 phút có tiếng, xem được trong Studio.

Pha 2 — song song
  G1: thêm nguồn ảnh dự phòng + nguồn clip video free (API, model chạy trên máy, hoặc đường làm tay)
  G2: ModelPicker trên card image_gen/video_gen + menu chế độ chạy + key mới trong Cài đặt
  G3: video_gen lặp theo shot + nhập clip làm tay + BGM ducking + SFX + chuyển cảnh
  G4: preset "Tập hoạt hình (tái dùng)", đổi tập bằng episodeId, nút xuất "gói shot" để làm clip tay

Mốc M2 (G4): Tập 1 Mức A, ảnh thật từ nguồn free, chọn trong ModelPicker.
Mốc M3 (G4): Tập 2 Mức A, cùng flow, chỉ đổi episodeId.
Mốc M4 (G4, Mức B): mỗi tập ≥5 shot có clip AI thật (từ API free hoặc nhập tay).
```

Luồng nào xong pha của mình sớm thì **làm tiếp pha sau trong plan của chính mình**, không làm sang phần của luồng khác.

---

## 3. Quyền sở hữu tệp (chống xung đột)

Chỉ **chủ sở hữu** được sửa tệp. Cần thay đổi ở tệp của luồng khác: ghi mục "Yêu cầu gửi G#" trong `status/G<số của mình>.md`, luồng chủ đọc và làm.

| Tệp / thư mục | Chủ |
|---|---|
| `tool/src/socnhotv/core/providers/*_provider.py` **mới** (pollinations, cloudflare, hf, local_*, …) | G1 |
| `tool/src/socnhotv/core/providers/factories.py` (**mới**) | G1 |
| `tool/src/socnhotv/core/providers/key_vault.py` | G1 |
| `tool/src/socnhotv/core/models_registry/models.yaml`, `registry.py` | G1 |
| `scripts/local_ai/**` (**mới**: cài/chạy model trên máy) | G1 |
| `ai/knowledge/free_ai_sources.md` (**mới**) | G1 |
| `tool/src/socnhotv/core/providers/router.py` | G2 |
| `tool/src/socnhotv/core/contracts/types.py` | G2 |
| `tool/src/socnhotv/core/api/app.py` | G2 |
| `tool/src/socnhotv/core/engine/run_manager.py` | G2 |
| `graph_runner.py`, **chỉ vùng chạy/kế hoạch**: `_effective_model_for_node`, `estimate_*`, `plan_execution`, `_save/_load_outputs_snapshot`, `_run_capabilities`, `_voice_line_cache_*`, `_synthesize_line`, `_is_real_provider`, `run` | G2 |
| Frontend: `store/**`, `components/canvas/StudioCanvas.tsx`, `components/canvas/NodeInputs.tsx`, `components/studio/tabs/NodeTab.tsx`, `ChatTab.tsx`, `CreateVideoModal.tsx`, `components/ui/StatusIsland.tsx`, `components/studio/ModelPicker.tsx` (mới), `lib/api/models.ts` (mới), `lib/core-contracts.ts`, `app/[locale]/settings/**`, `messages/vi.json`, `messages/en.json`, `messages/modules/nodes.*.json` | G2 |
| `graph_runner.py`, **chỉ vùng node**: `_render_dialogue` và các nhánh `elif node_type == "video_gen" / "hyperframes_render" / "export"` trong `_execute_node_handler` (mỗi nhánh chỉ thêm vài dòng gọi sang module mới) | G3 |
| `tool/src/socnhotv/core/engine/shot_video.py` (**mới**), `tool/src/socnhotv/video/**`, `core/adapters/hyperframes_adapter.py`, `core/adapters/audio_mastering.py`, `core/nodes/registry.py` | G3 |
| `core/engine/episode_script.py`, `script_parser.py`, `character_profile.py`, `core/api/data_routes.py` | G4 |
| Frontend: `components/studio/PreviewPane.tsx`, `components/studio/tabs/JobsCostTab.tsx`, `components/canvas/RunStatusBar.tsx`, `components/canvas/NodeBody.tsx`, `lib/graph-presets.ts`, `lib/preview.ts`, `messages/modules/video.*.json` | G4 |
| `tool/tests/conftest.py` | G4 |
| Test: `tool/tests/test_g1_*.py`, `test_g2_*.py`, `test_g3_*.py`, `test_g4_*.py` | luồng có số tương ứng |
| `tool/src/socnhotv/core/engine/character_consistency.py` (**mới**), `characters/<id>/consistency.json`, `components/characters/**`, `app/[locale]/characters/**`, `scripts/characters/**`, `tool/tests/test_g5_*.py`, `status/G5.md` | G5 |
| `status/G1.md` … `status/G4.md` | luồng có số tương ứng |
| `ai/map/TOOLS.md`, `ai/memory/CONTINUITY.md`, báo cáo cuối `status/G.md` | G4 (cuối cùng, gom từ các luồng) |

`graph_runner.py` có 2 chủ, chia theo vùng hàm. Ai sửa thì commit nhỏ, chạy `git pull --rebase` ngay trước khi commit, **không định dạng lại (reformat) cả tệp**.

---

## 4. Hợp đồng chung (chốt sẵn để làm song song)

**C1. Nhà máy provider** (G1 viết, G2 dùng): `core/providers/factories.py`
```python
PROVIDER_FACTORIES: dict[str, Callable[[ProjectStore, SpendGuard, Optional[str], str], BaseProvider]]
# tham số: (store, guard, key_or_None, source)
PROVIDER_META: dict[str, dict]  # {"label", "tier": "free|freemium|paid|local", "needs_key": bool, "key_name": "POLLINATIONS_TOKEN"|None, "quota_note": str}
```
`router.get_provider(pname)` (G2) tra `PROVIDER_FACTORIES` trước nhánh cũ. Provider mới **kế thừa `BaseProvider`**, cài `generate_images(...)` và/hoặc `generate_video(...)` **đúng chữ ký** trong `core/providers/base.py`, trả về `Artifact` lưu qua `store.store_bytes(...)`, ghi `provenance.provider/model/cost_usd` đúng sự thật.

**C2. Trường mới trong `models.yaml`** (G1 thêm, G2 hiển thị):
`tier` (free|freemium|paid|local), `supports_reference` (bool), `max_references` (int), `quota_note` (str), `speed_note` (str), `durations_sec` (video). `GET /models` trả về thêm `available` (đã có key hoặc không cần key) do G2 tính.

**C3. Chế độ chạy** (G2 làm, mọi luồng dựa vào): body chạy graph nhận
```json
{"runPolicy": {"image": "mock|real", "video": "off|mock|real", "text": "mock|real", "voice": "local|mock"}, "confirmPaidRun": false}
```
- Thiếu `runPolicy` thì suy từ `mockMode` cũ: `mockMode: true` → tất cả mock, **trừ** `voice: "local"`. Test cũ vẫn đặt được `voice: "mock"` để chạy nhanh.
- Nguồn `tier: free|local` có giá 0 nên **không** bắt `confirmPaidRun`.

**C4. Tham số `video_gen` lặp theo shot** (G3 làm backend, G2 làm UI):
`perShot: bool`, `maxClips: int` (mặc định 5), `shotIds: string[]` (rỗng = để máy chọn theo `priority`), `clipSource: "ai" | "manual" | "auto"` (auto = có clip làm tay thì dùng, không có thì sinh AI, AI không được thì giữ ảnh), `model: string`.
Khi lặp, cổng ra `scenes` giữ nguyên các trường cũ và thêm `video` (đường dẫn clip) cho shot nào có clip.

**C5. Clip làm tay** (G3 đọc, G4 xuất gói): `data/projects/<id>/content/episodes/<episodeId>/clips/<shotId>.mp4` (ví dụ `S07.mp4`). Có tệp này thì bộ dựng dùng clip, không có thì dùng ảnh.

**C6. Tên tệp xuất** (G3): `export.outputFileName` để trống thì tự đặt `<episodeId>.mp4` và ghi vào `output/<episodeId>/`.

---

## 5. Định nghĩa Done (áp dụng cho mọi mốc, bắt buộc kèm bằng chứng)

Video của một tập **chỉ được báo "xong"** khi qua đủ các kiểm tra sau (G4 viết `scripts/video/verify_episode.py` để chạy tự động):

1. `ffprobe`: 1920×1080, h264 + aac, thời lượng 600 ± 15 giây.
2. `volumedetect`: `mean_volume > -30 dB` (không im lặng). Loudness -14 LUFS ± 1.
3. Ảnh keyframe: **≥ 30 hash khác nhau** mỗi tập, `provenance.provider != "mock"`.
4. Giọng: mỗi câu thoại có provenance OmniVoice, đúng `voiceId` của nhân vật (đối chiếu `studio_characters.json`).
5. Tệp `runs/_node_outputs/<graph>/n_keyframes.json` có `"mock": false`.
6. Contact sheet 12 khung (`output/<episodeId>/contact_sheet.jpg`). **Người dùng xem bằng mắt** và xác nhận nhân vật đúng DNA, tỉ lệ đúng (Bi 100 cm, Koala 150 cm, theo `SCALE_LOCK.md`).
7. Phát và **tua** được trong Studio (nút Play ở node Xuất hoặc PreviewPane). Request video trả về `206 Partial Content`. Có ảnh chụp `data/projects/soc-nho-tv/shots/G_*.png`.
8. Mức B, thêm: số shot có clip thật ≥ 5 mỗi tập, liệt kê `shotId → nguồn clip`.

Báo cáo chỉ ghi những gì đã đo được. Bước nào chưa làm được thì ghi rõ **"CHƯA"** kèm lý do.

---

## 6. Luật chung cho mọi AI

- **Git:** làm trên `main`. Chỉ commit tệp mình sở hữu, **luôn kèm đường dẫn**: `git commit -m "..." -- <tệp1> <tệp2>`. Không bao giờ `git add -A` / `git add .`. **Không commit `data/`** (hiện có 844 tệp data/ nằm sẵn trong staging, đừng commit chúng). Chạy `git pull --rebase` trước khi push.
- **Không tạo hàng loạt tài khoản để cày credit miễn phí, không vượt CAPTCHA, không xoay vòng key để lách hạn mức.** Mỗi dịch vụ dùng tài khoản thật của người dùng, đúng điều khoản. Nếu cần người dùng đăng nhập, tạo key hay giải CAPTCHA: giữ trình duyệt mở, hướng dẫn rõ từng bước, rồi chờ người dùng làm.
- **Key:** chỉ lưu trong `.env` ở gốc repo hoặc qua KeyVault. Không in key ra log hay chat, không commit.
- **Tiền:** mọi nguồn có phí đều đi qua `SpendGuard` (trần `SOCNHOTV_SPEND_CAP_USD=5`). Không thêm đường nào tự gọi model trả phí khi đang có lỗi.
- **Test:** không ghi vào `data/projects/soc-nho-tv/` thật. Dùng `tmp_path` (G4 sửa `conftest.py`).
- **Trung thực:** báo cáo `status/G#.md` ghi lệnh đã chạy, kết quả đo được và cả những gì chưa làm. Không ghi "100%" nếu chưa qua mục 5.
- Tuân thủ `ai/AGENTS.md` (HyperFrames, voice `soc-nho`, Morphicons, không dùng `lucide-react`, đọc skill `video-craft` trước khi sửa phần dựng).
