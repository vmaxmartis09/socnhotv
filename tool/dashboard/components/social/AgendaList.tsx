"use client";

import React from "react";
import { format, isToday, isTomorrow, parseISO } from "date-fns";
import { vi } from "date-fns/locale";
import { CalendarItem } from "@/lib/api/social";
import { PostChip } from "./PostChip";
import { Calendar, Film } from "@/components/ui/icons";

interface AgendaListProps {
  items: CalendarItem[];
  onItemClick?: (item: CalendarItem) => void;
  emptyMessage?: string;
  maxDays?: number;
}

export function AgendaList({
  items,
  onItemClick,
  emptyMessage = "Không có bài viết nào được lên lịch.",
  maxDays,
}: AgendaListProps) {
  // Sort items by scheduled_at ascending
  const sorted = [...items].sort((a, b) => {
    const timeA = a.scheduled_at || "9999";
    const timeB = b.scheduled_at || "9999";
    return timeA.localeCompare(timeB);
  });

  // Group by Date string (YYYY-MM-DD)
  const groups: Record<string, CalendarItem[]> = {};
  for (const item of sorted) {
    const dStr = item.scheduled_at ? item.scheduled_at.slice(0, 10) : "Chưa lên lịch";
    if (!groups[dStr]) groups[dStr] = [];
    groups[dStr].push(item);
  }

  let groupKeys = Object.keys(groups);
  if (maxDays && groupKeys.length > maxDays) {
    groupKeys = groupKeys.slice(0, maxDays);
  }

  if (groupKeys.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center text-sm text-muted-foreground border border-dashed border-border rounded-xl">
        <Calendar className="h-8 w-8 mb-2 opacity-40" />
        <p>{emptyMessage}</p>
      </div>
    );
  }

  const formatDayHeader = (dateStr: string) => {
    if (dateStr === "Chưa lên lịch") return "Chưa ấn định ngày";
    try {
      const date = parseISO(dateStr);
      if (isToday(date)) return `Hôm nay · ${format(date, "dd/MM/yyyy")}`;
      if (isTomorrow(date)) return `Ngày mai · ${format(date, "dd/MM/yyyy")}`;
      return format(date, "EEEE, dd/MM/yyyy", { locale: vi });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-4">
      {groupKeys.map((dateStr) => {
        const dayItems = groups[dateStr];
        return (
          <div key={dateStr} className="space-y-2">
            <div className="flex items-center gap-2 border-b border-border/60 pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <Calendar className="h-3.5 w-3.5" />
              <span>{formatDayHeader(dateStr)}</span>
              <span className="ml-auto rounded-full bg-muted px-1.5 py-0.2 text-[10px] font-normal">
                {dayItems.length} bài
              </span>
            </div>
            <div className="grid gap-2">
              {dayItems.map((item) => (
                <div
                  key={item.target_id}
                  onClick={() => onItemClick && onItemClick(item)}
                  className="flex items-center gap-3 rounded-lg border border-border bg-card p-2.5 shadow-2xs hover:border-primary/40 transition-colors cursor-pointer"
                >
                  {item.thumb ? (
                    <img
                      src={item.thumb}
                      alt=""
                      className="h-10 w-10 rounded-md object-cover border border-border shrink-0"
                    />
                  ) : (
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
                      <Film className="h-5 w-5 opacity-50" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <PostChip item={item} compact />
                    </div>
                    {item.caption && (
                      <p className="line-clamp-1 text-xs text-muted-foreground">
                        {item.caption}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
