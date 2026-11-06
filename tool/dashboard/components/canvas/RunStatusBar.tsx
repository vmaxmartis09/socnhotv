"use client";

import React, { useMemo } from "react";
import { LoaderCircle, CircleCheck, CircleAlert, Square as SquareNode, ArrowUpRight as ArrowUpRightNode } from "lucide";
import { MorphIcon } from "@/components/ui/icons";

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

  const stateIcon =
    status === "completed" ? CircleCheck : status === "failed" ? CircleAlert : LoaderCircle;
  const stateColor =
    status === "completed" ? "text-emerald-400" : status === "failed" ? "text-rose-400" : "text-amber-400";
  const stateText =
    status === "completed" ? "Hoàn tất" : status === "failed" ? "Thất bại" : `Bước ${currentStepNumber}/6 · ${stageName}`;

  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-auto absolute bottom-4 left-1/2 z-40 -translate-x-1/2 max-w-[calc(100%-2rem)] animate-in fade-in slide-in-from-bottom-2 duration-300"
    >
      <div className="flex items-center gap-2.5 rounded-full border border-white/10 bg-zinc-900/85 py-1.5 pl-3 pr-1.5 text-zinc-100 shadow-lg shadow-black/20 backdrop-blur-xl">
        <MorphIcon
          icon={stateIcon}
          spring="snappy"
          size={15}
          className={`${stateColor} ${status === "running" ? "animate-spin" : ""}`}
        />
        <span className="max-w-[200px] truncate text-xs font-medium tracking-tight">{stateText}</span>

        {/* 6 chặng dạng vạch nhỏ */}
        <div className="flex items-center gap-1" aria-label="Tiến độ các bước">
          {STAGES.map((stg, idx) => {
            const st = stageStatuses[idx];
            return (
              <span
                key={stg.key}
                title={`${idx + 1}. ${stg.label}`}
                className={`h-1 w-4 rounded-full transition-colors duration-300 ${
                  st === "completed"
                    ? "bg-emerald-400"
                    : st === "running"
                    ? "animate-pulse bg-amber-400"
                    : st === "failed"
                    ? "bg-rose-500"
                    : "bg-white/15"
                }`}
              />
            );
          })}
        </div>

        <span className="font-mono text-[11px] tabular-nums text-zinc-400">{timeStr}</span>

        <div className="flex items-center gap-0.5">
          {onOpenJobsTab && (
            <button
              onClick={onOpenJobsTab}
              title="Xem chi tiết trong tab Jobs"
              aria-label="Mở tab Jobs"
              className="flex h-6 w-6 items-center justify-center rounded-full text-zinc-300 transition hover:bg-white/10"
            >
              <MorphIcon icon={ArrowUpRightNode} size={13} />
            </button>
          )}
          {status === "running" && (
            <button
              onClick={onCancel}
              title="Dừng"
              aria-label="Dừng chạy"
              className="flex h-6 w-6 items-center justify-center rounded-full bg-rose-500/90 text-white transition hover:bg-rose-500"
            >
              <MorphIcon icon={SquareNode} size={11} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
