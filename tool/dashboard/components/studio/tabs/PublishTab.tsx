"use client";

import React, { useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";
import { useStudioStore } from "@/store";
import { useSocialStore, HubView } from "@/store/modules/social";
import {
  Calendar,
  Clock,
  Zap,
  Plus,
  RefreshCw,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  Film,
  Smartphone,
} from "@/components/ui/icons";
import { VideoThumb } from "@/components/social/hub/common/VideoThumb";
import { AccountChip } from "@/components/social/hub/common/AccountChip";
import { StatusBadge } from "@/components/social/hub/common/StatusBadge";
import dynamic from "next/dynamic";

const PublishCenterModal = dynamic(
  () => import("@/components/social/PublishCenterModal").then((m) => m.PublishCenterModal),
  { ssr: false }
);

export function PublishTab() {
  const activeProjectId = useStudioStore((s) => s.activeProjectId);
  const {
    accounts,
    queueData,
    loadAccounts,
    loadQueue,
    openHub,
    setQueueBucket,
    isPublishCenterOpen,
    openPublishCenter,
    closePublishCenter,
  } = useSocialStore();

  useEffect(() => {
    if (activeProjectId) {
      loadAccounts(activeProjectId);
      loadQueue(activeProjectId, "upcoming");
    }
  }, [activeProjectId, loadAccounts, loadQueue]);

  const summary = queueData?.summary;
  const upcomingCount = summary?.upcoming_count ?? 0;
  const draftCount = summary?.draft_count ?? 0;
  const pendingCount = summary?.pending_approval_count ?? 0;
  const overdueCount = summary?.overdue_count ?? 0;
  const failedCount = summary?.failed_count ?? 0;

  // 5 genuine upcoming items (scheduled_at in future)
  const upcomingPosts = useMemo(() => {
    const items = queueData?.items || [];
    return items
      .filter((item) => item.scheduled_at && item.status === "scheduled")
      .slice(0, 5);
  }, [queueData]);

  const handleOpenHubView = (view: HubView, bucket?: "upcoming" | "draft" | "pending_approval" | "overdue" | "failed") => {
    if (bucket) {
      setQueueBucket(bucket);
    }
    openHub({ view });
  };

  return (
    <div className="flex h-full flex-col p-3.5 space-y-4 text-xs select-none overflow-y-auto">
      {/* 1. Header Banner & Open Social Hub Button */}
      <div className="rounded-xl border border-border bg-gradient-to-br from-card to-muted/40 p-3.5 shadow-2xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Calendar className="h-4 w-4" />
            </div>
            <div>
              <h4 className="font-bold text-foreground text-xs leading-none">
                Lịch Đăng Social
              </h4>
              <p className="text-[10px] text-muted-foreground mt-0.5 font-mono">
                {accounts.length}/10 tài khoản kết nối
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => activeProjectId && loadQueue(activeProjectId, "upcoming")}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground"
            aria-label="Tải lại"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Big Prominent "Mở Trung tâm Social" button */}
        <button
          type="button"
          onClick={() => handleOpenHubView("overview")}
          className="w-full py-2.5 px-3 rounded-lg bg-primary text-primary-foreground font-semibold text-xs flex items-center justify-center gap-2 hover:bg-primary/90 transition-all shadow-sm"
        >
          <Zap className="h-4 w-4" />
          Mở Trung tâm Social (Toàn màn hình)
        </button>

        {/* 4 Clickable Metric Pills */}
        <div className="grid grid-cols-2 gap-1.5 pt-1">
          <button
            type="button"
            onClick={() => handleOpenHubView("queue", "upcoming")}
            className="p-2 rounded-lg bg-background/80 hover:bg-background border border-border/60 text-left transition-colors flex items-center justify-between"
          >
            <span className="text-[11px] text-muted-foreground">Sắp tới</span>
            <span className="font-bold text-blue-400 font-mono text-xs">{upcomingCount}</span>
          </button>

          <button
            type="button"
            onClick={() => handleOpenHubView("queue", "draft")}
            className="p-2 rounded-lg bg-background/80 hover:bg-background border border-border/60 text-left transition-colors flex items-center justify-between"
          >
            <span className="text-[11px] text-muted-foreground">Bản nháp</span>
            <span className="font-bold text-zinc-400 font-mono text-xs">{draftCount}</span>
          </button>

          <button
            type="button"
            onClick={() => handleOpenHubView("queue", "pending_approval")}
            className="p-2 rounded-lg bg-background/80 hover:bg-background border border-border/60 text-left transition-colors flex items-center justify-between"
          >
            <span className="text-[11px] text-muted-foreground">Chờ duyệt</span>
            <span className="font-bold text-amber-400 font-mono text-xs">{pendingCount}</span>
          </button>

          <button
            type="button"
            onClick={() => handleOpenHubView("queue", "overdue")}
            className="p-2 rounded-lg bg-background/80 hover:bg-background border border-border/60 text-left transition-colors flex items-center justify-between"
          >
            <span className="text-[11px] text-muted-foreground">Quá hạn/Lỗi</span>
            <span className="font-bold text-rose-400 font-mono text-xs">{overdueCount + failedCount}</span>
          </button>
        </div>
      </div>

      {/* 2. Quick Plan Action */}
      <button
        type="button"
        onClick={() => openPublishCenter("plan")}
        className="w-full py-2 px-3 rounded-lg border border-border bg-card hover:bg-muted text-foreground font-medium text-xs flex items-center justify-center gap-1.5 transition-colors shadow-2xs"
      >
        <Plus className="h-3.5 w-3.5 text-primary" />
        Lên kế hoạch đăng mới
      </button>

      {/* 3. Section: 5 Bài Sắp Đăng */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            5 Bài sắp đăng tới
          </span>
          {upcomingPosts.length > 0 && (
            <button
              type="button"
              onClick={() => handleOpenHubView("queue", "upcoming")}
              className="text-[11px] text-primary hover:underline flex items-center gap-0.5"
            >
              Xem tất cả
              <ExternalLink className="h-3 w-3" />
            </button>
          )}
        </div>

        {upcomingPosts.length === 0 ? (
          <div className="py-6 px-3 text-center border border-dashed border-border rounded-xl bg-card/30 space-y-2">
            <Clock className="h-6 w-6 text-muted-foreground/60 mx-auto" />
            <p className="text-xs text-muted-foreground">Chưa có bài đăng nào được hẹn giờ</p>
            <button
              type="button"
              onClick={() => openPublishCenter("plan")}
              className="px-3 py-1 rounded bg-primary/10 text-primary text-[11px] font-medium hover:bg-primary/20 transition-colors"
            >
              + Lên lịch ngay
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {upcomingPosts.map((item) => {
              const acc = accounts.find((a) => a.id === item.account_id);
              const timeStr = item.scheduled_at
                ? new Date(item.scheduled_at).toLocaleTimeString("vi-VN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "";
              const dateStr = item.scheduled_at
                ? new Date(item.scheduled_at).toLocaleDateString("vi-VN", {
                    day: "2-digit",
                    month: "2-digit",
                  })
                : "";

              return (
                <div
                  key={item.target_id}
                  onClick={() => handleOpenHubView("queue", "upcoming")}
                  className="flex items-center gap-2.5 p-2 rounded-lg border border-border bg-card hover:border-primary/40 cursor-pointer transition-colors"
                >
                  <VideoThumb
                    thumb={item.thumbnail}
                    title={item.video_title}
                    className="w-12 h-8 rounded shrink-0"
                  />
                  <div className="min-w-0 flex-1">
                    <span className="font-semibold text-foreground line-clamp-1 text-xs">
                      {item.video_title || "Video"}
                    </span>
                    <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-mono mt-0.5">
                      <span>{dateStr} {timeStr}</span>
                      {acc && <span>· {acc.platform.toUpperCase()}</span>}
                    </div>
                  </div>
                  <StatusBadge status={item.status} size="sm" />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 4. Section: Tài khoản kết nối */}
      <div className="space-y-2 pt-1 border-t border-border/50">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Tài khoản kết nối ({accounts.length}/10)
          </span>
          <button
            type="button"
            onClick={() => handleOpenHubView("accounts")}
            className="text-[11px] text-primary hover:underline flex items-center gap-0.5"
          >
            Quản lý
            <ExternalLink className="h-3 w-3" />
          </button>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {accounts.map((acc) => (
            <AccountChip
              key={acc.id}
              account={acc}
              size="sm"
              onClick={() => handleOpenHubView("accounts")}
            />
          ))}
          {accounts.length < 10 && (
            <button
              type="button"
              onClick={() => handleOpenHubView("accounts")}
              className="px-2 py-0.5 rounded-full border border-dashed border-border hover:border-primary/50 text-[10px] text-muted-foreground hover:text-primary transition-colors"
            >
              + Thêm
            </button>
          )}
        </div>
      </div>

      {/* Large S1 Publish Center Modal if opened */}
      {isPublishCenterOpen && (
        <PublishCenterModal
          projectId={activeProjectId || "soc-nho-tv"}
          isOpen={isPublishCenterOpen}
          onClose={closePublishCenter}
        />
      )}
    </div>
  );
}
