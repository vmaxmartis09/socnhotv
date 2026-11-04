"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import { useSocialStore } from "@/store/modules/social";
import { videoApi, type RenderJob } from "@/lib/api/video";
import { CORE_URL } from "@/lib/repositories/core";
import {
  Layers,
  RotateCcw,
  X,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  CalendarDays,
  Download,
  Film,
  Play,
  ExternalLink,
} from "@/components/ui/icons";
import { cn } from "@/lib/utils";

type FilterTab = "all" | "running" | "completed" | "failed";

export function JobsCostTab() {
  const t = useTranslations("jobsTab");
  const {
    jobs,
    activeProjectId,
    totalSpentUsd,
    perRunSpendingLimitUsd,
    dailySpendingLimitUsd,
    setActiveRightTab,
    updateJob,
  } = useStudioStore();

  const { openComposer } = useSocialStore();

  const [filter, setFilter] = useState<FilterTab>("all");
  const [remoteJobs, setRemoteJobs] = useState<RenderJob[]>([]);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  // Sync with Core's video render jobs
  const fetchJobs = async () => {
    try {
      const list = await videoApi.listRenderJobs(activeProjectId);
      setRemoteJobs(list);
    } catch {
      // Keep store jobs as fallback
    }
  };

  useEffect(() => {
    if (activeProjectId) {
      fetchJobs();
      const interval = setInterval(fetchJobs, 4000);
      return () => clearInterval(interval);
    }
  }, [activeProjectId]);

  // Combine store jobs and core render jobs
  const combinedJobs = React.useMemo(() => {
    const list: Array<{
      id: string;
      model?: string;
      status: "queued" | "running" | "completed" | "failed";
      progress: number;
      actualCostUsd: number;
      outputs: Record<string, string>;
      createdAt: string;
      error?: string | null;
    }> = [];

    // From Core API
    for (const r of remoteJobs) {
      list.push({
        id: r.job_id,
        model: "HyperFrames Render",
        status: r.status === "done" ? "completed" : (r.status as any),
        progress: r.status === "done" ? 100 : r.status === "rendering" ? 60 : 0,
        actualCostUsd: 0.0,
        outputs: (r.outputs as any) || {},
        createdAt: r.created_at,
        error: r.error,
      });
    }

    // From Store (if not already in remoteJobs)
    for (const s of jobs) {
      if (!list.some((item) => item.id === s.id)) {
        list.push({
          id: s.id,
          model: s.model || s.type,
          status: s.status as any,
          progress: s.progress || 0,
          actualCostUsd: s.actualCostUsd || 0,
          outputs: s.outputUrl ? { default: s.outputUrl } : {},
          createdAt: s.createdAt,
          error: (s as any).error,
        });
      }
    }

    return list.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }, [remoteJobs, jobs]);

  const filteredJobs = combinedJobs.filter((j) => {
    if (filter === "running") return j.status === "running" || j.status === "queued";
    if (filter === "completed") return j.status === "completed";
    if (filter === "failed") return j.status === "failed";
    return true;
  });

  const handleCancel = async (jobId: string) => {
    setCancellingId(jobId);
    try {
      await videoApi.cancelRenderJob(activeProjectId, jobId);
      await fetchJobs();
      updateJob(jobId, { status: "failed" });
    } catch (err: any) {
      alert(`Huỷ job thất bại: ${err.message}`);
    } finally {
      setCancellingId(null);
    }
  };

  const handleSchedulePost = (job: (typeof combinedJobs)[0]) => {
    const outputs = job.outputs || {};
    const mediaUrl =
      outputs.tiktok ||
      outputs.shorts ||
      outputs.reels ||
      outputs.youtube ||
      Object.values(outputs)[0] ||
      "";

    openComposer(
      {
        id: `post_from_${job.id}`,
        title: `Video #${job.id.slice(0, 8)}`,
        media: [{ type: "video", path: mediaUrl }],
        targets: [],
        status: "draft",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as any
    );
    setActiveRightTab("publish");
  };

  const pctDaily = Math.min(
    100,
    Math.round((totalSpentUsd / Math.max(0.5, dailySpendingLimitUsd)) * 100)
  );

  return (
    <div className="p-3.5 space-y-4 text-xs select-none">
      {/* Spending vs Ceilings */}
      <section className="rounded-xl border border-border bg-card p-3.5 space-y-2">
        <h3 className="font-semibold text-foreground flex items-center justify-between">
          <span>{t("budgetTitle")}</span>
          <span className="text-[11px] font-mono text-muted-foreground">
            Trần: ${dailySpendingLimitUsd.toFixed(2)} USD
          </span>
        </h3>
        <div className="space-y-1 text-xs tnum">
          <div className="flex justify-between">
            <span className="text-muted-foreground">
              {t("spentToday", { spent: totalSpentUsd.toFixed(2) })}
            </span>
            <span className="font-medium text-foreground">{pctDaily}%</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded bg-accent">
            <div
              style={{ width: `${pctDaily}%` }}
              className="h-full bg-primary transition-[width]"
            />
          </div>
        </div>
      </section>

      {/* Filter Chips */}
      <div className="flex items-center gap-1.5 border-b border-border pb-2">
        {[
          { id: "all", label: `Tất cả (${combinedJobs.length})` },
          {
            id: "running",
            label: `Chạy (${combinedJobs.filter((j) => j.status === "running" || j.status === "queued").length})`,
          },
          {
            id: "completed",
            label: `Xong (${combinedJobs.filter((j) => j.status === "completed").length})`,
          },
          {
            id: "failed",
            label: `Lỗi (${combinedJobs.filter((j) => j.status === "failed").length})`,
          },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id as FilterTab)}
            className={cn(
              "px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors",
              filter === tab.id
                ? "bg-foreground text-background font-semibold"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Jobs Queue List */}
      <div className="space-y-2.5">
        {filteredJobs.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground text-xs">
            Không có job render nào trong mục này.
          </div>
        ) : (
          filteredJobs.map((j) => {
            const isDone = j.status === "completed";
            const isRunning = j.status === "running" || j.status === "queued";
            const isFailed = j.status === "failed";
            const outputPlatforms = Object.keys(j.outputs || {});

            return (
              <div
                key={j.id}
                className={cn(
                  "rounded-xl border p-3 space-y-2 transition-all",
                  isRunning
                    ? "border-primary/50 bg-primary/5"
                    : isDone
                    ? "border-border bg-card hover:border-border/80"
                    : "border-rose-500/20 bg-rose-500/5"
                )}
              >
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] font-bold text-foreground">
                      #{j.id.slice(0, 10)}
                    </span>
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.2 text-[10px] font-semibold uppercase tracking-wider",
                        isRunning
                          ? "bg-sky-500/10 text-sky-500 border border-sky-500/20"
                          : isDone
                          ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                          : "bg-rose-500/10 text-rose-500 border border-rose-500/20"
                      )}
                    >
                      {isRunning && <Loader2 className="mr-1 inline h-2.5 w-2.5 animate-spin" />}
                      {j.status}
                    </span>
                  </div>

                  <span className="text-[10px] text-muted-foreground">
                    {new Date(j.createdAt).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>

                {/* Progress bar if running */}
                {isRunning && (
                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-muted-foreground">
                      <span>Đang xử lý pipeline HyperFrames...</span>
                      <span>{j.progress}%</span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded bg-accent">
                      <div
                        style={{ width: `${Math.max(5, j.progress)}%` }}
                        className="h-full bg-primary transition-[width] duration-300"
                      />
                    </div>
                  </div>
                )}

                {/* Error message if failed */}
                {isFailed && j.error && (
                  <p className="text-[11px] text-rose-500 line-clamp-2">
                    {j.error}
                  </p>
                )}

                {/* Platform outputs & Action buttons */}
                <div className="flex items-center justify-between pt-1 border-t border-border/60">
                  <div className="flex items-center gap-1.5">
                    {outputPlatforms.map((p) => {
                      const rel = j.outputs[p];
                      const fullUrl = rel.startsWith("http")
                        ? rel
                        : `${CORE_URL}/projects/${activeProjectId}/${rel}`;
                      return (
                        <a
                          key={p}
                          href={fullUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 rounded bg-accent px-1.5 py-0.5 text-[10px] uppercase font-mono text-foreground hover:bg-accent/80"
                        >
                          <Film className="h-3 w-3 text-primary" />
                          <span>{p}</span>
                        </a>
                      );
                    })}
                  </div>

                  <div className="flex items-center gap-1.5">
                    {isRunning && (
                      <button
                        type="button"
                        onClick={() => handleCancel(j.id)}
                        disabled={cancellingId === j.id}
                        className="rounded px-2 py-0.5 text-[11px] text-rose-400 hover:bg-rose-500/10"
                      >
                        {cancellingId === j.id ? "Đang huỷ..." : "Huỷ"}
                      </button>
                    )}

                    {isDone && (
                      <button
                        type="button"
                        onClick={() => handleSchedulePost(j)}
                        className="flex items-center gap-1 rounded-lg bg-primary px-2.5 py-1 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-2xs"
                      >
                        <CalendarDays className="h-3.5 w-3.5" />
                        <span>Đăng / Lên lịch</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
