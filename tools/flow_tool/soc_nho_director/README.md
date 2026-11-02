# Sóc Nhỏ Director (bản chạy local)

Bản chép của tool "Remix of Sóc Nhỏ Director" trên Google Flow. Mã giao diện giữ nguyên, thư viện `flow-sdk` (chỉ có trong Flow) được thay bằng `src/flow-sdk.ts`.

## Chạy
```bash
npm install
npm run dev     # http://127.0.0.1:3000
```

## Hai chế độ
- **Chạy thử (mặc định):** không có khóa API, tool trả ảnh và video giả (video là webm 2 giây). Dùng để kiểm tra giao diện, nạp gói JSON, thứ tự cảnh, chuyển cảnh. Không tốn tiền.
- **API thật:** tạo `.env.local` với `GEMINI_API_KEY=...` (xem `.env.local.example`) rồi chạy lại `npm run dev`. Ảnh dùng `gemini-3-pro-image-preview` hoặc `gemini-2.5-flash-image`, video dùng Veo qua `predictLongRunning`. Tính tiền theo API Google, không dùng credit Flow. Ánh xạ model nằm trong `vite.config.ts`. Chưa kiểm tra với khóa thật.

## Gói dự án
`python3 scripts/flow_ai/build_flow_package.py --script <kich_ban.txt> --out <goi.json>` ở thư mục gốc project, rồi bấm "Mở dự án". Mẫu: `public/demo/goi_demo.json`.
