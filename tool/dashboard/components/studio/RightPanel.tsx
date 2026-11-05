"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import type { RightPanelTab } from "@/store/slices/rightPanelSlice";
import { ChatTab } from "./tabs/ChatTab";
import { NodeTab } from "./tabs/NodeTab";
import { ProjectTab } from "./tabs/ProjectTab";
import { PublishTab } from "./tabs/PublishTab";
import { JobsCostTab } from "./tabs/JobsCostTab";
import { ShortcutsView } from "./ShortcutsView";
import { PolicyTab } from "./tabs/PolicyTab";
import { ToolboxPanel } from "@/components/toolbox/ToolboxPanel";
import { X, PanelRightClose, PanelRightOpen } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

const TABS: RightPanelTab[] = ["project", "chat", "publish", "jobs", "node", "policy", "shortcuts"];

export function RightPanel() {
  const t = useTranslations("rightPanel");
  const c = useTranslations("common");
  const {
    activeRightTab,
    setActiveRightTab,
    rightPanelWidth,
    setRightPanelWidth,
    rightPanelCollapsed,
    setRightPanelCollapsed,
    mobileSheetOpen,
    setMobileSheetOpen,
  } = useStudioStore();

  const [isResizing, setIsResizing] = useState(false);
  const startXRef = useRef(0);
  const startWidthRef = useRef(380);

  const handleMouseDownResize = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsResizing(true);
      startXRef.current = e.clientX;
      startWidthRef.current = rightPanelWidth;
    },
    [rightPanelWidth]
  );

  useEffect(() => {
    if (!isResizing) return;
    let rafId: number | null = null;
    const onMove = (e: MouseEvent) => {
      if (rafId !== null) return;
      rafId = window.requestAnimationFrame(() => {
        const delta = startXRef.current - e.clientX;
        setRightPanelWidth(startWidthRef.current + delta);
        rafId = null;
      });
    };
    const onUp = () => {
      if (rafId !== null) {
        window.cancelAnimationFrame(rafId);
        rafId = null;
      }
      setIsResizing(false);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      if (rafId !== null) window.cancelAnimationFrame(rafId);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [isResizing, setRightPanelWidth]);

  const renderActiveTabContent = () => {
    switch (activeRightTab) {
      case "chat":
        return <ChatTab />;
      case "node":
        return <NodeTab />;
      case "project":
        return <ProjectTab />;
      case "publish":
        return <PublishTab />;
      case "jobs":
        return <JobsCostTab />;
      case "policy":
        return <PolicyTab />;
      case "toolbox":
        return <ToolboxPanel />;
      case "shortcuts":
        return <ShortcutsView />;
      default:
        return <ChatTab />;
    }
  };

  return (
    <>
      {/* Desktop Resizable Right Panel (>= 768px) */}
      {!rightPanelCollapsed && (
        <aside
          style={{ width: rightPanelWidth }}
          className="hidden md:flex relative shrink-0 flex-col border-l border-border bg-card h-full select-none"
        >
          {/* Left 4px resize handle (320px - 560px) */}
          <div
            role="separator"
            aria-orientation="vertical"
            aria-label={t("resizeHandle")}
            onMouseDown={handleMouseDownResize}
            className="absolute -left-1 top-0 bottom-0 z-20 w-2 cursor-col-resize hover:bg-brand/30"
          />

          {/* Top 5-tab bar with 2px chestnut brand underline on active tab */}
          <div className="flex h-10 shrink-0 items-center justify-between border-b border-border px-2">
            <div role="tablist" className="flex flex-1 items-center gap-0.5">
              {TABS.map((tab) => {
                const active = activeRightTab === tab;
                return (
                  <button
                    key={tab}
                    type="button"
                    role="tab"
                    aria-selected={active}
                    onClick={() => setActiveRightTab(tab)}
                    className={cn(
                      "relative flex h-10 items-center px-2.5 text-xs transition-colors",
                      active
                        ? "font-semibold text-foreground after:absolute after:inset-x-1.5 after:bottom-0 after:h-[2px] after:bg-brand"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {t(`tabs.${tab}` as any)}
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              onClick={() => setRightPanelCollapsed(true)}
              title={t("collapse")}
              aria-label={t("collapse")}
              className="flex h-6 w-6 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <PanelRightClose className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Tab Panel Content */}
          <div className="flex-1 min-h-0 overflow-y-auto select-text">
            {renderActiveTabContent()}
          </div>
        </aside>
      )}

      {/* Nút mở lại panel khi đang thu gọn (thay cho nút ở thanh trên đã bỏ) */}
      {rightPanelCollapsed && (
        <button
          type="button"
          onClick={() => setRightPanelCollapsed(false)}
          title={t("expand")}
          aria-label={t("expand")}
          className="hidden md:flex fixed right-3 top-3 z-30 h-8 w-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-transform hover:text-foreground active:scale-90"
        >
          <PanelRightOpen className="h-4 w-4" />
        </button>
      )}

      {/* Mobile Bottom Sheet (< 768px) */}
      {mobileSheetOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="md:hidden fixed inset-x-0 bottom-14 top-12 z-40 flex flex-col rounded-t-xl border-t border-border bg-card"
        >
          <div className="flex h-10 shrink-0 items-center justify-between border-b border-border px-3">
            <div role="tablist" className="flex items-center gap-1 overflow-x-auto">
              {TABS.map((tab) => {
                const active = activeRightTab === tab;
                return (
                  <button
                    key={tab}
                    type="button"
                    role="tab"
                    aria-selected={active}
                    onClick={() => setActiveRightTab(tab)}
                    className={cn(
                      "relative flex h-10 items-center px-2 text-xs",
                      active
                        ? "font-semibold text-foreground after:absolute after:inset-x-1 after:bottom-0 after:h-[2px] after:bg-brand"
                        : "text-muted-foreground"
                    )}
                  >
                    {t(`tabs.${tab}` as any)}
                  </button>
                );
              })}
            </div>
            <button
              type="button"
              onClick={() => setMobileSheetOpen(false)}
              aria-label={c("close")}
              className="flex h-7 w-7 items-center justify-center rounded text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto">
            {renderActiveTabContent()}
          </div>
        </div>
      )}
    </>
  );
}
