"use client";

import React, { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

interface Tip {
  text: string;
  x: number;
  y: number;
  side: "left" | "right" | "top" | "bottom";
}

const SELECTOR = "[data-tip], [title], button[aria-label], a[aria-label], [role=tab][aria-label]";

/** Nhãn của phần tử: title (đổi sang data-tip để tắt tooltip gốc chậm của trình duyệt) hoặc aria-label của nút chỉ có icon. */
function labelOf(el: HTMLElement): string {
  const title = el.getAttribute("title");
  if (title) {
    el.setAttribute("data-tip", title);
    el.removeAttribute("title");
  }
  const tip = el.getAttribute("data-tip");
  if (tip) return tip;
  const aria = el.getAttribute("aria-label");
  // Chỉ dùng aria-label khi nút không có chữ hiển thị (nút chỉ có icon)
  if (aria && !(el.textContent || "").replace(/\s+/g, "").length) return aria;
  return "";
}

/**
 * Tooltip tức thì dùng chung cho mọi nút icon: gắn một lần ở layout, tự nhận `title`,
 * `data-tip` và `aria-label` của nút không có chữ. Không cần gắn riêng từng nút.
 */
export function TooltipHost() {
  const [tip, setTip] = useState<Tip | null>(null);
  const timer = useRef<number | null>(null);
  const current = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const hide = () => {
      if (timer.current) window.clearTimeout(timer.current);
      current.current = null;
      setTip(null);
    };

    const onOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      const el = target?.closest?.(SELECTOR) as HTMLElement | null;
      if (!el || el === current.current) return;
      const text = labelOf(el);
      if (!text) return;
      current.current = el;
      if (timer.current) window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => {
        const r = el.getBoundingClientRect();
        const vw = window.innerWidth;
        const cx = r.left + r.width / 2;
        const side: Tip["side"] = cx > vw * 0.6 ? "left" : cx < vw * 0.4 && r.width < 80 ? "right" : r.top < 80 ? "bottom" : "top";
        const x = side === "left" ? r.left - 8 : side === "right" ? r.right + 8 : cx;
        const y = side === "top" ? r.top - 8 : side === "bottom" ? r.bottom + 8 : r.top + r.height / 2;
        setTip({ text, x, y, side });
      }, 120);
    };

    const onOut = (e: MouseEvent) => {
      const to = e.relatedTarget as HTMLElement | null;
      if (current.current && to && current.current.contains(to)) return;
      hide();
    };

    document.addEventListener("mouseover", onOver, true);
    document.addEventListener("mouseout", onOut, true);
    document.addEventListener("mousedown", hide, true);
    document.addEventListener("keydown", hide, true);
    window.addEventListener("scroll", hide, true);
    return () => {
      document.removeEventListener("mouseover", onOver, true);
      document.removeEventListener("mouseout", onOut, true);
      document.removeEventListener("mousedown", hide, true);
      document.removeEventListener("keydown", hide, true);
      window.removeEventListener("scroll", hide, true);
    };
  }, []);

  const transform =
    tip?.side === "left"
      ? "translate(-100%, -50%)"
      : tip?.side === "right"
      ? "translate(0, -50%)"
      : tip?.side === "top"
      ? "translate(-50%, -100%)"
      : "translate(-50%, 0)";

  return (
    <div className="pointer-events-none fixed z-[200]" style={tip ? { left: tip.x, top: tip.y, transform } : { display: "none" }}>
      <AnimatePresence>
        {tip && (
          <motion.div
            key={tip.text + tip.x + tip.y}
            role="tooltip"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.1 }}
            className="max-w-[260px] whitespace-nowrap rounded-md bg-foreground px-2 py-1 text-xs font-medium text-background"
          >
            {tip.text}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
