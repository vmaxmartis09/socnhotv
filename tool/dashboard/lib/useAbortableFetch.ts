import { useEffect } from "react";

/**
 * useAbortableEffect: Quản lý vòng đời fetch kèm AbortController và cờ kiểm tra hiệu lực.
 * Tự động hủy in-flight request và ngăn chặn race condition khi đổi dự án/tab nhanh.
 */
export function useAbortableEffect(
  effect: (signal: AbortSignal, isCurrent: () => boolean) => Promise<void> | void,
  deps: any[]
) {
  useEffect(() => {
    const controller = new AbortController();
    let current = true;

    const checkCurrent = () => current && !controller.signal.aborted;

    effect(controller.signal, checkCurrent);

    return () => {
      current = false;
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
