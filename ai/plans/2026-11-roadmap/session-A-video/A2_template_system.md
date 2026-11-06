# A2 — Hệ thống Template video + 8 template khởi đầu

Bạn là Session A. Đọc: `CONTRACTS.md`, `status/A.md` (kết quả A1), `ai/skills/hyperframes-creative/SKILL.md`, `ai/skills/hyperframes-animation/SKILL.md`, `ai/skills/hyperframes-registry/SKILL.md`, `ai/skills/embedded-captions/SKILL.md`, `data/shared/brand_kits/`, master DNA nhân vật `data/projects/soc-nho-tv/characters/`.

## Mục tiêu
Template = 1 thư mục tự mô tả. Người dùng/agent chỉ đổ dữ liệu vào slot → ra video đúng mọi nền tảng.

## 1. Schema `data/shared/templates/<template_id>/`
```
template.json        # meta + slots + scenes
composition.html.j2  # Jinja2 → HTML HyperFrames (GSAP paused timeline)
styles.css
preview.jpg / preview.mp4 (tự sinh)
sample.data.json     # dữ liệu mẫu render được ngay
```
`template.json`:
```json
{ "id":"tiktok-sales-v1", "name":"Bán hàng TikTok – Hook 3s", "version":1,
  "category":"sales|review|reup|animation|education|affiliate|story",
  "platforms":["tiktok","reels","shorts","douyin","facebook"], "default_platform":"tiktok",
  "duration": {"mode":"auto_from_voice","min":15,"max":60},
  "slots":[ {"key":"hook_text","type":"text","max_chars":40,"required":true},
            {"key":"product","type":"product","required":true},
            {"key":"clips","type":"media[]","min":1,"max":8},
            {"key":"price","type":"text"}, {"key":"cta","type":"text","default":"Bấm giỏ hàng ngay"} ],
  "voice": {"required":true, "default_voice_id":"soc-nho"},
  "captions": {"style":"anchor","position":"lower_third_safe"},
  "bgm": {"mood":"upbeat","duck_db":-12},
  "scenes":[ {"role":"hook","dur":"3s"}, {"role":"problem"}, {"role":"demo"}, {"role":"proof"}, {"role":"cta","dur":"3s"} ],
  "responsive": {"youtube":"blur-pad","facebook":"cover"} }
```
## 2. Code `tool/src/socnhotv/video/templates/`
- `schema.py` (pydantic `TemplateMeta`, `Slot`, validate data theo slot: thiếu/thừa/quá ký tự → lỗi rõ ràng tiếng Việt).
- `loader.py` (đọc/duyệt/cache, `list_templates()` thay stub trong contracts — giữ chữ ký).
- `compose.py`: data + platform → HTML: render Jinja2 với biến `platform` (w,h,safe_zone) để layout tự co theo tỉ lệ; timing scene tính từ độ dài voice (dùng `voice_adapter` đọc duration) hoặc `dur`; captions word-level từ `caption_adapter`; BGM ducking theo `hyperframes-audio`.
- `preview.py`: render `sample.data.json` ở 540p → `preview.mp4` + `preview.jpg`.
- Nối vào queue A1: `RenderRequest.template_id` → `compose` → `HyperFramesEngine`.

## 3. Tám template khởi đầu (mỗi cái phải render được bằng sample data)
| id | dùng cho | điểm nhấn |
|---|---|---|
| `tiktok-sales-v1` | Video bán hàng TikTok Shop | hook 3s, giá gạch ngang, badge giảm %, CTA giỏ hàng trong safe-zone |
| `koc-review-v1` | KOC nhân vật review sản phẩm | khung nhân vật (Sóc Nhỏ/KOC AI) + B-roll sản phẩm, lower-third ưu/nhược, chấm sao |
| `affiliate-compare-v1` | So sánh 2–3 sản phẩm affiliate | split screen, bảng tiêu chí animate, "Lựa chọn của mình" |
| `unboxing-v1` | Mở hộp | đếm ngược, zoom chi tiết (hyperframes-keyframes punch-in) |
| `localized-reup-v1` | Bản địa hoá video nguồn (có quyền) | khung brand của mình bao quanh clip, phụ đề VI, logo, nhân vật bình luận góc |
| `yt-animation-episode-v1` | Tập hoạt hình YT 16:9 | intro logo, title card, scene list nhân vật Bi/Koala (khoá tỉ lệ 100/150cm), outro end-screen 20s |
| `shorts-fact-v1` | Shorts/TikTok giáo dục "Bạn có biết" | kinetic typography, số liệu count-up |
| `story-cartoon-v1` | Truyện kể thiếu nhi dọc | trang truyện lật, nhân vật nói, karaoke caption |
Mỗi template có ít nhất 2 nền tảng dọc + `youtube` hoặc `facebook` (trừ khi vô nghĩa). Dùng brand kit trong `data/shared/brand_kits/` cho màu/font. Ưu tiên khối registry HyperFrames có sẵn trước khi tự vẽ (skill `hyperframes-registry`).

## 4. API (thêm vào `core/api/routes/video.py`)
`GET /video/templates?category=&platform=`, `GET /video/templates/{tid}` (meta + slots), `POST /video/templates/{tid}/validate` (body data), `POST /video/templates/{tid}/preview` (render nhanh 540p), `GET /video/templates/{tid}/preview.mp4`.

## 5. Node plugin `core/nodes/plugins/video.py`
Đăng ký `template_render` (input: text/script, image[], video[], audio; params: template_id, platforms, slot mapping; output: video per platform) và `platform_export` (1 video → nhiều tỉ lệ bằng fit strategy). Dùng `NodeDefinition`/`PortDefinition` như `registry.py`.

## Nghiệm thu
- `test_video_templates.py`: validate cả 8 template; render sample 2s mỗi template (cho phép mock CLI trong CI, nhưng chạy thật ít nhất 3 template trên máy).
- 8 thư mục template có `preview.jpg` thật.
- Node mới xuất hiện ở `GET /node-types`.
- Commit `feat(A2): template system + 8 starter templates`. Cập nhật `status/A.md` (bảng template + trạng thái preview).
