# BẢN ĐỒ DỮ LIỆU & CHÍNH SÁCH GIT (DATA DIRECTORY & GIT POLICY)

> **Cập nhật:** Session H7 (2026-11-06)  
> **Mục tiêu:** Chuẩn hoá kiến trúc thư mục dữ liệu `data/`, phân định tuyệt đối ranh giới dữ liệu được phép đưa lên Git và dữ liệu bảo mật / tạm thời bắt buộc bỏ qua (.gitignore), đồng thời thiết lập quy chuẩn vệ sinh dữ liệu.

---

## 1. Tổng Quan Cấu Trúc 3 Tầng của `data/`

Toàn bộ dữ liệu của dự án tuân thủ nguyên tắc **Zero Root Pollution**:

```
data/
├── workspace.json                 # Cấu hình danh sách dự án & dự án mặc định (soc-nho-tv)
├── shared/                        # Tài nguyên dùng chung giữa các dự án
│   ├── knowledge/                 # Tri thức video thực chiến (26 techniques, 7 playbooks, registry)
│   ├── templates/                 # Composition HyperFrames, styles, animation blueprints
│   ├── brand_kits/                # Bộ nhận diện thương hiệu, palette màu, typography
│   ├── models/                    # Cấu hình mô hình AI (loại trừ binary nặng)
│   ├── music_sfx/                 # Nhạc nền BGM, sound effects dùng chung
│   └── voice_vault/               # Kho mẫu giọng clone OmniVoice (TÀI SẢN RIÊNG TƯ)
└── projects/<project-id>/         # Dữ liệu độc lập của từng dự án (soc-nho-tv, anti-gate, ...)
    ├── project.json, graph.json   # Cấu hình dự án & graph xử lý video Studio
    ├── characters/                # Nhân vật Master DNA, Scale lock, prompts
    ├── content/                   # Kịch bản 51 tập, prompts chi tiết, phân cảnh
    ├── publishing/                # Lịch phát hành, template bài đăng, demo gói social
    ├── analytics/                 # Dữ liệu phân tích hiệu suất và học máy
    ├── products/                  # Thông tin sản phẩm affiliate / KOC
    ├── accounts/                  # Cấu hình tài khoản mạng xã hội (bảo mật)
    ├── assets/                    # Assets sinh tự động theo mã băm (TTS mp3, srt, meta.json)
    ├── raw/                       # Tư liệu thô, video capture, rác tạm (_trash/)
    ├── shots/                     # Ảnh chụp màn hình và kiểm tra DOM
    ├── output/                    # Video thành phẩm render (MP4 9:16 / 16:9)
    └── runs/                      # Lịch sử thực thi graph, node cache, hàng đợi render
```

---

## 2. Chính Sách Lưu Trữ Trên Git (Git Data Policy)

Vì repository `vmaxmartis09/socnhotv` đang ở chế độ **PUBLIC**, chính sách Git được thắt chặt tối đa để bảo vệ tài sản sở hữu trí tuệ, thông tin nhạy cảm và ngăn ngừa phình dung lượng repo:

### 2.1. Nhóm LƯU TRÊN GIT (Tracked by Git)
Những dữ liệu mang tính định nghĩa, thiết kế gốc và tri thức hệ thống:

| Thành phần | Đường dẫn | Ý nghĩa & Mục đích |
|---|---|---|
| **Cấu hình dự án** | `data/workspace.json`, `data/projects/*/project.json`, `graph.json`, `policy.json` | Cấu trúc studio, node flow, metadata dự án |
| **Nhân vật Master DNA** | `data/projects/*/characters/**` | Ảnh gốc nhận diện nhân vật (Sóc Nhỏ 100cm, Koala 150cm), scale lock, prompt DNA |
| **Kịch bản & Nội dung** | `data/projects/*/content/**` | Kịch bản 51 tập chuẩn, danh sách shot, video prompt |
| **Tri thức Video Craft** | `data/shared/knowledge/**` | 26 thẻ kỹ thuật video thực chiến, 7 playbooks, registry.json, STATUS.md |
| **Templates đồ hoạ** | `data/shared/templates/**` | Blueprint composition HyperFrames chuẩn |
| **Brand Kits** | `data/shared/brand_kits/**` | Token thiết kế, bảng màu, hướng dẫn thương hiệu |
| **Dữ liệu mẫu / Demo** | `data/projects/*/analytics/_demo/**`, `publishing/_demo/**`, `schedule.json` | Dữ liệu mẫu giúp dev chạy kiểm thử giao diện Studio |
| **Sổ chi tiêu ngân sách** | `data/projects/*/runs/spend.json`, `runs/.gitkeep` | Ghi nhận chi tiêu thực tế qua SpendGuard |

### 2.2. Nhóm BỎ QUA TRÊN GIT (Ignored in `.gitignore`)
Tuyệt đối không đưa lên Git repo công khai:

| Thành phần | Quy tắc `.gitignore` | Lý do loại trừ |
|---|---|---|
| **Kho giọng clone** | `data/shared/voice_vault/*` | **TÀI SẢN RIÊNG TƯ / BẢN QUYỀN:** Chứa file audio mẫu giọng người thật, prompt cache `.pt`, `.npy`. Khi repo công khai, việc đưa giọng clone lên tiềm ẩn rủi ro pháp lý và đạo đức AI sâu sắc. |
| **Assets sinh tự động** | `data/projects/*/assets/*` | Hàng ngàn file MP3 giọng đọc TTS, file phụ đề `.srt`, `.meta.json` sinh theo mã băm SHA256 (có thể tái tạo bất kỳ lúc nào từ flow). |
| **Tư liệu thô** | `data/projects/*/raw/*` | Video tải về, clip thô chưa cắt, thư mục rác `_trash/`. |
| **Lịch sử chạy flow** | `data/projects/*/runs/*` | Hàng trăm thư mục `run_*`, cache kết quả từng node, log runtime (trừ `.gitkeep` và `spend.json`). |
| **Video thành phẩm** | `data/projects/*/output/*` | Các file video MP4 render nặng từ vài chục đến hàng trăm MB. Lưu cục bộ hoặc CDN/Cloud Storage. |
| **Ảnh chụp kiểm tra** | `data/projects/*/shots/*` | Ảnh chụp màn hình debug bot, kiểm thử selector. |
| **Tài khoản & Khóa** | `data/projects/*/accounts/*` | Token truy cập mạng xã hội, cookies, credentials nhạy cảm. |
| **Binary công cụ** | `data/shared/models/ffmpeg-bin/` | File thực thi nhị phân nặng >25MB. |
| **Lock & Thumbnail phụ** | `data/projects/*/publishing/.store.lock`, `.thumbs/`, `.video_cache.json` | Runtime locks và cache hiển thị cục bộ. |

---

## 3. Quy Chuẩn Vệ Sinh Dữ Liệu Runs Định Kỳ

- **Công cụ thực thi:** `scripts/maintenance/clean_runs.py`
- **Nguyên tắc an toàn:**
  1. **Mặc định Dry-run:** Luôn chạy `--dry-run` trước để kiểm kê số lượng thư mục, dung lượng và danh mục đề xuất dọn.
  2. **Ưu tiên Trash thay vì Delete:** Khi thực thi thật, ưu tiên cờ `--trash` để chuyển vào Thùng rác hệ thống (có thể phục hồi khi cần) thay vì `--delete` vĩnh viễn.
  3. **Bảo vệ bất biến:** Không bao giờ xoá `.gitkeep`, `spend.json`, các hàng đợi hệ thống (`events/`, `render_queue/`, `_node_outputs/`, `_voice_lines/`) hoặc các run diễn ra trong vòng 2 giờ gần nhất (có thể cấu hình qua `--keep-recent-hours`).
