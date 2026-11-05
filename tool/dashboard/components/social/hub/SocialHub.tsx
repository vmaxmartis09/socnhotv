"use client";

import React, { useEffect, useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSocialStore, HubView } from "@/store/modules/social";
import { useStudioStore } from "@/store";
import {
  Zap,
  Film,
  Clock,
  Calendar,
  Smartphone,
  Bookmark,
  X,
  Plus,
  RefreshCw,
  MoreVertical,
} from "@/components/ui/icons";

import { OverviewView } from "./Overview/OverviewView";
import { VideoLibraryView } from "./VideoLibrary/VideoLibraryView";
import { QueueView } from "./Queue/QueueView";
import { CalendarView } from "./Calendar/CalendarView";
import { AccountsView } from "./Accounts/AccountsView";
import { TemplatesView } from "./Templates/TemplatesView";
import { DetailDrawer } from "./common/DetailDrawer";
import { PublishCenterModal } from "@/components/social/PublishCenterModal";

interface NavItem {
  id: HubView;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { id: "overview", label: "Tổng quan", icon: Zap },
  { id: "library", label: "Kho video", icon: Film },
  { id: "queue", label: "Hàng đợi", icon: Clock },
  { id: "calendar", label: "Lịch", icon: Calendar },
  { id: "accounts", label: "Tài khoản", icon: Smartphone },
  { id: "templates", label: "Mẫu nội dung", icon: Bookmark },
];

export function SocialHub() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const activeProjectId = useStudioStore((s) => s.activeProjectId);
  const {
    isHubOpen,
    hubView,
    hubSelectedEntity,
    hubPreselectedVideoIds,
    openHub,
    closeHub,
    setHubView,
    setHubSelectedEntity,
    isPublishCenterOpen,
    openPublishCenter,
    closePublishCenter,
    loadAll,
  } = useSocialStore();

  // 1. Deep Link synchronization (?hub=social&view=...)
  useEffect(() => {
    const hubParam = searchParams.get("hub");
    const viewParam = searchParams.get("view") as HubView | null;

    if (hubParam === "social") {
      if (!isHubOpen) {
        openHub({ view: viewParam || "overview" });
      } else if (viewParam && viewParam !== hubView) {
        setHubView(viewParam);
      }
    }
  }, [searchParams, isHubOpen, hubView, openHub, setHubView]);

  // Sync state changes back to URL query parameters
  const updateUrlParams = useCallback(
    (view: HubView, isOpen: boolean) => {
      const params = new URLSearchParams(searchParams.toString());
      if (isOpen) {
        params.set("hub", "social");
        params.set("view", view);
      } else {
        params.delete("hub");
        params.delete("view");
      }
      const newQuery = params.toString();
      const newUrl = newQuery ? `${pathname}?${newQuery}` : pathname;
      window.history.replaceState(null, "", newUrl);
    },
    [pathname, searchParams]
  );

  const handleNavClick = (view: HubView) => {
    setHubView(view);
    updateUrlParams(view, true);
  };

  const handleClose = useCallback(() => {
    closeHub();
    updateUrlParams(hubView, false);
  }, [closeHub, hubView, updateUrlParams]);

  // 2. Keyboard shortcut: Esc to close entity or close hub
  useEffect(() => {
    if (!isHubOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (isPublishCenterOpen) {
          closePublishCenter();
        } else if (hubSelectedEntity) {
          setHubSelectedEntity(null);
        } else {
          handleClose();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isHubOpen, isPublishCenterOpen, hubSelectedEntity, closePublishCenter, setHubSelectedEntity, handleClose]);

  // Handle Planning videos
  const handlePlanVideos = (videoIds: string[]) => {
    openHub({ view: hubView, videoIds });
    openPublishCenter("plan");
  };

  if (!isHubOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Trung tâm Quản lý Social"
      className="fixed inset-0 z-50 flex flex-col bg-background text-foreground animate-in fade-in duration-150 overflow-hidden"
    >
      {/* Top Bar for Mobile & Desktop Branding */}
      <header className="h-14 border-b border-border bg-card/80 backdrop-blur-md px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm md:text-base font-bold tracking-tight text-foreground flex items-center gap-2">
              <span>Trung Tâm Quản Lý Social</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                {activeProjectId || "soc-nho-tv"}
              </span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handlePlanVideos([])}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            Lên kế hoạch đăng
          </button>

          <button
            type="button"
            onClick={handleClose}
            aria-label="Đóng Trung tâm Social (Esc)"
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-hidden relative">
        {/* Left Sidebar Navigation (Desktop) */}
        <nav
          aria-label="Điều hướng Trung tâm Social"
          className="w-full md:w-56 lg:w-60 border-b md:border-b-0 md:border-r border-border bg-card/40 flex flex-row md:flex-col justify-between shrink-0 overflow-x-auto md:overflow-y-auto scroll-quiet"
        >
          <div className="p-2 md:p-3 space-x-1 md:space-x-0 md:space-y-1 flex flex-row md:flex-col">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = hubView === item.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleNavClick(item.id)}
                  className={cn(
                    "flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap text-left",
                    isActive
                      ? "bg-primary text-primary-foreground font-semibold shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                  )}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          {/* Quick info / status at bottom of nav */}
          <div className="hidden md:block p-3 border-t border-border/50 text-[11px] text-muted-foreground">
            <div className="flex items-center justify-between">
              <span>Phím tắt Esc:</span>
              <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono text-[10px]">Đóng</kbd>
            </div>
          </div>
        </nav>

        {/* Central Active View Content */}
        <main className="flex-1 flex flex-col min-h-0 overflow-hidden bg-background">
          {hubView === "overview" && (
            <OverviewView
              onNavigateView={handleNavClick}
              onOpenPlanWizard={() => handlePlanVideos([])}
            />
          )}

          {hubView === "library" && (
            <VideoLibraryView onPlanVideos={handlePlanVideos} />
          )}

          {hubView === "queue" && <QueueView />}

          {hubView === "calendar" && (
            <CalendarView onOpenPlanWizard={() => handlePlanVideos([])} />
          )}

          {hubView === "accounts" && <AccountsView />}

          {hubView === "templates" && <TemplatesView />}
        </main>

        {/* Right Detail Drawer */}
        <DetailDrawer
          onPlanVideo={(vId) => handlePlanVideos([vId])}
          onRefresh={() => {
            if (activeProjectId) {
              loadAll(activeProjectId);
            }
          }}
        />
      </div>

      {/* S1 Multi-Step Wizard Modal */}
      {isPublishCenterOpen && (
        <PublishCenterModal
          projectId={activeProjectId || "soc-nho-tv"}
          isOpen={isPublishCenterOpen}
          initialVideoIds={hubPreselectedVideoIds}
          onClose={closePublishCenter}
        />
      )}
    </div>
  );
}
