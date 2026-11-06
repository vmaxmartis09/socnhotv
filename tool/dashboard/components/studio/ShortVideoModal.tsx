"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useStudioStore } from "@/store";
import {
  X,
  Sparkles,
  Film,
  Check,
  Clock,
  Layers,
  Loader2,
  Play,
  ShieldCheck,
  AlertTriangle,
  DollarSign,
} from "@/components/ui/icons";
import {
  buildShortVideoPreset,
  estimateShortVideoCost,
  SHORT_VIDEO_PRESET_NAME,
} from "@/lib/short-video-preset";
import { runGraphOnCore } from "@/lib/core-api";
import type { RunMode } from "@/lib/core-contracts";

interface ShortVideoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (slug: string) => void;
}

const QUICK_PROMPT_SUGGESTIONS = [
  "Sóc Nhỏ tìm thấy quả thông khổng lồ phát sáng trong rừng sồi",
  "LyLy review áo thun cotton thoáng mát đi chơi hè",
  "Bác Koala hướng dẫn cách rèn luyện thói quen đọc sách cho trẻ",
  "Sóc Nhỏ và bạn bè cùng nhau xây cây cầu bắc qua dòng suối mát",
];

const CHARACTERS = [
  { id: "soc_nho", name: "Sóc Nhỏ (Bi - 100cm)", voiceId: "soc-nho", description: "Nhân vật chính Sóc Nhỏ, nhanh nhẹn, mắt to, đuôi xù" },
  { id: "koala", name: "Bác Koala (150cm)", voiceId: "soc-nho", description: "Bác Koala đeo kính, điềm tĩnh và thông thái" },
  { id: "gobi_koc", name: "LyLy (Gobi KOC)", voiceId: "soc-nho", description: "Cô nàng KOC thời trang trẻ trung, tràn đầy năng lượng" },
];

const DURATIONS = [
  { sec: 30, label: "30 giây", shots: 5, hint: "Chuẩn TikTok / Shorts nhanh gọn" },
  { sec: 45, label: "45 giây", shots: 6, hint: "Nhịp điệu vừa vặn, giữ chân cao" },
  { sec: 60, label: "60 giây", shots: 7, hint: "Kể chuyện đầy đủ các phân đoạn" },
  { sec: 90, label: "90 giây", shots: 9, hint: "Review chi tiết hoặc bài học sâu" },
];

export function ShortVideoModal({ isOpen, onClose, onSuccess }: ShortVideoModalProps) {
  const activeProjectId = useStudioStore((s) => s.activeProjectId) || "soc-nho-tv";
  const createEpisode = useStudioStore((s) => s.createEpisode);
  const selectEpisode = useStudioStore((s) => s.selectEpisode);
  const setNodesAndEdges = useStudioStore((s) => s.setNodesAndEdges);

  // Form State
  const [prompt, setPrompt] = useState("");
  const [mode, setMode] = useState<"static" | "ai_clip">("static");
  const [durationSec, setDurationSec] = useState<number>(30);
  const [aspectRatio, setAspectRatio] = useState<"9:16" | "16:9">("9:16");
  const [characterId, setCharacterId] = useState<string>("soc_nho");
  const [videoModel, setVideoModel] = useState<string>("google-veo-2");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [progressMsg, setProgressMsg] = useState("");

  const selectedChar = useMemo(
    () => CHARACTERS.find((c) => c.id === characterId) || CHARACTERS[0],
    [characterId]
  );

  const selectedDuration = useMemo(
    () => DURATIONS.find((d) => d.sec === durationSec) || DURATIONS[0],
    [durationSec]
  );

  // Live Cost Estimate
  const costEstimate = useMemo(() => {
    return estimateShortVideoCost({
      mode,
      durationSec,
      shotCount: selectedDuration.shots,
      videoModel,
      maxClips: selectedDuration.shots,
    });
  }, [mode, durationSec, selectedDuration.shots, videoModel]);

  if (!isOpen) return null;

  const handleApplyPreset = async (autoRun: boolean = false) => {
    const finalPrompt = prompt.trim() || QUICK_PROMPT_SUGGESTIONS[0];
    setIsSubmitting(true);
    setProgressMsg("Đang khởi tạo preset đồ thị Video ngắn...");

    try {
      // 1. Sinh đồ thị preset
      const bundle = buildShortVideoPreset({
        projectId: activeProjectId,
        topic: finalPrompt,
        characterId: selectedChar.id,
        characterName: selectedChar.name.split(" ")[0],
        durationSec,
        aspectRatio,
        mode,
        videoModel: mode === "ai_clip" ? videoModel : "mock-video",
        maxClips: selectedDuration.shots,
      });

      // 2. Tạo hoặc nạp vào Episode
      const epTitle = `Short: ${finalPrompt.slice(0, 32)}`;
      const newEp = createEpisode(epTitle, {
        customGraph: bundle.reactFlowGraph,
        autoSelect: true,
      });

      // Cập nhật canvas trực tiếp
      setNodesAndEdges(bundle.reactFlowGraph.nodes, bundle.reactFlowGraph.edges, true);

      // 3. Nếu người dùng chọn "Chạy ngay"
      if (autoRun) {
        setProgressMsg("Đang kích hoạt Core Engine chạy video...");
        try {
          await runGraphOnCore(activeProjectId, {
            graph: bundle.coreGraph,
            mode: "all",
            mockMode: mode === "static",
            confirmPaidRun: mode === "ai_clip",
          });
        } catch (runErr) {
          console.warn("Core run triggered with status:", runErr);
        }
      }

      setIsSubmitting(false);
      if (onSuccess) onSuccess(bundle.coreGraph.id);
      onClose();
    } catch (err: any) {
      console.error("Lỗi khi áp dụng preset video ngắn:", err);
      setIsSubmitting(false);
      alert(`Không thể nạp preset: ${err?.message || err}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-border bg-card shadow-2xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Film className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-foreground">
                  {SHORT_VIDEO_PRESET_NAME}
                </h3>
                <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">
                  Luồng H1
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Nhập 1 ý tưởng, tự động tạo kịch bản 4–10 shot, dựng video TikTok 9:16 trong Studio
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form Body */}
        <div className="space-y-5 p-6">
          {/* 1. Ý tưởng / Chủ đề */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              Ý tưởng hoặc chủ đề video:
            </label>
            <textarea
              rows={3}
              placeholder="Ví dụ: Sóc Nhỏ tìm thấy quả thông vàng kỳ diệu dưới gốc sồi già..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary transition-all resize-none"
            />
            {/* Quick chips */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="text-[10px] text-muted-foreground self-center mr-1">Gợi ý nhanh:</span>
              {QUICK_PROMPT_SUGGESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setPrompt(s)}
                  className="rounded-md border border-border/60 bg-muted/30 px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                  {s.slice(0, 36)}...
                </button>
              ))}
            </div>
          </div>

          {/* 2. Chế độ chạy: Ảnh tĩnh ($0) vs Clip AI */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-primary" />
              Chế độ hình ảnh & chuyển động:
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setMode("static")}
                className={`relative flex flex-col items-start p-3.5 rounded-xl border text-left transition-all ${
                  mode === "static"
                    ? "border-primary bg-primary/5 shadow-sm"
                    : "border-border bg-muted/10 hover:border-muted-foreground/40"
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span className="text-xs font-bold text-foreground">Ảnh tĩnh ($0.00 Miễn phí)</span>
                  <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-500">
                    Khuyên dùng
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Ảnh keyframe AI + Giọng OmniVoice + Camera điện ảnh GSAP (pan, zoom, tilt) mượt mà.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setMode("ai_clip")}
                className={`relative flex flex-col items-start p-3.5 rounded-xl border text-left transition-all ${
                  mode === "ai_clip"
                    ? "border-primary bg-primary/5 shadow-sm"
                    : "border-border bg-muted/10 hover:border-muted-foreground/40"
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span className="text-xs font-bold text-foreground">Clip AI chuyển động (Trả phí)</span>
                  <span className="rounded bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold text-amber-500">
                    Qua G3 perShot
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Sinh video clip chuyển động AI thật cho từng shot (Veo / Kling / LTX).
                </p>
              </button>
            </div>
          </div>

          {/* Nếu chọn Clip AI: Chọn model video */}
          {mode === "ai_clip" && (
            <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 space-y-2">
              <label className="text-[11px] font-semibold text-foreground flex items-center justify-between">
                <span>Model sinh video AI (G3 perShot):</span>
                <span className="text-amber-500 text-[10px]">Cần có API Key</span>
              </label>
              <select
                value={videoModel}
                onChange={(e) => setVideoModel(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground outline-none focus:border-primary"
              >
                <option value="google-veo-2">Google Veo 2 (~$0.15/giây) - Đẹp & Ổn định</option>
                <option value="fal-kling-v3-std">Kling v3 Pro (~$0.084/giây) - Mượt mà</option>
                <option value="fal-ltx-video">LTX Video (~$0.05/giây) - Tốc độ nhanh</option>
                <option value="mock-video">Mock Video ($0.00) - Kiểm thử không tốn phí</option>
              </select>
            </div>
          )}

          {/* 3. Thời lượng & Tỉ lệ khung hình */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Thời lượng */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-primary" />
                Thời lượng video:
              </label>
              <div className="grid grid-cols-4 gap-1.5">
                {DURATIONS.map((d) => (
                  <button
                    key={d.sec}
                    type="button"
                    onClick={() => setDurationSec(d.sec)}
                    className={`rounded-lg py-2 text-center text-xs font-semibold transition-all ${
                      durationSec === d.sec
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "border border-border bg-muted/20 text-muted-foreground hover:bg-muted"
                    }`}
                  >
                    <div>{d.sec}s</div>
                    <div className="text-[9px] opacity-80">{d.shots} shot</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Tỉ lệ khung hình */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Film className="h-3.5 w-3.5 text-primary" />
                Tỉ lệ khung hình:
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setAspectRatio("9:16")}
                  className={`rounded-lg py-2 text-center text-xs font-semibold transition-all ${
                    aspectRatio === "9:16"
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "border border-border bg-muted/20 text-muted-foreground hover:bg-muted"
                  }`}
                >
                  9:16 (TikTok / Shorts)
                </button>
                <button
                  type="button"
                  onClick={() => setAspectRatio("16:9")}
                  className={`rounded-lg py-2 text-center text-xs font-semibold transition-all ${
                    aspectRatio === "16:9"
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "border border-border bg-muted/20 text-muted-foreground hover:bg-muted"
                  }`}
                >
                  16:9 (YouTube)
                </button>
              </div>
            </div>
          </div>

          {/* 4. Nhân vật */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">
              Nhân vật chính & Giọng đọc:
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {CHARACTERS.map((char) => (
                <button
                  key={char.id}
                  type="button"
                  onClick={() => setCharacterId(char.id)}
                  className={`flex flex-col items-start p-2.5 rounded-xl border text-left transition-all ${
                    characterId === char.id
                      ? "border-primary bg-primary/5"
                      : "border-border bg-background hover:bg-muted/30"
                  }`}
                >
                  <span className="text-xs font-bold text-foreground">{char.name}</span>
                  <span className="text-[10px] text-muted-foreground">Giọng: {char.voiceId} ($0)</span>
                </button>
              ))}
            </div>
          </div>

          {/* 5. Khung ước tính chi phí (SpendGuard Compliant) */}
          <div className="rounded-xl border border-border bg-muted/30 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <DollarSign className="h-4 w-4 text-emerald-500" />
                Ước tính chi phí (SpendGuard):
              </span>
              <span
                className={`text-sm font-extrabold ${
                  costEstimate.isFree ? "text-emerald-500" : "text-amber-500"
                }`}
              >
                {costEstimate.isFree ? "$0.00 (Miễn phí 100%)" : `~$${costEstimate.totalUsd.toFixed(2)} USD`}
              </span>
            </div>

            <p className="text-[11px] text-muted-foreground">
              {costEstimate.note}
            </p>

            {costEstimate.spendGuardRequired && (
              <div className="flex items-center gap-2 rounded-lg bg-amber-500/10 p-2 text-[11px] text-amber-500 font-medium">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                <span>
                  Quy định an toàn: Mọi khoản phí thật sẽ hỏi ý kiến bạn trước khi trừ tiền.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border px-6 py-4 bg-muted/10">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-lg px-4 py-2 text-xs font-semibold text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            Đóng
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleApplyPreset(false)}
              className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-xs font-semibold text-foreground hover:bg-muted transition-colors shadow-sm"
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Nạp vào Studio Canvas</span>
            </button>

            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleApplyPreset(true)}
              className="flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>{progressMsg || "Đang xử lý..."}</span>
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-current" />
                  <span>Tạo & Chạy ngay</span>
                </>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
