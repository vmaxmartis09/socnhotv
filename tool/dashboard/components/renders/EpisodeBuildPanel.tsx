"use client";

import React, { useEffect, useState } from "react";
import {
  Clapperboard,
  Sparkles,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  DollarSign,
  FileText,
  Image as ImageIcon,
  Film,
  Download,
  Scissors,
  Layers,
} from "@/components/ui/icons";
import { EpisodePlan, EpisodeBuildStatus, ScenePlan, videoApi } from "@/lib/api/video";

interface EpisodeBuildPanelProps {
  projectId: string;
  episodeId: string;
  initialScript?: string;
  initialTitle?: string;
}

const DEFAULT_SAMPLE_SCRIPT = `Cảnh 1: Phòng khám Bác sĩ Koala
Bi: Bác sĩ Koala ơi, răng của em bị sâu đau quá!
Koala: Để bác xem nào, em ăn nhiều kẹo ngọt mà quên đánh răng đúng không?

Cảnh 2: Hướng dẫn chăm sóc răng miệng
Koala: Mỗi ngày em phải đánh răng 2 lần, sáng và tối nhé!
Bi: Dạ, em nhớ rồi ạ, em sẽ chăm chỉ đánh răng!

Cảnh 3: Kết thúc vui vẻ
Bi: Răng em hết đau rồi, cảm ơn Bác sĩ Koala!
Koala: Chúc Bi luôn vui khỏe và có nụ cười thật tươi!`;

export const EpisodeBuildPanel: React.FC<EpisodeBuildPanelProps> = ({
  projectId,
  episodeId,
  initialScript = DEFAULT_SAMPLE_SCRIPT,
  initialTitle = "Sóc Nhỏ và Chiếc Răng Sâu",
}) => {
  const [title, setTitle] = useState(initialTitle);
  const [script, setScript] = useState(initialScript);
  const [plan, setPlan] = useState<EpisodePlan | null>(null);
  const [status, setStatus] = useState<EpisodeBuildStatus | null>(null);

  const [isPlanning, setIsPlanning] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const [useMock, setUseMock] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Poll status nếu đang rendering
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    const checkStatus = async () => {
      try {
        const st = await videoApi.fetchEpisodeStatus(projectId, episodeId);
        setStatus(st);
        if (st.status === "rendering" || st.status === "queued") {
          // tiếp tục poll
        } else if (interval) {
          clearInterval(interval);
        }
      } catch (e) {
        // Chưa có status hoặc chưa build
      }
    };

    checkStatus();
    interval = setInterval(checkStatus, 3000);
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [projectId, episodeId]);

  const handlePlan = async () => {
    setIsPlanning(true);
    setError(null);
    try {
      const p = await videoApi.planEpisode(projectId, episodeId, script, title);
      setPlan(p);
    } catch (err: any) {
      setError(err.message || "Lỗi khi lập kế hoạch tập phim");
    } finally {
      setIsPlanning(false);
    }
  };

  const handleBuild = async () => {
    setIsBuilding(true);
    setError(null);
    try {
      const res = await videoApi.buildEpisode(projectId, episodeId, useMock);
      setStatus(res);
    } catch (err: any) {
      setError(err.message || "Lỗi khi khởi chạy build tập phim");
    } finally {
      setIsBuilding(false);
    }
  };

  const handleSceneActionChange = (index: number, newAction: string) => {
    if (!plan) return;
    const updatedScenes = [...plan.scenes];
    updatedScenes[index] = { ...updatedScenes[index], action: newAction };
    setPlan({ ...plan, scenes: updatedScenes });
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-neutral-900/60 border border-neutral-800 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400 mb-1">
            <Film className="w-4 h-4" />
            <span>YouTube 16:9 Pipeline + Auto Shorts 9:16</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-neutral-100 flex items-center gap-2">
            <span>Tập Phim: {episodeId.toUpperCase()}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Tuân thủ Scale Lock: Sóc Nhỏ (Bi) 100cm · Bạn Koala 150cm · Master DNA Pixar 3D
          </p>
        </div>

        {status && (
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                status.status === "done"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                  : status.status === "rendering"
                  ? "bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse"
                  : status.status === "failed"
                  ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
              }`}
            >
              {status.status === "rendering" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : status.status === "done" ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
              ) : (
                <Clapperboard className="w-3.5 h-3.5" />
              )}
              <span className="capitalize">{status.status}</span>
            </span>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Script & Planning Input */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <div className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800 space-y-4">
            <div className="flex items-center gap-2 font-semibold text-neutral-200 text-sm">
              <FileText className="w-4 h-4 text-amber-400" />
              <span>Kịch Bản Tập Phim (Script)</span>
            </div>

            <div>
              <label className="block text-xs font-medium text-neutral-400 mb-1.5">
                Tiêu đề tập phim
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-neutral-800/80 border border-neutral-700/80 text-sm text-neutral-100 focus:outline-none focus:border-amber-400/80"
                placeholder="Nhập tên tập phim..."
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-neutral-400">
                  Nội dung kịch bản
                </label>
                <button
                  type="button"
                  onClick={() => setScript(DEFAULT_SAMPLE_SCRIPT)}
                  className="text-[11px] text-amber-400/80 hover:text-amber-300 underline"
                >
                  Nạp mẫu
                </button>
              </div>
              <textarea
                value={script}
                onChange={(e) => setScript(e.target.value)}
                rows={9}
                className="w-full px-3 py-2 rounded-lg bg-neutral-800/80 border border-neutral-700/80 text-xs font-mono text-neutral-200 focus:outline-none focus:border-amber-400/80 leading-relaxed"
                placeholder="Nhập kịch bản phân cảnh..."
              />
            </div>

            <button
              type="button"
              onClick={handlePlan}
              disabled={isPlanning || !script.trim()}
              className="w-full py-2.5 px-4 rounded-xl font-medium text-sm text-neutral-900 bg-amber-400 hover:bg-amber-300 disabled:opacity-50 transition-colors flex items-center justify-center gap-2 shadow-lg shadow-amber-500/10"
            >
              {isPlanning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang phân tích kịch bản...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Phân tích & Lập Kế Hoạch (Plan)</span>
                </>
              )}
            </button>
          </div>

          {/* Action & Cost Panel */}
          {plan && (
            <div className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800 space-y-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
                Ước tính sản xuất
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-neutral-800/40 border border-neutral-700/40">
                  <div className="text-neutral-400 mb-1">Thời lượng</div>
                  <div className="text-base font-semibold text-neutral-200">
                    {plan.total_duration_est}s
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-neutral-800/40 border border-neutral-700/40">
                  <div className="text-neutral-400 mb-1">Chi phí ảnh</div>
                  <div className="text-base font-semibold text-emerald-400">
                    ${plan.estimated_cost_usd}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2 border-t border-neutral-800">
                <input
                  type="checkbox"
                  id="mockMode"
                  checked={useMock}
                  onChange={(e) => setUseMock(e.target.checked)}
                  className="rounded border-neutral-700 text-amber-500 focus:ring-amber-400"
                />
                <label htmlFor="mockMode" className="text-xs text-neutral-300 cursor-pointer">
                  Chế độ Mock (Fast preview / Zero API cost)
                </label>
              </div>

              <button
                type="button"
                onClick={handleBuild}
                disabled={isBuilding}
                className="w-full py-3 px-4 rounded-xl font-bold text-sm text-neutral-900 bg-emerald-400 hover:bg-emerald-300 disabled:opacity-50 transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/10"
              >
                {isBuilding ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Đang khởi động Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Sản Xuất: 1 YouTube + 3 Shorts</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* ScenePlan Table & Preview */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-semibold text-neutral-200 text-sm">
                <Layers className="w-4 h-4 text-amber-400" />
                <span>Danh Sách Phân Cảnh (ScenePlan)</span>
                {plan && (
                  <span className="text-xs text-neutral-400 font-normal">
                    ({plan.scenes.length} cảnh)
                  </span>
                )}
              </div>

              {plan && (
                <div className="text-xs text-amber-400/90 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20 font-medium">
                  Scale Lock: Bi 100cm · Koala 150cm
                </div>
              )}
            </div>

            {!plan ? (
              <div className="text-center py-16 text-neutral-500 text-sm">
                Nhập kịch bản và bấm "Phân tích & Lập Kế Hoạch" để sinh danh sách phân cảnh.
              </div>
            ) : (
              <div className="space-y-3">
                {plan.scenes.map((scene, idx) => (
                  <div
                    key={scene.scene_id}
                    className="p-4 rounded-xl bg-neutral-800/40 border border-neutral-700/60 hover:border-neutral-600 transition-colors space-y-2.5"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-amber-400">Cảnh {scene.scene_number}</span>
                        <span className="text-neutral-400">({scene.duration_est}s)</span>
                        <span className="px-2 py-0.5 rounded bg-neutral-700/50 text-[11px] text-neutral-300">
                          {scene.characters.join(", ")}
                        </span>
                      </div>
                      <span className="text-[11px] text-neutral-400 font-mono">
                        {scene.camera}
                      </span>
                    </div>

                    <div>
                      <input
                        type="text"
                        value={scene.action}
                        onChange={(e) => handleSceneActionChange(idx, e.target.value)}
                        className="w-full px-2.5 py-1.5 rounded-lg bg-neutral-900/60 border border-neutral-700/60 text-xs text-neutral-200 focus:outline-none focus:border-amber-400"
                        placeholder="Mô tả hành động nhân vật..."
                      />
                    </div>

                    {scene.dialogue.length > 0 && (
                      <div className="space-y-1 bg-neutral-900/30 p-2.5 rounded-lg text-xs">
                        {scene.dialogue.map((d, dIdx) => (
                          <div key={dIdx} className="flex gap-2">
                            <span className="font-semibold text-amber-300 min-w-[50px]">
                              {d.speaker}:
                            </span>
                            <span className="text-neutral-300">{d.line}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Results & Deliverables */}
          {status && (
            <div className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800 space-y-4">
              <div className="flex items-center gap-2 font-semibold text-neutral-200 text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Kết Quả Sản Xuất & Tự Động Phân Phối</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {/* Main Video */}
                <div className="p-4 rounded-xl bg-neutral-800/40 border border-neutral-700/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-neutral-200">YouTube 16:9 Chính</span>
                    <span className="text-[11px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono">
                      {status.main_job_id}
                    </span>
                  </div>
                  <p className="text-neutral-400 text-[11px]">
                    {status.chapters ? "Đã sinh chapters.txt & youtube_meta.json" : "Đang chờ render..."}
                  </p>
                  <a
                    href={`/renders`}
                    className="inline-flex items-center gap-1.5 text-amber-400 hover:text-amber-300 text-xs pt-1 font-medium"
                  >
                    <span>Xem hàng đợi Render</span>
                    <RotateCcw className="w-3.5 h-3.5" />
                  </a>
                </div>

                {/* 3 Shorts */}
                <div className="p-4 rounded-xl bg-neutral-800/40 border border-neutral-700/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-neutral-200">3 Video Shorts 9:16</span>
                    <span className="text-[11px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono">
                      {status.shorts_job_ids?.length || 3} jobs
                    </span>
                  </div>
                  <p className="text-neutral-400 text-[11px]">
                    Tự cắt Story clip, Fact/Education và Highlight clip cho TikTok/Reels/Shorts
                  </p>
                  <div className="text-[11px] text-emerald-400/90 font-medium">
                    ✓ Auto-Draft Post kích hoạt (Session C)
                  </div>
                </div>
              </div>

              {/* YouTube Chapters & Metadata preview */}
              {status.chapters && (
                <div className="space-y-1.5 pt-2">
                  <div className="text-xs font-medium text-neutral-400">Chapters YouTube tự động:</div>
                  <pre className="p-3 rounded-lg bg-neutral-950/70 border border-neutral-800 text-[11px] text-neutral-300 font-mono whitespace-pre-wrap">
                    {status.chapters}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
