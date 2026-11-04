"use client";

import React, { useEffect, useState, useMemo } from "react";
import { format, isToday, isTomorrow, parseISO } from "date-fns";
import { vi } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { useStudioStore } from "@/store";
import { useSocialStore } from "@/store/modules/social";
import { socialApi, SocialAccount, QueueItem, PlatformType } from "@/lib/api/social";
import { PostRow } from "@/components/social/PostRow";
import { PublishCenterModal } from "@/components/social/PublishCenterModal";
import { AccountDetailSheet } from "@/components/social/AccountDetailSheet";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock,
  ExternalLink,
  Layers,
  Plus,
  RefreshCw,
  Settings,
  ShieldCheck,
  Video,
  X,
} from "@/components/social/icons";

export function PublishTab() {
  const { activeProjectId } = useStudioStore();
  const {
    accounts,
    queueData,
    queueBucket,
    setQueueBucket,
    loadAccounts,
    loadQueue,
    loadAll,
    isPublishCenterOpen,
    publishCenterTab,
    openPublishCenter,
    closePublishCenter,
    openComposer,
  } = useSocialStore();

  const [selectedAccountFilter, setSelectedAccountFilter] = useState<string>("all");
  const [selectedPlatformFilter, setSelectedPlatformFilter] = useState<string>("all");

  // Account Sheet State
  const [editingAccount, setEditingAccount] = useState<SocialAccount | null>(null);
  const [isAccountSheetOpen, setIsAccountSheetOpen] = useState<boolean>(false);
  const [isCreatingNewAccount, setIsCreatingNewAccount] = useState<boolean>(false);

  // Initial load
  useEffect(() => {
    if (activeProjectId) {
      loadAll(activeProjectId);
      loadQueue(activeProjectId, queueBucket);
    }
  }, [activeProjectId, queueBucket, loadAll, loadQueue]);

  // Handle Tab Switch
  const handleTabChange = (bucket: "upcoming" | "overdue" | "published" | "failed") => {
    setQueueBucket(bucket);
    if (activeProjectId) {
      loadQueue(activeProjectId, bucket);
    }
  };

  const summary = queueData?.summary || {
    accounts_count: accounts.length,
    max_accounts: 10,
    pending_approval_count: 0,
    overdue_count: 0,
    upcoming_count: 0,
    published_count: 0,
    failed_count: 0,
    next_post_time: null,
  };

  const items = queueData?.items || [];

  // Filter items by selected account/platform if any
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (selectedAccountFilter !== "all" && item.account_id !== selectedAccountFilter) return false;
      if (selectedPlatformFilter !== "all" && item.platform !== selectedPlatformFilter) return false;
      return true;
    });
  }, [items, selectedAccountFilter, selectedPlatformFilter]);

  // Group items by date string
  const groupedItems = useMemo(() => {
    const groups: Record<string, QueueItem[]> = {};
    for (const item of filteredItems) {
      let groupKey = "Chưa hẹn giờ";
      if (item.scheduled_at) {
        try {
          const dt = parseISO(item.scheduled_at);
          if (isToday(dt)) {
            groupKey = "Hôm nay, " + format(dt, "dd/MM", { locale: vi });
          } else if (isTomorrow(dt)) {
            groupKey = "Ngày mai, " + format(dt, "dd/MM", { locale: vi });
          } else {
            groupKey = format(dt, "EEEE, dd/MM/yyyy", { locale: vi });
          }
        } catch {
          groupKey = item.scheduled_at.slice(0, 10);
        }
      }
      if (!groups[groupKey]) groups[groupKey] = [];
      groups[groupKey].push(item);
    }
    return groups;
  }, [filteredItems]);

  // Actions on PostRow
  const handleOpenItem = (item: QueueItem) => {
    openPublishCenter("calendar");
  };

  const handlePublishNow = async (item: QueueItem) => {
    if (!activeProjectId) return;
    try {
      await socialApi.publishNow(activeProjectId, item.post_id);
      await loadQueue(activeProjectId, queueBucket);
    } catch (err: any) {
      alert(`Lỗi xuất bản ngay: ${err.message}`);
    }
  };

  const handleMarkPublished = async (item: QueueItem) => {
    if (!activeProjectId) return;
    const url = window.prompt("Nhập URL bài viết đã đăng trên mạng xã hội:");
    if (!url) return;
    try {
      await socialApi.markPublished(activeProjectId, item.post_id, item.target_id, url);
      await loadQueue(activeProjectId, queueBucket);
    } catch (err: any) {
      alert(`Lỗi cập nhật: ${err.message}`);
    }
  };

  const handleDownloadPackage = (item: QueueItem) => {
    if (!activeProjectId) return;
    window.open(socialApi.getPackageZipUrl(activeProjectId, item.post_id, item.platform), "_blank");
  };

  const handleCancelPost = async (item: QueueItem) => {
    if (!activeProjectId) return;
    try {
      await socialApi.cancelPost(activeProjectId, item.post_id);
      await loadQueue(activeProjectId, queueBucket);
    } catch (err: any) {
      alert(`Lỗi hủy lịch: ${err.message}`);
    }
  };

  const isFullAccounts = accounts.length >= 10;

  return (
    <div className="flex h-full flex-col p-3.5 space-y-3.5 text-xs select-none overflow-y-auto">
      {/* 1. Header Banner & Status Strip */}
      <div className="rounded-xl border border-border bg-card p-3 shadow-2xs space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <CalendarDays className="h-4 w-4" />
            </div>
            <div>
              <h4 className="font-bold text-foreground text-xs leading-none">
                Quản lý Xuất bản & Đăng bài
              </h4>
              <p className="text-[10px] text-muted-foreground mt-0.5 font-mono">
                {accounts.length}/10 tài khoản đa kênh
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => openPublishCenter("calendar")}
            className="flex items-center gap-1 rounded-lg border border-border bg-background px-2.5 py-1 text-[11px] font-semibold text-foreground hover:bg-accent transition-colors shadow-2xs"
          >
            <CalendarDays className="h-3.5 w-3.5 text-primary" />
            <span>Xem Lịch</span>
          </button>
        </div>

        {/* Dynamic Status Strip */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-border/60 text-[11px]">
          {/* Accounts indicator */}
          <span
            onClick={() => {
              setIsCreatingNewAccount(true);
              setIsAccountSheetOpen(true);
            }}
            className="cursor-pointer hover:underline font-semibold text-foreground"
          >
            {summary.accounts_count}/10 tài khoản
          </span>
          <span className="text-muted-foreground/40">·</span>

          {/* Pending approvals indicator */}
          <span
            onClick={() => handleTabChange("upcoming")}
            className={cn(
              "cursor-pointer hover:underline font-semibold",
              summary.pending_approval_count > 0 ? "text-amber-500" : "text-muted-foreground"
            )}
          >
            {summary.pending_approval_count} chờ duyệt
          </span>
          <span className="text-muted-foreground/40">·</span>

          {/* Overdue indicator */}
          <span
            onClick={() => handleTabChange("overdue")}
            className={cn(
              "cursor-pointer hover:underline font-semibold",
              summary.overdue_count > 0 ? "text-rose-500" : "text-muted-foreground"
            )}
          >
            {summary.overdue_count} quá hạn
          </span>
          <span className="text-muted-foreground/40">·</span>

          {/* Next Post indicator */}
          <span className="text-muted-foreground font-mono">
            {summary.next_post_time ? `bài kế tiếp ${summary.next_post_time}` : "Không có bài kế tiếp"}
          </span>
        </div>
      </div>

      {/* Primary Action Button: Open Publish Center Wizard */}
      <button
        type="button"
        onClick={() => openPublishCenter("plan")}
        className="w-full flex items-center justify-center gap-2 rounded-xl bg-primary py-2.5 text-xs font-bold text-primary-foreground hover:bg-primary/90 transition-colors shadow-md cursor-pointer"
      >
        <Plus className="h-4 w-4" />
        <span>+ Lên kế hoạch đăng</span>
      </button>

      {/* 2. Accounts Horizontal Scrollable Bar */}
      <section className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="font-semibold uppercase tracking-wider text-[10px] text-muted-foreground">
            Tài khoản mạng xã hội ({accounts.length}/10)
          </span>
          {isFullAccounts && (
            <span className="text-[10px] font-semibold text-amber-500">
              Đã đủ 10 tài khoản
            </span>
          )}
        </div>

        {/* Scrollable chip row */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1.5 scrollbar-none">
          {accounts.map((acc) => {
            const isConnected = acc.status === "connected";
            const isManual = acc.auth?.mode === "manual";
            const isExpired = acc.status === "expired";

            return (
              <div
                key={acc.id}
                onClick={() => {
                  setEditingAccount(acc);
                  setIsCreatingNewAccount(false);
                  setIsAccountSheetOpen(true);
                }}
                className={cn(
                  "group relative flex shrink-0 items-center gap-2 rounded-xl border border-border bg-card px-2.5 py-1.5 cursor-pointer hover:border-primary/50 transition-all shadow-2xs select-none max-w-[170px]",
                  selectedAccountFilter === acc.id ? "border-primary bg-primary/10" : ""
                )}
              >
                {/* Avatar / Platform Badge */}
                <div className="relative flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-accent text-[10px] font-bold uppercase text-foreground">
                  {acc.avatar ? (
                    <img src={acc.avatar} alt="Avatar" className="h-full w-full rounded-lg object-cover" />
                  ) : (
                    acc.platform.slice(0, 2)
                  )}
                  {/* Status Colored Dot */}
                  <span
                    title={isExpired ? "OAuth hết hạn" : isConnected ? "Đang kết nối" : "Thủ công"}
                    className={cn(
                      "absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full ring-1 ring-card",
                      isExpired ? "bg-rose-500" : isConnected ? "bg-emerald-500" : "bg-amber-500"
                    )}
                  />
                </div>

                {/* Handle / Name */}
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-foreground truncate" title={acc.display_name}>
                    {acc.display_name || acc.handle}
                  </p>
                  <p className="text-[9px] text-muted-foreground truncate font-mono">
                    {acc.handle}
                  </p>
                </div>
              </div>
            );
          })}

          {/* Add Account Dashed Button */}
          {!isFullAccounts ? (
            <button
              type="button"
              onClick={() => {
                setEditingAccount(null);
                setIsCreatingNewAccount(true);
                setIsAccountSheetOpen(true);
              }}
              className="flex shrink-0 items-center gap-1.5 rounded-xl border-2 border-dashed border-border px-3 py-1.5 text-[11px] font-semibold text-muted-foreground hover:border-primary/50 hover:bg-primary/5 hover:text-foreground transition-all"
            >
              <Plus className="h-3.5 w-3.5 text-primary" />
              <span>+ Thêm</span>
            </button>
          ) : (
            <div className="flex shrink-0 items-center gap-1 rounded-xl bg-muted px-2.5 py-1.5 text-[10px] font-semibold text-muted-foreground">
              Đã đủ 10
            </div>
          )}
        </div>
      </section>

      {/* 3. Queue Tabs & PostRow List */}
      <section className="space-y-2 pt-1 border-t border-border flex-1 flex flex-col">
        {/* Queue Sub-tabs */}
        <div className="flex items-center justify-between border-b border-border/60 pb-1.5">
          <div className="flex items-center gap-1 rounded-xl bg-muted/60 p-0.5 text-[11px]">
            {[
              { key: "upcoming", label: "Sắp tới", count: summary.upcoming_count },
              { key: "overdue", label: "Quá hạn", count: summary.overdue_count },
              { key: "published", label: "Đã đăng", count: summary.published_count },
              { key: "failed", label: "Lỗi", count: summary.failed_count },
            ].map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => handleTabChange(t.key as any)}
                className={cn(
                  "flex items-center gap-1 rounded-lg px-2.5 py-1 font-semibold transition-all",
                  queueBucket === t.key
                    ? "bg-background text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <span>{t.label}</span>
                {t.count > 0 && (
                  <span
                    className={cn(
                      "rounded-full px-1.5 py-0.2 text-[9px] font-bold font-mono",
                      t.key === "overdue" && t.count > 0
                        ? "bg-rose-500 text-white"
                        : t.key === "upcoming"
                        ? "bg-primary/20 text-primary"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    {t.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => {
              if (activeProjectId) loadQueue(activeProjectId, queueBucket);
            }}
            title="Làm mới hàng đợi"
            className="flex h-6 w-6 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Grouped Queue Items */}
        <div className="space-y-3 flex-1 overflow-y-auto">
          {filteredItems.length === 0 ? (
            /* Clean Empty State */
            <div className="py-12 text-center space-y-3 rounded-2xl border-2 border-dashed border-border bg-card/40 p-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted text-muted-foreground mx-auto">
                <Video className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-semibold text-foreground">
                  {queueBucket === "upcoming"
                    ? "Chưa có bài viết nào được lên lịch sắp tới."
                    : queueBucket === "overdue"
                    ? "Không có bài viết nào bị quá hạn."
                    : queueBucket === "published"
                    ? "Chưa có bài viết nào được xuất bản."
                    : "Không có bài viết nào bị lỗi."}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  Bấm nút bên dưới để chọn video và lên lịch đăng bài đa nền tảng
                </p>
              </div>

              <div className="flex items-center justify-center gap-2 pt-1">
                {accounts.length === 0 ? (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingAccount(null);
                      setIsCreatingNewAccount(true);
                      setIsAccountSheetOpen(true);
                    }}
                    className="rounded-xl bg-primary px-3.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-2xs"
                  >
                    + Thêm tài khoản đầu tiên
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => openPublishCenter("plan")}
                    className="rounded-xl bg-primary px-3.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-2xs"
                  >
                    + Lên lịch video ngay
                  </button>
                )}
              </div>
            </div>
          ) : (
            Object.entries(groupedItems).map(([dateLabel, groupList]) => (
              <div key={dateLabel} className="space-y-1.5">
                <div className="sticky top-0 z-10 flex items-center justify-between bg-background/90 backdrop-blur-xs py-1 text-[11px] font-bold text-foreground">
                  <span className="flex items-center gap-1.5">
                    <Clock className="h-3 w-3 text-primary" />
                    {dateLabel}
                  </span>
                  <span className="text-[10px] font-normal text-muted-foreground font-mono">
                    {groupList.length} bài
                  </span>
                </div>

                <div className="space-y-1.5">
                  {groupList.map((item) => (
                    <PostRow
                      key={item.target_id}
                      item={item}
                      onOpen={handleOpenItem}
                      onEdit={handleOpenItem}
                      onPublishNow={handlePublishNow}
                      onMarkPublished={handleMarkPublished}
                      onDownloadPackage={handleDownloadPackage}
                      onCancel={handleCancelPost}
                    />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Modals */}
      {/* 1. Large Publish Center Modal (5-Step Plan + Calendar View) */}
      <PublishCenterModal
        projectId={activeProjectId}
        isOpen={isPublishCenterOpen}
        initialTab={publishCenterTab}
        onClose={closePublishCenter}
      />

      {/* 2. Account Detail / Create Sheet */}
      <AccountDetailSheet
        projectId={activeProjectId}
        isOpen={isAccountSheetOpen}
        account={editingAccount}
        isNew={isCreatingNewAccount}
        totalAccountsCount={accounts.length}
        onClose={() => setIsAccountSheetOpen(false)}
        onSaved={() => {
          if (activeProjectId) {
            loadAccounts(activeProjectId);
            loadQueue(activeProjectId, queueBucket);
          }
        }}
      />
    </div>
  );
}
