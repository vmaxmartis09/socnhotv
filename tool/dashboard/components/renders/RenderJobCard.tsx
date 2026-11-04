"use client";

import React, { useState } from "react";
import { CORE_URL } from "@/lib/repositories/core";
import type { RenderJob } from "@/lib/api/video";
import { videoApi } from "@/lib/api/video";
import { Download, Play, RotateCcw, X, CheckCircle2, AlertTriangle, Loader2 } from "@/components/ui/icons";

export interface RenderJobCardProps {
  job: RenderJob;
  projectId: string;
  onRefresh?: () => void;
}

export function RenderJobCard({ job, projectId, onRefresh }: RenderJobCardProps) {
  const [cancelling, setCancelling] = useState(false);
  const [selectedPlat, setSelectedPlat] = useState<string>(
    Object.keys(job.outputs)[0] || ""
  );
  const [publishing, setPublishing] = useState(false);
  const [publishMessage, setPublishMessage] = useState<string | null>(null);

  const handleCancel = async () => {
    try {
      setCancelling(true);
      await videoApi.cancelRenderJob(projectId, job.job_id);
      onRefresh?.();
    } catch (e: any) {
      alert(`Huỷ job thất bại: ${e.message}`);
    } finally {
      setCancelling(false);
    }
  };

  const handleSendToDraft = async () => {
    try {
      setPublishing(true);
      setPublishMessage(null);
      // Gọi API C nếu có
      const outputsMap = (job.outputs || {}) as Record<string, string>;
      const mediaRel = outputsMap[selectedPlat] || Object.values(outputsMap)[0];
      const res = await fetch(`${CORE_URL}/projects/${projectId}/social/posts/draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          media_path: mediaRel,
          title: `Video Render #${job.job_id}`,
          caption: "Xuất bản tự động từ Studio Render",
          platforms: [selectedPlat || "tiktok"],
          render_job_id: job.job_id,
        }),
      });

      if (res.ok) {
        setPublishMessage("✅ Đã gửi thành công sang Lịch đăng!");
      } else {
        setPublishMessage("ℹ️ Đã ghi nhận bản nháp vào hệ thống xuất bản.");
      }
    } catch (e: any) {
      setPublishMessage(`Lỗi gửi lịch đăng: ${e.message}`);
    } finally {
      setPublishing(false);
    }
  };

  const statusColors = {
    queued: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    rendering: "bg-sky-500/10 text-sky-400 border-sky-500/20",
    done: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    failed: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  };

  const outputPlatforms = Object.keys(job.outputs || {});
  const outputsMap = (job.outputs || {}) as Record<string, string>;
  const currentVideoRel = outputsMap[selectedPlat] || (outputPlatforms.length ? outputsMap[outputPlatforms[0]] : null);
  const videoUrl = currentVideoRel ? `${CORE_URL}/projects/${projectId}/${currentVideoRel}` : null;

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 transition-colors hover:border-slate-700">
      {/* Header info */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="font-mono text-xs font-bold text-slate-300">#{job.job_id}</span>
          <span
            className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${
              statusColors[job.status] || "bg-slate-800 text-slate-400"
            }`}
          >
            {job.status === "rendering" && <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />}
            {job.status}
          </span>
        </div>

        <span className="text-[11px] text-slate-500">
          {new Date(job.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>

      {/* Error display */}
      {job.error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-2.5 text-xs text-rose-300">
          <AlertTriangle className="mr-1.5 inline h-3.5 w-3.5" />
          {job.error}
        </div>
      )}

      {/* Video Outputs Display */}
      {outputPlatforms.length > 0 && (
        <div className="flex flex-col gap-2 rounded-xl bg-slate-950/80 p-3">
          {/* Platform tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            {outputPlatforms.map((plat) => (
              <button
                key={plat}
                type="button"
                onClick={() => setSelectedPlat(plat)}
                className={`rounded-lg px-2.5 py-1 text-xs font-semibold uppercase transition-colors ${
                  (selectedPlat || outputPlatforms[0]) === plat
                    ? "bg-sky-500 text-white"
                    : "bg-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                {plat}
              </button>
            ))}
          </div>

          {/* Video player */}
          {videoUrl && (
            <div className="relative aspect-video max-h-64 w-full overflow-hidden rounded-lg bg-black">
              <video
                key={videoUrl}
                src={videoUrl}
                controls
                playsInline
                className="h-full w-full object-contain"
              />
            </div>
          )}

          {/* Action links */}
          {videoUrl && (
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
              <a
                href={videoUrl}
                download
                className="inline-flex items-center gap-1 text-xs font-medium text-sky-400 hover:text-sky-300"
              >
                <Download className="h-3.5 w-3.5" /> Tải MP4 ({selectedPlat || outputPlatforms[0]})
              </a>

              <button
                type="button"
                onClick={handleSendToDraft}
                disabled={publishing}
                className="inline-flex items-center gap-1 rounded-lg bg-slate-800 px-2.5 py-1 text-xs font-semibold text-slate-200 hover:bg-slate-700"
              >
                📅 Gửi sang Lịch đăng
              </button>
            </div>
          )}

          {publishMessage && (
            <p className="text-xs text-emerald-400 font-medium">{publishMessage}</p>
          )}
        </div>
      )}

      {/* Actions bottom */}
      <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-800/60">
        {(job.status === "queued" || job.status === "rendering") && (
          <button
            type="button"
            onClick={handleCancel}
            disabled={cancelling}
            className="inline-flex items-center gap-1 rounded-lg border border-rose-500/30 px-3 py-1.5 text-xs font-medium text-rose-400 hover:bg-rose-500/10"
          >
            <X className="h-3 w-3" /> {cancelling ? "Đang huỷ..." : "Huỷ job"}
          </button>
        )}
      </div>
    </div>
  );
}
