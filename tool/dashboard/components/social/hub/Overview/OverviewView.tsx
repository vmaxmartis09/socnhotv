"use client";

import React, { useEffect } from "react";
import { cn } from "@/lib/utils";
import { useSocialStore, HubView } from "@/store/modules/social";
import { useStudioStore } from "@/store";
import {
  Clock,
  AlertCircle,
  CheckCircle,
  Calendar,
  Zap,
  ArrowUpRight,
  Flame,
  Plus,
  RefreshCw,
} from "@/components/ui/icons";
import { AccountChip } from "../common/AccountChip";

interface OverviewViewProps {
  onNavigateView: (view: HubView) => void;
  onOpenPlanWizard: () => void;
}

export function OverviewView({ onNavigateView, onOpenPlanWizard }: OverviewViewProps) {
  const { activeProjectId } = useStudioStore();
  const { overviewData, loadOverview, loading: isLoadingOverview, accounts, queueData } = useSocialStore();

  useEffect(() => {
    if (activeProjectId) {
      loadOverview(activeProjectId);
    }
  }, [activeProjectId, loadOverview]);

  const upcoming24h = overviewData?.summary?.upcoming_24h_count ?? overviewData?.upcoming_24h_count ?? 0;
  const overdueCount = overviewData?.summary?.overdue_count ?? overviewData?.overdue_count ?? 0;
  const failedCount = overviewData?.summary?.failed_count ?? overviewData?.failed_count ?? 0;
  const pendingCount = overviewData?.summary?.pending_approval_count ?? overviewData?.pending_approval_count ?? 0;
  const draftsCount = queueData?.summary?.draft_count ?? overviewData?.drafts_count ?? 0;
  const expiringTokens = overviewData?.token_expiring_accounts ?? overviewData?.expiring_tokens ?? [];
  const emptySlots = overviewData?.empty_slots_7d ?? overviewData?.empty_slots ?? [];

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
      {/* Top Banner / Hero */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-gradient-to-r from-card to-muted/40 border border-border shadow-sm">
        <div>
          <h2 className="text-lg md:text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <span>Việc Cần Xử Lý Hôm Nay</span>
            {isLoadingOverview && (
              <RefreshCw className="w-4 h-4 text-muted-foreground animate-spin" />
            )}
          </h2>
          <p className="text-xs md:text-sm text-muted-foreground mt-1">
            Tổng quan lịch đăng, cảnh báo bài quá hạn, lỗi kênh và khoảng trống khung giờ vàng
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onOpenPlanWizard}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium text-xs md:text-sm hover:bg-primary/90 transition-all shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Lên kế hoạch đăng
          </button>
        </div>
      </div>

      {/* Main Metric Action Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 md:gap-4">
        {/* 1. Sắp đăng 24h tới */}
        <button
          type="button"
          onClick={() => onNavigateView("queue")}
          className="flex flex-col justify-between p-4 rounded-xl border border-blue-500/20 bg-blue-500/5 hover:bg-blue-500/10 hover:border-blue-500/40 transition-all text-left group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-blue-400">24h Tới</span>
            <Clock className="w-4 h-4 text-blue-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </div>
          <div className="mt-3">
            <span className="text-2xl md:text-3xl font-bold text-foreground">{upcoming24h}</span>
            <span className="text-xs text-muted-foreground block mt-0.5">Bài đã hẹn giờ</span>
          </div>
        </button>

        {/* 2. Quá hạn */}
        <button
          type="button"
          onClick={() => onNavigateView("queue")}
          className={cn(
            "flex flex-col justify-between p-4 rounded-xl border transition-all text-left group",
            overdueCount > 0
              ? "border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20"
              : "border-border bg-card/50 hover:bg-muted/40"
          )}
        >
          <div className="flex items-center justify-between">
            <span className={cn("text-xs font-medium", overdueCount > 0 ? "text-amber-400" : "text-muted-foreground")}>
              Quá hạn
            </span>
            <AlertCircle className={cn("w-4 h-4", overdueCount > 0 ? "text-amber-400" : "text-muted-foreground")} />
          </div>
          <div className="mt-3">
            <span className="text-2xl md:text-3xl font-bold text-foreground">{overdueCount}</span>
            <span className="text-xs text-muted-foreground block mt-0.5">Cần dời giờ hoặc hủy</span>
          </div>
        </button>

        {/* 3. Lỗi cần đăng lại */}
        <button
          type="button"
          onClick={() => onNavigateView("queue")}
          className={cn(
            "flex flex-col justify-between p-4 rounded-xl border transition-all text-left group",
            failedCount > 0
              ? "border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20"
              : "border-border bg-card/50 hover:bg-muted/40"
          )}
        >
          <div className="flex items-center justify-between">
            <span className={cn("text-xs font-medium", failedCount > 0 ? "text-rose-400" : "text-muted-foreground")}>
              Lỗi đăng
            </span>
            <AlertCircle className={cn("w-4 h-4", failedCount > 0 ? "text-rose-400" : "text-muted-foreground")} />
          </div>
          <div className="mt-3">
            <span className="text-2xl md:text-3xl font-bold text-foreground">{failedCount}</span>
            <span className="text-xs text-muted-foreground block mt-0.5">Cần kiểm tra & thử lại</span>
          </div>
        </button>

        {/* 4. Chờ duyệt */}
        <button
          type="button"
          onClick={() => onNavigateView("queue")}
          className="flex flex-col justify-between p-4 rounded-xl border border-border bg-card/50 hover:bg-muted/40 transition-all text-left group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Chờ duyệt</span>
            <CheckCircle className="w-4 h-4 text-muted-foreground" />
          </div>
          <div className="mt-3">
            <span className="text-2xl md:text-3xl font-bold text-foreground">{pendingCount}</span>
            <span className="text-xs text-muted-foreground block mt-0.5">Cần xác nhận</span>
          </div>
        </button>

        {/* 5. Bản nháp */}
        <button
          type="button"
          onClick={() => onNavigateView("queue")}
          className="flex flex-col justify-between p-4 rounded-xl border border-border bg-card/50 hover:bg-muted/40 transition-all text-left group col-span-2 md:col-span-1"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Bản nháp</span>
            <Zap className="w-4 h-4 text-muted-foreground" />
          </div>
          <div className="mt-3">
            <span className="text-2xl md:text-3xl font-bold text-foreground">{draftsCount}</span>
            <span className="text-xs text-muted-foreground block mt-0.5">Chưa hẹn giờ</span>
          </div>
        </button>
      </div>

      {/* Two Column Layout: Expiring Tokens & Empty Gold Slots */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Expiring Tokens */}
        <div className="rounded-xl border border-border bg-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              Cảnh báo Token Tài khoản (7 ngày tới)
            </h3>
            <button
              type="button"
              onClick={() => onNavigateView("accounts")}
              className="text-xs text-primary hover:underline flex items-center gap-1"
            >
              Xem tài khoản
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>

          {expiringTokens.length === 0 ? (
            <div className="py-6 text-center text-xs text-muted-foreground">
              Mọi tài khoản đang kết nối ổn định, không có token nào sắp hết hạn.
            </div>
          ) : (
            <div className="space-y-2">
              {expiringTokens.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-foreground">
                      {(item as any).display_name || (item as any).handle || (item as any).account_id}
                    </span>
                    <span className="text-muted-foreground">({item.platform})</span>
                  </div>
                  <span className="text-amber-400 font-mono text-[11px]">
                    {item.days_left !== undefined
                      ? `Còn ${item.days_left} ngày`
                      : item.expires_at
                      ? `Hết hạn: ${new Date(item.expires_at).toLocaleDateString("vi-VN")}`
                      : "Sắp hết hạn"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Empty Gold Slots */}
        <div className="rounded-xl border border-border bg-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Flame className="w-4 h-4 text-amber-500" />
              Khoảng Trống Khung Giờ Vàng (7 ngày tới)
            </h3>
            <button
              type="button"
              onClick={() => onNavigateView("calendar")}
              className="text-xs text-primary hover:underline flex items-center gap-1"
            >
              Mở Lịch
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>

          {emptySlots.length === 0 ? (
            <div className="py-6 text-center text-xs text-muted-foreground">
              Các khung giờ vàng đều đã có bài đăng được lên lịch hoặc chưa thiết lập khung giờ vàng.
            </div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {emptySlots.slice(0, 6).map((slot, idx) => {
                const acc = accounts.find((a) => a.id === slot.account_id);
                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 rounded-lg bg-muted/40 border border-border/50 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                        {slot.date}
                      </span>
                      <span className="font-mono font-medium text-amber-400">
                        {(slot as any).time_slot || (slot.start ? `${slot.start} - ${slot.end}` : "Khung giờ vàng")}
                      </span>
                      {acc && <AccountChip account={acc} size="sm" />}
                    </div>
                    <button
                      type="button"
                      onClick={() => onOpenPlanWizard()}
                      className="px-2 py-1 rounded bg-primary/10 hover:bg-primary/20 text-primary text-[11px] font-medium transition-colors"
                    >
                      Hẹn bài vào đây
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
