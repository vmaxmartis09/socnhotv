"use client";

import React, { useEffect } from "react";
import { useRouter } from "@/i18n/routing";
import { useStudioStore } from "@/store";
import { useSocialStore } from "@/store/modules/social";
import { AgendaList } from "@/components/social/AgendaList";
import { PostComposer } from "@/components/social/PostComposer";
import { CalendarDays, ExternalLink, Plus } from "@/components/ui/icons";

export function PublishTab() {
  const router = useRouter();
  const { activeProjectId } = useStudioStore();
  const {
    calendarData,
    accounts,
    loadAll,
    openComposer,
  } = useSocialStore();

  useEffect(() => {
    if (activeProjectId) {
      loadAll(activeProjectId);
    }
  }, [activeProjectId, loadAll]);

  const items = calendarData?.items || [];

  return (
    <div className="p-3.5 space-y-4 text-xs">
      {/* Top Banner & Quick Link to Social Manager */}
      <div className="flex items-center justify-between rounded-lg border border-border bg-accent/40 p-3">
        <div className="space-y-0.5">
          <h4 className="font-semibold text-foreground text-xs flex items-center gap-1.5">
            <CalendarDays className="h-4 w-4 text-primary" />
            Social Manager
          </h4>
          <p className="text-[11px] text-muted-foreground">
            Lịch đăng 7 ngày tới ({accounts.length} kênh kết nối)
          </p>
        </div>
        <button
          onClick={() => router.push("/social")}
          className="flex items-center gap-1 rounded-md border border-border bg-background px-2.5 py-1 text-xs font-semibold text-foreground hover:bg-muted shadow-2xs"
        >
          <span>Mở toàn màn hình</span>
          <ExternalLink className="h-3 w-3" />
        </button>
      </div>

      {/* Action: Add Schedule Button */}
      <button
        onClick={() => openComposer()}
        className="w-full flex items-center justify-center gap-1.5 rounded-lg border-2 border-dashed border-border py-2 text-xs font-semibold text-foreground hover:border-primary/50 hover:bg-primary/5 transition-colors"
      >
        <Plus className="h-4 w-4 text-primary" />
        <span>+ Lên lịch xuất bản</span>
      </button>

      {/* 7 Days Agenda Preview */}
      <div className="space-y-2">
        <div className="flex items-center justify-between border-b border-border/80 pb-1.5">
          <span className="font-semibold uppercase tracking-wider text-[11px] text-muted-foreground">
            Lịch đăng tuần này
          </span>
          <span className="text-[11px] font-mono text-muted-foreground">
            {items.length} bài
          </span>
        </div>

        <AgendaList
          items={items}
          maxDays={7}
          onItemClick={() => openComposer()}
          emptyMessage="Chưa có bài viết nào được lên lịch trong 7 ngày tới."
        />
      </div>

      {/* Post Composer Drawer instance */}
      <PostComposer projectId={activeProjectId} />
    </div>
  );
}
