# Khóa tỉ lệ kích thước giữa các nhân vật (KHÔNG ĐỔI)

Chuẩn: Sóc Nhỏ Bi = 100 cm = 1.0

| Nhân vật | Cao | Tỉ lệ so với Bi |
|---|---|---|
| Sóc Nhỏ Bi | 100 cm | 1.0 |
| Bác sĩ Koala | 150 cm | 1.5 (Bi đứng ngang ngực/bụng bác sĩ) |

Quy tắc: mọi ảnh/video có 2 nhân vật trở lên phải giữ đúng tỉ lệ này ở mọi góc máy.
Thêm câu vào prompt: "Bi the squirrel is two-thirds the height of the koala doctor, his head reaches the doctor's chest".
Nhân vật mới: thêm hàng vào bảng, không sửa các hàng cũ.

## Bổ sung Series "Bi Và Những Người Bạn" (APPEND — Không sửa các hàng cũ)

| Nhân vật | ID | Cao | Tỉ lệ so với Bi (100 cm = 1.0) | Mốc so sánh trực quan |
|---|---|---|---|---|
| Dê Bông (anh trai, dê trắng) | `bong` | 115 cm | 1.15 | Đỉnh đầu Bi chạm tới cằm anh Bông (`Bi's head reaches Bong's chin`) |
| Cún Lu (chó cỏ Việt Nam, bé gái) | `lu` | 105 cm | 1.05 | Cao hơn Bi một chút xíu (`almost the same height as Bi, 5cm taller`) |
| Sóc Bi (nhân vật chính chuẩn) | `bi` | 100 cm | 1.00 | Chuẩn gốc (1.0) |
| Mèo Mimi (mèo tam thể, bé gái) | `mimi` | 95 cm | 0.95 | Thấp hơn Bi nửa cái đầu nhỏ (`slightly shorter than Bi, 5cm shorter`) |
| Dê Mun (em trai, dê đen) | `mun` | 85 cm | 0.85 | Đỉnh đầu Mun chạm tới mũi Bi (`Mun's head reaches Bi's nose`) |
| Mẹ Sóc (mẹ của Bi) | `me_soc` | 145 cm | 1.45 | Đỉnh đầu Bi ngang ngực Mẹ Sóc (`Bi's head reaches Mother Squirrel's chest`) |
| Bác sĩ Koala (đã khóa ở bảng gốc) | `bac_si_koala` | 150 cm | 1.50 | Bi cao bằng 2/3 Bác sĩ Koala, đầu Bi ngang ngực bác sĩ |
| Ông Dê Râu Bạc (ông nội Bông & Mun) | `ong_de_rau_bac` | 155 cm | 1.55 | Đầu Bi ngang ngực dưới Ông Dê; đầu Mun ngang bụng Ông Dê |
| Cô giáo Hươu Sao (trường Lá Xanh) | `co_huou_sao` | 160 cm | 1.60 | Đầu Bi ngang bụng/ngực dưới Cô giáo Hươu Sao (tính cả gạc nhỏ dịu dàng) |
| Bác Voi (bán hàng chợ làng) | `bac_voi` | 180 cm | 1.80 | Nhân vật lớn nhất làng; Bi đứng ngang thắt lưng/bụng Bác Voi |

**Câu khóa tỉ lệ bắt buộc chèn vào mọi prompt có ≥2 nhân vật trong nhóm bạn nhỏ:**
`"Height order from tallest: Bong 115cm > Lu 105cm > Bi 100cm > Mimi 95cm > Mun 85cm; Bi's head reaches Bong's chin, Mun's head reaches Bi's nose."`
