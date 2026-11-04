# Playbook 01: Hook & Tỷ Lệ Giữ Chân Người Xem (Hook & Retention Mastery)

> Áp dụng cho: Mọi video ngắn Shorts, TikTok, Reels (Đặc biệt: Sóc Nhỏ Bi & KOC AI Gobi)  
> Mục tiêu cốt lõi: Đạt tỷ lệ giữ chân 3 giây đầu (3-second hold rate) ≥ 65% và hoàn thành video (Completion rate) ≥ 30%.

---

## 1. Danh Sách Kỹ Thuật Sử Dụng
- [`confession-hook`](../techniques/confession-hook.md): Hook thú nhận bí mật hậu trường, bẻ gãy tâm lý đề phòng quảng cáo.
- [`pre-publish-hook-retention-prediction`](../techniques/pre-publish-hook-retention-prediction.md): Tiền kiểm thử và chấm điểm hook theo luật cấu trúc đo được (≤12 từ, ≤3s).
- [`evergreen-shortform-foundations`](../techniques/evergreen-shortform-foundations.md): Nhịp cắt dồn dập 1.5s - 2.5s, loại bỏ khoảng lặng, vòng lặp Loop vô tận.
- [`virtual-influencer-paradox-storytelling`](../techniques/virtual-influencer-paradox-storytelling.md): Nghịch lý nhân vật ảo phá vỡ bức tường thứ 4.
- [`rapid-montage-proof`](../techniques/rapid-montage-proof.md): Bằng chứng dồn dập trong 2s đầu củng cố uy tín.

---

## 2. Quy Trình Từng Bước (Step-by-Step Workflow)

### Bước 1: Chọn Góc Tiếp Cận Hook
Dựa vào chủ đề video, chọn 1 trong 4 khuôn mẫu hook hiệu quả:
1. **Confession / Bí mật hậu trường:** Bắt đầu bằng hành động đời thường, giây thứ 2-3 lật ngược vấn đề bằng bí mật bất ngờ.
2. **Nghịch lý / Paradox:** Khẳng định một sự thật trái ngược với định kiến thông thường ("Càng chăm da kiểu này, da càng mụn").
3. **Thách thức nhận thức / Bức tường thứ 4:** Nhân vật nhìn thẳng camera nói điều không ai ngờ ("Em mới có mặt trên đời 10 phút thôi").
4. **Con số & Bằng chứng tức thì:** Đưa ra con số cụ thể hoặc kết quả trước/sau ngay giây đầu tiên.

### Bước 2: Sinh 3 Biến Thể A/B/C
- Luôn tạo 3 biến thể hook độc lập cho cùng 1 nội dung kịch bản.
- Chạy qua bộ lọc Heuristic Hook Scorer (`tool/src/socnhotv/video/craft/hooks.py`) để chọn hook điểm cao nhất.

### Bước 3: Đồng Bộ Âm Thanh & Phụ Đề
- Chữ đầu tiên của hook bắt buộc xuất hiện trong vòng **≤ 0.5 giây**.
- Voiceover đọc dứt khoát, không mở đầu bằng lời chào xã giao như *"Chào các bạn", "Hôm nay mình sẽ chia sẻ..."*.
- Thêm SFX nhấn điểm chuyển (Whoosh, Glitch, Camera Shutter) ngay khoảnh khắc lật ngược vấn đề.

### Bước 4: Thiết Kế Vòng Lặp Vô Tận (Seamless Loop)
- Câu kết thúc kịch bản nối liền mạch với câu mở đầu hook thành một câu có nghĩa.
- Frame cuối cùng và frame đầu tiên giữ cùng trường độ hoặc góc camera để khi video phát lại trên TikTok không bị khựng.

---

## 3. Khuôn Mẫu Hook Điển Hình (Templates)

### Khuôn 1: Sóc Nhỏ Thiếu Nhi / Khoa Học Khám Phá
```
[Hành động quan sát kỳ lạ] + "Ủa mà đố các bạn biết..." + [Bí mật khoa học bất ngờ]
Ví dụ: "Bi vừa nhìn lên bầu trời thấy cầu vồng đẹp ghê nè! Nhưng đố các bạn biết, cầu vồng thật ra không có 7 màu đâu nha!"
```

### Khuôn 2: KOC Review / Bán Hàng Thời Trang
```
[Trải nghiệm thực tế khen thật] + "Nhưng mà sự thật là..." + [Bí mật giá / công nghệ / chất liệu]
Ví dụ: "Mặc chiếc đầm này đi tiệc ai cũng khen tiền triệu! Nhưng sự thật là giá nó chưa bằng 2 ly trà sữa đâu!"
```

### Khuôn 3: Nhân Vật Ảo / Paradox
```
"Đừng tin những gì bạn vừa thấy! [Điều vừa thấy] thực ra chỉ là [bản chất thật]!"
Ví dụ: "Đừng tin vào mái tóc bồng bềnh này! Thực ra em là AI và mái tóc này vẽ bằng code đó!"
```

---

## 4. Sai Lầm Thường Gặp (Pitfalls to Avoid)
1. **Chào hỏi dông dài:** Tốn 2-3 giây đầu chào *"Hello cả nhà, chúc mọi người ngày mới tốt lành"* -> 80% người xem đã lướt qua.
2. **Hook quá dài (>12 từ hoặc >3.5 giây):** Người xem không kiên nhẫn nghe hết tiền đề.
3. **Mồi chài giật gân giả (Clickbait lừa dối):** Hook hứa hẹn điều giật gân nhưng thân bài không giải thích -> Bị thuật toán phạt tỷ lệ bỏ ngang.
4. **Thiếu phụ đề động trong 0.5s đầu:** 60% người dùng lướt TikTok ở chế độ tắt tiếng; không có chữ to rõ sẽ mất người xem ngay.

---

## 5. Checklist Trước Khi Xuất Bản (Pre-Publish Checklist)
- [ ] Hook có độ dài ≤ 12 từ hoặc đọc dưới 3.0 giây.
- [ ] Chữ phụ đề đầu tiên xuất hiện trước hoặc đúng giây thứ 0.5.
- [ ] Tuyệt đối không có từ chào hỏi xã giao ở đầu video.
- [ ] Có chứa từ khóa kích thích thị giác hoặc cảm xúc bất ngờ.
- [ ] Nhịp cắt cảnh đầu tiên chuyển đổi trước giây thứ 3.0.
- [ ] Câu kết nối nhịp nhàng với câu mở đầu tạo cảm giác loop vô tận.
