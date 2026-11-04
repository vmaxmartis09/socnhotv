"use client";

import React from "react";
import { useDraggable } from "@dnd-kit/core";
import { cn } from "@/lib/utils";
import type { CalendarItem, PlatformType, PostStatus } from "@/lib/api/social";

interface PostChipProps {
  item: CalendarItem;
  onClick?: (item: CalendarItem) => void;
  compact?: boolean;
}

const PLATFORM_STYLES: Record<PlatformType, { badge: string; label: string }> = {
  youtube: { badge: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20", label: "YT" },
  tiktok: { badge: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/20", label: "TT" },
  facebook: { badge: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20", label: "FB" },
  instagram: { badge: "bg-pink-500/10 text-pink-600 dark:text-pink-400 border-pink-500/20", label: "IG" },
  douyin: { badge: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20", label: "DY" },
  threads: { badge: "bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20", label: "TH" },
  x: { badge: "bg-neutral-500/10 text-neutral-600 dark:text-neutral-400 border-neutral-500/20", label: "X" },
};

const STATUS_DOTS: Record<PostStatus, string> = {
  draft: "bg-muted-foreground/60",
  pending_approval: "bg-amber-500",
  approved: "bg-emerald-500",
  scheduled: "bg-sky-500",
  publishing: "bg-indigo-500 animate-pulse",
  published: "bg-emerald-600",
  failed: "bg-rose-500",
  cancelled: "bg-zinc-400",
};

export function PostChip({ item, onClick, compact = false }: PostChipProps) {
  const isPublished = item.status === "published";
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `chip_${item.target_id}`,
    disabled: isPublished,
    data: { item },
  });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 50,
      }
    : undefined;

  const timeStr = item.scheduled_at ? item.scheduled_at.slice(11, 16) : "--:--";
  const plat = PLATFORM_STYLES[item.platform] || { badge: "bg-muted text-foreground border-border", label: item.platform };
  const dotColor = STATUS_DOTS[item.status] || "bg-muted-foreground";

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={(e) => {
        if (!isDragging && onClick) {
          e.stopPropagation();
          onClick(item);
        }
      }}
      className={cn(
        "group relative flex items-center gap-1.5 rounded-md border px-1.5 py-1 text-xs shadow-xs transition-all",
        plat.badge,
        isPublished ? "cursor-default opacity-85" : "cursor-grab active:cursor-grabbing hover:brightness-105",
        isDragging && "opacity-50 ring-2 ring-primary",
        compact ? "py-0.5 text-[11px]" : "py-1"
      )}
      title={`${item.title} (${item.platform}) - ${timeStr} [${item.status}]`}
    >
      <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", dotColor)} />
      <span className="font-mono text-[10px] font-semibold opacity-90">{timeStr}</span>
      <span className="shrink-0 rounded px-1 py-0.2 text-[9px] font-bold uppercase tracking-wider bg-background/50">
        {plat.label}
      </span>
      <span className="truncate font-medium flex-1">{item.title}</span>
    </div>
  );
}
