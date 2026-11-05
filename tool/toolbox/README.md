# SOCNHOTV TOOLBOX

Hệ thống công cụ video & AI độc lập, nhẹ, chạy CPU, tự đóng gói trong môi trường ảo riêng biệt, chia sẻ tài nguyên qua các kho dùng chung (`data/shared/`).

---

## 1. Nguyên Tắc & Ràng Buộc Cốt Lõi

1. **Cách ly tuyệt đối (Zero Pollution):**
   - Mỗi tool nằm trong `tool/toolbox/tools/<tool-id>/`.
   - Mỗi tool có môi trường ảo riêng (`.venv/`), `requirements.txt` riêng, **KHÔNG** can thiệp môi trường toàn cục, **KHÔNG** import mã nội bộ của `tool/src/socnhotv/`.
2. **Chạy CPU mặc định:**
   - Mọi tool ưu tiên tối đa khả năng chạy trên CPU (ONNX Runtime CPU, int8 models). Nếu bắt buộc cần GPU, phải khai báo rõ `requires_gpu: true` trong `tool.json`.
3. **Kiểm tra giấy phép bản quyền (License Gate):**
   - Kiểm tra độc lập giấy phép của **mã nguồn (code)** và **trọng số mô hình (weights)**.
   - Ghi rõ vào `tool.json.license` (`code`, `weights`, `commercial_ok`, `source_url`, `checked_on`). Mô hình mang tính chất phi thương mại (Non-Commercial / CC-BY-NC) không được cấu hình làm mặc định.
4. **Hợp đồng thực thi chuẩn hóa:**
   - Mỗi tool chỉ có duy nhất một điểm vào CLI:
     ```bash
     python run.py --in in.json --out out.json
     ```
   - Chỉ in đường dẫn tuyệt đối của `out.json` ra stdout khi kết thúc. Mọi nhật ký chi tiết hoặc cảnh báo ghi vào trường `warnings` hoặc file log riêng.
   - Trả mã thoát (Exit code) trung thực:
     - `0`: Thành công
     - `1`: Lỗi thực thi không xác định
     - `2`: Thiếu dependency hoặc weights model (có hướng dẫn khắc phục trong `error.fix_hint`)
     - `3`: Input sai hoặc thiếu file đầu vào

---

## 2. Cấu Trúc Thư Mục

```
tool/toolbox/
  ├── README.md               # Hướng dẫn kiến trúc và vận hành
  ├── .gitignore              # Bỏ qua venv, weights, files tạm
  ├── toolbox_cli/            # CLI mỏng dùng Python stdlib quản trị toàn bộ toolbox
  ├── contracts/              # JSON Schemas cho tool manifest, IO, và shared store
  │   ├── tool.schema.json
  │   ├── run_io.schema.json
  │   └── store_record.schema.json
  ├── _template/              # Khung mẫu để nhân bản tool mới
  │   ├── tool.json
  │   ├── run.py
  │   └── requirements.txt
  └── tools/
      ├── bg-remove/          # Tách nền (rembg / BiRefNet)
      ├── stt-align/          # Phiên âm canh từ (faster-whisper / whisper.cpp)
      ├── voice-clone/        # Clone giọng (OmniVoice wrapper)
      ├── scene-cut/          # Tách cảnh / cắt khoảng lặng
      ├── depth-layers/       # Tách 3 lớp tiền/trung/hậu cảnh (Depth Anything V2)
      └── ffmpeg-bin/         # Bundle static ffmpeg CPU
```

---

## 3. Cách Tạo Một Tool Mới

1. Sao chép thư mục `tool/toolbox/_template/` sang `tool/toolbox/tools/<tool-id>/`.
2. Cập nhật `tool.json` với thông tin mô tả, giấy phép nguồn, đường dẫn tải model, input/output.
3. Tạo môi trường ảo riêng cho tool:
   ```bash
   py -3.11 -m venv tool/toolbox/tools/<tool-id>/.venv
   tool/toolbox/tools/<tool-id>/.venv/Scripts/python -m pip install -r tool/toolbox/tools/<tool-id>/requirements.txt
   ```
4. Viết logic thực thi trong `run.py` tuân thủ đầu vào `in.json` và trả về `out.json`.
5. Chạy thử kiểm tra với CLI Toolbox:
   ```bash
   py -3.11 tool/toolbox/toolbox_cli/cli.py run <tool-id> --in sample_in.json --out sample_out.json
   ```

---

## 4. Kho Dùng Chung (`data/shared/`)

- `data/shared/assets/cutouts/<sha8>/`: Chứa ảnh PNG tách nền kèm mask và source metadata.
- `data/shared/voice_vault/<voice-id>/`: Chứa mẫu giọng, cấu hình `voice.json` và chỉ mục `index.jsonl`.
- `data/shared/models/<tool-id>/`: Chứa weights và nhị phân mô hình, được tải tự động có kiểm SHA256.
- `data/shared/toolbox/runs.jsonl`: Nhật ký lịch sử các lần chạy tool (append-only, atomic lock).
