import { create } from "zustand";
import type { ReactNode } from "react";

export interface PreviewMedia {
  url: string;
  name: string;
}

export type PreviewItem =
  | { kind: "image" | "video"; title: string; items: PreviewMedia[]; index: number }
  | { kind: "markdown"; title: string; url?: string; text?: string }
  | { kind: "project"; title: string; projectId: string }
  /** Nội dung tùy biến (ví dụ form chỉnh sửa) hiển thị trong vùng mở rộng thay cho modal */
  | { kind: "custom"; title: string; render: (close: () => void) => ReactNode };

interface PreviewState {
  item: PreviewItem | null;
  open: (item: PreviewItem) => void;
  go: (index: number) => void;
  close: () => void;
}

/**
 * Quy tắc UI: nơi nào mở rộng được thì mở rộng panel sang trái để xem trước,
 * không bật modal che màn hình. Mọi nơi gọi `usePreview.getState().open(...)`.
 */
export const usePreview = create<PreviewState>((set) => ({
  item: null,
  open: (item) => set({ item }),
  go: (index) =>
    set((s) => (s.item && (s.item.kind === "image" || s.item.kind === "video") ? { item: { ...s.item, index } } : s)),
  close: () => set({ item: null }),
}));
