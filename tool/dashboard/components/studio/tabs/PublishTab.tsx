"use client";

import React, { useEffect, useMemo, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { useStudioStore } from "@/store";
import { useSocialStore, HubView } from "@/store/modules/social";
import { socialApi, KPISummary } from "@/lib/api/social";
import {
  Calendar,
  Clock,
  Zap,
  Plus,
  RefreshCw,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  CheckCircle2,
  Film,
  Smartphone,
  Download,
  Sparkles,
  FileText,
  Copy,
} from "@/components/ui/icons";
import { VideoThumb } from "@/components/social/hub/common/VideoThumb";
import { AccountChip } from "@/components/social/hub/common/AccountChip";
import { StatusBadge } from "@/components/social/hub/common/StatusBadge";
import dynamic from "next/dynamic";
import { ManualPackageModal } from "@/components/social/ManualPackageModal";
import { ManualMetricsModal } from "@/components/social/ManualMetricsModal";

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

  // Package Modal State
  const [selectedPackagePost, setSelectedPackagePost] = useState<any | null>(null);

  // Metrics Modal State
  const [metricsModalOpen, setMetricsModalOpen] = useState(false);

  // Learnings & Analytics State
  const [learningsData, setLearningsData] = useState<{
    kpis?: KPISummary;
    recommendations?: any;
    learnings_md?: string;
  } | null>(null);
  const [loadingLearnings, setLoadingLearnings] = useState(false);
  const [showFullLearnings, setShowFullLearnings] = useState(false);

  const fetchLearnings = useCallback(async (pid: string) => {
    setLoadingLearnings(true);
    try {
      const res = await socialApi.getAnalyticsLearnings(pid);
      setLearningsData({
        recommendations: res.recommendations,
        learnings_md: res.learnings_md,
      });

      // Also get overview KPIs
      const ov = await socialApi.getAnalyticsOverview(pid, "30d");
      setLearningsData((prev) => ({
        ...prev,
        kpis: ov.kpis,
      }));
    } catch {
      // Ignore if no analytics yet
    } finally {
      setLoadingLearnings(false);
    }
  }, []);

  useEffect(() => {
    if (activeProjectId) {
      loadAccounts(activeProjectId);
      loadQueue(activeProjectId, "upcoming");
      fetchLearnings(activeProjectId);
    }
  }, [activeProjectId, loadAccounts, loadQueue, fetchLearnings]);

  const summary = queueData?.summary;
  const upcomingCount = summary?.upcoming_count ?? 0;
  const draftCount = summary?.draft_count ?? 0;
  const pendingCount = summary?.pending_approval_count ?? 0;
  const overdueCount = summary?.overdue_count ?? 0;
  const failedCount = summary?.failed_count ?? 0;

  // 5 genuine upcoming items or recent items
  const upcomingPosts = useMemo(() => {
    const items = queueData?.items || [];
    return items
      .filter((item) => item.status === "scheduled" || item.status === "draft" || item.status === "pending_approval")
      .slice(0, 5);
  }, [queueData]);

  // Target list for manual metrics
  const publishedTargets = useMemo(() => {
    const items = queueData?.items || [];
    return items.map((i) => ({
      target_id: i.target_id,
      post_id: i.post_id,
      title: i.video_title || i.title || "Video",
      platform: i.platform,
    }));
  }, [queueData]);

  const handleOpenHubView = (view: HubView, bucket?: "upcoming" | "draft" | "pending_approval" | "overdue" | "failed") => {
    if (bucket) {
      setQueueBucket(bucket);
    }
    openHub({ view });
  };

  const handleMarkPublished = async (postId: string, targetId: string, url: string) => {
    if (!activeProjectId) return;
    await socialApi.markPublished(activeProjectId, postId, targetId, url);
    loadQueue(activeProjectId, "upcoming");
    fetchLearnings(activeProjectId);
  };

  const handleRefreshAll = () => {
    if (activeProjectId) {
      loadAccounts(activeProjectId);
      loadQueue(activeProjectId, "upcoming");
      fetchLearnings(activeProjectId);
    }
  };

  const nextEp = learningsData?.recommendations?.next_episode_suggestions;

  return (
    <div className="flex h-full flex-col p-3.5 space-y-4 text-xs select-none overflow-y-auto scroll-quiet">
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
            onClick={handleRefreshAll}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground"
            aria-label="Tải lại"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", loadingLearnings && "animate-spin")} />
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

      {/* 2. Quick Actions */}
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => openPublishCenter("plan")}
          className="py-2 px-2.5 rounded-lg border border-border bg-card hover:bg-muted text-foreground font-medium text-xs flex items-center justify-center gap-1.5 transition-colors shadow-2xs"
        >
          <Plus className="h-3.5 w-3.5 text-primary" />
          <span>Lên kế hoạch đăng</span>
        </button>

        <button
          type="button"
          onClick={() => setMetricsModalOpen(true)}
          className="py-2 px-2.5 rounded-lg border border-border bg-card hover:bg-muted text-foreground font-medium text-xs flex items-center justify-center gap-1.5 transition-colors shadow-2xs"
        >
          <Sparkles className="h-3.5 w-3.5 text-amber-400" />
          <span>Nhập số liệu & Gợi ý</span>
        </button>
      </div>

      {/* 3. Section: Gói Đăng Thủ Công & 5 Bài Sắp Đăng */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Bài đăng & Gói xuất bản
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
            <p className="text-xs text-muted-foreground">Chưa có bài đăng nào trong hàng đợi</p>
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
                : "Bản nháp";
              const dateStr = item.scheduled_at
                ? new Date(item.scheduled_at).toLocaleDateString("vi-VN", {
                    day: "2-digit",
                    month: "2-digit",
                  })
                : "";

              return (
                <div
                  key={item.target_id}
                  className="p-2.5 rounded-lg border border-border bg-card hover:border-primary/40 transition-colors space-y-2"
                >
                  <div className="flex items-center gap-2.5">
                    <VideoThumb
                      thumb={item.thumbnail}
                      title={item.video_title}
                      className="w-12 h-8 rounded shrink-0"
                    />
                    <div className="min-w-0 flex-1">
                      <span className="font-semibold text-foreground line-clamp-1 text-xs">
                        {item.video_title || item.title || "Video"}
                      </span>
                      <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-mono mt-0.5">
                        <span>{dateStr} {timeStr}</span>
                        {acc && <span>· {acc.platform.toUpperCase()}</span>}
                      </div>
                    </div>
                    <StatusBadge status={item.status} size="sm" />
                  </div>

                  {/* Manual Publishing Action Bar */}
                  <div className="flex items-center justify-end gap-1.5 pt-1 border-t border-border/40">
                    <button
                      type="button"
                      onClick={() =>
                        setSelectedPackagePost({
                          post_id: item.post_id,
                          target_id: item.target_id,
                          title: item.video_title || item.title,
                          platform: item.platform,
                          caption: item.caption,
                        })
                      }
                      className="px-2 py-1 rounded bg-primary/10 hover:bg-primary/20 text-primary text-[10px] font-semibold flex items-center gap-1 transition-colors"
                    >
                      <Download className="h-3 w-3" />
                      <span>Gói đăng (.zip)</span>
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setSelectedPackagePost({
                          post_id: item.post_id,
                          target_id: item.target_id,
                          title: item.video_title || item.title,
                          platform: item.platform,
                          caption: item.caption,
                        })
                      }
                      className="px-2 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 text-[10px] font-semibold flex items-center gap-1 transition-colors"
                    >
                      <CheckCircle2 className="h-3 w-3" />
                      <span>Tôi đã đăng</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 4. Section: Số Liệu Thực Tế & Gợi Ý Tập Sau (Analytics Card) */}
      <div className="rounded-xl border border-border bg-card p-3.5 space-y-3 shadow-2xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-amber-500/10 text-amber-500">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <h4 className="font-bold text-foreground text-xs leading-none">
              Số Liệu & Gợi Ý Tập Sau
            </h4>
          </div>
          <button
            type="button"
            onClick={() => activeProjectId && fetchLearnings(activeProjectId)}
            className="text-[10px] text-primary hover:underline"
          >
            Cập nhật
          </button>
        </div>

        {/* Real KPI summary chips */}
        <div className="grid grid-cols-3 gap-1.5 text-center font-mono">
          <div className="p-2 rounded-lg bg-muted/40 border border-border/40">
            <span className="text-[10px] text-muted-foreground block font-sans">Lượt xem</span>
            <span className="font-bold text-foreground text-xs">
              {(learningsData?.kpis?.total_views ?? 0).toLocaleString()}
            </span>
          </div>

          <div className="p-2 rounded-lg bg-muted/40 border border-border/40">
            <span className="text-[10px] text-muted-foreground block font-sans">Giữ chân</span>
            <span className="font-bold text-emerald-500 text-xs">
              {learningsData?.kpis?.avg_retention_pct ?? 0}%
            </span>
          </div>

          <div className="p-2 rounded-lg bg-muted/40 border border-border/40">
            <span className="text-[10px] text-muted-foreground block font-sans">Tương tác ER</span>
            <span className="font-bold text-blue-400 text-xs">
              {learningsData?.kpis?.engagement_rate ?? 0}%
            </span>
          </div>
        </div>

        {/* AI Next Episode Recommendation Box */}
        {nextEp ? (
          <div className="p-2.5 rounded-lg border border-amber-500/20 bg-amber-500/5 space-y-1.5 text-[11px]">
            <div className="font-semibold text-amber-400 flex items-center gap-1 text-[11px]">
              <Sparkles className="h-3.5 w-3.5 shrink-0" />
              <span>Gợi ý cho kịch bản tập sau:</span>
            </div>
            <p className="text-foreground leading-relaxed">
              {nextEp.hook_recommendation}
            </p>
            <div className="flex flex-wrap gap-2 text-[10px] text-muted-foreground font-mono pt-1 border-t border-border/40">
              <span>Nhịp dựng: ~{nextEp.recommended_shot_pacing_s}s/shot</span>
              <span>Thời lượng: {nextEp.target_duration_s}s</span>
              <span>Tỉ lệ: {nextEp.character_ratio}</span>
            </div>
          </div>
        ) : (
          <div className="p-2.5 rounded-lg border border-dashed border-border bg-muted/20 text-center text-muted-foreground text-[11px] space-y-1">
            <p>Chưa có dữ liệu phân tích tập trước.</p>
            <button
              type="button"
              onClick={() => setMetricsModalOpen(true)}
              className="text-primary hover:underline font-semibold"
            >
              + Nhập số liệu lượt xem / giữ chân để sinh gợi ý
            </button>
          </div>
        )}

        {/* Action Button */}
        <div className="flex items-center justify-between pt-1">
          <button
            type="button"
            onClick={() => setMetricsModalOpen(true)}
            className="px-2.5 py-1 rounded bg-muted hover:bg-muted/80 text-foreground text-[11px] font-medium transition-colors border border-border flex items-center gap-1"
          >
            <FileText className="h-3 w-3" />
            <span>Nhập số liệu (Tay / CSV)</span>
          </button>

          {learningsData?.learnings_md && (
            <button
              type="button"
              onClick={() => setShowFullLearnings(!showFullLearnings)}
              className="text-[11px] text-muted-foreground hover:text-foreground underline"
            >
              {showFullLearnings ? "Thu gọn" : "Xem đúc kết chi tiết"}
            </button>
          )}
        </div>

        {showFullLearnings && learningsData?.learnings_md && (
          <div className="p-3 rounded-lg border border-border bg-muted/30 text-[10px] font-mono text-muted-foreground whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed select-text">
            {learningsData.learnings_md}
          </div>
        )}
      </div>

      {/* 5. Section: Tài khoản kết nối */}
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

      {/* Manual Package Modal */}
      {selectedPackagePost && (
        <ManualPackageModal
          isOpen={Boolean(selectedPackagePost)}
          onClose={() => setSelectedPackagePost(null)}
          projectId={activeProjectId || "soc-nho-tv"}
          post={selectedPackagePost}
          onMarkPublished={handleMarkPublished}
        />
      )}

      {/* Manual Metrics & CSV Import Modal */}
      {metricsModalOpen && (
        <ManualMetricsModal
          isOpen={metricsModalOpen}
          onClose={() => setMetricsModalOpen(false)}
          projectId={activeProjectId || "soc-nho-tv"}
          targets={publishedTargets}
          onSuccess={() => {
            if (activeProjectId) {
              fetchLearnings(activeProjectId);
            }
          }}
        />
      )}

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
