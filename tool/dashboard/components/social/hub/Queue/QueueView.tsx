"use client";

import React, { useState, useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";
import { useSocialStore, HubQueueBucket } from "@/store/modules/social";
import { useStudioStore } from "@/store";
import {
  Search,
  Filter,
  CheckCircle,
  Clock,
  AlertCircle,
  Calendar,
  RefreshCw,
  Trash2,
  MoreHorizontal,
  ExternalLink,
  Zap,
} from "@/components/ui/icons";
import { VideoThumb } from "../common/VideoThumb";
import { StatusBadge } from "../common/StatusBadge";
import { AccountChip } from "../common/AccountChip";
import { QueueItem, VideoPostTarget } from "@/lib/api/social";

interface QueueViewProps {
  onRefresh?: () => void;
}

const TABS: { id: HubQueueBucket; label: string; icon: string }[] = [
  { id: "upcoming", label: "Đã hẹn", icon: "🕒" },
  { id: "draft", label: "Bản nháp", icon: "⚪" },
  { id: "pending_approval", label: "Chờ duyệt", icon: "⏳" },
  { id: "overdue", label: "Quá hạn", icon: "⚠️" },
  { id: "failed", label: "Lỗi", icon: "❌" },
  { id: "published", label: "Đã đăng", icon: "✅" },
];

export function QueueView({ onRefresh }: QueueViewProps) {
  const activeProjectId = useStudioStore((s) => s.activeProjectId);
  const {
    queueData,
    queueBucket,
    setQueueBucket,
    loadQueue,
    loading: isLoadingQueue,
    accounts,
    bulkAction,
    setHubSelectedEntity,
    hubSelectedEntity,
  } = useSocialStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [accountFilter, setAccountFilter] = useState("all");
  const [platformFilter, setPlatformFilter] = useState("all");
  const [selectedTargetIds, setSelectedTargetIds] = useState<string[]>([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [targetAccountForDuplicate, setTargetAccountForDuplicate] = useState("");

  useEffect(() => {
    if (activeProjectId) {
      loadQueue(activeProjectId, queueBucket);
    }
  }, [activeProjectId, queueBucket, loadQueue]);

  const items = queueData?.items || [];
  const summary = queueData?.summary;

  // Filter items
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = item.video_title?.toLowerCase().includes(q);
        const matchesCaption = item.caption?.toLowerCase().includes(q);
        const matchesAccount = item.account_name?.toLowerCase().includes(q);
        if (!matchesTitle && !matchesCaption && !matchesAccount) return false;
      }
      if (accountFilter !== "all" && item.account_id !== accountFilter) return false;
      if (platformFilter !== "all" && item.platform !== platformFilter) return false;
      return true;
    });
  }, [items, searchQuery, accountFilter, platformFilter]);

  const handleTabChange = (bucket: HubQueueBucket) => {
    setQueueBucket(bucket);
    setSelectedTargetIds([]);
  };

  const handleToggleSelect = (targetId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedTargetIds((prev) =>
      prev.includes(targetId) ? prev.filter((id) => id !== targetId) : [...prev, targetId]
    );
  };

  const handleSelectAll = () => {
    if (selectedTargetIds.length === filteredItems.length) {
      setSelectedTargetIds([]);
    } else {
      setSelectedTargetIds(filteredItems.map((item) => item.target_id));
    }
  };

  const handleBulkApprove = async () => {
    if (!activeProjectId || selectedTargetIds.length === 0) return;
    setActionLoading(true);
    try {
      await bulkAction(activeProjectId, selectedTargetIds, "approve");
      setSelectedTargetIds([]);
      loadQueue(activeProjectId, queueBucket);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkReschedule = async (hours: number) => {
    if (!activeProjectId || selectedTargetIds.length === 0) return;
    setActionLoading(true);
    try {
      await bulkAction(activeProjectId, selectedTargetIds, "reschedule", { shift_hours: hours });
      setSelectedTargetIds([]);
      loadQueue(activeProjectId, queueBucket);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkCancel = async () => {
    if (!activeProjectId || selectedTargetIds.length === 0) return;
    if (!confirm(`Bạn có chắc muốn hủy ${selectedTargetIds.length} bài đăng đã chọn?`)) return;
    setActionLoading(true);
    try {
      await bulkAction(activeProjectId, selectedTargetIds, "cancel");
      setSelectedTargetIds([]);
      loadQueue(activeProjectId, queueBucket);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkRetry = async () => {
    if (!activeProjectId || selectedTargetIds.length === 0) return;
    setActionLoading(true);
    try {
      await bulkAction(activeProjectId, selectedTargetIds, "retry");
      setSelectedTargetIds([]);
      loadQueue(activeProjectId, queueBucket);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkDuplicate = async () => {
    if (!activeProjectId || selectedTargetIds.length === 0 || !targetAccountForDuplicate) return;
    setActionLoading(true);
    try {
      await bulkAction(activeProjectId, selectedTargetIds, "duplicate_to", {
        target_account_id: targetAccountForDuplicate,
      });
      setSelectedTargetIds([]);
      loadQueue(activeProjectId, queueBucket);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkDeleteDraft = async () => {
    if (!activeProjectId || selectedTargetIds.length === 0) return;
    if (!confirm(`Bạn có chắc muốn xóa vĩnh viễn ${selectedTargetIds.length} bản nháp đã chọn?`)) return;
    setActionLoading(true);
    try {
      await bulkAction(activeProjectId, selectedTargetIds, "delete_draft");
      setSelectedTargetIds([]);
      loadQueue(activeProjectId, queueBucket);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSelectRow = (item: QueueItem) => {
    // Map QueueItem to VideoPostTarget for detail drawer
    const targetData: VideoPostTarget = {
      target_id: item.target_id,
      post_id: item.post_id,
      account_id: item.account_id,
      platform: item.platform,
      status: item.status,
      scheduled_at: item.scheduled_at,
      caption: item.caption,
      title: item.title,
      thumb: item.thumb,
      error_message: item.error_message,
    };

    setHubSelectedEntity({
      type: "post",
      id: item.target_id,
      data: targetData,
    });
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      {/* Bucket Tabs Bar */}
      <div className="border-b border-border bg-card/60 px-4 pt-2 flex items-center justify-between overflow-x-auto shrink-0">
        <div className="flex items-center gap-1">
          {TABS.map((tab) => {
            const count =
              tab.id === "upcoming"
                ? summary?.upcoming_count
                : tab.id === "draft"
                ? summary?.draft_count
                : tab.id === "pending_approval"
                ? summary?.pending_approval_count
                : tab.id === "overdue"
                ? summary?.overdue_count
                : tab.id === "failed"
                ? summary?.failed_count
                : tab.id === "published"
                ? summary?.published_count
                : undefined;

            const isActive = queueBucket === tab.id;

            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => handleTabChange(tab.id)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap",
                  isActive
                    ? "border-primary text-foreground font-semibold"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                )}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
                {typeof count === "number" && (
                  <span
                    className={cn(
                      "px-1.5 py-0.2 rounded-full text-[10px] font-mono",
                      isActive
                        ? "bg-primary/20 text-primary"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <button
          type="button"
          onClick={() => activeProjectId && loadQueue(activeProjectId, queueBucket)}
          className="p-1.5 text-muted-foreground hover:text-foreground transition-colors shrink-0"
          aria-label="Tải lại hàng đợi"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", isLoadingQueue && "animate-spin")} />
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-3 border-b border-border bg-card/40 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2 flex-1 min-w-[200px] max-w-sm">
          <div className="relative w-full">
            <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Tìm theo video, caption, kênh..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-background border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={accountFilter}
            onChange={(e) => setAccountFilter(e.target.value)}
            className="px-2 py-1.5 rounded-lg bg-background border border-border text-xs text-foreground focus:outline-none"
          >
            <option value="all">Tất cả tài khoản</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.display_name} ({acc.platform})
              </option>
            ))}
          </select>

          <select
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value)}
            className="px-2 py-1.5 rounded-lg bg-background border border-border text-xs text-foreground focus:outline-none"
          >
            <option value="all">Tất cả nền tảng</option>
            <option value="youtube">YouTube</option>
            <option value="tiktok">TikTok</option>
            <option value="facebook">Facebook</option>
            <option value="instagram">Instagram</option>
          </select>
        </div>
      </div>

      {/* Bulk Action Bar */}
      {selectedTargetIds.length > 0 && (
        <div className="bg-primary/10 border-b border-primary/20 px-4 py-2 flex flex-wrap items-center justify-between gap-2 shrink-0 animate-in fade-in">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-primary">
              Đã chọn {selectedTargetIds.length} mục
            </span>
            <button
              type="button"
              onClick={() => setSelectedTargetIds([])}
              className="text-xs text-muted-foreground hover:underline"
            >
              Bỏ chọn
            </button>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            {/* Pending approval bulk action */}
            {queueBucket === "pending_approval" && (
              <button
                type="button"
                disabled={actionLoading}
                onClick={handleBulkApprove}
                className="px-2.5 py-1 rounded-md bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-500 transition-colors flex items-center gap-1"
              >
                <CheckCircle className="w-3 h-3" />
                Duyệt ({selectedTargetIds.length})
              </button>
            )}

            {/* Reschedule buttons */}
            {(queueBucket === "upcoming" || queueBucket === "overdue") && (
              <>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => handleBulkReschedule(2)}
                  className="px-2.5 py-1 rounded-md bg-muted hover:bg-muted/80 text-foreground text-xs font-medium transition-colors border border-border"
                >
                  +2h
                </button>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => handleBulkReschedule(24)}
                  className="px-2.5 py-1 rounded-md bg-muted hover:bg-muted/80 text-foreground text-xs font-medium transition-colors border border-border"
                >
                  +1 ngày
                </button>
              </>
            )}

            {/* Retry for failed */}
            {queueBucket === "failed" && (
              <button
                type="button"
                disabled={actionLoading}
                onClick={handleBulkRetry}
                className="px-2.5 py-1 rounded-md bg-rose-600 text-white text-xs font-medium hover:bg-rose-500 transition-colors flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                Đăng lại ({selectedTargetIds.length})
              </button>
            )}

            {/* Duplicate to another account */}
            <div className="flex items-center gap-1 bg-background border border-border rounded-md px-1.5 py-0.5">
              <span className="text-[11px] text-muted-foreground">Nhân bản sang:</span>
              <select
                value={targetAccountForDuplicate}
                onChange={(e) => setTargetAccountForDuplicate(e.target.value)}
                className="bg-transparent text-xs text-foreground focus:outline-none"
              >
                <option value="">Chọn kênh...</option>
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.display_name} ({acc.platform})
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={actionLoading || !targetAccountForDuplicate}
                onClick={handleBulkDuplicate}
                className="px-2 py-0.5 rounded bg-primary text-primary-foreground text-xs font-medium disabled:opacity-50"
              >
                Sao chép
              </button>
            </div>

            {/* Cancel / Delete Draft */}
            {queueBucket === "draft" ? (
              <button
                type="button"
                disabled={actionLoading}
                onClick={handleBulkDeleteDraft}
                className="px-2.5 py-1 rounded-md bg-destructive/10 text-destructive text-xs font-medium hover:bg-destructive/20 transition-colors border border-destructive/20 flex items-center gap-1"
              >
                <Trash2 className="w-3 h-3" />
                Xóa nháp
              </button>
            ) : (
              <button
                type="button"
                disabled={actionLoading}
                onClick={handleBulkCancel}
                className="px-2.5 py-1 rounded-md bg-destructive/10 text-destructive text-xs font-medium hover:bg-destructive/20 transition-colors border border-destructive/20 flex items-center gap-1"
              >
                <Trash2 className="w-3 h-3" />
                Hủy
              </button>
            )}
          </div>
        </div>
      )}

      {/* Table Content */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        {isLoadingQueue && items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <RefreshCw className="w-8 h-8 animate-spin mb-3 text-primary" />
            <p className="text-xs">Đang tải danh sách bài trong hàng đợi...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center border-2 border-dashed border-border rounded-xl p-6">
            <Clock className="w-10 h-10 text-muted-foreground mb-3" />
            <h3 className="text-sm font-semibold text-foreground">Hàng đợi đang trống</h3>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm">
              Không có bài đăng nào trong mục {TABS.find((t) => t.id === queueBucket)?.label}.
            </p>
          </div>
        ) : (
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-muted-foreground">
                  <th className="p-3 w-10 text-center">
                    <input
                      type="checkbox"
                      checked={selectedTargetIds.length === filteredItems.length && filteredItems.length > 0}
                      onChange={handleSelectAll}
                      className="rounded border-border text-primary focus:ring-primary w-3.5 h-3.5 cursor-pointer"
                    />
                  </th>
                  <th className="p-3 font-semibold w-16">Video</th>
                  <th className="p-3 font-semibold">Tên & Caption</th>
                  <th className="p-3 font-semibold w-44">Tài khoản đích</th>
                  <th className="p-3 font-semibold w-36">Thời gian hẹn</th>
                  <th className="p-3 font-semibold w-28">Trạng thái</th>
                  <th className="p-3 font-semibold w-24 text-right">Chi tiết</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredItems.map((item) => {
                  const isSelected = selectedTargetIds.includes(item.target_id);
                  const isEntityActive = hubSelectedEntity?.id === item.target_id;
                  const acc = accounts.find((a) => a.id === item.account_id);

                  return (
                    <tr
                      key={item.target_id}
                      onClick={() => handleSelectRow(item)}
                      className={cn(
                        "virtual-row hover:bg-muted/40 cursor-pointer transition-colors",
                        isEntityActive && "bg-muted/60",
                        isSelected && "bg-primary/5"
                      )}
                    >
                      <td className="p-3 text-center" onClick={(e) => handleToggleSelect(item.target_id, e)}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="rounded border-border text-primary focus:ring-primary w-3.5 h-3.5 cursor-pointer"
                        />
                      </td>

                      <td className="p-2">
                        <VideoThumb
                          thumb={item.thumbnail}
                          title={item.video_title}
                          className="w-14 h-9 rounded"
                        />
                      </td>

                      <td className="p-3">
                        <div className="font-semibold text-foreground line-clamp-1">
                          {item.video_title || "Video không tên"}
                        </div>
                        <div className="text-[11px] text-muted-foreground line-clamp-2 mt-0.5">
                          {item.caption || "(Chưa có caption)"}
                        </div>
                        {item.error_message && (
                          <div className="text-[10px] text-rose-400 mt-1 flex items-center gap-1 font-mono">
                            <AlertCircle className="w-3 h-3 shrink-0" />
                            <span className="line-clamp-1">{item.error_message}</span>
                          </div>
                        )}
                      </td>

                      <td className="p-3">
                        {acc ? (
                          <AccountChip account={acc} size="sm" />
                        ) : (
                          <span className="font-mono text-[11px] text-muted-foreground">
                            {item.account_name || item.account_id}
                          </span>
                        )}
                      </td>

                      <td className="p-3 text-muted-foreground">
                        {item.scheduled_at ? (
                          <div className="flex flex-col">
                            <span className="font-medium text-foreground">
                              {new Date(item.scheduled_at).toLocaleTimeString("vi-VN", {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                            <span className="text-[10px] text-muted-foreground">
                              {new Date(item.scheduled_at).toLocaleDateString("vi-VN")}
                            </span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground/60 italic">Bản nháp</span>
                        )}
                      </td>

                      <td className="p-3">
                        <StatusBadge status={item.status} size="sm" />
                      </td>

                      <td className="p-3 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectRow(item);
                          }}
                          className="px-2.5 py-1 rounded bg-muted hover:bg-muted/80 text-foreground text-[11px] font-medium transition-colors"
                        >
                          Xem
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
