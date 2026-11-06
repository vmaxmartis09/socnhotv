# Nguồn nhạc nền & SFX hợp lệ bản quyền (I7)

- **Nguồn chính:** Openverse API (`https://api.openverse.org/v1/audio/`), không cần tài khoản, ẩn danh 20 truy vấn/phút, 200/ngày.
- **Giấy phép chấp nhận:** chỉ `cc0` và `by` (CC BY). Loại NC, SA, ND. CC BY phải ghi credit khi đăng video (tên, tác giả, giấy phép, link).
- **Nhà cung cấp thực tế:** SFX chủ yếu từ Freesound; nhạc từ Jamendo (CC BY) và Wikimedia Audio.
- **Quy trình:** `python3 scripts/audio/list_candidates.py <out.json>` liệt kê ứng viên (không tải) → người dùng duyệt `CANDIDATES.md` → tải → ghi từng tệp vào `data/shared/music_sfx/index.json` (id, title, creator, license, license_url, landing_url, download_url).
- **Lưu ý:** Openverse chỉ chuyển tiếp metadata giấy phép của nhà cung cấp; tác giả có thể gắn sai. Nghe thử bằng tai trước khi dùng cho phim thiếu nhi (từ khoá không đảm bảo hợp nội dung).
- **Hạn chế đã gặp:** từ khoá "kids/cartoon" trên Jamendo trả nhiều bài không hợp (Giáng sinh, nhạc ngoại ngữ, ballad); cần lọc bằng tai.
