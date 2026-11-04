# Technique: Foreground Occlusion & 3-Layer Spatial Depth Partitioning

## Tóm Tắt Kỹ Thuật
Kỹ thuật chỉ đạo khuôn hình điện ảnh (Cinematic Framing Direction) ứng dụng trong câu lệnh Prompt AI (Flux, Midjourney, Kling, Runway) bằng cách phân tách không gian thành 3 tầng độc lập: Tiền cảnh che khuất mờ nhoè (Foreground Occlusion), Trung cảnh bắt nét căng (In-focus Midground), và Hậu cảnh mờ khí quyển (Atmospheric Background), xoá bỏ hoàn toàn cảm giác "phẳng và giả tạo" (Flat AI effect).

---

## 1. Cấu Trúc Phân Tách 3 Tầng Không Gian

```mermaid
flowchart LR
    subgraph Layer 1: Foreground (0m - 0.5m)
        F["Vật cản sát ống kính (Lá cây, ngọn cỏ, cánh hoa, bờ vai) - OUT OF FOCUS BOKEH"]
    end
    subgraph Layer 2: Midground (1.5m - 5m)
        M["Chủ thể chính thực hiện hành động - SHARP FOCUS, HIGH DETAIL"]
    end
    subgraph Layer 3: Background (> 10m)
        B["Bối cảnh xa (Đồi núi, đô thị, bầu trời) - ATMOSPHERIC HAZE"]
    end
    F --> M --> B
```

---

## 2. Thư Viện Archetypes Tiền Cảnh

| Bối cảnh | Tiền cảnh gợi ý (Prompt keyword) | Hiệu ứng tâm lý |
|---|---|---|
| **Rừng núi / Thiên nhiên** | `low-angle shot with blurred wild grass brushing against camera lens` | Chân thực, người xem như đang chạy theo nhân vật |
| **Phố thị / Sự kiện** | `over-the-shoulder view through blurred silhouette of pedestrians with umbrellas` | Cảm giác đông đúc, tấp nập, quan sát khách quan |
| **Phòng đọc / Nội tâm** | `peeking through a narrow slit between blurred antique books on a wooden shelf` | Cảm giác tò mò, khám phá bí mật (Voyeuristic / Mystery) |
| **Phòng thử đồ / Fashion** | `blurred garment rack and velvet hanger framing the model in background mirror` | Sang trọng, bối cảnh studio chuyên nghiệp |

---

## 3. Template Prompt Chuẩn Cho Sóc Nhỏ TV
```text
Cinematic 3-layer shot of [CHARACTER_ACTION], 
[FOREGROUND_OBJECT] blurred in extreme foreground creating shallow depth of field (f/1.8), 
sharp crisp focus on [CHARACTER_NAME] in midground with vivid emotional expression, 
soft warm atmospheric lighting in distant background [ENVIRONMENT_SETTING], 
35mm film grain, anamorphic lens flare.
```
