import { create } from "zustand";
import type { ReactNode } from "react";

export type ConfirmTone = "danger" | "warning" | "info" | "success";

export interface AnchorRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface ConfirmOptions {
  /** Vị trí icon đã gọi hộp (tự lấy từ lần bấm gần nhất nếu không truyền) */
  anchor?: AnchorRect | null;
  title: string;
  message?: ReactNode;
  tone?: ConfirmTone;
  /** Nhãn nút xác nhận (mặc định theo tone) */
  confirmLabel?: string;
  cancelLabel?: string;
}

interface ConfirmState {
  current: (ConfirmOptions & { resolve: (ok: boolean) => void }) | null;
}

// Ghi nhớ nút vừa được bấm để hộp xác nhận mở sát nó và "mọc" ra từ icon
let lastTrigger: { rect: AnchorRect; at: number } | null = null;
if (typeof document !== "undefined") {
  document.addEventListener(
    "pointerdown",
    (e) => {
      const el = (e.target as HTMLElement | null)?.closest?.("button, a, [role=button]");
      if (!el) return;
      const r = el.getBoundingClientRect();
      lastTrigger = { rect: { left: r.left, top: r.top, width: r.width, height: r.height }, at: Date.now() };
    },
    true
  );
}

export const useConfirmStore = create<ConfirmState>(() => ({ current: null }));

/**
 * Hộp xác nhận dùng chung. Gọi `await confirm({...})` trước mọi hành động xóa/tạo/đổi quan trọng.
 * Trả về true nếu người dùng xác nhận.
 */
export function confirm(options: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    // Nếu đang có hộp khác thì coi như hủy hộp cũ
    useConfirmStore.getState().current?.resolve(false);
    useConfirmStore.setState({
      current: {
        tone: "info",
        ...options,
        anchor: options.anchor ?? (lastTrigger && Date.now() - lastTrigger.at < 8000 ? lastTrigger.rect : null),
        resolve: (ok) => {
          useConfirmStore.setState({ current: null });
          resolve(ok);
        },
      },
    });
  });
}
