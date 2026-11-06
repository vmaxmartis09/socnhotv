"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useLocale } from "next-intl";
import { CORE_URL } from "@/lib/repositories/core";
import { useStudioStore } from "@/store";
import type { ShotItem, EditorEpisodeResponse, RenderResult } from "./types";
import { ScrubbablePlayer } from "./ScrubbablePlayer";
import { TimelineBar } from "./TimelineBar";
import { ShotCard } from "./ShotCard";
import {
  Film,
  Zap,
  RotateCcw,
  RefreshCw,
  Sliders,
  CheckCircle,
  Filter,
} from "./icons";
import { cn } from "@/lib/utils";
import { confirm, showAlert } from "@/lib/confirm";

interface TimelineEditorProps {
  episodeId?: string;
  onClose?: () => void;
}

export function TimelineEditor({ episodeId: propEpisodeId, onClose }: TimelineEditorProps) {
  const locale = useLocale();
  const isEn = locale === "en";
  const activeProjectId = useStudioStore((s) => s.activeProjectId) || "soc-nho-tv";

  // Lấy episodeId từ prop hoặc tìm episodeId từ node kịch bản đang chọn
  const storeEpisodeId = useStudioStore(
    (s) =>
      (s.nodes.find((n) => n.data?.nodeType === "script" && n.data?.params?.mode === "episode")
        ?.data?.params?.episodeId as string | undefined) || "ep01-nui-lua-trong-bung-bi"
  );
  const episodeId = propEpisodeId || storeEpisodeId;

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<EditorEpisodeResponse | null>(null);
  const [selectedShotId, setSelectedShotId] = useState<string | null>(null);
  const [currentTimeSec, setCurrentTimeSec] = useState(0);
  const [filterMode, setFilterMode] = useState<"all" | "modified" | "disabled" | "p1">("all");
  const [renderLoading, setRenderLoading] = useState(false);
  const [renderResult, setRenderResult] = useState<RenderResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 1. Tải dữ liệu timeline từ Backend
  const fetchTimeline = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await fetch(`${CORE_URL}/projects/${activeProjectId}/editor/${episodeId}`);
      if (!res.ok) {
        throw new Error(isEn ? `Failed to load timeline (${res.status})` : `Không thể tải timeline (${res.status})`);
      }
      const json: EditorEpisodeResponse = await res.json();
      setData(json);
      if (json.shots.length > 0 && !selectedShotId) {
        setSelectedShotId(json.shots[0].shotId);
      }
    } catch (err: any) {
      setErrorMsg(err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeProjectId && episodeId) {
      fetchTimeline();
    }
  }, [activeProjectId, episodeId]);

  // 2. Gửi quyết định chỉnh sửa lên Backend
  const handleApplyDecision = async (
    action: string,
    shotId?: string,
    params?: Record<string, any>
  ) => {
    try {
      const res = await fetch(`${CORE_URL}/projects/${activeProjectId}/editor/${episodeId}/decisions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, shotId, params }),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || (isEn ? "Failed to save decision" : "Lưu quyết định thất bại"));
      }
      const resJson = await res.json();
      if (resJson.effectiveShots && data) {
        setData({
          ...data,
          shots: resJson.effectiveShots,
          effectiveDurationSec: resJson.totalDurationSec || data.effectiveDurationSec,
          hasDecisions: true,
        });
      }
    } catch (err: any) {
      await showAlert(isEn ? "Error" : "Lỗi", err.message || String(err), "danger");
    }
  };

  // 3. Render lại vi sai (Selective Re-render)
  const handleSelectiveRender = async () => {
    try {
      setRenderLoading(true);
      setRenderResult(null);
      const res = await fetch(`${CORE_URL}/projects/${activeProjectId}/editor/${episodeId}/render`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ forceAll: false }),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || (isEn ? "Render failed" : "Render vi sai thất bại"));
      }
      const result: RenderResult = await res.json();
      setRenderResult(result);
      if (data) {
        setData({
          ...data,
          outputVideoUrl: result.videoUrl,
          thumbUrl: result.thumbUrl || data.thumbUrl,
        });
      }
    } catch (err: any) {
      await showAlert(isEn ? "Render Error" : "Lỗi Render", err.message || String(err), "danger");
    } finally {
      setRenderLoading(false);
    }
  };

  // Đồng bộ activeShot theo currentTimeSec khi tua
  const activeShot = useMemo(() => {
    if (!data?.shots) return null;
    if (selectedShotId) {
      const found = data.shots.find((s) => s.shotId === selectedShotId);
      if (found) return found;
    }
    return (
      data.shots.find(
        (s) => s.enabled && currentTimeSec >= s.startSec && currentTimeSec < s.endSec
      ) || data.shots[0] || null
    );
  }, [data?.shots, selectedShotId, currentTimeSec]);

  // Bộ lọc shot
  const filteredShots = useMemo(() => {
    if (!data?.shots) return [];
    if (filterMode === "modified") return data.shots.filter((s) => s.isModified);
    if (filterMode === "disabled") return data.shots.filter((s) => !s.enabled);
    if (filterMode === "p1") return data.shots.filter((s) => s.priority === 1);
    return data.shots;
  }, [data?.shots, filterMode]);

  // Reorder handlers
  const handleMove = (index: number, direction: "up" | "down") => {
    if (!data?.shots) return;
    const currentOrder = data.shots.map((s) => s.shotId);
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= currentOrder.length) return;

    const newOrder = [...currentOrder];
    const temp = newOrder[index];
    newOrder[index] = newOrder[targetIndex];
    newOrder[targetIndex] = temp;

    handleApplyDecision("reorder", undefined, { order: newOrder });
  };

  if (loading) {
    return (
      <div className="flex h-96 w-full items-center justify-center p-8 text-center text-muted-foreground">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 opacity-60" />
        <p className="text-sm">{isEn ? "Loading timeline..." : "Đang nạp timeline theo shot..."}</p>
      </div>
    );
  }

  if (errorMsg || !data) {
    return (
      <div className="p-6 text-center text-destructive space-y-2">
        <p className="font-semibold">{isEn ? "Failed to load timeline" : "Lỗi nạp timeline"}</p>
        <p className="text-xs text-muted-foreground">{errorMsg}</p>
        <button
          onClick={fetchTimeline}
          className="px-3 py-1.5 text-xs rounded-md bg-secondary text-foreground hover:bg-secondary/80 font-medium"
        >
          {isEn ? "Retry" : "Thử lại"}
        </button>
      </div>
    );
  }

  const enabledCount = data.shots.filter((s) => s.enabled).length;
  const modifiedCount = data.shots.filter((s) => s.isModified).length;

  return (
    <div className="flex flex-col h-full w-full bg-background text-foreground overflow-hidden">
      {/* Top Main Navigation & Action Bar */}
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-2.5 bg-card shrink-0">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Sliders className="h-4 w-4" />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-tight text-foreground truncate max-w-xs md:max-w-md">
                {data.title}
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-secondary border border-border text-muted-foreground">
                {data.episodeId}
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground font-mono">
              {Math.floor(data.effectiveDurationSec / 60)}:
              {String(Math.floor(data.effectiveDurationSec % 60)).padStart(2, "0")} · {enabledCount}/{data.shots.length} {isEn ? "shots active" : "shot đang bật"}
              {modifiedCount > 0 && ` · ${modifiedCount} ${isEn ? "modified" : "đã sửa"}`}
            </p>
          </div>
        </div>

        {/* Top Buttons: Reset all, Render Selective */}
        <div className="flex items-center gap-2">
          {data.hasDecisions && (
            <button
              onClick={async () => {
                const ok = await confirm({
                  title: isEn ? "Reset All Edits" : "Đặt lại tất cả",
                  message: isEn
                    ? "Reset all manual edits and restore base script timeline?"
                    : "Đặt lại toàn bộ chỉnh sửa về kịch bản gốc?",
                  tone: "warning",
                  confirmLabel: isEn ? "Reset" : "Đặt lại",
                });
                if (ok) {
                  handleApplyDecision("reset_all");
                }
              }}
              className="px-2.5 py-1.5 rounded-lg border border-border hover:bg-muted text-xs text-muted-foreground hover:text-foreground flex items-center gap-1.5 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>{isEn ? "Reset All" : "Đặt lại tất cả"}</span>
            </button>
          )}

          <button
            onClick={handleSelectiveRender}
            disabled={renderLoading}
            className={cn(
              "px-3.5 py-1.5 rounded-lg font-medium text-xs flex items-center gap-1.5 transition-all shadow-sm",
              renderLoading
                ? "bg-primary/50 text-primary-foreground cursor-wait"
                : "bg-primary text-primary-foreground hover:bg-primary/90"
            )}
            title={isEn ? "Render only changed shots (Incremental Re-render)" : "Render lại chỉ phần bị đổi (tiết kiệm thời gian)"}
          >
            {renderLoading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Zap className="w-3.5 h-3.5 text-amber-300" />
            )}
            <span>
              {renderLoading
                ? (isEn ? "Rendering..." : "Đang render vi sai...")
                : (isEn ? "Selective Render" : "Render lại (Vi sai)")}
            </span>
          </button>
        </div>
      </header>

      {/* Render Benchmark Result Toast Banner */}
      {renderResult && (
        <div className="bg-emerald-500/10 border-b border-emerald-500/30 px-4 py-2 flex items-center justify-between text-xs text-emerald-500 shrink-0">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            <span>
              {isEn ? "Render complete:" : "Render vi sai thành công:"}{" "}
              <strong>{renderResult.renderedShotsCount} {isEn ? "rendered" : "shot render mới"}</strong>,{" "}
              <strong>{renderResult.cachedShotsCount} {isEn ? "cached" : "shot tái sử dụng"}</strong> trong{" "}
              <strong>{renderResult.elapsedSec}s</strong> ({isEn ? "engine" : "bộ dựng"}: {renderResult.engine})
            </span>
          </div>
          <button
            onClick={() => setRenderResult(null)}
            className="text-xs hover:underline text-muted-foreground"
          >
            {isEn ? "Close" : "Đóng"}
          </button>
        </div>
      )}

      {/* Main Two-Column Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 min-h-0 overflow-hidden">
        {/* Left Column (5/12): Scrubbable Player & Timeline Bar */}
        <div className="lg:col-span-5 flex flex-col gap-3 min-h-0 overflow-y-auto pr-1">
          <ScrubbablePlayer
            videoUrl={data.outputVideoUrl}
            thumbUrl={data.thumbUrl}
            totalDurationSec={data.effectiveDurationSec}
            activeShot={activeShot}
            currentTimeSec={currentTimeSec}
            onTimeUpdate={(sec) => setCurrentTimeSec(sec)}
            aspect={data.aspect}
            isEn={isEn}
          />

          <TimelineBar
            shots={data.shots}
            totalDurationSec={data.effectiveDurationSec}
            currentTimeSec={currentTimeSec}
            selectedShotId={selectedShotId}
            onSelectShot={(sid) => setSelectedShotId(sid)}
            onSeek={(t) => setCurrentTimeSec(t)}
          />

          {/* Quick info card */}
          <div className="rounded-xl border border-border/80 bg-card p-3 text-xs space-y-2">
            <div className="flex items-center justify-between text-muted-foreground font-medium">
              <span>{isEn ? "Timeline Overview" : "Thông số kịch bản"}</span>
              <span className="font-mono">{data.aspect}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-secondary/40 rounded p-1.5">
                <span className="block text-[10px] text-muted-foreground">{isEn ? "Total Shots" : "Tổng shot"}</span>
                <span className="font-bold text-sm font-mono">{data.shots.length}</span>
              </div>
              <div className="bg-secondary/40 rounded p-1.5">
                <span className="block text-[10px] text-muted-foreground">{isEn ? "Base Time" : "Thời lượng gốc"}</span>
                <span className="font-bold text-sm font-mono">{data.baseDurationSec}s</span>
              </div>
              <div className="bg-secondary/40 rounded p-1.5">
                <span className="block text-[10px] text-muted-foreground">{isEn ? "Effective" : "Sau chỉnh sửa"}</span>
                <span className="font-bold text-sm font-mono text-primary">{Math.round(data.effectiveDurationSec)}s</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (7/12): Filterable Shot Editing List */}
        <div className="lg:col-span-7 flex flex-col min-h-0 bg-card rounded-xl border border-border shadow-sm overflow-hidden">
          {/* Filter Bar */}
          <div className="flex items-center justify-between border-b border-border px-3.5 py-2 bg-muted/20 shrink-0">
            <div className="flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-semibold text-muted-foreground">
                {isEn ? "Shot List:" : "Danh sách Shot:"}
              </span>
            </div>

            <div className="flex items-center gap-1">
              {[
                { id: "all", labelVi: "Tất cả", labelEn: "All" },
                { id: "modified", labelVi: `Đã sửa (${modifiedCount})`, labelEn: `Modified (${modifiedCount})` },
                { id: "disabled", labelVi: `Đã tắt (${data.shots.length - enabledCount})`, labelEn: `Disabled (${data.shots.length - enabledCount})` },
                { id: "p1", labelVi: "Shot chính P1", labelEn: "Hero P1" },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setFilterMode(f.id as any)}
                  className={cn(
                    "text-[11px] px-2 py-1 rounded transition-colors font-medium",
                    filterMode === f.id
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  )}
                >
                  {isEn ? f.labelEn : f.labelVi}
                </button>
              ))}
            </div>
          </div>

          {/* Scrollable Shot Cards */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3">
            {filteredShots.map((shot, idx) => (
              <ShotCard
                key={shot.shotId}
                shot={shot}
                index={idx}
                totalShots={filteredShots.length}
                isSelected={selectedShotId === shot.shotId}
                onSelect={() => {
                  setSelectedShotId(shot.shotId);
                  setCurrentTimeSec(shot.startSec);
                }}
                onMoveUp={() => handleMove(idx, "up")}
                onMoveDown={() => handleMove(idx, "down")}
                onToggle={(enabled) =>
                  handleApplyDecision("toggle_shot", shot.shotId, { enabled })
                }
                onDurationChange={(durSec) =>
                  handleApplyDecision("update_duration", shot.shotId, { durationSec: durSec })
                }
                onMediaChange={(mediaSrc) =>
                  handleApplyDecision("replace_media", shot.shotId, { mediaSrc })
                }
                onSubtitleChange={(subtitle) =>
                  handleApplyDecision("update_subtitle", shot.shotId, { subtitle })
                }
                onReset={() => handleApplyDecision("reset_shot", shot.shotId)}
                isEn={isEn}
              />
            ))}

            {filteredShots.length === 0 && (
              <div className="p-8 text-center text-muted-foreground text-xs">
                {isEn ? "No shots match the selected filter." : "Không có shot nào phù hợp với bộ lọc."}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
