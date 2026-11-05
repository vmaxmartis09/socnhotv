"use client";

import React, { useMemo } from "react";
import { Loader2, Square, ArrowUpRight, CheckCircle2, AlertCircle } from "@/components/ui/icons";

export interface RunStateInfo {
  runId?: string;
  status?: string;
  stage?: string;
  currentNodeId?: string;
  progress?: number;
  progressPct?: number;
  elapsedSec?: number;
  startedAt?: number;
  error?: string;
  nodes?: Array<{
    id: string;
    type: string;
    state: string;
    progressPct?: number;
  }>;
}

interface RunStatusBarProps {
  isRunning: boolean;
  activeRun: RunStateInfo | null;
  onCancel: () => void;
  onOpenJobsTab?: () => void;
}

const STAGES = [
  { key: "script", label: "Kịch bản", types: ["text", "script", "idea"] },
  { key: "voice", label: "Giọng đọc", types: ["character", "voice_tts", "audio"] },
  { key: "captions", label: "Phụ đề", types: ["captions"] },
  { key: "visuals", label: "Hình ảnh", types: ["image", "image_gen", "scene"] },
  { key: "render", label: "Dựng video", types: ["hyperframes_render", "video_gen"] },
  { key: "export", label: "Xuất bản", types: ["export", "quality_check"] },
];

export const RunStatusBar: React.FC<RunStatusBarProps> = ({
  isRunning,
  activeRun,
  onCancel,
  onOpenJobsTab,
}) => {
  if (!isRunning && !activeRun) return null;

  const currentNodes = activeRun?.nodes || [];
  const status = activeRun?.status || (isRunning ? "running" : "idle");
  const progressPct = Math.min(100, Math.max(0, activeRun?.progressPct ?? (activeRun?.progress ? Math.round(activeRun.progress * 100) : 0)));

  // Isolated local ticker: only re-renders RunStatusBar each second, never canvas
  const [now, setNow] = React.useState(Date.now());
  React.useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [isRunning]);

  const elapsed = React.useMemo(() => {
    if (activeRun?.startedAt) {
      return Math.max(0, Math.floor((now - activeRun.startedAt) / 1000));
    }
    return Math.round(activeRun?.elapsedSec || 0);
  }, [activeRun?.startedAt, activeRun?.elapsedSec, now]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  const timeStr = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

  // Tính trạng thái của 6 bước
  const stageStatuses = useMemo(() => {
    return STAGES.map((stg, idx) => {
      const matchNodes = currentNodes.filter((n) => stg.types.includes(n.type));
      if (matchNodes.length === 0) {
        // Dự đoán theo tổng tiến độ % nếu nodes chưa populate
        const stepProgress = ((idx + 1) / STAGES.length) * 100;
        const prevStepProgress = (idx / STAGES.length) * 100;
        if (progressPct >= stepProgress) return "completed";
        if (progressPct > prevStepProgress) return "running";
        return "pending";
      }

      const anyRunning = matchNodes.some((n) => n.state === "running");
      const anyFailed = matchNodes.some((n) => n.state === "failed");
      const allCompleted = matchNodes.every((n) => ["completed", "succeeded"].includes(n.state));

      if (anyFailed) return "failed";
      if (anyRunning) return "running";
      if (allCompleted) return "completed";
      return "pending";
    });
  }, [currentNodes, progressPct]);

  const activeStageIndex = stageStatuses.findIndex((s) => s === "running");
  const currentStepNumber = activeStageIndex >= 0 ? activeStageIndex + 1 : Math.min(6, Math.max(1, Math.ceil((progressPct / 100) * 6)));
  const stageName = activeRun?.stage || STAGES[currentStepNumber - 1]?.label || "Đang xử lý";

  return (
    <div className="absolute top-3 left-4 right-4 z-40 bg-zinc-900/95 border border-zinc-700/80 rounded-xl shadow-2xl backdrop-blur-md p-3.5 text-zinc-100 animate-in fade-in slide-in-from-top duration-300">
      <div className="flex items-center justify-between gap-4 mb-2.5">
        {/* Left: Badge & Stage Info */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1 bg-amber-500/20 border border-amber-500/40 rounded-full text-xs font-medium text-amber-300">
            {status === "running" ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
                <span>Đang chạy</span>
              </>
            ) : status === "completed" ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-300">Hoàn tất</span>
              </>
            ) : status === "failed" ? (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                <span className="text-rose-300">Thất bại</span>
              </>
            ) : (
              <span>Chờ</span>
            )}
          </div>

          <div className="text-sm font-medium tracking-tight flex items-center gap-2">
            <span className="text-zinc-400">Bước {currentStepNumber}/6:</span>
            <span className="text-white font-semibold">{stageName}</span>
          </div>
        </div>

        {/* Right: Timer, Actions */}
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 px-2 py-1 bg-zinc-800/80 rounded-md border border-zinc-700/60 font-mono text-zinc-300">
            <span>⏱</span>
            <span>{timeStr}</span>
          </div>

          {onOpenJobsTab && (
            <button
              onClick={onOpenJobsTab}
              className="px-2.5 py-1 text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 rounded-md flex items-center gap-1 transition"
              title="Xem chi tiết trong tab Jobs"
            >
              <span>Jobs</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          )}

          {status === "running" && (
            <button
              onClick={onCancel}
              className="px-2.5 py-1 text-xs bg-rose-600/90 hover:bg-rose-600 text-white font-medium rounded-md flex items-center gap-1 shadow-sm transition"
            >
              <Square className="w-3 h-3 fill-white" />
              <span>Dừng</span>
            </button>
          )}
        </div>
      </div>

      {/* Stepper 6 Stages */}
      <div className="grid grid-cols-6 gap-2 mb-2">
        {STAGES.map((stg, idx) => {
          const stgStatus = stageStatuses[idx];
          return (
            <div key={stg.key} className="flex flex-col gap-1">
              <div
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  stgStatus === "completed"
                    ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                    : stgStatus === "running"
                    ? "bg-amber-400 animate-pulse shadow-[0_0_10px_rgba(251,191,36,0.6)]"
                    : stgStatus === "failed"
                    ? "bg-rose-500"
                    : "bg-zinc-800"
                }`}
              />
              <div className="flex items-center justify-between text-[11px] px-0.5">
                <span
                  className={`truncate ${
                    stgStatus === "running"
                      ? "text-amber-300 font-semibold"
                      : stgStatus === "completed"
                      ? "text-zinc-300 font-medium"
                      : "text-zinc-500"
                  }`}
                >
                  {idx + 1}. {stg.label}
                </span>
                {stgStatus === "completed" && (
                  <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 shrink-0" />
                )}
                {stgStatus === "running" && (
                  <Loader2 className="w-2.5 h-2.5 text-amber-400 animate-spin shrink-0" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall Progress Bar */}
      <div className="w-full bg-zinc-800/80 rounded-full h-1 overflow-hidden">
        <div
          className="bg-gradient-to-r from-amber-500 via-orange-400 to-emerald-400 h-full transition-all duration-300"
          style={{ width: `${progressPct}%` }}
        />
      </div>
    </div>
  );
};
