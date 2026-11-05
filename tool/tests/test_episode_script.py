from socnhotv.core.engine.episode_script import parse_episode_markdown, resolve_facet, script_to_scenes

MD = """# Kịch Bản Tập 07: Thử nghiệm

- **Series**: Bi và Những Người Bạn
- **Thời lượng chuẩn**: `10 phút 00 giây`
- **Tỉ lệ khung hình & Phong cách**: `16:9 Widescreen` | `3D Pixar`
- **Dàn nhân vật xuất hiện trong tập**: **Sóc Bi (100cm), Dê Mun (85cm)**
- **Câu thần chú**: *"Xòe tay hít sâu!"*

---

## 4. Kịch Bản Phân Cảnh Chi Tiết

### 🎬 Cảnh 1 (00:00 - 01:00): Mở đầu
- **Vị trí bối cảnh cụ thể**: Nhà cây

#### 🔹 Shot `S01` (`00:00 - 00:20` | Thời lượng: `20s` | Cỡ cảnh: `WS` | Góc máy: `eye-level`, `28mm`)
- **Nhân vật xuất hiện trong khung hình**: Sóc Bi (100cm)
- **Lời thoại (`Sóc Bi (100cm)`)**: **"Chào các bạn!"**
- **Prompt Tạo Ảnh & Tạo Video (AI Production Prompts)**:
```text
Image Prompt: a squirrel
Video Prompt: waves hand
Negative Prompt: blur
```
"""


def test_parse_and_facets():
    d = parse_episode_markdown(MD, "ep07")
    assert d["episodeNumber"] == 7 and d["title"] == "Thử nghiệm"
    assert d["durationSec"] == 600 and d["aspect"] == "16:9 Widescreen"
    assert [c["name"] for c in d["cast"]] == ["Sóc Bi", "Dê Mun"]
    sh = d["scenes"][0]["shots"][0]
    assert sh["id"] == "S01" and sh["dialogue"] == "Chào các bạn!"
    assert sh["imagePrompt"] == "a squirrel" and sh["negativePrompt"] == "blur"
    assert resolve_facet(d, "dialogue", "S01") == "Chào các bạn!"
    assert resolve_facet(d, "mantra") == "Xòe tay hít sâu!"
    assert script_to_scenes(d)[0]["imagePrompt"] == "a squirrel"
