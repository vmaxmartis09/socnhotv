"use client";

import React, { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useConfirmStore, type ConfirmTone } from "@/lib/confirm";
import { Trash2, AlertTriangle, Info, CheckCircle2, X, Check } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

const TONES: Record<
  ConfirmTone,
  { Icon: React.ComponentType<{ className?: string }>; ring: string; bg: string; text: string; btn: string; label: string }
> = {
  danger: { Icon: Trash2, ring: "ring-semantic-danger/30", bg: "bg-semantic-danger/10", text: "text-semantic-danger", btn: "bg-semantic-danger text-white", label: "Xóa" },
  warning: { Icon: AlertTriangle, ring: "ring-semantic-warning/30", bg: "bg-semantic-warning/10", text: "text-semantic-warning", btn: "bg-semantic-warning text-white", label: "Tiếp tục" },
  info: { Icon: Info, ring: "ring-brand/30", bg: "bg-brand/10", text: "text-brand", btn: "bg-primary text-primary-foreground", label: "Xác nhận" },
  success: { Icon: CheckCircle2, ring: "ring-semantic-success/30", bg: "bg-semantic-success/10", text: "text-semantic-success", btn: "bg-semantic-success text-white", label: "Hoàn tất" },
};

/** Gắn một lần ở layout: hiển thị hộp xác nhận cho mọi lời gọi `confirm()`. */
export function ConfirmHost() {
  const current = useConfirmStore((s) => s.current);

  useEffect(() => {
    if (!current) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        current.resolve(false);
      } else if (e.key === "Enter") {
        e.preventDefault();
        current.resolve(true);
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [current]);

  const tone = TONES[current?.tone ?? "info"];
  const Icon = tone.Icon;

  // Vị trí: sát icon đã gọi (trái/phải tùy phía màn hình); không có thì giữa màn hình
  const W = 320;
  const H = 168;
  let pos: { left: number; top: number; originX: number; originY: number } | null = null;
  if (current?.anchor && typeof window !== "undefined") {
    const a = current.anchor;
    const cx = a.left + a.width / 2;
    const cy = a.top + a.height / 2;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const onRight = cx > vw / 2;
    let left = onRight ? a.left - W - 12 : a.left + a.width + 12;
    left = Math.max(12, Math.min(vw - W - 12, left));
    const top = Math.max(12, Math.min(vh - H - 12, cy - 56));
    pos = { left, top, originX: cx - left, originY: cy - top };
  }

  return (
    <AnimatePresence>
      {current && (
        <motion.div
          key="confirm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={cn("fixed inset-0 z-[100]", pos ? "" : "flex items-center justify-center bg-black/40 p-4")}
          onMouseDown={(e) => e.target === e.currentTarget && current.resolve(false)}
        >
          <motion.div
            role="alertdialog"
            aria-modal="true"
            aria-label={current.title}
            initial={{ opacity: 0, scale: pos ? 0.7 : 0.97, y: 0, borderRadius: 18 }}
            animate={{ opacity: 1, scale: 1, y: 0, borderRadius: 18 }}
            exit={{ opacity: 0, scale: pos ? 0.85 : 0.98 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            style={{
              ...(pos ? { position: "fixed", left: pos.left, top: pos.top, width: W, transformOrigin: `${pos.originX}px ${pos.originY}px` } : {}),
              willChange: "transform, opacity",
              transform: "translateZ(0)",
            }}
            className={cn("border border-border bg-card p-4", pos ? "shadow-[0_12px_40px_rgba(0,0,0,0.16)]" : "w-full max-w-sm p-5")}
          >
            <div className="flex items-start gap-3">
              <span className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-full ring-4", tone.bg, tone.text, tone.ring)}>
                <Icon className="h-5 w-5" />
              </span>
              <div className="min-w-0">
                <h2 className="text-[15px] font-semibold leading-snug text-foreground">{current.title}</h2>
                {current.message && <div className="mt-1 text-[13px] leading-relaxed text-muted-foreground">{current.message}</div>}
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                title={current.cancelLabel || "Hủy (Esc)"}
                aria-label={current.cancelLabel || "Hủy"}
                onClick={() => current.resolve(false)}
                className="flex h-9 items-center gap-1.5 rounded-full border border-border bg-card px-3 text-[13px] text-foreground transition-transform hover:bg-accent active:scale-95"
              >
                <X className="h-4 w-4" />
                {current.cancelLabel && <span>{current.cancelLabel}</span>}
              </button>
              <button
                type="button"
                autoFocus
                title={`${current.confirmLabel || tone.label} (Enter)`}
                aria-label={current.confirmLabel || tone.label}
                onClick={() => current.resolve(true)}
                className={cn("flex h-9 items-center gap-1.5 rounded-full px-4 text-[13px] font-medium transition-transform active:scale-95", tone.btn)}
              >
                <Check className="h-4 w-4" />
                <span>{current.confirmLabel || tone.label}</span>
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
