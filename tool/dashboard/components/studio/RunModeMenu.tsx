"use client";

import React, { useState, useRef, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { cn } from "@/lib/utils";
import { useStudioStore } from "@/store";
import { getRunPresetMode, RUN_PRESETS, type RunPolicy, type RunPresetMode } from "@/lib/core-contracts";
import {
  ChevronDown,
  Check,
  Zap,
  Film,
  Sparkles,
  Sliders,
  Volume2,
  Image as ImageIcon,
  Video as VideoIcon,
  FileText,
} from "@/components/ui/icons";

interface RunModeMenuProps {
  className?: string;
}

export function RunModeMenu({ className }: RunModeMenuProps) {
  const { runPolicy, setRunPolicy, setRunPreset } = useStudioStore(
    useShallow((s) => ({
      runPolicy: s.runPolicy || RUN_PRESETS.animatic,
      setRunPolicy: s.setRunPolicy,
      setRunPreset: s.setRunPreset,
    }))
  );

  const [isOpen, setIsOpen] = useState(false);
  const [showCustom, setShowCustom] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const activeMode = getRunPresetMode(runPolicy);

  // Đóng khi bấm ra ngoài
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const presetLabels: Record<
    Exclude<RunPresetMode, "custom">,
    { title: string; subtitle: string; icon: any; color: string }
  > = {
    animatic: {
      title: "Animatic",
      subtitle: "Ảnh thật $0, video tắt, giọng thật trên máy",
      icon: Film,
      color: "text-brand bg-brand/10 border-brand/30",
    },
    quick: {
      title: "Thử nhanh",
      subtitle: "Mọi thứ mock, $0, tức thì",
      icon: Zap,
      color: "text-muted-foreground bg-muted/60 border-border",
    },
    full: {
      title: "Đầy đủ",
      subtitle: "Ảnh thật + Video AI thật + Giọng thật",
      icon: Sparkles,
      color: "text-amber-500 bg-amber-500/10 border-amber-500/30",
    },
  };

  const currentLabel =
    activeMode === "custom"
      ? { title: "Tuỳ chỉnh", color: "text-purple-500 bg-purple-500/10 border-purple-500/30", icon: Sliders }
      : presetLabels[activeMode];

  const CurrentIcon = currentLabel.icon;

  return (
    <div className={cn("relative inline-block text-left", className)} ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        title="Chế độ chạy luồng Studio (Animatic / Thử nhanh / Đầy đủ / Tuỳ chỉnh)"
        className={cn(
          "flex h-8 items-center gap-1.5 rounded-full px-3 text-xs font-medium border transition-colors select-none",
          currentLabel.color
        )}
      >
        <CurrentIcon className="h-3.5 w-3.5 shrink-0" />
        <span>{currentLabel.title}</span>
        <ChevronDown className={cn("h-3 w-3 opacity-60 transition-transform", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1.5 w-72 origin-top-right rounded-xl border bg-popover/95 p-1.5 text-popover-foreground shadow-xl backdrop-blur-md z-50 animate-in fade-in-50 zoom-in-95">
          <div className="px-2.5 py-1.5 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Chế độ chạy
          </div>

          {/* 3 Lựa chọn Preset */}
          <div className="space-y-0.5">
            {/* Animatic (Mặc định khuyên dùng) */}
            <button
              type="button"
              onClick={() => {
                setRunPreset("animatic");
                setShowCustom(false);
                setIsOpen(false);
              }}
              className={cn(
                "w-full flex items-start gap-2.5 rounded-lg px-2.5 py-2 text-left text-xs transition-colors hover:bg-muted/60",
                activeMode === "animatic" && "bg-brand/10 text-brand"
              )}
            >
              <Film className="h-4 w-4 shrink-0 mt-0.5 text-brand" />
              <div className="flex-1 min-w-0">
                <div className="font-semibold flex items-center justify-between">
                  <span>Animatic (Khuyên dùng)</span>
                  {activeMode === "animatic" && <Check className="h-3.5 w-3.5" />}
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Ảnh thật free/local, video tắt, giọng thật OmniVoice
                </p>
              </div>
            </button>

            {/* Thử nhanh (Mock) */}
            <button
              type="button"
              onClick={() => {
                setRunPreset("quick");
                setShowCustom(false);
                setIsOpen(false);
              }}
              className={cn(
                "w-full flex items-start gap-2.5 rounded-lg px-2.5 py-2 text-left text-xs transition-colors hover:bg-muted/60",
                activeMode === "quick" && "bg-muted text-foreground"
              )}
            >
              <Zap className="h-4 w-4 shrink-0 mt-0.5 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <div className="font-semibold flex items-center justify-between">
                  <span>Thử nhanh (Mock)</span>
                  {activeMode === "quick" && <Check className="h-3.5 w-3.5" />}
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Mọi thứ giả lập, kiểm tra luồng, $0
                </p>
              </div>
            </button>

            {/* Đầy đủ (Full Video AI) */}
            <button
              type="button"
              onClick={() => {
                setRunPreset("full");
                setShowCustom(false);
                setIsOpen(false);
              }}
              className={cn(
                "w-full flex items-start gap-2.5 rounded-lg px-2.5 py-2 text-left text-xs transition-colors hover:bg-muted/60",
                activeMode === "full" && "bg-amber-500/10 text-amber-600 dark:text-amber-400"
              )}
            >
              <Sparkles className="h-4 w-4 shrink-0 mt-0.5 text-amber-500" />
              <div className="flex-1 min-w-0">
                <div className="font-semibold flex items-center justify-between">
                  <span>Đầy đủ (Video AI)</span>
                  {activeMode === "full" && <Check className="h-3.5 w-3.5" />}
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Ảnh thật + sinh clip AI theo shot + giọng thật
                </p>
              </div>
            </button>

            {/* Mục Tuỳ chỉnh */}
            <button
              type="button"
              onClick={() => setShowCustom(!showCustom)}
              className={cn(
                "w-full flex items-center justify-between rounded-lg px-2.5 py-2 text-left text-xs transition-colors hover:bg-muted/60",
                (activeMode === "custom" || showCustom) && "bg-muted/40 font-medium"
              )}
            >
              <span className="flex items-center gap-2">
                <Sliders className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span>Tuỳ chỉnh từng loại</span>
              </span>
              <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", showCustom && "rotate-180")} />
            </button>
          </div>

          {/* Form Tuỳ chỉnh chi tiết */}
          {showCustom && (
            <div className="mt-1.5 border-t pt-2 px-1 space-y-2 text-xs">
              {/* Ảnh */}
              <div className="flex items-center justify-between py-1">
                <span className="flex items-center gap-1.5 text-muted-foreground">
                  <ImageIcon className="h-3.5 w-3.5" />
                  <span>Ảnh</span>
                </span>
                <div className="flex items-center gap-1 bg-muted/50 p-0.5 rounded-md">
                  <button
                    type="button"
                    onClick={() => setRunPolicy({ image: "mock" })}
                    className={cn(
                      "px-2 py-0.5 rounded text-[11px] transition-colors",
                      runPolicy.image === "mock" && "bg-background shadow font-semibold"
                    )}
                  >
                    Mock
                  </button>
                  <button
                    type="button"
                    onClick={() => setRunPolicy({ image: "real" })}
                    className={cn(
                      "px-2 py-0.5 rounded text-[11px] transition-colors",
                      runPolicy.image === "real" && "bg-background shadow font-semibold text-brand"
                    )}
                  >
                    Thật
                  </button>
                </div>
              </div>

              {/* Video */}
              <div className="flex items-center justify-between py-1">
                <span className="flex items-center gap-1.5 text-muted-foreground">
                  <VideoIcon className="h-3.5 w-3.5" />
                  <span>Video</span>
                </span>
                <div className="flex items-center gap-1 bg-muted/50 p-0.5 rounded-md">
                  <button
                    type="button"
                    onClick={() => setRunPolicy({ video: "off" })}
                    className={cn(
                      "px-2 py-0.5 rounded text-[11px] transition-colors",
                      runPolicy.video === "off" && "bg-background shadow font-semibold"
                    )}
                  >
                    Tắt
                  </button>
                  <button
                    type="button"
                    onClick={() => setRunPolicy({ video: "mock" })}
                    className={cn(
                      "px-2 py-0.5 rounded text-[11px] transition-colors",
                      runPolicy.video === "mock" && "bg-background shadow font-semibold"
                    )}
                  >
                    Mock
                  </button>
                  <button
                    type="button"
                    onClick={() => setRunPolicy({ video: "real" })}
                    className={cn(
                      "px-2 py-0.5 rounded text-[11px] transition-colors",
                      runPolicy.video === "real" && "bg-background shadow font-semibold text-brand"
                    )}
                  >
                    Thật
                  </button>
                </div>
              </div>

              {/* Giọng đọc */}
              <div className="flex items-center justify-between py-1">
                <span className="flex items-center gap-1.5 text-muted-foreground">
                  <Volume2 className="h-3.5 w-3.5" />
                  <span>Giọng</span>
                </span>
                <div className="flex items-center gap-1 bg-muted/50 p-0.5 rounded-md">
                  <button
                    type="button"
                    onClick={() => setRunPolicy({ voice: "local" })}
                    className={cn(
                      "px-2 py-0.5 rounded text-[11px] transition-colors",
                      runPolicy.voice === "local" && "bg-background shadow font-semibold text-cyan-600 dark:text-cyan-400"
                    )}
                  >
                    Trên máy ($0)
                  </button>
                  <button
                    type="button"
                    onClick={() => setRunPolicy({ voice: "mock" })}
                    className={cn(
                      "px-2 py-0.5 rounded text-[11px] transition-colors",
                      runPolicy.voice === "mock" && "bg-background shadow font-semibold"
                    )}
                  >
                    Mock
                  </button>
                </div>
              </div>

              {/* Kịch bản / Text */}
              <div className="flex items-center justify-between py-1">
                <span className="flex items-center gap-1.5 text-muted-foreground">
                  <FileText className="h-3.5 w-3.5" />
                  <span>Kịch bản</span>
                </span>
                <div className="flex items-center gap-1 bg-muted/50 p-0.5 rounded-md">
                  <button
                    type="button"
                    onClick={() => setRunPolicy({ text: "mock" })}
                    className={cn(
                      "px-2 py-0.5 rounded text-[11px] transition-colors",
                      runPolicy.text === "mock" && "bg-background shadow font-semibold"
                    )}
                  >
                    Mock
                  </button>
                  <button
                    type="button"
                    onClick={() => setRunPolicy({ text: "real" })}
                    className={cn(
                      "px-2 py-0.5 rounded text-[11px] transition-colors",
                      runPolicy.text === "real" && "bg-background shadow font-semibold text-brand"
                    )}
                  >
                    Thật
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
