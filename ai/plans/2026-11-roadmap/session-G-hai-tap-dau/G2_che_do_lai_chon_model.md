# G2: Chế độ chạy lai + chọn model/nguồn trong Studio

> Thuộc Session G. Đọc trước: `status/THUC_TRANG_2026-11-06.md` (N2, N3), `README.md` (mục 3, 4, 6).
> Báo cáo tiến độ: `status/G2.md`.

## Vấn đề
- **N2:** `mockMode` là công tắc chung. Bật Mock thì giọng OmniVoice (chạy trên máy, miễn phí, đang chạy tốt) bị thay bằng WAV im lặng (`router.speak_voice`). Tắt Mock thì node ảnh `mock-image` bị chuyển sang google, thiếu key nên lỗi. Không có chế độ "ảnh tạm + giọng thật".
- **N3:** UI không dùng `/models`, `/providers`. `NodeTab.tsx` viết cứng dropdown. Card `image_gen` không có chỗ chọn model. Không hiện nguồn nào có key, miễn phí hay trả phí, giá, có nhận ảnh tham chiếu không.

## Tệp sở hữu
`core/providers/router.py`, `core/contracts/types.py`, `core/api/app.py`, `core/engine/run_manager.py`. Trong `graph_runner.py` **chỉ vùng chạy/kế hoạch** (`_effective_model_for_node`, `estimate_*`, `plan_execution`, `_save/_load_outputs_snapshot`, `_run_capabilities`, `_voice_line_cache_*`, `_synthesize_line`, `_is_real_provider`, `run`).
Frontend: `store/**`, `components/canvas/StudioCanvas.tsx`, `components/canvas/NodeInputs.tsx`, `components/studio/tabs/NodeTab.tsx`, `ChatTab.tsx`, `CreateVideoModal.tsx`, `components/ui/StatusIsland.tsx`, `components/studio/ModelPicker.tsx` (mới), `lib/api/models.ts` (mới), `lib/core-contracts.ts`, `app/[locale]/settings/**`, `messages/vi.json`, `messages/en.json`, `messages/modules/nodes.*.json`. Test `tool/tests/test_g2_*.py`.

## Bước làm

### Pha 1: backend (làm trước, mốc M1 cần phần này)
1. **`runPolicy`** theo hợp đồng **C3** (README mục 4):
   - `contracts/types.py`: thêm `RunPolicy` vào `GraphRunRequest`, giữ `mock_mode` để tương thích ngược. Không có `runPolicy` thì suy từ `mockMode`: tất cả mock, **trừ `voice: "local"`**.
   - `router.py`: nhận `run_policy`. `_pick()` theo loại (image, video, text). `speak_voice` dùng `VoiceAdapter` (OmniVoice) **trừ khi** `voice == "mock"`.
   - `graph_runner.py` (đúng vùng của mình): các chỗ dùng `req.mock_mode` (`plan_execution`, ước tính giá, snapshot `is_mock`, cache giọng `_voice_line_cache_*`, `_synthesize_line`, `_run_capabilities`) đổi sang hỏi theo loại node. Ví dụ `self._is_mock_for(node_or_kind, req)`. Snapshot và cache phải khoá theo **kiểu chạy thật của riêng node đó**. Như vậy giọng thật đã sinh ở chế độ lai thì lần chạy sau dùng lại được, không bị coi là mock.
   - `app.py`: các endpoint chạy graph và `plan` nhận `runPolicy`. Nguồn `tier: free|local` có giá 0 nên không bắt `confirmPaidRun`.
2. **Nhà máy provider:** `router.get_provider(pname)` tra `socnhotv.core.providers.factories.PROVIDER_FACTORIES` (của G1, hợp đồng C1) **trước** các nhánh google/fal/replicate. Chưa có tệp thì `try/except ImportError` để không vỡ.
3. **Chuỗi dự phòng:** provider ném `ProviderErrorKind.QUOTA` hoặc `AUTH` thì router thử model kế tiếp trong `node.params.fallbackModels` (danh sách), **chỉ** trong các model `tier` free hoặc local. Không bao giờ tự rơi sang nguồn trả phí.
4. **`GET /models`** trả thêm `available` (đã có key hợp lệ hoặc không cần key) và các trường C2 (`tier`, `supports_reference`, `quota_note`, …). **`GET /providers`** trả thêm `tier`, `needs_key`.
5. Test `test_g2_run_policy.py`:
   - (a) Chế độ lai: image mock + voice local. Kiểm hàm giọng thật được gọi (dùng fake VoiceAdapter, không chạy OmniVoice thật trong test).
   - (b) `mockMode: true` cũ vẫn ra đúng hành vi cũ.
   - (c) Nguồn free hết hạn mức thì chuyển sang dự phòng free, không chuyển sang paid.
   - (d) Snapshot/cache không trộn mock với thật.

### Pha 2: frontend
6. **Menu chế độ chạy** thay nút Mock/Live ở `StudioCanvas.tsx` và `StatusIsland.tsx`: 3 lựa chọn đặt sẵn và 1 tuỳ chỉnh.
   - **Thử nhanh** (mọi thứ mock).
   - **Animatic** (ảnh thật free/local, video tắt, giọng thật).
   - **Đầy đủ** (ảnh + video thật).
   - Tuỳ chỉnh từng loại.
   - Mặc định của dự án `soc-nho-tv`: **Animatic**. Store đổi `isMockMode` thành `runPolicy`. Các chỗ đọc `isMockMode` (ChatTab, CreateVideoModal, NodeTab ước tính giá) đọc qua selector suy ra.
7. **`ModelPicker.tsx`** dùng chung (một component cho mọi chỗ):
   - Lấy dữ liệu từ `GET /models`, lọc theo `kind` (image, video, text).
   - Mỗi dòng hiện: tên, nguồn, nhãn **Miễn phí / Trên máy / Trả phí $x**, biểu tượng "nhận ảnh tham chiếu", trạng thái key (Sẵn sàng / Thiếu key → link sang Cài đặt), ghi chú hạn mức.
   - Model chưa `available` thì làm mờ nhưng vẫn bấm được, bấm vào thì mở Cài đặt.
   - Có ô "Dự phòng khi hết hạn mức" (chọn nhiều) ghi vào `params.fallbackModels`.
   - Icon dùng `@/components/ui/icons` (Morphicons), **không dùng `lucide-react`**.
8. Gắn `ModelPicker` vào **card** `image_gen`, `image_edit`, `video_gen` (`NodeInputs.tsx`) và tab Node (`NodeTab.tsx`). Xoá dropdown viết cứng.
9. Card `video_gen`: điều khiển cho tham số **C4** (`perShot`, `maxClips`, `shotIds`, `clipSource`). Hiển thị trước "sẽ tạo N clip × giá = $…" từ `plan`.
10. **Cài đặt** (`app/[locale]/settings`): ô nhập key cho các nguồn mới mà G1 đưa vào `key_vault.PROVIDER_SPECS`. Có nút "Kiểm tra key" gọi endpoint kiểm (không tốn phí), báo hợp lệ hay không. Key cũ đang hỏng phải hiện "**Không hợp lệ**", không được hiện "Đã cấu hình".
11. i18n vi/en cho mọi chữ mới. Chạy `npm run check:style` (nếu có) và `NEXT_DIST_DIR=.next-build npx next build` (**không** build vào `.next` khi dev server cổng 3000 đang chạy).

## Done khi
- Chạy flow Tập 1 với chế độ **Animatic**, ảnh để `mock-image`, thì ra MP4 **có tiếng** (G4 kiểm ở mốc M1).
- Trên card `image_gen` chọn được model free của G1, thấy nhãn Miễn phí và trạng thái key. Chạy dùng đúng model đó (provenance khớp).
- `pytest tool/tests/test_g2_*` pass, các test cũ không vỡ, `next build` sạch.
- Có ảnh chụp `shots/G2_model_picker_*.png` (sáng + tối) và `shots/G2_run_mode_menu.png`.
