# Báo Cáo Cắt Gọt UI — Session E (Bước 1)

## 1. Mục tiêu đã thực hiện
- Cắt bỏ toàn bộ 6 trang cấp cao độc lập và các module cồng kềnh ngoài 3 mục tiêu trọng tâm:
  - Trang & Route: `/templates`, `/templates/[id]`, `/renders`, `/renders/episode/[eid]`, `/sources`, `/products`, `/intel`, `/social`, `/publish` đã chuyển thành redirect về `/studio`.
  - Component độc lập: `components/intel/*`, `components/products/*`, `components/sources/*`, `components/renders/EpisodeBuildPanel.tsx`.
  - Component mạng xã hội dư thừa: `components/social/{AnalyticsTab,AutomationRulesModal,ManualMetricsModal,NotificationDrawer,PostsTab,ApprovalsTab}.tsx`.
  - Module điều hướng cũ: `components/navigation/nav-modules/*`.
  - `PageBar`: Tối giản chỉ còn `Sảnh › [Tên dự án đang mở]`.
  - Ẩn node phụ khỏi bảng thêm node và menu nối nhanh: `source_video`, `localize`, `blueprint_analyze`, `script_from_blueprint`, `channel_insight`. Giữ nguyên hiển thị `template_render` và `platform_export`.
  - Dữ liệu mẫu phân tích (2.6): Di chuyển `data/projects/soc-nho-tv/analytics/{metrics,insights,recommendations.json,learnings.md}` sang `analytics/_demo/`. Thêm ghi chú cảnh báo dữ liệu mẫu vào đầu `status/REQUESTS.md`.

## 2. Thống kê số dòng code (LOC)
- **Tổng số dòng frontend trước khi cắt (Bước 0):** 28.463 dòng
- **Tổng số dòng frontend sau khi cắt (Bước 1):** 20.585 dòng
- **Số dòng đã cắt giảm:** 7.878 dòng (~27.7% toàn bộ codebase frontend, loại bỏ 100% trang thừa)

## 3. Danh sách file/thư mục đã xoá
- `tool/dashboard/app/[locale]/renders/episode/[eid]/page.tsx`
- `tool/dashboard/app/[locale]/templates/[id]/page.tsx`
- `tool/dashboard/components/navigation/nav-modules/` (toàn bộ 5 files: `index.ts`, `social.ts`, `sources-icons.ts`, `sources.ts`, `video.ts`)
- `tool/dashboard/components/intel/` (toàn bộ 7 files: `AddChannelModal.tsx`, `BlueprintView.tsx`, `ChannelDetailView.tsx`, `IdeaBoard.tsx`, `ScriptWizardModal.tsx`, `StrategyView.tsx`, `icons.ts`)
- `tool/dashboard/components/products/` (toàn bộ 5 files: `AddProductModal.tsx`, `ProductCard.tsx`, `ProductDetailModal.tsx`, `ProductsList.tsx`, `icons.ts`)
- `tool/dashboard/components/sources/` (toàn bộ 5 files: `AddSourcesModal.tsx`, `LocalizeStudio.tsx`, `SourceCard.tsx`, `SourceDetailModal.tsx`, `SourcesList.tsx`)
- `tool/dashboard/components/renders/EpisodeBuildPanel.tsx`
- `tool/dashboard/components/social/AnalyticsTab.tsx`
- `tool/dashboard/components/social/ApprovalsTab.tsx`
- `tool/dashboard/components/social/AutomationRulesModal.tsx`
- `tool/dashboard/components/social/ManualMetricsModal.tsx`
- `tool/dashboard/components/social/NotificationDrawer.tsx`
- `tool/dashboard/components/social/PostsTab.tsx`
