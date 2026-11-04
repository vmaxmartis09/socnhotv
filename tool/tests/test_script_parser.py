import pytest
from socnhotv.core.engine.script_parser import parse_script


def test_parse_script_empty():
    assert parse_script("") == []
    assert parse_script("   \n\t  ") == []


def test_parse_script_with_scene_headers():
    raw = """
Cảnh 1: Khám phá nhà cây
(Sóc Bi vẫy tay chào)
Camera: Dolly zoom vào nụ cười của Bi
Sóc Nhỏ: Chào các bạn nhỏ, mình là Sóc Nhỏ Bi đây!

Cảnh 2: Kệ kẹo ngọt ngào
Sóc Nhỏ: Oa, bao nhiêu là kẹo mút ngon lành!
(Bi với tay lấy chiếc kẹo dâu)

Cảnh 3: Bài học đánh răng
Bác sĩ Koala: Bi ơi, ăn kẹo xong phải nhớ chải răng nhé!
Sóc Nhỏ: Vâng ạ, Bi sẽ chải răng thật sạch!
"""
    scenes = parse_script(raw)
    assert len(scenes) == 3
    assert scenes[0]["sceneNumber"] == 1
    assert "Khám phá nhà cây" in scenes[0]["title"]
    assert "Sóc Nhỏ Bi đây" in scenes[0]["dialogue"]
    assert "Sóc Bi vẫy tay" in scenes[0]["imagePrompt"]
    assert "Dolly zoom" in scenes[0]["videoPrompt"]

    assert scenes[1]["sceneNumber"] == 2
    assert "kẹo mút" in scenes[1]["dialogue"].lower()

    assert scenes[2]["sceneNumber"] == 3
    assert "Bác sĩ Koala" in scenes[2]["dialogue"]
    assert "Sóc Nhỏ" in scenes[2]["dialogue"]


def test_parse_script_with_horizontal_dividers():
    raw = """
Sóc Bi tỉnh dậy sau giấc ngủ dài, vươn vai đón ánh nắng sớm.
Sóc Nhỏ: Buổi sáng ở rừng thông thật là đẹp!
---
Bi chạy ra bờ suối rửa mặt cùng các bạn thú.
Bi: Nước suối mát lạnh quá các bạn ơi!
---
Cả nhóm ngồi quây quần cùng nhau ăn bữa sáng vui vẻ.
Koala: Bữa sáng ngon tuyệt vời!
"""
    scenes = parse_script(raw)
    assert len(scenes) == 3
    assert scenes[0]["sceneNumber"] == 1
    assert "Buổi sáng ở rừng thông" in scenes[0]["dialogue"]
    assert scenes[1]["sceneNumber"] == 2
    assert "Nước suối mát lạnh" in scenes[1]["dialogue"]
    assert scenes[2]["sceneNumber"] == 3
    assert "Bữa sáng ngon" in scenes[2]["dialogue"]


def test_parse_script_with_blank_lines():
    raw = """
(Sóc Bi cầm trái thông trên tay)
Sóc Nhỏ: Đố các bạn biết trái thông này dành cho ai?

Bi đưa trái thông cho bạn Sóc Nâu.
Sóc Nâu: Cảm ơn bạn Bi tốt bụng nhé!
"""
    scenes = parse_script(raw)
    assert len(scenes) == 2
    assert "trái thông" in scenes[0]["dialogue"]
    assert "Sóc Nâu" in scenes[1]["dialogue"]


def test_parse_script_single_long_paragraph():
    raw = (
        "Hôm nay trời nắng đẹp trong khu rừng diệu kỳ. Sóc Nhỏ Bi thức dậy sớm và chuẩn bị đi hái nấm. "
        "Trên đường đi, Bi gặp bạn Thỏ Trắng đang buồn bã vì bị lạc đường. Bi liền vui vẻ dắt tay bạn Thỏ "
        "về tận hang của mẹ Thỏ. Mẹ Thỏ cảm ơn Bi và tặng cho Bi một giỏ táo chín đỏ mọng."
    )
    scenes = parse_script(raw, target_scene_count=4)
    assert len(scenes) >= 3
    for s in scenes:
        assert s["sceneNumber"] >= 1
        assert s["imagePrompt"]
        assert s["durationSec"] > 0


def test_parse_script_vietnamese_characters_and_actions():
    raw = """
Phân cảnh 1: Sóc Nhỏ chuẩn bị đi học
(Bi mang balo màu vàng rực rỡ, đuôi xù vẫy nhẹ)
Hình ảnh: Khu rừng thông xanh mát với ánh nắng ban mai rọi qua tán lá
Bi: Mẹ ơi, con đi học đây ạ!
Mẹ Sóc: Đi học ngoan nhé con yêu!
"""
    scenes = parse_script(raw)
    assert len(scenes) == 1
    sc = scenes[0]
    assert "Sóc Nhỏ chuẩn bị đi học" in sc["title"]
    assert "balo màu vàng" in sc["imagePrompt"]
    assert "Khu rừng thông xanh mát" in sc["imagePrompt"]
    assert "Bi: Mẹ ơi, con đi học đây ạ!" in sc["dialogue"]
    assert "Mẹ Sóc: Đi học ngoan nhé con yêu!" in sc["dialogue"]
    assert sc["durationSec"] >= 3.0
