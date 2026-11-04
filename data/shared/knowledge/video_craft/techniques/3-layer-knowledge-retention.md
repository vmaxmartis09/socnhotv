# Kỹ Thuật: 3-Layer Knowledge Retention & Origin Traceability

- **Mã kỹ thuật**: `3-layer-knowledge-retention`
- **Nguồn cảm hứng**: Phân tích từ video `seq_016_1761186394916521` (AI xàm xí - HKU Knowledge System)
- **Tags**: knowledge-base | documentation | architecture | traceability | zero-root-pollution

---

## 1. Bản Chất Kỹ Thuật
Cấu trúc quản trị tri thức chống suy giảm ngữ cảnh (Context Decay Prevention) gồm 3 tầng:

```
┌────────────────────────────────────────────────────────┐
│ TẦNG 1: TASK & STRATEGY LAYER (Nhiệm vụ & Chiến lược)   │
│ (ai/plans/, ROADMAP.md, CONTRACTS.md, status/D.md)    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ TẦNG 2: REUSABLE KNOWLEDGE & PATTERNS (Thẻ kỹ thuật)   │
│ (data/shared/knowledge/video_craft/techniques/*.md)   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ TẦNG 3: GROUND TRUTH & EVIDENCE (Bằng chứng gốc)       │
│ (videos/<id>/meta.json, transcript.json, shotlist.md)  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Tiêu Chuẩn Truy Xuất Nguồn Gốc (Traceability Standard)
- Mỗi kỹ thuật trong Tầng 2 **BẮT BUỘC** phải có trường `Nguồn cảm hứng: seq_XXX_<id>`.
- Mỗi video trong Tầng 3 **BẮT BUỘC** phải có:
  - `meta.json` (canonical URL, video ID, metrics).
  - `transcript.json` (timestamp từng câu thoại).
  - `contact_sheet.jpg` (bằng chứng thị giác).
  - `edit_metrics.json` (loudness LUFS, speech rate, aspect ratio).
- Nhờ cấu trúc này, bất kỳ Agent nào (A, B, C, D) hay người vận hành đều có thể kiểm tra ngược lại thực tế trong 1 giây mà không bao giờ bị phụ thuộc vào trí nhớ tạm thời (RAM/context limit).
