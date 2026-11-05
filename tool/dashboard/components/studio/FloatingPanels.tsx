"use client";

import React, { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useLocale, useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import type { RightPanelTab } from "@/store/slices/rightPanelSlice";
import { ChatTab } from "./tabs/ChatTab";
import { NodeTab } from "./tabs/NodeTab";
import { PublishTab } from "./tabs/PublishTab";
import { JobsList } from "@/components/jobs/JobsList";
import { ProjectHub, type HubTab } from "@/components/project/ProjectHub";
import { FolderGit2, Users, MessageSquare, Calendar, Activity, Sliders, Keyboard } from "@/components/ui/icons";
import { ShortcutsView } from "./ShortcutsView";
import { ToolboxPanel } from "@/components/toolbox/ToolboxPanel";
import { Wrench } from "@/components/ui/icons";
import { PreviewPane } from "./PreviewPane";
import { usePreview } from "@/lib/preview";
import { useHubScope } from "@/lib/hub";
import { useConfirmStore } from "@/lib/confirm";
import { cn } from "@/lib/utils";

type View = "project" | "characters" | "chat" | "publish" | "jobs" | "node" | "toolbox" | "shortcuts";

const ICONS: Record<View, React.ComponentType<{ className?: string }>> = {
  project: FolderGit2,
  characters: Users,
  chat: MessageSquare,
  publish: Calendar,
  jobs: Activity,
  node: Sliders,
  toolbox: Wrench,
  shortcuts: Keyboard,
};

const ORDER: View[] = ["project", "characters", "chat", "publish", "jobs", "node", "toolbox", "shortcuts"];

const NAV_CLOSED = 52;
const NAV_OPEN = 148;
const TOOLBOX_MIN = 360;
const BTN = 38;
const GAP = 2;
const PAD = 8;
const EDGE = 12;
const DOCK_H = ORDER.length * BTN + (ORDER.length - 1) * GAP + PAD * 2;

/**
 * Dock + panel là MỘT khối: khi đóng chỉ là dải biểu tượng; khi mở, khối tự to ra
 * (rộng, cao) và dải biểu tượng hiện thêm nhãn, nội dung nằm liền bên trái.
 */
export function FloatingPanels() {
  const t = useTranslations("rightPanel");
  const locale = useLocale();
  const { activeRightTab, setActiveRightTab, rightPanelCollapsed, setRightPanelCollapsed } =
    useStudioStore();
  const [hubTab, setHubTab] = useState<HubTab>("projects");
  const hostRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 1200, h: 800 });
  // Toolbox: mặc định 35% màn hình, kéo mép trái để to/nhỏ; nhớ lại lần sau
  const [toolboxW, setToolboxW] = useState<number | null>(null);
  const [resizing, setResizing] = useState(false);
  useEffect(() => {
    try {
      const v = Number(window.localStorage.getItem("toolboxPanelW"));
      if (v > 0) setToolboxW(v);
    } catch {}
  }, []);
  const startResize = (e: React.PointerEvent, current: number, max: number) => {
    e.preventDefault();
    const startX = e.clientX;
    setResizing(true);
    let last = current;
    const move = (ev: PointerEvent) => {
      last = Math.max(TOOLBOX_MIN, Math.min(max, current + (startX - ev.clientX)));
      setToolboxW(last);
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      setResizing(false);
      try {
        window.localStorage.setItem("toolboxPanelW", String(Math.round(last)));
      } catch {}
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };

  useEffect(() => {
    const el = hostRef.current;
    if (!el) return;
    let rafId: number | null = null;
    const ro = new ResizeObserver(() => {
      if (rafId !== null) return;
      rafId = window.requestAnimationFrame(() => {
        if (el) setSize({ w: el.clientWidth, h: el.clientHeight });
        rafId = null;
      });
    });
    ro.observe(el);
    setSize({ w: el.clientWidth, h: el.clientHeight });
    return () => {
      if (rafId !== null) window.cancelAnimationFrame(rafId);
      ro.disconnect();
    };
  }, []);

  const running = useStudioStore((st) => st.jobs.filter((j) => j.status === "running" || j.status === "queued").length);
  const pendingTab = useHubScope((h) => h.pendingTab);
  const preview = usePreview((st) => st.item);
  const closePreview = usePreview((st) => st.close);
  const open = !rightPanelCollapsed;
  const view: View =
    activeRightTab === "project" ? (hubTab === "characters" ? "characters" : "project") : (activeRightTab as View);

  const label = (v: View) => t(`tabs.${v}` as any);

  const select = (v: View) => {
    closePreview(); // đổi panel thì tab mở rộng đi kèm phải tắt
    if (open && view === v) {
      setRightPanelCollapsed(true);
      return;
    }
    if (v === "characters") {
      setHubTab("characters");
      setActiveRightTab("project");
    } else if (v === "project") {
      if (hubTab === "characters") setHubTab("projects");
      setActiveRightTab("project");
    } else {
      setActiveRightTab(v as RightPanelTab);
    }
  };

  // Phím tắt toàn cục: Esc đóng xem trước rồi thu gọn panel; ? mở phím tắt; Alt+1..7 chuyển panel
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (useConfirmStore.getState().current) return;
      const el = e.target as HTMLElement | null;
      const typing = !!el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.tagName === "SELECT" || el.isContentEditable);
      if (e.key === "Escape") {
        if (usePreview.getState().item) {
          closePreview();
          e.preventDefault();
        } else if (!useStudioStore.getState().rightPanelCollapsed) {
          setRightPanelCollapsed(true);
          e.preventDefault();
        }
        return;
      }
      if (typing) return;
      if (e.key === "?") {
        e.preventDefault();
        setActiveRightTab("shortcuts");
      } else if (e.altKey && /^[1-7]$/.test(e.code.replace("Digit", ""))) {
        e.preventDefault();
        select(ORDER[Number(e.code.replace("Digit", "")) - 1]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hubTab, open, view]);

  // Nơi khác yêu cầu mở một tab của hub (ví dụ gợi ý "Tạo nhân vật")
  useEffect(() => {
    if (!pendingTab) return;
    setHubTab(pendingTab);
    setActiveRightTab("project");
    useHubScope.getState().clearPending();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingTab]);

  // Đóng panel hoặc đổi panel thì đóng xem trước
  useEffect(() => {
    if (!open) closePreview();
  }, [open, closePreview]);

  const wide = view === "project" || view === "characters";
  const navW = open ? NAV_OPEN : NAV_CLOSED;
  const previewW = open && preview ? Math.max(340, Math.min(640, Math.round(size.w * 0.38))) : 0;
  const maxFree = Math.max(300, size.w - NAV_OPEN - previewW - 24);
  const isToolbox = view === "toolbox";
  const panelW = isToolbox
    ? Math.max(TOOLBOX_MIN, Math.min(maxFree, toolboxW ?? Math.round(size.w * 0.35)))
    : Math.max(300, Math.min(wide ? 720 : 400, maxFree));
  const totalW = Math.min(size.w - EDGE * 2, navW + (open ? panelW : 0) + previewW);
  const height = open ? Math.max(DOCK_H, size.h - EDGE * 2) : DOCK_H;
  const top = open ? EDGE : Math.max(EDGE, (size.h - DOCK_H) / 2);

  const body = () => {
    switch (view) {
      case "project":
      case "characters":
        return <ProjectHub tab={hubTab} onTab={setHubTab} compact />;
      case "chat":
        return <ChatTab />;
      case "node":
        return <NodeTab />;
      case "publish":
        return <PublishTab />;
      case "jobs":
        return (
          <div className="p-3">
            <JobsList compact />
          </div>
        );
      case "toolbox":
        return <ToolboxPanel />;
      case "shortcuts":
        return <ShortcutsView />;
    }
  };

  return (
    <div ref={hostRef} className="pointer-events-none absolute inset-0 z-30 overflow-clip">
      <motion.div
        initial={false}
        animate={{ top, height, width: totalW }}
        transition={{ duration: resizing ? 0 : 0.24, ease: [0.22, 1, 0.36, 1] }}
        style={{
          right: EDGE,
          willChange: "width, height, top",
          transform: "translateZ(0)",
          contain: "paint",
        }}
        className={cn(
          "pointer-events-auto absolute flex overflow-clip rounded-[22px] border border-border bg-card",
          open && "shadow-[0_10px_40px_rgba(0,0,0,0.10)]"
        )}
      >
        {/* Xem trước: mở rộng sang trái khi chọn một mục */}
        <AnimatePresence initial={false}>
          {open && preview && (
            <motion.div
              key="preview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1, transition: { delay: 0.1, duration: 0.18 } }}
              exit={{ opacity: 0, transition: { duration: 0.08 } }}
              style={{ width: previewW }}
              className="h-full shrink-0 overflow-hidden border-r border-border bg-muted/10"
            >
              <PreviewPane item={preview} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Nội dung panel (nằm bên trái dải biểu tượng, cùng một khối) */}
        <div className="relative min-w-0 flex-1 overflow-hidden">
          {open && isToolbox && (
            <div
              role="separator"
              aria-orientation="vertical"
              aria-label="Kéo để đổi độ rộng"
              data-tip="Kéo để đổi độ rộng"
              onPointerDown={(e) => startResize(e, panelW, maxFree)}
              onDoubleClick={() => {
                setToolboxW(null);
                try {
                  window.localStorage.removeItem("toolboxPanelW");
                } catch {}
              }}
              className={cn(
                "absolute inset-y-0 left-0 z-10 w-1.5 cursor-col-resize touch-none transition-colors hover:bg-foreground/15",
                resizing && "bg-foreground/20"
              )}
            />
          )}
          <AnimatePresence initial={false}>
            {open && (
              <motion.div
                key="content"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1, transition: { delay: 0.12, duration: 0.18 } }}
                exit={{ opacity: 0, transition: { duration: 0.08 } }}
                style={{ width: panelW }}
                className="scroll-quiet h-full overflow-y-auto overflow-x-hidden select-text"
                role="dialog"
                aria-label={label(view)}
              >
                {/* Đã mở rồi thì đổi panel không chạy lại animation */}
                <div key={wide ? "hub" : view} className="min-h-full">
                  {body()}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Dải điều hướng: biểu tượng; khi mở thì hiện kèm nhãn */}
        <motion.nav
          animate={{ width: navW }}
          transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
          role="toolbar"
          aria-orientation="vertical"
          aria-label="Panels"
          style={{ padding: PAD, willChange: "width" }}
          className={cn("flex shrink-0 flex-col self-center", open && "h-full self-start border-l border-border")}
        >
          <div className="flex flex-col" style={{ gap: GAP }}>
            {ORDER.map((v) => {
              const I = ICONS[v];
              const active = open && view === v;
              return (
                <motion.button
                  key={v}
                  type="button"
                  title={label(v)}
                  aria-label={label(v)}
                  aria-pressed={active}
                  onClick={() => select(v)}
                  whileTap={{ scale: 0.97 }}
                  style={{ height: BTN }}
                  className={cn(
                    "flex items-center gap-2.5 overflow-hidden rounded-[14px] px-[11px] text-left transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  )}
                >
                  <span className="relative shrink-0">
                    <I className="h-4 w-4" />
                    {v === "jobs" && running > 0 && (
                      <span className="absolute -right-1.5 -top-1.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-brand px-0.5 text-[9px] font-semibold text-white tnum">{running}</span>
                    )}
                  </span>
                  <AnimatePresence initial={false}>
                    {open && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1, transition: { delay: 0.08, duration: 0.15 } }}
                        exit={{ opacity: 0, transition: { duration: 0.06 } }}
                        className="truncate text-[13px] font-medium"
                      >
                        {label(v)}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.button>
              );
            })}
          </div>
        </motion.nav>
      </motion.div>
    </div>
  );
}
