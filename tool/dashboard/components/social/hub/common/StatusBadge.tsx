"use client";

import React from "react";
import { cn } from "@/lib/utils";

export type HubStatusType =
  | "draft"
  | "pending_approval"
  | "scheduled"
  | "published"
  | "failed"
  | "overdue"
  | "unposted"
  | "cancelled";

interface StatusBadgeProps {
  status: HubStatusType | string;
  size?: "sm" | "md";
  className?: string;
  onClick?: () => void;
}

const CONFIG: Record<
  string,
  { label: string; icon: string; bg: string; text: string; border: string }
> = {
  draft: {
    label: "Bản nháp",
    icon: "⚪",
    bg: "bg-zinc-500/10",
    text: "text-zinc-400",
    border: "border-zinc-500/20",
  },
  unposted: {
    label: "Chưa đăng",
    icon: "⚪",
    bg: "bg-zinc-500/10",
    text: "text-zinc-400",
    border: "border-zinc-500/20",
  },
  pending_approval: {
    label: "Chờ duyệt",
    icon: "⏳",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
  },
  scheduled: {
    label: "Đã hẹn",
    icon: "🕒",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/30",
  },
  published: {
    label: "Đã đăng",
    icon: "✅",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
  },
  failed: {
    label: "Lỗi",
    icon: "⚠️",
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/30",
  },
  overdue: {
    label: "Quá hạn",
    icon: "🛑",
    bg: "bg-orange-500/10",
    text: "text-orange-400",
    border: "border-orange-500/30",
  },
  cancelled: {
    label: "Đã huỷ",
    icon: "✕",
    bg: "bg-zinc-800",
    text: "text-zinc-500",
    border: "border-zinc-700",
  },
};

export function StatusBadge({
  status,
  size = "sm",
  className,
  onClick,
}: StatusBadgeProps) {
  const norm = (status || "draft").toLowerCase();
  const cfg = CONFIG[norm] || {
    label: norm,
    icon: "•",
    bg: "bg-zinc-800",
    text: "text-zinc-400",
    border: "border-zinc-700",
  };

  return (
    <span
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1 font-medium rounded-full border transition-colors select-none",
        size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs",
        cfg.bg,
        cfg.text,
        cfg.border,
        onClick && "cursor-pointer hover:brightness-110 active:scale-95",
        className
      )}
    >
      <span className="text-[10px] leading-none">{cfg.icon}</span>
      <span>{cfg.label}</span>
    </span>
  );
}
