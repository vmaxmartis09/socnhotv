"use client";

import React, { useState, useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { useStudioStore } from "@/store";
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Clock,
  Flame,
  Plus,
  RefreshCw,
} from "@/components/ui/icons";
import { AccountChip } from "../common/AccountChip";
import { VideoThumb } from "../common/VideoThumb";
import { StatusBadge } from "../common/StatusBadge";
import { VideoPostTarget, QueueItem } from "@/lib/api/social";

interface CalendarViewProps {
  onOpenPlanWizard?: () => void;
}

export function CalendarView({ onOpenPlanWizard }: CalendarViewProps) {
  const activeProjectId = useStudioStore((s) => s.activeProjectId);
  const {
    queueData,
    loadQueue,
    accounts,
    bulkAction,
    setHubSelectedEntity,
  } = useSocialStore();

  const [currentDate, setCurrentDate] = useState(() => new Date());
  const [draggedTargetId, setDraggedTargetId] = useState<string | null>(null);
  const [draftItems, setDraftItems] = useState<QueueItem[]>([]);
  const [isLoadingDrafts, setIsLoadingDrafts] = useState(false);

  // Load upcoming/all posts and drafts
  const refreshCalendarData = React.useCallback(async () => {
    if (!activeProjectId) return;
    loadQueue(activeProjectId);

    // Also fetch drafts
    setIsLoadingDrafts(true);
    try {
      const res = await fetch(`/core/projects/${activeProjectId}/social/queue?bucket=draft`);
      if (res.ok) {
        const data = await res.json();
        setDraftItems(data.items || []);
      }
    } catch {
      // Ignore
    } finally {
      setIsLoadingDrafts(false);
    }
  }, [activeProjectId, loadQueue]);

  useEffect(() => {
    refreshCalendarData();
  }, [refreshCalendarData]);

  // Calendar calculations
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth(); // 0-based

  const daysInMonth = useMemo(() => {
    return new Date(year, month + 1, 0).getDate();
  }, [year, month]);

  const firstDayOfWeek = useMemo(() => {
    // 0 = Sunday, 1 = Monday...
    return new Date(year, month, 1).getDay();
  }, [year, month]);

  const monthLabel = useMemo(() => {
    return currentDate.toLocaleDateString("vi-VN", { month: "long", year: "numeric" });
  }, [currentDate]);

  const allPosts = queueData?.items || [];

  // Group scheduled posts by YYYY-MM-DD
  const postsByDate = useMemo(() => {
    const map: Record<string, QueueItem[]> = {};
    for (const p of allPosts) {
      if (p.scheduled_at) {
        const dStr = p.scheduled_at.slice(0, 10);
        if (!map[dStr]) map[dStr] = [];
        map[dStr].push(p);
      }
    }
    return map;
  }, [allPosts]);

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const handleDropOnDate = async (dateStr: string) => {
    if (!draggedTargetId || !activeProjectId) return;
    try {
      // Default time 11:30
      const newScheduledAt = `${dateStr}T11:30:00`;
      await bulkAction(activeProjectId, [draggedTargetId], "reschedule", {
        new_scheduled_at: newScheduledAt,
      });
      refreshCalendarData();
    } finally {
      setDraggedTargetId(null);
    }
  };

  const handlePostClick = (post: QueueItem) => {
    const targetData: VideoPostTarget = {
      target_id: post.target_id,
      post_id: post.post_id,
      account_id: post.account_id,
      platform: post.platform,
      status: post.status,
      scheduled_at: post.scheduled_at,
      caption: post.caption,
      title: post.title,
      thumb: post.thumb,
    };
    setHubSelectedEntity({
      type: "post",
      id: post.target_id,
      data: targetData,
    });
  };

  return (
    <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-hidden">
      {/* Main Calendar View Area */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden border-r border-border">
        {/* Calendar Navigation Header */}
        <div className="p-4 border-b border-border bg-card/60 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-bold text-foreground capitalize flex items-center gap-2">
              <CalendarIcon className="w-4 h-4 text-primary" />
              {monthLabel}
            </h2>
            <button
              type="button"
              onClick={handleToday}
              className="px-2.5 py-1 rounded-md text-xs font-medium border border-border bg-background hover:bg-muted transition-colors"
            >
              Hôm nay
            </button>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handlePrevMonth}
              className="p-1.5 rounded-md border border-border bg-background hover:bg-muted text-muted-foreground transition-colors"
              aria-label="Tháng trước"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={handleNextMonth}
              className="p-1.5 rounded-md border border-border bg-background hover:bg-muted text-muted-foreground transition-colors"
              aria-label="Tháng sau"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={refreshCalendarData}
              className="p-1.5 rounded-md border border-border bg-background hover:bg-muted text-muted-foreground transition-colors ml-2"
              aria-label="Tải lại lịch"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Days of week header */}
        <div className="grid grid-cols-7 border-b border-border bg-muted/30 text-center text-[11px] font-semibold text-muted-foreground py-2 shrink-0">
          <span>CN</span>
          <span>T2</span>
          <span>T3</span>
          <span>T4</span>
          <span>T5</span>
          <span>T6</span>
          <span>T7</span>
        </div>

        {/* Calendar Grid */}
        <div className="flex-1 grid grid-cols-7 grid-rows-5 md:grid-rows-6 gap-[1px] bg-border overflow-y-auto scroll-quiet">
          {/* Empty cells before month start */}
          {Array.from({ length: firstDayOfWeek }).map((_, idx) => (
            <div key={`empty-${idx}`} className="bg-card/30 p-1.5 min-h-[90px]" />
          ))}

          {/* Days in Month */}
          {Array.from({ length: daysInMonth }).map((_, idx) => {
            const dayNum = idx + 1;
            const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(dayNum).padStart(2, "0")}`;
            const postsForDay = postsByDate[dateStr] || [];
            const isToday =
              new Date().toISOString().slice(0, 10) === dateStr;

            return (
              <div
                key={dateStr}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => handleDropOnDate(dateStr)}
                className={cn(
                  "bg-card p-1.5 min-h-[95px] flex flex-col justify-between transition-colors group relative",
                  isToday && "bg-primary/5",
                  draggedTargetId && "hover:bg-primary/10"
                )}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "text-xs font-semibold px-1.5 py-0.5 rounded",
                      isToday ? "bg-primary text-primary-foreground font-bold" : "text-foreground"
                    )}
                  >
                    {dayNum}
                  </span>
                  {postsForDay.length > 0 && (
                    <span className="text-[10px] text-muted-foreground font-mono">
                      {postsForDay.length} bài
                    </span>
                  )}
                </div>

                {/* Posts in this day */}
                <div className="space-y-1 my-1 overflow-y-auto max-h-24 scroll-quiet">
                  {postsForDay.slice(0, 3).map((p) => {
                    const acc = accounts.find((a) => a.id === p.account_id);
                    const timeStr = p.scheduled_at ? p.scheduled_at.slice(11, 16) : "";

                    return (
                      <div
                        key={p.target_id}
                        draggable
                        onDragStart={() => setDraggedTargetId(p.target_id)}
                        onClick={() => handlePostClick(p)}
                        className="p-1 rounded bg-muted/80 hover:bg-muted text-[10px] border border-border/60 cursor-pointer flex items-center justify-between gap-1 transition-colors"
                      >
                        <div className="flex items-center gap-1 min-w-0">
                          <span className="font-mono text-muted-foreground">{timeStr}</span>
                          <span className="font-medium truncate">{p.title || p.video_title || "Video"}</span>
                        </div>
                        {acc && (
                          <span className="text-[9px] font-bold px-1 rounded bg-primary/10 text-primary shrink-0">
                            {acc.platform.slice(0, 2).toUpperCase()}
                          </span>
                        )}
                      </div>
                    );
                  })}
                  {postsForDay.length > 3 && (
                    <span className="text-[9px] text-muted-foreground block text-center">
                      +{postsForDay.length - 3} bài khác
                    </span>
                  )}
                </div>

                {/* Gold slot hint */}
                <div className="text-[9px] text-semantic-warning/80 flex items-center gap-0.5">
                  <Flame className="w-2.5 h-2.5" />
                  <span>11:30 · 19:30</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Draft Sidebar: Drag into calendar */}
      <div className="w-full md:w-72 bg-card/40 p-4 flex flex-col shrink-0 border-t md:border-t-0 md:border-l border-border">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
              Bản nháp chưa hẹn
            </span>
            <span className="text-[11px] font-mono text-muted-foreground">({draftItems.length})</span>
          </div>
          <button
            type="button"
            onClick={refreshCalendarData}
            className="p-1 text-muted-foreground hover:text-foreground"
            aria-label="Tải lại nháp"
          >
            <RefreshCw className={cn("w-3 h-3", isLoadingDrafts && "animate-spin")} />
          </button>
        </div>

        <p className="text-[11px] text-muted-foreground mt-2 mb-3">
          Kéo thả các bản nháp vào ô ngày trên lịch để tự động hẹn giờ đăng.
        </p>

        <div className="flex-1 overflow-y-auto space-y-2 pr-1 scroll-quiet">
          {draftItems.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted-foreground border border-dashed border-border rounded-lg p-3">
              Không có bản nháp nào cần hẹn giờ.
            </div>
          ) : (
            draftItems.map((draft) => (
              <div
                key={draft.target_id}
                draggable
                onDragStart={() => setDraggedTargetId(draft.target_id)}
                onClick={() => handlePostClick(draft)}
                className="p-2.5 rounded-lg border border-border bg-card hover:border-primary/50 cursor-grab active:cursor-grabbing transition-all text-xs space-y-1.5 group shadow-sm"
              >
                <div className="flex items-center gap-2">
                  <VideoThumb
                    thumb={draft.thumb || draft.thumbnail}
                    title={draft.title || draft.video_title}
                    className="w-10 h-7 rounded"
                  />
                  <div className="min-w-0 flex-1">
                    <span className="font-semibold text-foreground line-clamp-1 group-hover:text-primary">
                      {draft.title || draft.video_title || "Bản nháp video"}
                    </span>
                    <span className="text-[10px] text-muted-foreground font-mono">
                      {draft.account_name || draft.platform}
                    </span>
                  </div>
                </div>
                <div className="text-[10px] text-muted-foreground line-clamp-2">
                  {draft.caption || "Chưa có caption"}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
