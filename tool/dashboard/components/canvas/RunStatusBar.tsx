"use client";

import React, { useMemo } from "react";
import { LoaderCircle, CircleCheck, CircleAlert, CircleX, X as XNode, Square as SquareNode, ArrowUpRight as ArrowUpRightNode, ChevronUp as ChevronUpNode, ChevronDown as ChevronDownNode, Circle as CircleNode } from "lucide";
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
  nodes?: Array<RunNodeInfo>;
}

export interface RunNodeInfo {
  id: string;
  type: string;
  /** Tên hiển thị của node trên canvas */
  name?: string;
  state: string;
  progressPct?: number;
  /** Việc đang làm / nguồn dữ liệu (vd. "Đọc kịch bản tập ep01 · 30 cảnh") */
  detail?: string;
  model?: string;
  provider?: string;
  estimatedCostUsd?: number;
  costUsd?: number;
  durationSec?: number;
  startedAt?: number;
  logs?: string[];
}

const PROVIDER_LABEL: Record<string, string> = {
  mock: "Mock (không tốn phí)",
  local: "Chạy trên máy",
  local_tool: "Công cụ cục bộ",
  google: "Google",
  gemini: "Google Gemini",
  fal: "fal.ai",
  replicate: "Replicate",
};

interface RunStatusBarProps {
  isRunning: boolean;
  activeRun: RunStateInfo | null;
  onCancel: () => void;
  onOpenJobsTab?: () => void;
  /** Tắt thanh sau khi phiên đã kết thúc (xong / lỗi / đã huỷ). */
  onDismiss?: () => void;
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
  onDismiss,
}) => {
  const currentNodes = activeRun?.nodes || [];
  const rawStatus = activeRun?.status || (isRunning ? "running" : "idle");
  const status = rawStatus === "cancelled" || rawStatus === "canceled" ? "cancelled" : rawStatus;
  const isLive = status === "running" && isRunning;
  const progressPct = Math.min(100, Math.max(0, activeRun?.progressPct ?? (activeRun?.progress ? Math.round(activeRun.progress * 100) : 0)));

  // Isolated local ticker: only re-renders RunStatusBar each second, never canvas
  const [now, setNow] = React.useState(Date.now());
  React.useEffect(() => {
    if (!isLive) return;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [isLive]);

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
      if (status === "completed") return "completed";
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
      const allCompleted = matchNodes.every((n) => ["completed", "succeeded", "skipped"].includes(n.state));

      if (anyFailed) return "failed";
      if (anyRunning) return "running";
      if (allCompleted) return "completed";
      return "pending";
    });
  }, [currentNodes, progressPct, status]);

  const activeStageIndex = stageStatuses.findIndex((s) => s === "running");
  const currentStepNumber = activeStageIndex >= 0 ? activeStageIndex + 1 : Math.min(6, Math.max(1, Math.ceil((progressPct / 100) * 6)));
  const stageName = activeRun?.stage || STAGES[currentStepNumber - 1]?.label || "Đang xử lý";

  const [open, setOpen] = React.useState(false);
  // Đang chạy thì tự mở bảng chi tiết lần đầu để người dùng thấy ngay tiến trình
  const autoOpened = React.useRef(false);
  React.useEffect(() => {
    if (isLive && !autoOpened.current) {
      autoOpened.current = true;
      setOpen(true);
    }
    if (!isLive && !activeRun) autoOpened.current = false;
  }, [isLive, activeRun]);
  const totalCost = currentNodes.reduce((sum, n) => sum + (n.costUsd || 0), 0);
  const totalEst = currentNodes.reduce((sum, n) => sum + (n.estimatedCostUsd || 0), 0);
  const doneCount = currentNodes.filter((n) => ["completed", "succeeded", "skipped"].includes(n.state)).length;
  const finished = status === "completed" || status === "failed" || status === "cancelled";
  const stateIcon =
    status === "completed" ? CircleCheck : status === "failed" ? CircleAlert : status === "cancelled" ? CircleX : LoaderCircle;
  const stateColor =
    status === "completed" ? "text-emerald-400" : status === "failed" ? "text-rose-400" : status === "cancelled" ? "text-zinc-400" : "text-amber-400";
  const stateText =
    status === "completed"
      ? "Hoàn tất"
      : status === "failed"
      ? "Thất bại"
      : status === "cancelled"
      ? `Đã huỷ · dừng ở bước ${currentStepNumber}/6`
      : `Bước ${currentStepNumber}/6 · ${stageName}`;

  // Thoát sớm phải đặt SAU mọi hook (quy tắc hooks của React)
  if (!isRunning && !activeRun) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-auto absolute bottom-4 left-1/2 z-40 -translate-x-1/2 max-w-[calc(100%-2rem)] animate-in fade-in slide-in-from-bottom-2 duration-300"
    >
      {open && currentNodes.length > 0 && (
        <div className="mb-2 w-[min(560px,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/90 text-zinc-100 shadow-xl shadow-black/30 backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-white/10 px-3.5 py-2 text-[11px] text-zinc-400">
            <span>
              {doneCount}/{currentNodes.length} node xong
            </span>
            <span className="tabular-nums">
              Chi phí {totalCost > 0 ? `$${totalCost.toFixed(4)}` : "$0"}
              {totalEst > 0 && totalCost === 0 && isLive ? ` · dự kiến $${totalEst.toFixed(4)}` : ""}
            </span>
          </div>
          <ul className="max-h-[320px] divide-y divide-white/5 overflow-y-auto">
            {currentNodes.map((n) => {
              const skipped = n.state === "skipped";
              const done = ["completed", "succeeded"].includes(n.state);
              const running = n.state === "running";
              const failed = n.state === "failed";
              const icon = done || skipped ? CircleCheck : failed ? CircleAlert : running ? LoaderCircle : CircleNode;
              const color = done ? "text-emerald-400" : skipped ? "text-zinc-500" : failed ? "text-rose-400" : running ? "text-amber-400" : "text-zinc-600";
              const prov = n.provider ? PROVIDER_LABEL[n.provider] || n.provider : "";
              return (
                <li key={n.id} className="space-y-1 px-3.5 py-2">
                  <div className="flex items-center gap-2">
                    <MorphIcon icon={icon} size={14} className={`${color} ${running ? "animate-spin" : ""}`} />
                    <span className="min-w-0 flex-1 truncate text-[13px] font-medium">{n.name || n.id}</span>
                    {n.durationSec !== undefined && (
                      <span className="text-[11px] tabular-nums text-zinc-500">{n.durationSec.toFixed(1)}s</span>
                    )}
                    <span className="w-16 text-right text-[11px] tabular-nums text-zinc-400">
                      {done
                        ? (n.costUsd || 0) > 0
                          ? `$${(n.costUsd || 0).toFixed(4)}`
                          : "$0"
                        : running && n.estimatedCostUsd
                        ? `~$${n.estimatedCostUsd.toFixed(4)}`
                        : ""}
                    </span>
                  </div>
                  {(n.detail || n.model) && (
                    <div className="pl-[22px] text-[11px] leading-snug text-zinc-400">
                      {n.detail && <div>{n.detail}</div>}
                      {n.model && (
                        <div className="text-zinc-500">
                          Model <span className="font-mono text-zinc-300">{n.model}</span>
                          {prov && <> · Nguồn {prov}</>}
                        </div>
                      )}
                    </div>
                  )}
                  {running && (
                    <div className="ml-[22px] h-1 overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full bg-amber-400 transition-[width] duration-300"
                        style={{ width: `${Math.max(6, Math.min(100, n.progressPct ?? 10))}%` }}
                      />
                    </div>
                  )}
                  {(running || failed) && n.logs && n.logs.length > 0 && (
                    <div className="ml-[22px] font-mono text-[10.5px] leading-snug text-zinc-500">
                      {n.logs.slice(-3).map((l, i) => (
                        <div key={i} className="truncate">
                          {l}
                        </div>
                      ))}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
      <div className="mx-auto flex w-fit items-center gap-2.5 rounded-full border border-white/10 bg-zinc-900/85 py-1.5 pl-3 pr-1.5 text-zinc-100 shadow-lg shadow-black/20 backdrop-blur-xl">
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
                    ? status === "running"
                      ? "animate-pulse bg-amber-400"
                      : "bg-zinc-500"
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
          <button
            onClick={() => setOpen((v) => !v)}
            title={open ? "Thu gọn chi tiết" : "Xem chi tiết từng node"}
            aria-label={open ? "Thu gọn chi tiết" : "Xem chi tiết từng node"}
            aria-expanded={open}
            className="flex h-6 w-6 items-center justify-center rounded-full text-zinc-300 transition hover:bg-white/10"
          >
            <MorphIcon icon={open ? ChevronDownNode : ChevronUpNode} spring="snappy" size={13} />
          </button>
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
          {finished && onDismiss && (
            <button
              onClick={onDismiss}
              title="Tắt thanh trạng thái"
              aria-label="Tắt thanh trạng thái"
              className="flex h-6 w-6 items-center justify-center rounded-full text-zinc-300 transition hover:bg-white/10"
            >
              <MorphIcon icon={XNode} size={13} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
