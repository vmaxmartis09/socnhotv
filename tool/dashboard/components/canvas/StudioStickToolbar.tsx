"use client";

import { enterOnce } from "@/lib/motion";
import React from "react";
import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import {
  Plus,
  MousePointer2,
  Hand,
  Copy,
  Trash2,
  Undo2,
  Redo2,
  Layers,
  InfinityIcon,
  ArrowRight,
} from "@/components/ui/icons";
import { cn } from "@/lib/utils";
import { TOOL_KEYS } from "@/lib/shortcuts";

export type CanvasMode = "select" | "pan";

interface Props {
  mode: CanvasMode;
  onMode: (m: CanvasMode) => void;
  addOpen: boolean;
  onToggleAdd: () => void;
  /** Popover chọn loại node, hiện bên phải nút + */
  addMenu: React.ReactNode;
  hasSelection: boolean;
  onStepBefore: () => void;
  onStepAfter: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onGroup: () => void;
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  snap: boolean;
  onToggleSnap: () => void;
}

function Btn({
  label,
  keys,
  onClick,
  active,
  disabled,
  children,
}: {
  label: string;
  /** Phím tắt hiện trong tooltip */
  keys?: string;
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <motion.button
      type="button"
      title={keys ? `${label} (${keys})` : label}
      aria-label={label}
      aria-pressed={active}
      disabled={disabled}
      onClick={onClick}
      whileTap={{ scale: 0.94 }}
      transition={{ duration: 0.12 }}
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-full transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "disabled:pointer-events-none disabled:opacity-30",
        active
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:bg-accent hover:text-foreground"
      )}
    >
      {children}
    </motion.button>
  );
}

const Sep = () => <div className="my-0.5 h-px w-5 bg-border" aria-hidden="true" />;

/** Thanh công cụ stick dọc bên trái canvas, chỉ dùng biểu tượng (tên hiện khi rê chuột). */
export function StudioStickToolbar(p: Props) {
  const t = useTranslations("canvas");
  const i = "h-4 w-4";
  return (
    <motion.div
      initial={enterOnce("stick", { opacity: 0, x: -12 })}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="relative"
    >
      <div
        role="toolbar"
        aria-orientation="vertical"
        aria-label="Studio"
        className="flex flex-col items-center gap-0.5 rounded-full border border-border bg-card px-1 py-1.5"
      >
        <Btn label={t("tools.add")} keys={TOOL_KEYS.add} active={p.addOpen} onClick={p.onToggleAdd}>
          <Plus className={i} />
        </Btn>
        <Btn label={t("tools.select")} keys={TOOL_KEYS.select} active={p.mode === "select"} onClick={() => p.onMode("select")}>
          <MousePointer2 className={i} />
        </Btn>
        <Btn label={t("tools.pan")} keys={TOOL_KEYS.pan} active={p.mode === "pan"} onClick={() => p.onMode("pan")}>
          <Hand className={i} />
        </Btn>
        <Sep />
        <Btn label={t("addStepBefore")} keys={TOOL_KEYS.stepBefore} disabled={!p.hasSelection} onClick={p.onStepBefore}>
          <ArrowRight className={cn(i, "rotate-180")} />
        </Btn>
        <Btn label={t("addStepAfter")} keys={TOOL_KEYS.stepAfter} disabled={!p.hasSelection} onClick={p.onStepAfter}>
          <ArrowRight className={i} />
        </Btn>
        <Btn label={t("tools.duplicate")} keys={TOOL_KEYS.duplicate} disabled={!p.hasSelection} onClick={p.onDuplicate}>
          <Copy className={i} />
        </Btn>
        <Btn label={t("tools.delete")} keys={TOOL_KEYS.delete} disabled={!p.hasSelection} onClick={p.onDelete}>
          <Trash2 className={i} />
        </Btn>
        <Btn label={t("tools.group")} keys={TOOL_KEYS.group} onClick={p.onGroup}>
          <Layers className={i} />
        </Btn>
        <Sep />
        <Btn label={t("tools.undo")} keys={TOOL_KEYS.undo} disabled={!p.canUndo} onClick={p.onUndo}>
          <Undo2 className={i} />
        </Btn>
        <Btn label={t("tools.redo")} keys={TOOL_KEYS.redo} disabled={!p.canRedo} onClick={p.onRedo}>
          <Redo2 className={i} />
        </Btn>
        <div className="relative">
          <Btn label={t("tools.snap")} keys={TOOL_KEYS.snap} active={p.snap} onClick={p.onToggleSnap}>
            <InfinityIcon className={i} />
          </Btn>
          {p.snap && (
            <span className="pointer-events-none absolute -right-2 -top-0.5 rounded bg-primary px-1 text-[9px] font-semibold leading-4 text-primary-foreground">
              ON
            </span>
          )}
        </div>
      </div>
      {p.addOpen && <div className="absolute left-12 top-0">{p.addMenu}</div>}
    </motion.div>
  );
}
