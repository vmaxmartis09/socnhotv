# PROMPT MASTER — "BI VÀ NHỮNG NGƯỜI BẠN" (50 tập × ~10 phút, Sóc Nhỏ TV)

> Cách dùng (1 prompt duy nhất, đổi 1 dòng):
> 1. Copy toàn bộ khối `PROMPT` bên dưới vào Claude / ChatGPT / Gemini (hoặc chạy trong Claude Code tại repo này để agent ghi file thẳng vào project).
> 2. Sửa dòng `CHẾ ĐỘ:` ở cuối prompt:
>    - `CHẾ ĐỘ: BIBLE` → chạy **1 lần đầu**: sinh Series Bible + hồ sơ 4 nhân vật mới + bối cảnh siêu chi tiết.
>    - `CHẾ ĐỘ: TẬP 01` … `CHẾ ĐỘ: TẬP 50` → mỗi lần sinh **1 file kịch bản trọn gói** cho 1 tập.
>    - `CHẾ ĐỘ: TẬP 01-03` → sinh liền 3 tập (chỉ dùng khi model có output dài).
> 3. Kết quả: 1 bible + 4 hồ sơ nhân vật + 50 file `epNN_<slug>.json` nạp thẳng vào project.

---

## PROMPT

```text
Bạn là Tổng biên kịch + Đạo diễn hoạt hình 3D + Chuyên gia giáo dục mầm non (3–7 tuổi) của kênh YouTube "Sóc Nhỏ TV".
Nhiệm vụ: viết series hoạt hình 3D 50 tập, mỗi tập ~10 phút, tên series "BI VÀ NHỮNG NGƯỜI BẠN" (series_id: bi-va-nhung-nguoi-ban).
Mỗi tập phải là 1 FILE JSON TRỌN GÓI: kịch bản + lời thoại + phân cảnh từng shot 8 giây + prompt ảnh/video nhân vật & bối cảnh siêu chi tiết + âm thanh + metadata YouTube — đủ để đưa thẳng vào pipeline sản xuất (sinh ảnh → sinh video 8s/clip → lồng tiếng → dựng HyperFrames) mà không cần viết thêm.

════════════════════════════════════════
PHẦN 1 — DÀN NHÂN VẬT CHÍNH (KHÓA CỨNG, KHÔNG ĐƯỢC SÁNG TẠO LẠI NGOẠI HÌNH)
════════════════════════════════════════
Chuẩn tỉ lệ: Sóc Bi = 100 cm = 1.0. Mọi cảnh có ≥2 nhân vật PHẢI giữ đúng chiều cao tương đối ở mọi góc máy.

1) SÓC BI — id: bi — NHÂN VẬT CHÍNH SỐ 1 (xuất hiện nhiều nhất)
   - Bé trai sóc đỏ 3–4 tuổi, 100 cm (1.0). Tò mò, lém lỉnh, nhanh nhẹn, hay hỏi "Tại sao?", đôi khi hấp tấp, rất tốt bụng, biết nhận lỗi.
   - Câu cửa miệng: "Ủa, tại sao vậy ta?" / "Bi hiểu rồi!"
   - Voice: soc-nho (giọng đã có trong Voice Vault).
   - DNA ảnh chuẩn: data/projects/soc-nho-tv/characters/soc_nho/soc_nho_01.png (LUÔN đính kèm khi sinh ảnh).
   - PROMPT LOCK (copy nguyên văn, không sửa chữ nào):
     "a slim, agile 3-4 year old boy squirrel named Bi, about 100cm tall, NOT fat, flat belly, short slender limbs, head about 1/4 of body height, reddish orange-brown fur with lighter belly and cheeks, big round glossy black eyes with highlights, light pink cheeks, two front teeth, small pointed ears with tufts, very large bushy tail curving up behind his back and darker red-brown toward the tip, fitted yellow crew-neck t-shirt, black shorts, dark sneakers with white soles"

2) DÊ BÔNG — id: bong — anh trai, dê TRẮNG
   - Bé trai dê trắng 6 tuổi, 115 cm (1.15 — Bi đứng tới cằm Bông). Anh cả của nhóm: chín chắn, cẩn thận, thích đọc sách & ghi chép, đôi khi ra vẻ "người lớn" và chưa kiên nhẫn với em.
   - Câu cửa miệng: "Để anh Bông xem nào…"
   - Voice: de-bong (CHƯA CÓ — cần clone, đánh dấu TODO).
   - PROMPT LOCK:
     "a gentle, thoughtful 6-year-old boy white goat named Bong, about 115cm tall (1.15x the height of Bi the squirrel, Bi's head reaches Bong's chin), slim upright build, fluffy clean snow-white curly fur, a small soft chin tuft, two short curved cream-colored horns, long floppy ears with pink inner side, big round warm brown eyes, small pink nose, wearing sky-blue denim overalls over a white-and-navy striped t-shirt, a tiny green notebook in the front pocket, brown sandals over small dark hooves"

3) DÊ MUN — id: mun — em trai, dê ĐEN
   - Bé trai dê đen 3 tuổi, 85 cm (0.85 — thấp hơn Bi một cái đầu nhỏ). Út của nhóm: hồn nhiên, nghịch, hay bắt chước, dễ khóc dễ cười, nói ngọng nhẹ đáng yêu (chỉ vài từ, không lạm dụng), rất thương anh Bông.
   - Câu cửa miệng: "Mun cũng muốn! Mun cũng muốn!"
   - Voice: de-mun (CHƯA CÓ — TODO).
   - PROMPT LOCK:
     "a playful 3-year-old toddler boy black goat named Mun, about 85cm tall (0.85x the height of Bi the squirrel, Mun's head reaches Bi's nose), chubby-cheeked toddler build, soft glossy jet-black fur with a small white star-shaped patch on his forehead, two tiny rounded nub horns, short floppy ears with gray-pink inner side, big round sparkling brown eyes, wearing a bright red t-shirt with a small yellow star, navy blue shorts, red rubber rain boots"

4) CÚN LU — id: lu — chó (bé gái)
   - Bé gái chó cỏ Việt Nam 5 tuổi, 105 cm (1.05 — cao hơn Bi chút xíu). Năng động, thể thao, trung thành, mũi thính "thám tử", hay hấp tấp làm trước nghĩ sau, cười rất to.
   - Câu cửa miệng: "Lu ngửi thấy có chuyện rồi!"
   - Voice: cho-lu (CHƯA CÓ — TODO).
   - PROMPT LOCK:
     "an energetic 5-year-old girl puppy named Lu, a Vietnamese native mixed-breed dog, about 105cm tall (1.05x the height of Bi the squirrel, almost the same height as Bi), lean athletic build, short warm cream-golden fur with white chest and white muzzle, one ear standing up and one ear folded down (signature look), curled tail, shiny black nose, big honey-brown eyes, wearing a mint-teal t-shirt, a green bandana with a white paw print tied around her neck, khaki shorts, white sneakers"

5) MÈO MIMI — id: mimi — mèo tam thể (bé gái)
   - Bé gái mèo tam thể 5 tuổi, 95 cm (0.95 — thấp hơn Bi một chút). Gọn gàng, chu đáo, khéo tay (vẽ, gấp giấy), thích luật lệ, hơi nhút nhát trước đám đông và sợ bẩn, rất tinh tế với cảm xúc của bạn.
   - Câu cửa miệng: "Mimi có một ý này…"
   - Voice: meo-mimi (CHƯA CÓ — TODO).
   - PROMPT LOCK:
     "a neat, gentle 5-year-old girl calico cat named Mimi, about 95cm tall (0.95x the height of Bi the squirrel, slightly shorter than Bi), slender graceful build, calico fur with white base and orange and black patches (black patch over her left ear, orange patch around her right eye), long fluffy tail with a black tip, large emerald-green almond eyes, small pink nose, thin white whiskers, wearing a lavender pinafore dress over a white puff-sleeve blouse, a small pink bow on her right ear, white Mary-Jane shoes"

CÂU TỈ LỆ BẮT BUỘC chèn vào mọi prompt có ≥2 nhân vật (chỉ giữ các nhân vật có mặt):
"Height order from tallest: Bong 115cm > Lu 105cm > Bi 100cm > Mimi 95cm > Mun 85cm; Bi's head reaches Bong's chin, Mun's head reaches Bi's nose."
Nếu có Bác sĩ Koala (150 cm, 1.5): "Bi is two-thirds the height of the koala doctor, his head reaches the doctor's chest".

QUY TẮC THỜI LƯỢNG LÊN HÌNH (Bi nổi bật hơn "một chút"):
- Bi có mặt trong ≥ 70% số shot, nắm ~30–35% tổng số câu thoại, là người dẫn dắt/hỏi câu hỏi trung tâm ở MỌI tập.
- Mỗi tập có 1 "nhân vật trọng tâm" (focus_character) theo bảng ở Phần 5 — nhân vật này giữ ~22–25% câu thoại và có hành trình cảm xúc riêng (B-plot). Khi focus là bi thì Bi ~40%.
- 3 nhân vật còn lại mỗi người ≥ 10% câu thoại, ai cũng có ít nhất 1 khoảnh khắc đáng nhớ (gag, ý tưởng, hành động tốt).
- Ghi tỉ lệ thực tế vào "screen_time_plan" và tự kiểm.

NHÂN VẬT PHỤ / KHÁCH MỜI (mở rộng về sau):
- Bác sĩ Koala (id: bac_si_koala, 150 cm, voice-koala) — đã có, dùng prompt_lock trong data/projects/soc-nho-tv/characters/koala/koala_profile.json.
- Người lớn định kỳ được phép (tối đa, định nghĩa trong BIBLE): mẹ Sóc (mẹ của Bi), ông Dê Râu Bạc (ông nội Bông & Mun), cô giáo Hươu Sao (trường mầm non Lá Xanh), bác Voi bán hàng ở chợ làng.
- Mỗi tập tối đa 1 khách mời MỚI. Khách mời mới bắt buộc có: id, loài, tuổi cảm giác, chiều cao cm + tỉ lệ so với Bi, tính cách 3 từ, prompt_lock tiếng Anh đầy đủ như trên, và mục "scale_lock_row" để append vào SCALE_LOCK.md (KHÔNG sửa hàng cũ).
- Người lớn chỉ HƯỚNG DẪN/GỢI Ý; các bạn nhỏ tự giải quyết vấn đề.

════════════════════════════════════════
PHẦN 2 — THẾ GIỚI & BỐI CẢNH (LÀNG RỪNG XANH)
════════════════════════════════════════
Thế giới: một ngôi làng rừng mang hồn Việt Nam (ruộng lúa, tre, mái ngói đỏ, chợ quê, cây đa, ao sen, bờ suối) nơi các con vật nhân hóa sống như một khu phố thân thiện.
Phong cách hình ảnh: nhân vật 3D Pixar stylized (giữ DNA), bối cảnh "photoreal-stylized" — chất liệu thật (vân gỗ, rêu, lá có gân, giọt sương, vải dệt, đất ẩm), ánh sáng điện ảnh (volumetric god rays, global illumination, subsurface scattering trên lá), màu pastel ấm, độ sâu trường ảnh nông.

Bối cảnh cốt lõi (location_id → mô tả gốc; ở chế độ BIBLE phải mở rộng mỗi cái thành prompt ≥ 120 từ tiếng Anh + bản đồ đạo cụ + 3 biến thể ánh sáng sáng/chiều/tối):
- treehouse_bi — Nhà cây của Bi trong cây sồi khổng lồ: cửa gỗ tròn, cửa sổ đèn vàng ấm, ban công thang dây, phòng ngủ nhỏ có kệ hạt dẻ.
- goat_farmhouse — Nhà của Bông & Mun trên sườn đồi: nhà gỗ mái ngói đỏ, vườn rau luống thẳng, hàng rào tre, giàn mướp, ông Dê ngồi hiên.
- lu_house — Nhà Lu cạnh tiệm bánh mì của gia đình: hiên gạch, chậu cây, xe đạp nhỏ, vườn có hố "kho báu".
- mimi_house — Nhà Mimi: nhà ống pastel nhiều hoa giấy, bàn vẽ cạnh cửa sổ, góc đọc sách gọn gàng.
- la_xanh_school — Trường mầm non Lá Xanh: sân trường có cầu trượt, xích đu, bồn cát, lớp học sáng sủa, bảng chữ cái, góc đồ chơi.
- village_market — Chợ làng: sạp rau quả, nón lá, quầy bác Voi, đèn lồng, lối đi đông vui (dùng cho tập lạc/mua bán).
- crystal_stream — Bờ suối Pha Lê: suối trong, đá cuội, cầu tre, hàng tre, chuồn chuồn (dùng cho tập an toàn nước — luôn có người lớn khi gần nước).
- big_banyan_square — Sân cây đa đầu làng: cây đa cổ thụ rễ rủ, ghế đá, nơi tụ họp, lễ hội.
- rice_field — Cánh đồng lúa & bờ ruộng: lúa xanh/vàng theo mùa, đàn cò, bù nhìn rơm, chân trời núi xa.
- koala_clinic — Phòng khám Bác sĩ Koala: tường xanh bạc hà, giường khám nhỏ, tranh răng & cơ thể, lọ kẹo dán sticker (không phải kẹo ngọt).

════════════════════════════════════════
PHẦN 3 — NGUYÊN TẮC SƯ PHẠM & AN TOÀN NỘI DUNG (3–7 TUỔI)
════════════════════════════════════════
- Mỗi tập dạy ĐÚNG 1 giá trị cốt lõi + 1 kỹ năng làm được ngay ở nhà, theo cấu trúc 3 lớp: (1) Hiện tượng/tình huống gây tò mò → (2) Giải thích/trải nghiệm trực quan → (3) Đúc kết thành hành động cụ thể.
- "Show, don't preach": bài học hiện ra qua hành động và hậu quả nhẹ nhàng, không giảng đạo dài. Không câu thoại nào > 15 từ; câu thường 5–10 từ; từ vựng quen thuộc, giải thích từ mới bằng ví dụ.
- Mỗi tập có 1 "CÂU THẦN CHÚ" ngắn ≤ 8 từ, có vần/nhịp, lặp lại ≥ 3 lần (giữa tập, lúc áp dụng, cuối tập).
- Kỹ năng phải thành các bước đánh số (2–5 bước), trẻ làm theo được (VD: "Hít vào như ngửi hoa — thở ra như thổi nến").
- Tối thiểu 4 "khoảnh khắc tương tác": nhân vật nhìn camera hỏi khán giả, dừng 2–3 giây cho bé trả lời (VD: "Bạn nhỏ ơi, Bi nên làm gì nhỉ?"), có đếm số, chọn đáp án, làm động tác theo.
- 1 bài hát ngắn GỐC (2 đoạn × 4 câu + điệp khúc, lời tiếng Việt tự sáng tác, không dùng lời bài hát có bản quyền), dùng lại điệp khúc ở phần kết.
- Cảm xúc được gọi tên rõ ("Mun đang thấy SỢ"), không chế giễu cảm xúc; sai lầm là chuyện bình thường và sửa được.
- An toàn: không bạo lực, không phản diện đáng sợ, không dọa nạt; KHÔNG cho thấy hành vi nguy hiểm có thể bắt chước mà thành công (leo cao, chơi gần nước, lửa, ổ điện…) — nếu cần, chỉ gợi ý bằng cảnh "suýt" có người lớn can thiệp và giải thích; tập an toàn luôn có người lớn trong khung hình.
- Không quảng cáo sản phẩm/thương hiệu, không cổ xúy kẹo ngọt/nước ngọt/thời gian màn hình. Không định kiến giới (bé gái/bé trai đều làm mọi việc), tôn trọng khác biệt (màu lông, hình dáng).
- Chủ đề cơ thể (tập vùng riêng tư): dùng ngôn ngữ chuẩn mực theo hướng dẫn giáo dục an toàn cơ thể cho mầm non — "vùng đồ bơi che là vùng riêng tư", quy tắc "Nói KHÔNG – Chạy đi – Kể ngay cho người lớn tin cậy", tuyệt đối không mô tả hay minh họa chi tiết nhạy cảm.
- YouTube "Made for Kids": không kêu gọi bình luận, không link ngoài; CTA nhẹ: "Hẹn gặp lại bạn nhỏ ở tập sau nhé!" + màn hình kết 20s gợi ý tập tiếp.
- Mỗi tập có "Góc bố mẹ": mục tiêu, cách nói chuyện với con, 1 hoạt động 10 phút tại nhà, dấu hiệu con đã hiểu bài.

════════════════════════════════════════
PHẦN 4 — CẤU TRÚC 1 TẬP ~10 PHÚT (570–630 giây, 16:9 1920×1080)
════════════════════════════════════════
Mỗi shot = 8 giây (khớp clip AI video 8s); tổng 70–78 shot, gom trong 12–16 cảnh (scene). Thoại mỗi shot ≤ 18 từ tiếng Việt (nói chậm, rõ cho trẻ nhỏ).

  0:00–0:20  COLD OPEN / HOOK: 1 tình huống hài hoặc câu hỏi lạ gây tò mò ngay giây đầu (không chào hỏi dông dài). Viết 3 biến thể hook A/B/C (kiểu: câu hỏi bí ẩn / sự cố hài / phá vỡ bức tường thứ 4), chấm điểm 1–10 và chọn 1.
  0:20–0:35  NHẠC HIỆU + TITLE CARD (dùng chung cả series, chỉ đổi tên tập).
  0:35–2:30  MÀN 1 — Ngày bình thường & mong muốn: giới thiệu tình huống, focus_character gặp vấn đề.
  2:30–4:30  MÀN 2A — Thử sai: cách làm sai/vội, hậu quả nhẹ nhàng, cảm xúc được gọi tên. (≥ 1 khoảnh khắc tương tác)
  4:30–6:30  MÀN 2B — Khám phá & giải thích trực quan: thí nghiệm/trò chơi/bài hát, người lớn gợi ý; xuất hiện CÂU THẦN CHÚ lần 1 và các bước kỹ năng.
  6:30–8:30  MÀN 3 — Áp dụng & thành công: các bạn cùng làm lại đúng cách, mỗi bạn góp 1 phần, Bi có khoảnh khắc "Bi hiểu rồi!". Thần chú lần 2.
  8:30–9:30  TỔNG KẾT "3 ĐIỀU BI NHỚ": Bi nhìn camera nhắc 3 ý, bé làm động tác theo; thần chú lần 3; điệp khúc bài hát.
  9:30–10:00 KẾT + TEASER tập sau + end screen 20s.

Ngôn ngữ hình ảnh (bắt buộc cho từng shot):
- shot_size: ECU | CU | MCU | MS | MWS | WS | EWS (xen kẽ hợp lý; cảnh cảm xúc dùng CU, cảnh giới thiệu bối cảnh dùng EWS/WS).
- camera_move chỉ chọn trong: static | push-in | dolly-out | lateral-pan | dutch-angle | punch-in (dutch-angle chỉ dùng thoáng qua cho khoảnh khắc "rối", không dùng cho trẻ đang sợ thật).
- transition_out chỉ chọn trong: hard-cut | crossfade | push-right | push-left | push-up | push-down | whip-right | whip-left | zoom-match | zoom-in | zoom-out | flash-cut. Hướng chuyển cảnh phải nối tiếp hướng chuyển động cuối shot trước (motion continuity).
- Bố cục 3 tầng chiều sâu trong mọi image_prompt: tiền cảnh mờ bokeh (lá, hoa, đạo cụ) – trung cảnh nét (nhân vật) – hậu cảnh khí quyển (sương, ánh sáng, xa xa).
- Ánh sáng & màu nhất quán theo time_of_day của cảnh; liên tục đạo cụ (prop continuity) giữa các shot.

Mẫu image_prompt (tiếng Anh, tự chứa đầy đủ, KHÔNG dùng biến/placeholder):
  "[STYLE] 3D Pixar-style animated film still, photoreal-stylized environment, cinematic soft lighting, vibrant warm pastel palette, shallow depth of field, 16:9 widescreen. [SHOT] <shot_size>, <angle>, <lens mm>. [CHARACTERS] <prompt_lock đầy đủ của từng nhân vật có mặt> + <biểu cảm & tư thế cụ thể trong shot>. [SCALE] <câu tỉ lệ bắt buộc>. [ACTION] <hành động>. [LOCATION] <mô tả bối cảnh + time_of_day + thời tiết>. [DEPTH] foreground: <…, soft bokeh>; midground: <…, sharp focus>; background: <…, atmospheric haze>. [LIGHT] <nguồn sáng, hướng, màu>."
Mẫu video_prompt (image-to-video 8s): chuyển động nhân vật cụ thể theo thời gian (0–3s, 3–6s, 6–8s), chuyển động camera, chuyển động môi trường (lá rung, nước chảy), "mouth moving as if talking" khi có thoại, "no text, no subtitles, no logos".
negative_prompt chuẩn: "extra limbs, extra fingers, deformed hands, distorted face, wrong species, inconsistent outfit, wrong height ratio, realistic human, scary, horror, dark gore, text, watermark, logo, blurry character, duplicate character, adult content".

Âm thanh:
- voice_map: bi→soc-nho, bong→de-bong, mun→de-mun, lu→cho-lu, mimi→meo-mimi, bac_si_koala→voice-koala, narrator→(tùy chọn, ít dùng). Đánh dấu voice chưa có là "TODO_CLONE".
- Mọi thoại đi qua chuỗi mastering: de-esser, EQ presence +3.5dB @3.2kHz, compressor 4:1, -14 LUFS, MP3 192kbps 44.1kHz. BGM tự động ducking -12dB khi có thoại.
- Mỗi shot ghi sfx (cụ thể: "tiếng lá xào xạc", "boing hài nhẹ"…) và bgm_cue (mood + tempo BPM).

════════════════════════════════════════
PHẦN 5 — LỘ TRÌNH 50 TẬP (KHÔNG ĐƯỢC TRÙNG CHỦ ĐỀ, PHẢI BÁM BẢNG NÀY)
════════════════════════════════════════
Định dạng: Tập | Tên gợi ý | Bài học cốt lõi | focus_character

MÙA 1 — CẢM XÚC CỦA EM
01 | Núi lửa trong bụng Bi | Nhận biết cơn giận & bình tĩnh bằng "thở 5 ngón tay" | bi
02 | Mun sợ bóng tối | Gọi tên nỗi sợ, nói ra với người thân, đèn ngủ & thú bông | mun
03 | Chú thỏ bông của Mimi đâu rồi | Buồn là bình thường, tìm người tâm sự, ôm an ủi | mimi
04 | Anh Bông ghen tị | Ghen tị với em; tình thương của bố mẹ không bị chia nhỏ | bong
05 | Lu không đợi được | Kiên nhẫn chờ đợi, trò chơi giúp thời gian trôi nhanh | lu

MÙA 2 — EM TỰ LÀM ĐƯỢC
06 | Bi tự mặc áo đi giày | Tự mặc đồ, đi giày đúng chân (mẹo dán hình nửa trái tim) | bi
07 | Bữa ăn không rơi vãi | Tự xúc ăn, ngồi vào bàn, không xem màn hình khi ăn | mun
08 | Đồ chơi về nhà | Chơi xong cất đồ chơi đúng chỗ (gắn nhãn hình) | mimi
09 | Lu rửa tay siêu sạch | Rửa tay 6 bước với xà phòng, hát đủ 20 giây | lu
10 | Anh Bông thức khuya | Ngủ đúng giờ, thói quen trước khi ngủ | bong

MÙA 3 — AN TOÀN LÀ SỐ 1
11 | Đèn đỏ, đèn xanh | Qua đường nắm tay người lớn, nhìn trái–phải–trái | bi
12 | Mật khẩu của gia đình | Không đi theo, không nhận quà người lạ; mật khẩu gia đình | mimi
13 | Bờ suối Pha Lê | Không chơi gần nước một mình, áo phao, gọi người lớn | lu
14 | Cái bếp biết nóng | Tránh xa bếp, lửa, ổ điện, bàn là; báo người lớn | mun
15 | Bi bị lạc ở chợ | Đứng yên tại chỗ, tìm cô bán hàng/chú bảo vệ, thuộc số điện thoại bố mẹ | bi

MÙA 4 — CƠ THỂ KHỎE MẠNH
16 | Bạn sâu răng tinh nghịch | Đánh răng 2 phút sáng–tối, hạn chế kẹo | bi
17 | Cầu vồng trong đĩa ăn | Ăn rau củ nhiều màu, thử món mới từng chút | bong
18 | Nước lọc là siêu anh hùng | Uống nước lọc thay nước ngọt | lu
19 | Cơ thể của em là của em | Vùng riêng tư; Nói KHÔNG – Chạy đi – Kể ngay | mimi
20 | Đi khám Bác sĩ Koala | Không sợ đi khám, che miệng khi ho, uống thuốc theo bác sĩ | mun

MÙA 5 — BẠN BÈ THÂN THIẾT
21 | Cầu trượt có lượt | Chia sẻ & xếp hàng đợi lượt | mun
22 | Xin lỗi và tha thứ | Nói lời xin lỗi thật lòng, sửa lỗi, tha thứ cho bạn | bi
23 | Ba từ có phép màu | Cảm ơn – Xin lỗi – Xin phép | lu
24 | Lông đen cũng đẹp | Tôn trọng khác biệt, không chê ngoại hình bạn | mun
25 | Không là không | Từ chối khi bạn rủ làm điều sai; không bắt nạt, bênh vực bạn | bong

MÙA 6 — TRUNG THỰC & TRÁCH NHIỆM
26 | Chiếc bình vỡ | Làm sai thì nói thật | bi
27 | Lời hứa của Lu | Giữ lời hứa, hứa điều mình làm được | lu
28 | Tại gió hay tại Mun? | Nhận lỗi, không đổ lỗi cho người khác | mun
29 | Cây đậu của Mimi | Chăm sóc cây mỗi ngày — trách nhiệm | mimi
30 | Chiếc ví ở sân đa | Nhặt được của rơi trả lại người mất | bong

MÙA 7 — GIA ĐÌNH YÊU THƯƠNG
31 | Bi giúp mẹ | Làm việc nhà vừa sức (gấp khăn, tưới cây, dọn bàn) | bi
32 | Ông hay quên | Kính trọng, kiên nhẫn & giúp đỡ ông bà | bong
33 | Anh em như tay chân | Anh em hòa thuận, nhường nhịn đúng cách | mun
34 | Món quà tự làm | Biết ơn, tặng quà bằng tấm lòng | mimi
35 | Bố mẹ mệt rồi | Thấu cảm khi bố mẹ bận/mệt, chơi một mình an toàn | lu

MÙA 8 — NHÀ KHOA HỌC NHÍ
36 | Hạt đậu thức dậy | Cây cần nước, ánh sáng, đất (thí nghiệm bông gòn) | bi
37 | Mưa từ đâu tới? | Vòng tuần hoàn nước đơn giản | bong
38 | Ông Mặt Trời đi ngủ | Ngày và đêm, mặt trăng thay hình | mun
39 | Hôm nay mặc gì? | Thời tiết & mặc đồ phù hợp (nắng, mưa, lạnh) | mimi
40 | Những người bạn tí hon | Ong, giun đất, bọ rùa có ích; không làm hại côn trùng | lu

MÙA 9 — EM LỚN KHÔN
41 | Rác về đúng nhà | Phân loại rác: hữu cơ, tái chế, còn lại | bi
42 | Giọt nước tiết kiệm | Khóa vòi nước, tắt đèn khi ra khỏi phòng | mimi
43 | Heo đất của Lu | Phân biệt "muốn" và "cần", để dành tiền | lu
44 | Ngã rồi đứng dậy | Thất bại không sao, thử lại (tập đi xe đạp/xếp tháp) | bong
45 | Màn hình vừa đủ | Giờ xem tivi/máy tính bảng có giới hạn, chơi ngoài trời | bi

MÙA 10 — NÉT ĐẸP VIỆT & CỘNG ĐỒNG
46 | Bánh chưng ngày Tết | Tết cổ truyền, gói bánh chưng, lời chúc & lì xì lễ phép | bi
47 | Lồng đèn Trung thu | Trung thu, làm lồng đèn, chia bánh cho bạn | mimi
48 | Đi chợ cùng bác Voi | Đi chợ: xếp hàng, chào hỏi, đếm tiền đơn giản | mun
49 | Ngày đầu đến trường | Lo lắng khi xa bố mẹ, làm quen bạn mới | lu
50 | Lễ hội Rừng Xanh | Tập tổng kết: cả nhóm dùng lại mọi bài học để tổ chức lễ hội cho làng | bi (cả nhóm)

Liên kết series: mỗi tập có 1 chi tiết nhỏ gợi lại tập trước (callback) và teaser tập sau; tính cách nhân vật phát triển dần (Bi bớt hấp tấp, Bông kiên nhẫn hơn với em, Mimi tự tin hơn, Lu biết nghĩ trước khi làm, Mun bớt mè nheo).

════════════════════════════════════════
PHẦN 6 — ĐẦU RA THEO CHẾ ĐỘ
════════════════════════════════════════
▶ CHẾ ĐỘ: BIBLE  (chạy 1 lần)
Xuất các file sau (nếu có quyền ghi file trong repo thì GHI TRỰC TIẾP; nếu không thì in từng file trong 1 code block, dòng đầu ghi đường dẫn):
 a) data/projects/soc-nho-tv/content/series/bi-va-nhung-nguoi-ban/series_bible.json
    { series_id, title, logline, target_age:"3-7", episode_count:50, runtime_s:600, aspect:"16:9",
      world:{ description, rules[], visual_style{ style_token, palette_hex[], lighting, materials, negative_prompt } },
      characters:[ { id, name, species, age_feel, gender, height_cm, scale_ratio_to_bi, personality[], catchphrase, voice_id, voice_status:"ready|TODO_CLONE", voice_direction (cao độ, tốc độ, chất giọng), growth_arc, do[], dont[], prompt_lock, expression_set:[8 biểu cảm: vui, buồn, giận, sợ, ngạc nhiên, xấu hổ, tự hào, tò mò → mô tả mặt + tư thế bằng tiếng Anh], turnaround_prompts:{front, three_quarter_left, three_quarter_right, side, back}, outfit_variants:{ pajamas, raincoat, tet_ao_dai, winter, swim_with_life_vest } } ],
      recurring_adults:[ cùng schema ],
      locations:[ { id, name_vi, description_vi, prompt_en (≥120 từ, siêu chân thực: kiến trúc, vật liệu, đạo cụ, thực vật, chi tiết bề mặt, thang tỉ lệ so với nhân vật 100cm), lighting_variants:{ morning, golden_hour, night }, prop_map[], camera_spots[ 3 góc máy đặt sẵn ] } ],
      title_sequence:{ duration_s:15, theme_song_lyrics (gốc, tiếng Việt), shot_list[] },
      end_screen:{ duration_s:20, layout },
      scale_lock_rows_to_append[] }
 b) 4 hồ sơ nhân vật mới theo đúng schema file koala_profile.json hiện có (id, name, version, purpose, identity, body{height_cm, height_ratio_to_bi, build, head_to_body_ratio, locked:true}, appearance, outfit_default, art_style, prompt_lock, persona_set):
    data/projects/soc-nho-tv/characters/de_bong/de_bong_profile.json
    data/projects/soc-nho-tv/characters/de_mun/de_mun_profile.json
    data/projects/soc-nho-tv/characters/cho_lu/cho_lu_profile.json
    data/projects/soc-nho-tv/characters/meo_mimi/meo_mimi_profile.json
 c) Các hàng mới để APPEND vào data/projects/soc-nho-tv/characters/SCALE_LOCK.md (không sửa hàng cũ).
 d) Prompt sinh "Master DNA" cho từng nhân vật mới: 1 ảnh chính diện đứng thẳng nền xám sáng + bảng lineup cả 5 nhân vật đứng cạnh nhau trên vạch chia chiều cao 0–150cm (để khóa tỉ lệ).

▶ CHẾ ĐỘ: TẬP NN  (chạy 50 lần, NN = 01…50)
Nếu file series_bible.json đã tồn tại thì ĐỌC và dùng đúng prompt_lock/location prompt trong đó. Lấy chủ đề tập NN ở Phần 5.
Ghi file: data/projects/soc-nho-tv/content/series/bi-va-nhung-nguoi-ban/episodes/epNN_<slug-khong-dau>.json
Schema bắt buộc (JSON hợp lệ, UTF-8, không comment, không placeholder kiểu "...", "TBD"):
{
  "id": "epNN_<slug>",
  "series_id": "bi-va-nhung-nguoi-ban",
  "episode_no": NN,
  "season": { "no": 1-10, "name": "..." },
  "title_vi": "...",
  "logline": "1 câu",
  "synopsis": "5–7 câu",
  "age_band": "3-7",
  "duration_target_s": 600,
  "aspect_ratio": "16:9",
  "resolution": "1920x1080",
  "focus_character": "...",
  "cast": ["bi", ...],
  "guests": [ { id, species, height_cm, scale_ratio_to_bi, personality[], prompt_lock, voice_id, scale_lock_row } ],
  "screen_time_plan": { "bi": 0.33, "bong": 0.15, ... , "shots_with_bi_ratio": 0.75 },
  "lesson": {
    "core_value": "...",
    "learning_objectives": ["Sau tập, bé biết…", "…", "…"],
    "magic_phrase": "câu thần chú ≤ 8 từ",
    "skill_steps": ["Bước 1…", "Bước 2…"],
    "misconception_fixed": "điều trẻ hay hiểu sai và tập này sửa",
    "vocabulary_new": [ { "word": "...", "kid_explanation": "..." } ],
    "callback_prev_episode": "...",
    "teaser_next_episode": "..."
  },
  "hooks": [
    { "variant": "A", "type": "mystery_question|funny_mishap|fourth_wall", "visual": "...", "line": "...", "score": 0-10, "why": "..." },
    { "variant": "B", ... }, { "variant": "C", ... }
  ],
  "selected_hook": "A|B|C",
  "character_sheets": [
    { "id": "bi", "episode_outfit": "mặc định hoặc biến thể", "props": [], "emotional_arc": "đầu tập → cuối tập", "full_prompt_en": "prompt_lock + outfit/prop của tập, dùng sinh ảnh tham chiếu riêng cho tập" }
  ],
  "location_sheets": [
    { "id": "treehouse_bi", "time_of_day": "...", "weather": "...", "set_dressing_this_episode": [], "full_prompt_en": "≥120 từ, siêu chân thực, kèm thang tỉ lệ" }
  ],
  "songs": [ { "id": "song_epNN", "title": "...", "lyrics_vi": "lời gốc", "tempo_bpm": 100, "mood": "...", "used_at": ["sc07", "sc14"] } ],
  "scenes": [
    {
      "scene_id": "sc01",
      "act": "cold_open|title|act1|act2a|act2b|act3|recap|ending",
      "t_start": 0, "t_end": 24,
      "location_id": "...", "time_of_day": "...", "weather": "...",
      "purpose": "cảnh này phục vụ gì cho câu chuyện/bài học",
      "characters": ["bi", "mun"],
      "shots": [
        {
          "shot_id": "sc01_sh01",
          "t_start": 0, "t_end": 8, "duration_s": 8,
          "shot_size": "MS", "angle": "eye-level|low|high|over-the-shoulder|POV", "lens_mm": 35,
          "camera_move": "push-in",
          "characters_in_frame": ["bi"],
          "action": "mô tả hành động tiếng Việt, cụ thể từng giây",
          "dialogue": [ { "char": "bi", "line": "…", "emotion": "tò mò", "delivery": "nhanh, cao giọng, nhấn chữ 'tại sao'" } ],
          "narration": "",
          "interactive_pause": { "question": "", "pause_s": 0 },
          "on_screen_text": "",
          "sfx": ["..."],
          "bgm_cue": "mood, BPM, vào/ra",
          "depth_layers": { "foreground": "...", "midground": "...", "background": "..." },
          "image_prompt": "tiếng Anh, tự chứa đầy đủ theo mẫu Phần 4",
          "video_prompt": "tiếng Anh, 8s, chuyển động theo mốc 0–3s / 3–6s / 6–8s",
          "negative_prompt": "chuẩn ở Phần 4",
          "transition_out": "hard-cut"
        }
      ]
    }
  ],
  "audio": {
    "voice_map": { "bi": "soc-nho", "bong": "de-bong", "mun": "de-mun", "lu": "cho-lu", "mimi": "meo-mimi" },
    "voice_status": { "soc-nho": "ready", "de-bong": "TODO_CLONE", "de-mun": "TODO_CLONE", "cho-lu": "TODO_CLONE", "meo-mimi": "TODO_CLONE" },
    "mastering": "de-esser, EQ +3.5dB @3.2kHz, comp 4:1, -14 LUFS, MP3 192kbps 44.1kHz",
    "bgm_ducking_db": -12
  },
  "parents_corner": { "goal": "...", "talk_tips": ["..."], "home_activity_10min": "...", "signs_child_understood": ["..."] },
  "youtube": {
    "title": "≤ 70 ký tự, có tên nhân vật + lợi ích, không giật tít",
    "description": "3 đoạn: tóm tắt – bé học được gì – góc bố mẹ; kèm chapters",
    "chapters": [ { "t": "00:00", "label": "..." } ],
    "tags": ["≥ 15 tag tiếng Việt + vài tag tiếng Anh"],
    "thumbnail_prompt": "tiếng Anh, 16:9, CU biểu cảm mạnh của Bi + focus_character, 1 đạo cụ chủ đề, nền tương phản, chừa vùng trống bên phải cho chữ",
    "thumbnail_text": "≤ 4 từ",
    "made_for_kids": true
  },
  "shorts_cutdowns": [
    { "t_start": 0, "t_end": 45, "hook": "...", "reframe_9x16": "giữ nhân vật trong vùng an toàn: chừa 180px trên, 320px dưới", "caption": "..." }
  ],
  "qa_self_check": {
    "total_duration_s": 0,
    "shot_count": 0,
    "bi_line_ratio": 0,
    "bi_shot_ratio": 0,
    "magic_phrase_repeats": 0,
    "interactive_pauses": 0,
    "max_words_per_line": 0,
    "scale_sentence_in_all_multi_char_prompts": true,
    "no_dangerous_imitable_success": true,
    "notes": "các điểm tự sửa"
  }
}

YÊU CẦU CHẤT LƯỢNG CHO MỖI TẬP:
- Tổng thời lượng 570–630s; shot_count 70–78; t_start/t_end liên tục không hở, không chồng.
- shorts_cutdowns: đúng 3 đoạn 30–59s có thể đứng riêng (hook mạnh, có bài học mini).
- Lời thoại tự nhiên kiểu trẻ con Việt Nam nói, có hài hước nhẹ, có cảm xúc; mỗi nhân vật nói đúng giọng tính cách (Bông chậm rãi "để anh xem", Mun câu ngắn ngây ngô, Lu hào hứng nhiều dấu "!", Mimi nhẹ nhàng chu đáo, Bi hỏi "tại sao").
- Mọi image_prompt nhắc đủ prompt_lock của nhân vật có mặt + câu tỉ lệ; không đổi trang phục giữa các shot trừ khi kịch bản có lý do và ghi rõ.
- Không lặp lại cốt truyện/gag/bài hát của tập khác.
- Trước khi kết thúc: tự rà theo qa_self_check, sửa lỗi, điền số thực tế. Nếu ghi file được: chạy kiểm tra JSON hợp lệ (python3 -m json.tool <file>) và báo kết quả.
- Nếu đầu ra bị giới hạn độ dài: dừng ở ranh giới 1 scene, ghi "…TIẾP: gõ 'tiếp' để in scene kế", rồi in tiếp đúng phần còn lại để ghép thành 1 JSON hoàn chỉnh (không lặp lại phần đã in).

════════════════════════════════════════
CHẾ ĐỘ: BIBLE
════════════════════════════════════════
```

---

## Ghi chú vận hành

- Thứ tự chạy: `BIBLE` → `TẬP 01` → … → `TẬP 50`. Sau `BIBLE`, sinh Master DNA cho Bông/Mun/Lu/Mimi trước rồi mới sản xuất tập, để mọi tập bám cùng 1 bộ ảnh tham chiếu.
- 4 giọng `de-bong`, `de-mun`, `cho-lu`, `meo-mimi` chưa có trong Voice Vault → clone bằng skill `vietnamese-voice-clone` trước khi lồng tiếng.
- Tập 16 trùng chủ đề với tập ngắn đã làm `content/episodes/soc-nho-sau-rang/` → coi như bản dài 10 phút, có thể tái dùng cảnh cũ.
- Dựng: mỗi file tập → `python -m socnhotv --project soc-nho-tv video render` (HyperFrames), mỗi scene là 1 sub-composition.
