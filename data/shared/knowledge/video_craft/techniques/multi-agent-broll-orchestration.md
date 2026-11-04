---
id: multi-agent-broll-orchestration
title: Multi-Agent B-Roll Orchestration & Parallel Asset Generation
status: knowledge
build: partial
reproducible_with_our_stack: 'yes'
needs:
- Python asyncio
- AI Providers
implemented_in:
- tool/src/socnhotv/intelligence/
evidence_videos:
- seq_N05
confidence: high
last_verified: '2026-11-04'
expires_at: '2027-11-04'
tags:
- multi-agent
- orchestration
- parallel-gen
- b-roll
---

# Kỹ Thuật: Multi-Agent B-Roll Orchestration & QA Inspection

- **Mã kỹ thuật**: `multi-agent-broll-orchestration`
- **Nguồn cảm hứng**: Phân tích từ video `seq_n02_28160631690277676` (Tài Xài Tech)
- **Tags**: multi-agent | b-roll-assembly | orchestration | qa-agent | gemini-flash | session-a | session-b

---

## 1. Bản Chất Kỹ Thuật
Kiến trúc tự động hóa dựng video kết hợp A-Roll (video nói chính) và B-Roll (hình ảnh minh họa) thông qua mô hình đa tác tử (Hierarchical Multi-Agent System):

```
                     ┌───────────────────────┐
                     │     LEADER AGENT      │
                     │ (Orchestrator/Router) │
                     └───────────┬───────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼────────┐     ┌────────▼────────┐     ┌────────▼────────┐
│  TRANSCRIPT &   │     │  B-ROLL MATCHER │     │  HOOK SPECIALIST│
│  SEGMENT AGENT  │     │    SUB-AGENT    │     │    SUB-AGENT    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   QA INSPECTOR  │
                        │    SUB-AGENT    │
                        └─────────────────┘
```

---

## 2. Quy Trình 4 Bước Thực Thi
1. **Bước 1 (Decomposition)**: `Transcript Agent` bóc tách lời thoại và đánh dấu các khoảng trống cần chèn B-roll.
2. **Bước 2 (Asset Sourcing & Semantic Match)**: `B-Roll Matcher` phân tích semantic similarity giữa câu thoại và metadata của video B-roll trong kho `data/projects/<id>/library/`.
3. **Bước 3 (Hook Fortification)**: `Hook Specialist` rà soát 3 giây đầu, chèn hiệu ứng punch-in hoặc sound effect giật gân để tối đa hóa CTR.
4. **Bước 4 (QA Gate)**: `QA Inspector Agent` kiểm tra tính hợp lệ của render composition trước khi gửi sang Session C để xuất bản.
