import { create } from "zustand";

interface HubState {
  /** Dự án panel Project đang XEM; null = theo dự án đang mở trong Studio */
  projectId: string | null;
  set: (id: string | null) => void;
  /** Dự án đang mở chi tiết ở tab Dự án; giữ nguyên khi đổi tab, chỉ về danh sách khi bấm Quay lại hoặc nhấn đúp tab Dự án */
  detailProjectId: string | null;
  setDetail: (id: string | null) => void;
  /** Yêu cầu mở một tab của hub (từ nơi khác, ví dụ gợi ý "Tạo nhân vật"); FloatingPanels xử lý rồi xóa */
  pendingTab: "projects" | "characters" | "scripts" | "episodes" | "videos" | "images" | "policy" | null;
  /** Việc cần làm ngay khi tab mở (ví dụ mở form tạo nhân vật). Tab đích xử lý rồi xóa. */
  pendingAction: "create-character" | "compose-script" | "create-episode" | null;
  /** Mục cần chọn sẵn khi tab đích mở (id nhân vật / tập). Tab đích xử lý rồi xóa. */
  pendingFocus: string | null;
  openTab: (tab: NonNullable<HubState["pendingTab"]>, action?: HubState["pendingAction"], focusId?: string | null) => void;
  clearFocus: () => void;
  clearPending: () => void;
  clearAction: () => void;
}

export const useHubScope = create<HubState>((set) => ({
  projectId: null,
  set: (projectId) => set({ projectId }),
  detailProjectId: null,
  setDetail: (detailProjectId) => set({ detailProjectId }),
  pendingTab: null,
  pendingAction: null,
  pendingFocus: null,
  openTab: (pendingTab, action = null, focusId = null) => set({ pendingTab, pendingAction: action, pendingFocus: focusId }),
  clearFocus: () => set({ pendingFocus: null }),
  clearPending: () => set({ pendingTab: null }),
  clearAction: () => set({ pendingAction: null }),
}));
