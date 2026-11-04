"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { PageBar } from "@/components/studio/PageBar";
import { RenderJobCard } from "@/components/renders/RenderJobCard";
import { videoApi, type RenderJob } from "@/lib/api/video";
import { useVideoStore } from "@/store/modules/video";
import { useStudioStore } from "@/store";
import { Clapperboard, RotateCcw, Loader2 } from "@/components/ui/icons";

export default function RendersPage() {
  const t = useTranslations("video");
  const activeProjectId = useStudioStore((state) => state.activeProjectId || "soc-nho-tv");
  const { renderJobs, setRenderJobs, loading, setLoading } = useVideoStore();
  const [filterStatus, setFilterStatus] = useState<string>("all");

  const loadJobs = async () => {
    try {
      setLoading(true);
      const statusParam = filterStatus === "all" ? undefined : filterStatus;
      const data = await videoApi.listRenderJobs(activeProjectId, statusParam);
      setRenderJobs(data);
    } catch (e) {
      console.error("Lỗi nạp render jobs:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
    // Poll mỗi 3s nếu có job đang rendering/queued
    const interval = setInterval(() => {
      const hasActive = renderJobs.some((j) => j.status === "queued" || j.status === "rendering");
      if (hasActive) {
        loadJobs();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [activeProjectId, filterStatus]);

  const filteredJobs = renderJobs.filter((j) => {
    if (filterStatus === "all") return true;
    return j.status === filterStatus;
  });

  return (
    <div className="relative h-full w-full overflow-clip bg-slate-950 text-slate-100">
      <PageBar page="renders" />
      <div className="scroll-quiet h-full overflow-y-auto">
        <div className="mx-auto max-w-5xl space-y-6 px-4 pb-16 pt-16 md:px-8">
          {/* Header */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
                <Clapperboard className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight text-white">{t("renders")}</h1>
                <p className="text-xs text-slate-400">Tiến trình kết xuất video HyperFrames theo thời gian thực</p>
              </div>
            </div>

            <button
              type="button"
              onClick={loadJobs}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs font-semibold text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Làm mới
            </button>
          </div>

          {/* Status filters */}
          <div className="flex flex-wrap items-center gap-2">
            {[
              { id: "all", label: "Tất cả" },
              { id: "rendering", label: "Đang render" },
              { id: "queued", label: "Đang chờ" },
              { id: "done", label: "Hoàn tất" },
              { id: "failed", label: "Thất bại" },
            ].map((st) => (
              <button
                key={st.id}
                type="button"
                onClick={() => setFilterStatus(st.id)}
                className={`rounded-full px-3.5 py-1 text-xs font-semibold transition-all ${
                  filterStatus === st.id
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                    : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-800"
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {/* Jobs list */}
          <div className="flex flex-col gap-4">
            {filteredJobs.map((job) => (
              <RenderJobCard
                key={job.job_id}
                job={job}
                projectId={activeProjectId}
                onRefresh={loadJobs}
              />
            ))}

            {filteredJobs.length === 0 && !loading && (
              <div className="rounded-2xl border border-dashed border-slate-800 py-16 text-center text-sm text-slate-500">
                {t("noJobs")}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
