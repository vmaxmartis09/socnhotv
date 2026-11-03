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
import { X, PanelRightClose } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

const TABS: RightPanelTab[] = ["chat", "node", "project", "publish", "jobs"];

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
    const onMove = (e: MouseEvent) => {
      const delta = startXRef.current - e.clientX;
      setRightPanelWidth(startWidthRef.current + delta);
    };
    const onUp = () => setIsResizing(false);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
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
