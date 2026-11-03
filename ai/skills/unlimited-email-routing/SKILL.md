---
name: unlimited-email-routing
description: "Tự động tạo và quản lý không giới hạn địa chỉ email miễn phí (Catch-all Email Routing) qua Addy.io hoặc Cloudflare để nhận mã OTP xác thực đăng ký hàng loạt tài khoản mạng xã hội (TikTok, Facebook, Instagram, Google). Dùng khi user yêu cầu: 'tạo mail mới', 'tạo nhiều email', 'sinh email nuôi nick', 'cấu hình email routing', hoặc 'quản lý email chòm sao'."
---

# Unlimited Email Routing & Multi-Account Email Matrix Skill

Kỹ năng chuyên biệt để tạo và quản lý **hàng trăm địa chỉ email độc lập hoàn toàn miễn phí** (hoặc siêu rẻ với tên miền riêng) sử dụng cơ chế **Catch-All Email Routing**. Tất cả các email này đều tự động gom mã OTP và thư xác nhận về duy nhất **1 hộp thư Gmail chính của người dùng**, phục vụ mục đích đăng ký và nuôi dàn tài khoản mạng xã hội (TikTok, Facebook, Instagram, Shopee).

---

## 🎯 1. NGUYÊN TẮC CỐT LÕI (CORE ARCHITECTURE)

Thay vì cố gắng tạo nhiều tài khoản Gmail riêng lẻ (thường bị Google yêu cầu số điện thoại OTP hoặc đánh dấu spam/bot), kiến trúc chuẩn mực bao gồm:

1. **Hộp thư Đích (Destination Mailbox):** Hộp thư Gmail chính của người dùng (ví dụ: `dinhthienthoai@gmail.com`).
2. **Hệ thống Catch-All Forwarder:** Tiếp nhận mọi email gửi đến bất kỳ tiền tố nào (`*@subdomain.domain`) và tự động chuyển tiếp thẳng về hộp thư đích.
3. **Ma trận Định danh KOC (Account Matrix):** Gán các tiền tố email chuẩn hóa theo chiến dịch (ví dụ: `gobi-aries@...`, `gobi-taurus@...` theo 12 Cung Hoàng Đạo) và đồng bộ vào công cụ quản trị `gobi account`.

---

## 🚀 2. PHƯƠNG PHÁP 1: MIỄN PHÍ 100% QUA ADDY.IO (ANONADDY)

Đây là phương pháp **không mất phí ($0)**, không cần thẻ ngân hàng (Visa/Mastercard) và kích hoạt tức thì.

### 2.1. Cơ chế Subdomain Catch-All
Khi người dùng đăng ký tài khoản miễn phí trên [Addy.io](https://addy.io) với username đại diện (ví dụ: `gobikoc`):
- Tên miền email miễn phí được cấp: `@<username>.anonaddy.com` (hoặc `.anonaddy.me`).
- **Mặc định bật Catch-All:** Bất kỳ địa chỉ nào bạn nghĩ ra trước ký tự `@` (ví dụ: `gobi-aries@gobikoc.anonaddy.com`) đều tự động hợp lệ và được Addy.io chuyển tiếp ngay lập tức về Gmail gốc.

### 2.2. Quy trình Tự động hóa qua Ego Lite
Khi cần thiết lập cho người dùng qua trình duyệt **Ego Lite**:
1. **Mở form đăng ký:** Điều hướng tới `https://app.addy.io/register`.
2. **Điền thông tin:**
   - `username`: Tên nhận diện (ví dụ `gobikoc`).
   - `email` & `email_confirmation`: Gmail người dùng (`dinhthienthoai@gmail.com`).
   - `password`: Mật khẩu bảo mật ngẫu nhiên (lưu lại và bàn giao cho người dùng).
   - Checkbox `terms`: Tick đồng ý điều khoản.
3. **Giải Cloudflare Turnstile:** Bắt sự kiện widget hoặc click xác nhận human check.
4. **Gửi thư xác thực:** Bấm `Accept and Send Verification Email`.
5. **Tự động bắt link kích hoạt:**
   - Mở tab Gmail của người dùng (`https://mail.google.com`).
   - Tìm thư mới nhất từ `addy.io — Verify Email Address`.
   - Trích xuất link xác nhận `https://app.addy.io/email/verify/...` và điều hướng tới link đó.
   - Trạng thái tài khoản chuyển sang `Verified` -> Kích hoạt hoàn tất!

---

## 🌐 3. PHƯƠNG PHÁP 2: TÊN MIỀN RIÊNG QUA CLOUDFLARE EMAIL ROUTING

Dành cho trường hợp người dùng muốn sở hữu địa chỉ email mang thương hiệu riêng hoàn toàn độc lập (ví dụ `@gobikoc.site` hoặc `@yourbrand.com`).

### 3.1. Các bước thiết lập:
1. **Chuẩn bị tên miền:** Mua tên miền đuôi rẻ (`.site`, `.xyz`, `.top` khoảng 25k - 120k/năm) trên Spaceship, Namecheap, Porkbun hoặc mua trực tiếp qua Cloudflare Registrar.
2. **Đăng nhập Cloudflare:** Dùng Ego Lite đăng nhập tài khoản Cloudflare của người dùng qua Google OAuth.
3. **Thêm Destination Address:**
   - Vào mục **Email Service** -> **Email Routing** -> **Destination addresses**.
   - Nhập Gmail của người dùng -> Cloudflare tự động xác nhận `Verified` nếu đó là email đăng nhập tài khoản.
4. **Bật Catch-All Rule:**
   - Thêm domain vào Cloudflare (`+ Onboard Domain`).
   - Tạo rule: `Catch-all` -> `Forward to <Gmail của người dùng>`.
   - Bấm áp dụng tự động các bản ghi DNS (MX & TXT) của Cloudflare.

---

## 🛠️ 4. QUẢN TRỊ MA TRẬN TÀI KHOẢN QUA GOBI CLI

Toàn bộ danh sách email sau khi tạo được tích hợp trực tiếp vào hệ thống quản lý `gobi-social`:

### 4.1. Cập nhật tên miền mới vào hệ sinh thái
```bash
python3 -m gobi account apply-domain --domain gobikoc.anonaddy.com
```

### 4.2. Xem bảng trạng thái 12 tài khoản chòm sao
```bash
python3 -m gobi account list
```

### 4.3. Xuất file cấu hình nạp vào trình duyệt nuôi nick (Antidetect)
```bash
python3 -m gobi account export --format csv --domain gobikoc.anonaddy.com
```
*File xuất chuẩn định dạng tại: `output/accounts/gobi_zodiac_profiles.csv`, tương thích 100% với AdsPower, GoLogin, Hidemyacc.*

### 4.4. Tra cứu quy trình làm ấm (Warm-up) tránh 0 view
```bash
python3 -m gobi account warmup --day 1  # 0 đến 5
```

---

## ⚠️ 5. QUY CHUẨN AN TOÀN KHI DÙNG ĐĂNG KÝ TIKTOK

1. **Không tạo hàng loạt trong 1 ngày:** Dù có sẵn 12 email, chỉ nên đăng ký rải rác 1-2 tài khoản/ngày.
2. **Cách ly thiết bị & IP:**
   - Dùng Antidetect Browser (mỗi tài khoản 1 profile độc lập).
   - Sử dụng mạng 4G di động (reset IP trước mỗi lần tạo) hoặc Residential Proxy.
3. **Băng thông miễn phí:** Addy.io gói Free cung cấp 10MB/tháng (đủ nhận hàng chục nghìn email OTP dạng văn bản). Không dùng để nhận file đính kèm dung lượng lớn.
