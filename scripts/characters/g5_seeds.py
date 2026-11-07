"""Dữ liệu gieo (seed) cho consistency.json của 5 nhân vật Tập 1–2.

Phần ĐO được (chiều cao, bảng màu HEX, tên, giọng) KHÔNG nằm ở đây: build_consistency.py đọc thẳng từ
SCALE_LOCK.md, <id>_profile.json và studio_characters.json để không lệch nguồn thật.

Ở đây chỉ có phần cần con mắt người/AI nhìn ảnh:
- refs: đề xuất ảnh tham chiếu theo vai trò (AI xem contact sheet rồi đề xuất, NGƯỜI DÙNG duyệt mới khoá).
- features / forbidden / defaultOutfit: đặc điểm không đổi và điều cấm, suy từ ảnh + profile.md + trường do/dont
  trong script.json của Tập 1–2 (không thêm đặc điểm mới cho nhân vật).
- gaps: vai trò mà bộ ảnh hiện có KHÔNG có (ghi thật, không bịa ảnh).

Mọi tên tệp tính từ characters/<id>/.
"""
from __future__ import annotations

from typing import Any, Dict

SEEDS: Dict[str, Dict[str, Any]] = {
    # ------------------------------------------------------------------ Sóc Nhỏ (Bi)
    "soc_nho": {
        "promptName": "Bi",
        "aliases": ["Sóc Bi", "Bi", "Sóc Nhỏ"],
        "speciesEn": "3D Pixar-style red squirrel boy",
        "headBodyRatioEn": "1:4, slim, flat tummy",
        "features": [
            {"vi": "đuôi bông xù lớn cong chữ S, cao bằng lưng", "en": "big fluffy S-curved bushy tail as tall as his back"},
            {"vi": "tai dựng, chóp lông nhỏ", "en": "upright tufted squirrel ears"},
            {"vi": "má, cằm, bụng màu kem; hai răng cửa trắng nhỏ khi cười", "en": "soft cream cheeks and chest, two small white front teeth when smiling"},
            {"vi": "mắt đen to tròn có đốm sáng trắng", "en": "large glossy black eyes with white highlights"},
            {"vi": "thân thon, bụng phẳng", "en": "slim agile build, flat tummy"},
        ],
        "defaultOutfit": {
            "vi": "áo thun cổ tròn vàng nắng, quần short đen than, giày sneaker tối màu đế trắng",
            "en": "bright sunny yellow crew-neck t-shirt, charcoal black shorts, dark sneakers with white rubber soles",
        },
        "forbidden": [
            {"vi": "bụng phệ, béo tròn", "en": "chubby belly, fat round body, potbelly"},
            {"vi": "lùn tịt như thú nhồi bông biến dạng", "en": "stubby plush-toy proportions, oversized head"},
            {"vi": "đuôi quá ngắn hoặc mảnh", "en": "short thin tail, tail missing"},
            {"vi": "đổi trang phục mặc định khi kịch bản không yêu cầu", "en": "different outfit, different t-shirt color"},
            {"vi": "lông lạc tông (xám, vàng nhạt, nâu sẫm)", "en": "grey fur, pale yellow fur, dark brown fur"},
        ],
        "refs": {
            "front": ("soc_nho_11.png", "đứng chính diện, tay chống hông, nền đơn giản"),
            "three_quarter": ("soc_nho_02.png", "3/4, một tay chống hông, một tay vẫy"),
            "profile": ("soc_nho_10.png", "thân nghiêng ngang (dáng đi), thấy rõ đuôi và áo"),
            "back": ("soc_nho_04.png", "quay lưng/3/4 sau, thấy đuôi to"),
            "full_body": ("soc_nho_01.png", "toàn thân, vẫy tay, nền đơn giản"),
            "closeup": ("soc_nho_05.png", "cận mặt, cười, thấy rõ mắt/răng/má"),
            "action": ("soc_nho_07.png", "chạy ngang, dùng cho shot chuyển động"),
            "expressions": {
                "happy": ("soc_nho_14.png", "cười tươi, giơ ngón cái"),
                "surprised": ("soc_nho_06.png", "ngạc nhiên, hai tay áp má"),
                "sad": ("soc_nho_15.png", "lo lắng/ngại, tay đưa lên miệng; gần nhất với buồn hoặc sợ"),
            },
        },
        "gaps": [
            {"role": "expression:angry", "reason": "bộ ảnh hiện có không có ảnh giận; shot giận dùng closeup + prompt biểu cảm"},
        ],
    },
    # ------------------------------------------------------------------ Dê Mun
    "de_mun": {
        "promptName": "De Mun",
        "aliases": ["Dê Mun", "Mun"],
        "speciesEn": "3D Pixar-style toddler black goat",
        "headBodyRatioEn": "1:3.6, toddler",
        "features": [
            {"vi": "đốm sao trắng nhỏ giữa trán", "en": "small white star marking on center of forehead"},
            {"vi": "hai mầm sừng tròn tí hon màu kem", "en": "two tiny rounded cream horn buds"},
            {"vi": "tai cụp mềm, má phúng phính", "en": "soft drooping ears, chubby cheeks"},
            {"vi": "mắt nâu sẫm to tròn", "en": "huge sparkling dark brown eyes"},
        ],
        "defaultOutfit": {
            "vi": "áo thun đỏ in sao vàng lớn, quần short xanh navy, ủng cao su đỏ viền vàng",
            "en": "bright red crew-neck t-shirt with big yellow star, dark navy shorts, little red rubber boots with yellow trim",
        },
        "forbidden": [
            {"vi": "sừng dài nhọn như dê lớn", "en": "long pointed horns, large adult goat horns"},
            {"vi": "mất đốm sao trắng trên trán", "en": "no forehead star, forehead mark missing"},
            {"vi": "cao bằng Bi hoặc Mimi", "en": "tall child, same height as the others"},
            {"vi": "áo không có sao vàng, màu áo khác đỏ", "en": "shirt without yellow star, non-red shirt"},
            {"vi": "lông xám hoặc nâu thay vì đen tuyền", "en": "grey fur, brown fur"},
        ],
        "refs": {
            "front": ("de_mun_02.png", "đứng chính diện, nền trắng"),
            "three_quarter": ("de_mun_03.png", "hơi xoay 3/4"),
            "back": ("de_mun_04.png", "quay lưng, thấy áo đỏ và ủng"),
            "full_body": ("de_mun_01.png", "toàn thân, vẫy tay"),
            "closeup": ("de_mun_05.png", "cận mặt, cười, thấy rõ sao trắng và sừng"),
            "action": ("de_mun_07.png", "chạy lon ton (3/4)"),
            "expressions": {
                "happy": ("de_mun_05.png", "cười tươi (cùng ảnh closeup)"),
                "surprised": ("de_mun_06.png", "ngạc nhiên, miệng chữ O, hai tay giơ"),
            },
        },
        "gaps": [
            {"role": "profile", "reason": "chưa có ảnh nghiêng 90 độ; shot góc ngang dùng three_quarter làm dự phòng"},
            {"role": "expression:sad", "reason": "chưa có ảnh buồn/khóc (Tập 2 có 2 shot Mun buồn); dùng closeup + prompt biểu cảm"},
        ],
    },
    # ------------------------------------------------------------------ Mẹ Sóc
    "me_soc": {
        "promptName": "Me Soc",
        "aliases": ["Mẹ Sóc"],
        "speciesEn": "3D Pixar-style adult mother red squirrel",
        "headBodyRatioEn": "1:5.2, slender maternal build",
        "features": [
            {"vi": "đuôi sóc bông xù lớn cong mềm", "en": "large graceful bushy tail"},
            {"vi": "tai dựng có chóp lông", "en": "tufted upright squirrel ears"},
            {"vi": "tạp dề kem thêu hạt dẻ ở túi trước", "en": "cream apron with embroidered chestnut on the front pocket"},
            {"vi": "má và cổ kem, mắt nâu hạt dẻ hiền, mi cong", "en": "cream cheeks and throat, kind chestnut-brown eyes with soft lashes"},
        ],
        "defaultOutfit": {
            "vi": "váy dài lanh xanh xô thơm, tạp dề kem thêu hạt dẻ, giày bệt nâu đất",
            "en": "long sage-green linen dress, cream apron with chestnut embroidery, earth-brown flat shoes",
        },
        "forbidden": [
            {"vi": "thiếu tạp dề hoặc thiếu hạt dẻ thêu", "en": "no apron, apron without chestnut embroidery"},
            {"vi": "váy khác màu xanh xô thơm", "en": "red dress, blue dress, non-sage-green dress"},
            {"vi": "cao ngang hoặc thấp hơn Bi, dáng như trẻ con", "en": "child proportions, same height as a child"},
            {"vi": "đuôi quá ngắn", "en": "short thin tail"},
            {"vi": "lông cam sáng như Bi (Mẹ là nâu đỏ quế)", "en": "bright orange fur like a child squirrel"},
        ],
        "refs": {
            "front": ("me_soc_02.png", "đứng chính diện, hai tay đan trước tạp dề"),
            "three_quarter": ("me_soc_03.png", "3/4, đuôi bên trái"),
            "back": ("me_soc_04.png", "quay lưng, thấy đuôi và nơ tạp dề"),
            "full_body": ("me_soc_01.png", "toàn thân, vẫy tay"),
            "closeup": ("me_soc_05.png", "cận mặt, cười nhẹ"),
        },
        "gaps": [
            {"role": "profile", "reason": "chưa có ảnh nghiêng 90 độ; dùng three_quarter làm dự phòng"},
            {"role": "expressions", "reason": "bộ ảnh chỉ có nụ cười hiền; chưa có buồn/ngạc nhiên/giận"},
        ],
    },
    # ------------------------------------------------------------------ Dê Bông
    "de_bong": {
        "promptName": "De Bong",
        "aliases": ["Dê Bông", "Bông"],
        "speciesEn": "3D Pixar-style 6-year-old white goat boy",
        "headBodyRatioEn": "1:4.2",
        "features": [
            {"vi": "lông trắng xoăn bông như mây ở đầu, má và tay", "en": "fluffy curly cloud-white wool"},
            {"vi": "hai sừng ngắn bo tròn màu kem bơ", "en": "two short rounded buttercream horns"},
            {"vi": "lòng tai hồng phấn", "en": "soft blush-pink inner ears"},
            {"vi": "sổ tay bìa xanh lá cài ở túi ngực yếm", "en": "small green notebook in the overalls chest pocket"},
        ],
        "defaultOutfit": {
            "vi": "áo thun sọc ngang trắng-navy, yếm jean xanh da trời có 2 cúc gỗ, sandal da nâu",
            "en": "navy-and-white striped t-shirt, sky-blue denim overalls with two wooden buttons, brown leather sandals",
        },
        "forbidden": [
            {"vi": "thiếu hai sừng ngắn màu kem", "en": "no horns, long curved horns"},
            {"vi": "lông thẳng thay vì xoăn bông", "en": "straight smooth hair, grey fur"},
            {"vi": "thấp bằng hoặc thấp hơn Bi và Lu", "en": "short child, same height as the other kids"},
            {"vi": "yếm khác màu jean xanh nhạt", "en": "dark denim, black overalls, different outfit"},
            {"vi": "thiếu sổ tay xanh lá", "en": "no green notebook"},
        ],
        "refs": {
            "front": ("de_bong_02.png", "đứng gần chính diện, tay buông"),
            "three_quarter": ("de_bong_01.png", "3/4, vẫy tay"),
            "back": ("de_bong_03.png", "quay lưng, thấy yếm và sandal"),
            "full_body": ("de_bong_01.png", "toàn thân (cùng ảnh 3/4)"),
            "closeup": ("de_bong_04.png", "cận mặt, cười, thấy rõ sừng và len xoăn"),
            "action": ("de_bong_07.png", "chạy (3/4)"),
            "expressions": {
                "surprised": ("de_bong_06.png", "ngạc nhiên, miệng chữ O, hai tay buông"),
            },
        },
        "gaps": [
            {"role": "profile", "reason": "chưa có ảnh nghiêng 90 độ; dùng three_quarter làm dự phòng"},
            {"role": "expression:sad", "reason": "chưa có ảnh buồn; dùng closeup + prompt biểu cảm"},
            {"role": "note", "reason": "script.json Tập 2 nhắc 'chùm râu cằm nhỏ màu trắng' nhưng ảnh DNA không thấy rõ; chưa khoá vào đặc điểm"},
        ],
    },
    # ------------------------------------------------------------------ Ông Dê Râu Bạc
    "ong_de_rau_bac": {
        "promptName": "Ong De Rau Bac",
        "aliases": ["Ông Dê Râu Bạc", "Ông Dê", "Ông Nội"],
        "speciesEn": "3D Pixar-style elderly wise grandfather mountain goat",
        "headBodyRatioEn": "1:5.2, slightly stooped",
        "features": [
            {"vi": "chòm râu bạc dài mềm", "en": "long neat silver beard"},
            {"vi": "đôi sừng cong màu hổ phách", "en": "curved amber-tan horns"},
            {"vi": "kính lão tròn gọng đồi mồi nâu", "en": "tortoise-shell round reading glasses"},
            {"vi": "khăn rằn caro vắt vai, gậy tre vàng đầu cong", "en": "checkered scarf over shoulder, bamboo walking cane"},
        ],
        "defaultOutfit": {
            "vi": "áo bà ba nâu đất cài cúc gỗ, quần đũi kem ngà, dép",
            "en": "earth-brown Vietnamese ba ba tunic with wooden buttons, cream linen trousers, sandals",
        },
        "forbidden": [
            {"vi": "thiếu chòm râu bạc dài", "en": "no beard, short beard, black beard"},
            {"vi": "thiếu kính tròn", "en": "no glasses, square glasses"},
            {"vi": "sừng thẳng hoặc ngắn như Bông/Mun", "en": "short straight horns, tiny horn buds"},
            {"vi": "dáng trẻ trung, thẳng lưng như người lớn trẻ", "en": "young adult, muscular, upright youthful posture"},
            {"vi": "trông khó tính hoặc cổ hủ", "en": "grumpy angry old man"},
        ],
        "refs": {
            "front": ("ong_de_rau_bac_03.png", "đứng chính diện, chống gậy"),
            "three_quarter": ("ong_de_rau_bac_02.png", "hơi xoay 3/4, chống gậy"),
            "back": ("ong_de_rau_bac_04.png", "quay lưng, thấy khăn rằn và gậy"),
            "full_body": ("ong_de_rau_bac_01.png", "toàn thân, vẫy tay"),
            "closeup": ("ong_de_rau_bac_05.png", "cận mặt, cười, thấy râu, kính, sừng"),
        },
        "gaps": [
            {"role": "profile", "reason": "chưa có ảnh nghiêng 90 độ; dùng three_quarter làm dự phòng"},
            {"role": "expressions", "reason": "bộ ảnh chỉ có nụ cười hiền; chưa có buồn/ngạc nhiên"},
        ],
    },
}

# nhãn tiếng Anh cho từng phần trong bảng màu (khoá lấy từ <id>_profile.json -> colors)
PART_EN: Dict[str, str] = {
    "primary_fur": "fur",
    "secondary_fur": "cream fur",
    "forehead_mark": "forehead star",
    "horns": "horns",
    "eyes": "eyes",
    "nose": "nose",
    "shirt": "shirt",
    "pants": "pants",
    "shoes": "shoes",
    "boots": "boots",
    "dress": "dress",
    "apron": "apron",
    "overalls": "overalls",
    "accessory": "notebook",
    "beard_horns": "beard and horns",
    "glasses": "glasses",
    "scarf_pants": "scarf and trousers",
    "prop": "cane",
}

# Giữ ảnh bảng DNA ra khỏi danh sách ảnh tham chiếu: nó là ảnh có chữ, đưa vào model sinh ảnh sẽ in chữ lên hình.
EXCLUDED_FROM_REFS = ("_dna_sheet.png",)

DEFAULT_IDS = ["soc_nho", "de_mun", "me_soc", "de_bong", "ong_de_rau_bac"]
