"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { PageBar } from "@/components/studio/PageBar";
import { useStudioStore } from "@/store";
import { useSocialStore } from "@/store/modules/social";
import { CalendarView } from "@/components/social/CalendarView";
import { ApprovalsTab } from "@/components/social/ApprovalsTab";
import { PostsTab } from "@/components/social/PostsTab";
import { AccountsTab } from "@/components/social/AccountsTab";
import { AnalyticsTab } from "@/components/social/AnalyticsTab";
import { NotificationDrawer } from "@/components/social/NotificationDrawer";
import { PostComposer } from "@/components/social/PostComposer";
import { cn } from "@/lib/utils";
import {
  Calendar,
  CalendarDays,
  CheckCircle2,
  FileText,
  ListOrdered,
  Plus,
  Users2,
  Activity,
} from "@/components/ui/icons";
import { Bell, Zap } from "@/components/social/icons";

export default function SocialPage() {
  const t = useTranslations("social");
  const { activeProjectId } = useStudioStore();
  const {
    activeTab,
    setActiveTab,
    posts,
    loadAll,
    openComposer,
    loading,
    unreadNotifCount,
    setNotifDrawerOpen,
    setAutomationModalOpen,
  } = useSocialStore();

  useEffect(() => {
    if (activeProjectId) {
      loadAll(activeProjectId);
    }
  }, [activeProjectId, loadAll]);

  const pendingApprovalsCount = posts.filter(
    (p) =>
      p.status === "pending_approval" ||
      p.targets.some((t) => t.status === "pending_approval")
  ).length;

  return (
    <div className="relative h-full w-full overflow-hidden flex flex-col bg-background">
      <PageBar page="social" />

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto scroll-quiet">
        <div className="mx-auto max-w-7xl space-y-5 px-4 sm:px-6 pb-12 pt-16 md:pr-20">
          {/* Top Header Card */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-border bg-card p-4 sm:p-5 shadow-xs">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary shadow-2xs">
                <CalendarDays className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-foreground tracking-tight">
                  {t("title")}
                </h1>
                <p className="text-xs text-muted-foreground">
                  Dự án: <span className="font-semibold text-foreground font-mono">{activeProjectId}</span> · Lịch xuất bản đa kênh & tự động hoá
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutomationModalOpen(true)}
                className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-semibold text-foreground hover:bg-muted transition-colors"
                title="Quy tắc tự động hoá"
              >
                <Zap className="h-4 w-4 text-amber-500" />
                <span className="hidden sm:inline">Tự động hoá</span>
              </button>

              <button
                onClick={() => setNotifDrawerOpen(true)}
                className="relative flex items-center justify-center rounded-lg border border-border p-2 text-xs font-semibold text-foreground hover:bg-muted transition-colors"
                title="Thông báo"
              >
                <Bell className="h-4 w-4" />
                {unreadNotifCount > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-[9px] font-bold text-white">
                    {unreadNotifCount}
                  </span>
                )}
              </button>

              <button
                onClick={() => openComposer()}
                className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow-xs hover:bg-primary/90 transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>+ Soạn bài mới</span>
              </button>
            </div>
          </div>

          {/* Navigation Sub-Tabs */}
          <div className="flex overflow-x-auto border-b border-border text-xs scroll-quiet gap-1">
            <button
              onClick={() => setActiveTab("calendar")}
              className={cn(
                "flex items-center gap-2 border-b-2 px-4 py-2.5 font-semibold transition-all shrink-0",
                activeTab === "calendar"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <Calendar className="h-4 w-4" />
              <span>Lịch xuất bản</span>
            </button>

            <button
              onClick={() => setActiveTab("approvals")}
              className={cn(
                "flex items-center gap-2 border-b-2 px-4 py-2.5 font-semibold transition-all shrink-0",
                activeTab === "approvals"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>Hàng chờ duyệt</span>
              {pendingApprovalsCount > 0 && (
                <span className="rounded-full bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30 px-1.5 py-0.2 text-[10px] font-bold">
                  {pendingApprovalsCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("posts")}
              className={cn(
                "flex items-center gap-2 border-b-2 px-4 py-2.5 font-semibold transition-all shrink-0",
                activeTab === "posts"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <FileText className="h-4 w-4" />
              <span>Tất cả bài viết</span>
              <span className="rounded-full bg-muted text-muted-foreground px-1.5 py-0.2 text-[10px]">
                {posts.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab("accounts")}
              className={cn(
                "flex items-center gap-2 border-b-2 px-4 py-2.5 font-semibold transition-all shrink-0",
                activeTab === "accounts"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <Users2 className="h-4 w-4" />
              <span>Tài khoản & Kênh</span>
            </button>

            <button
              onClick={() => setActiveTab("analytics")}
              className={cn(
                "flex items-center gap-2 border-b-2 px-4 py-2.5 font-semibold transition-all shrink-0",
                activeTab === "analytics"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <Activity className="h-4 w-4" />
              <span>Phân tích</span>
            </button>
          </div>

          {/* Active Tab Views */}
          <div className="pt-2">
            {activeTab === "calendar" && <CalendarView projectId={activeProjectId} />}
            {activeTab === "approvals" && <ApprovalsTab projectId={activeProjectId} />}
            {activeTab === "posts" && <PostsTab projectId={activeProjectId} />}
            {activeTab === "accounts" && <AccountsTab projectId={activeProjectId} />}
            {activeTab === "analytics" && <AnalyticsTab projectId={activeProjectId} />}
          </div>
        </div>
      </div>

      {/* Global Post Composer Drawer */}
      <PostComposer projectId={activeProjectId} />

      {/* Global Notification Drawer */}
      <NotificationDrawer projectId={activeProjectId} />
    </div>
  );
}
