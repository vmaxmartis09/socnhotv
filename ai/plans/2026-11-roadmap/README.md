# ROADMAP 2026-11 — Từ "Studio node" thành "Nhà máy video đa nền tảng"

> Folder này dành cho Antigravity. Mỗi file là 1 prompt độc lập. Chạy đúng thứ tự dưới đây.
> Ngày khảo sát: 2026-11-04 · Nhánh: `main` @ 16463e2

---

## 1. Thực trạng thật (nhìn thẳng)

| Mảng | Có gì thật trong code | % |
|---|---|---|
| Core engine (graph runner, validator, providers fal/google/replicate/mock, spend guard, key vault) | `tool/src/socnhotv/core/**` ~8.2k dòng, có test step1→5 | **70%** |
| Studio canvas UI (node, nối dây, auto layout, panels) | `tool/dashboard/components/canvas/**`, StudioCanvas 1.5k dòng | **75%** |
| Nhân vật + Voice clone (OmniVoice, mastering -14 LUFS) | `characters/`, `voice_adapter.py`, `audio_mastering.py`, VoiceCloneModal | **70%** |
| Render HyperFrames | Chỉ có `core/adapters/hyperframes_adapter.py` (sinh 1 kiểu HTML + fallback FFmpeg). **`tool/src/socnhotv/video/` TRỐNG**, `hyperframes_engine.py` mà CLAUDE.md nhắc **không tồn tại**, CLI `hyperframes` chưa cài | **35%** |
| Hệ thống Template video | `data/shared/templates/` chỉ có `services/`. Không có schema, không có gallery | **5%** |
| Xuất đa nền tảng (TikTok/Reels/Shorts/YT 16:9/FB/Douyin, safe-zone) | Chỉ cứng 9:16 | **10%** |
| Reup / bản địa hoá Douyin | Không có downloader (`yt-dlp` chưa cài), không pipeline | **0%** |
| Video bán hàng TikTok / KOC review | Có skill `motion-mimic`, thư mục `products/` rỗng, không pipeline | **10%** |
| YT hoạt hình dài tập | Có Episode/ScriptComposer, chưa có pipeline scene→render 16:9 + cắt Shorts | **15%** |
| Học / sao chép cấu trúc kênh YT | `tool/src/socnhotv/intelligence/` **TRỐNG** | **0%** |
| Sao chép cấu trúc video affiliate | Không có | **0%** |
| Lịch đăng / Quản lý social | `PublishTab.tsx` (form 1 nền tảng, giờ "Hàng ngày · 19:00" dạng chuỗi), frontend gọi `POST /publishing/schedule` **không tồn tại** ở backend, `accounts/` rỗng, `social/` **TRỐNG**, không adapter đăng, không scheduler | **15%** |
| Analytics / tự học | `analytics/` rỗng, CONTINUITY 16 dòng | **5%** |
| Workspace module (`tool/src/socnhotv/workspace/`) mà CLAUDE.md bắt buộc | **TRỐNG** (đang dùng `ProjectStore`) | **20%** |

**Tổng thể so với mục tiêu "nhà máy video đa nền tảng": ≈ 28%.**
Nền móng (engine + canvas + nhân vật + voice) tốt. Phần tạo ra giá trị (template, nguồn nội dung, đa nền tảng, đăng bài) gần như chưa có.

Nợ kỹ thuật cần biết:
- `studio/` ở gốc repo là bản sao cũ của `tool/dashboard/` → KHÔNG sửa `studio/`.
- `src/gobi/` ở gốc là code legacy → không sửa, chỉ tham khảo.
- `lucide-react` vẫn nằm trong `package.json` dù luật cấm dùng → không import.

---

## 2. Thứ tự chạy

```
00_BOOTSTRAP.md            ← chạy 1 LẦN, 1 session, xong mới tách (≈15–20 phút)
        │
        ├── Session A: A1 → A2 → A3 → A4   (Video engine · Template · Đa nền tảng · YT hoạt hình)
        ├── Session B: B1 → B2 → B3 → B4   (Nguồn nội dung · Douyin · KOC/Affiliate · Học kênh YT)
        └── Session C: C1 → C2 → C3 → C4   (Social Manager · Lịch đăng · Adapter đăng · Analytics)
        │
99_FINAL_INTEGRATION.md     ← chạy khi cả 3 session xong
```

Cách dán vào Antigravity cho mỗi bước:
> Đọc và thực hiện đầy đủ file `ai/plans/2026-11-roadmap/<file>.md`. Trước khi làm, đọc `ai/plans/2026-11-roadmap/CONTRACTS.md`.

Ba session chạy song song **trên cùng checkout** được vì:
1. Mỗi session chỉ sửa file trong vùng sở hữu của mình (bảng ở `CONTRACTS.md`).
2. Các điểm "đụng nhau" (đăng ký router, node, menu, i18n, deps) đã được 00_BOOTSTRAP biến thành cơ chế plugin tự nạp → không session nào phải sửa file chung.
3. Giao tiếp giữa session qua **hợp đồng** (`contracts.py` + file JSON hàng đợi), không gọi code nội bộ của nhau.
4. Commit theo đường dẫn: `git add <vùng của mình>` rồi `git commit`, không `git add -A`.

---

## 3. Kết quả khi xong cả 12 prompt
- 8+ template HyperFrames, render 1 nội dung ra 6 nền tảng (đúng tỉ lệ + safe-zone).
- Dán link Douyin/TikTok/YT → tải, tách lời, dịch, viết lại, lồng giọng mới, dựng lại bằng template của mình.
- Phân tích video affiliate/KOC mẫu → "blueprint" (hook, nhịp, CTA) → kịch bản mới cho sản phẩm của mình → render.
- Phân tích kênh YT → blueprint kênh + gợi ý lịch nội dung.
- Social Manager: tài khoản đa nền tảng, lịch tháng/tuần kéo-thả, hàng chờ duyệt, đăng qua API chính chủ hoặc xuất "gói đăng tay", scheduler, analytics quay về tự học.
