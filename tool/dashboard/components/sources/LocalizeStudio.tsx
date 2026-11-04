"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import {
  X,
  Play,
  Wand2,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  ExternalLink,
  Check,
} from "@/components/ui/icons";
import { Link } from "@/i18n/routing";
import { VoiceSelectorWithClone } from "@/components/voice/VoiceSelectorWithClone";
import { cn } from "@/lib/utils";
import type { SourceItem } from "@/lib/api/sources";
import {
  getScript,
  getSourceFileUrl,
  getTranscript,
  localizeSource,
  updateScript,
  updateTranscript,
} from "@/lib/api/sources";

interface LocalizeStudioProps {
  source: SourceItem;
  projectId: string;
  onClose: () => void;
}

export function LocalizeStudio({ source, projectId, onClose }: LocalizeStudioProps) {
  const t = useTranslations("sources");

  // Mode & configuration
  const [mode, setMode] = useState<"R" | "L">("R");
  const [style, setStyle] = useState<"faithful" | "hook_boost" | "character">("faithful");
  const [voiceId, setVoiceId] = useState("soc-nho");
  const [platforms, setPlatforms] = useState<string[]>(["tiktok", "reels", "shorts"]);
  const [submitting, setSubmitting] = useState(false);
  const [localizeResult, setLocalizeResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Subtitles / script state
  const [activeTab, setActiveTab] = useState<"orig" | "vi" | "script">("vi");
  const [origLines, setOrigLines] = useState<any[]>([]);
  const [viLines, setViLines] = useState<any[]>([]);
  const [scriptLines, setScriptLines] = useState<any[]>([]);
  const [loadingLines, setLoadingLines] = useState(false);

  const videoUrl = source.files.video ? getSourceFileUrl(projectId, source.id, "video.mp4") : null;
  const isReferenceOnly = source.rights === "reference_only";

  // Load transcripts & scripts
  const loadData = async () => {
    setLoadingLines(true);
    try {
      const orig = await getTranscript(projectId, source.id, "orig").catch(() => []);
      setOrigLines(orig);
      const vi = await getTranscript(projectId, source.id, "vi").catch(() => []);
      setViLines(vi);
      const scr = await getScript(projectId, source.id, style).catch(() => []);
      setScriptLines(scr);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingLines(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId, source.id, style]);

  const togglePlatform = (p: string) => {
    if (platforms.includes(p)) {
      if (platforms.length > 1) setPlatforms(platforms.filter((x) => x !== p));
    } else {
      setPlatforms([...platforms, p]);
    }
  };

  const handleStartLocalize = async () => {
    if (mode === "L" && isReferenceOnly) {
      setError("Nguồn này đang là 'Chỉ tham khảo'. Chế độ Localize (Mode L) bị khóa để tuân thủ bản quyền.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const res = await localizeSource(projectId, source.id, {
        mode,
        style,
        voice_id: voiceId,
        platforms,
      });
      setLocalizeResult(res);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Lỗi bản địa hoá");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md">
      <div className="relative flex h-[92vh] w-full max-w-7xl flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-3.5 bg-card">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Wand2 className="h-4 w-4" />
            </span>
            <div>
              <h2 className="text-sm font-bold text-foreground">
                Studio Bản Địa Hoá: <span className="font-medium text-muted-foreground">{source.title || source.id}</span>
              </h2>
              <span className="text-[11px] text-muted-foreground uppercase">{source.platform} · {source.rights}</span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 border-b border-rose-500/20 bg-rose-500/10 px-6 py-2.5 text-xs text-rose-500">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 3 Columns Layout */}
        <div className="grid flex-1 grid-cols-1 overflow-hidden md:grid-cols-12 divide-y md:divide-y-0 md:divide-x divide-border">
          {/* Column 1: Video Player (3 cols) */}
          <div className="flex flex-col p-4 md:col-span-3 bg-background/50">
            <span className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Video gốc
            </span>
            <div className="relative aspect-[9/16] w-full max-h-[480px] overflow-hidden rounded-xl bg-black">
              {videoUrl ? (
                <video
                  src={videoUrl}
                  controls
                  className="h-full w-full object-contain"
                  poster={source.files.thumb ? getSourceFileUrl(projectId, source.id, "thumb.jpg") : undefined}
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center p-4 text-center text-xs text-muted-foreground">
                  Chưa có video cục bộ
                </div>
              )}
            </div>
            {source.files.audio && (
              <div className="mt-3 rounded-lg border border-border bg-card p-2 text-xs">
                <span className="block font-medium text-muted-foreground">Audio 16kHz mono đã tách sẵn</span>
              </div>
            )}
          </div>

          {/* Column 2: Subtitle & Script Table (5 cols) */}
          <div className="flex flex-col overflow-hidden p-4 md:col-span-5 bg-card">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex gap-1.5">
                <button
                  type="button"
                  onClick={() => setActiveTab("vi")}
                  className={cn(
                    "rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors",
                    activeTab === "vi" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                  )}
                >
                  Dịch VI ({viLines.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("script")}
                  className={cn(
                    "rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors",
                    activeTab === "script" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                  )}
                >
                  Kịch bản ({scriptLines.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("orig")}
                  className={cn(
                    "rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors",
                    activeTab === "orig" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                  )}
                >
                  Gốc ({origLines.length})
                </button>
              </div>

              <button
                type="button"
                onClick={loadData}
                title="Tải lại bảng câu"
                className="rounded-lg p-1 text-muted-foreground hover:bg-accent"
              >
                <RotateCcw className={loadingLines ? "h-3.5 w-3.5 animate-spin" : "h-3.5 w-3.5"} />
              </button>
            </div>

            {/* Table / List */}
            <div className="flex-1 overflow-y-auto pt-3 space-y-2 pr-1">
              {activeTab === "vi" &&
                viLines.map((line, idx) => (
                  <div key={idx} className="rounded-xl border border-border bg-background p-2.5 text-xs space-y-1">
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span className="font-semibold text-foreground">#{idx + 1}</span>
                      <span className="tnum">{line.start}s - {line.end}s</span>
                    </div>
                    <textarea
                      rows={2}
                      value={line.text}
                      onChange={(e) => {
                        const updated = [...viLines];
                        updated[idx].text = e.target.value;
                        setViLines(updated);
                      }}
                      onBlur={() => updateTranscript(projectId, source.id, viLines, "vi")}
                      className="w-full rounded border border-transparent bg-transparent p-1 text-xs text-foreground focus:border-border focus:bg-card focus:outline-none"
                    />
                  </div>
                ))}

              {activeTab === "script" &&
                scriptLines.map((line, idx) => (
                  <div key={idx} className="rounded-xl border border-border bg-background p-2.5 text-xs space-y-1">
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span className="font-semibold text-primary">#{line.line_idx || idx + 1} ({style})</span>
                      <span className="tnum">{line.start}s - {line.end}s ({line.target_duration_s}s)</span>
                    </div>
                    <textarea
                      rows={2}
                      value={line.text}
                      onChange={(e) => {
                        const updated = [...scriptLines];
                        updated[idx].text = e.target.value;
                        setScriptLines(updated);
                      }}
                      onBlur={() => updateScript(projectId, source.id, scriptLines, style)}
                      className="w-full rounded border border-transparent bg-transparent p-1 text-xs text-foreground focus:border-border focus:bg-card focus:outline-none"
                    />
                  </div>
                ))}

              {activeTab === "orig" &&
                origLines.map((line, idx) => (
                  <div key={idx} className="rounded-xl border border-border bg-background p-2.5 text-xs space-y-1">
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span className="font-semibold text-foreground">#{idx + 1}</span>
                      <span className="tnum">{line.start}s - {line.end}s</span>
                    </div>
                    <p className="text-foreground">{line.text}</p>
                  </div>
                ))}

              {((activeTab === "vi" && viLines.length === 0) ||
                (activeTab === "orig" && origLines.length === 0) ||
                (activeTab === "script" && scriptLines.length === 0)) && (
                <div className="p-8 text-center text-xs text-muted-foreground">
                  Chưa có dữ liệu. Bấm nút "Bắt đầu Bản địa hoá" để tự động nhận diện giọng nói và dịch kịch bản!
                </div>
              )}
            </div>
          </div>

          {/* Column 3: Configuration & Render (4 cols) */}
          <div className="flex flex-col justify-between overflow-y-auto p-4 md:col-span-4 bg-background/50 space-y-5">
            <div className="space-y-4">
              {/* Mode Selection */}
              <div>
                <label className="text-xs font-semibold text-foreground">Chế độ xử lý</label>
                <div className="mt-1.5 grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setMode("R")}
                    className={cn(
                      "flex flex-col items-start rounded-xl border p-2.5 text-left transition-all",
                      mode === "R"
                        ? "border-primary bg-primary/10 text-foreground"
                        : "border-border bg-card text-muted-foreground hover:bg-accent"
                    )}
                  >
                    <span className="text-xs font-bold text-foreground">Mode R (Remake)</span>
                    <span className="text-[10px] text-muted-foreground leading-tight mt-0.5">
                      Học cấu trúc + dựng bằng ảnh/video riêng. An toàn 100%.
                    </span>
                  </button>

                  <button
                    type="button"
                    disabled={isReferenceOnly}
                    onClick={() => setMode("L")}
                    className={cn(
                      "flex flex-col items-start rounded-xl border p-2.5 text-left transition-all relative",
                      isReferenceOnly
                        ? "opacity-50 cursor-not-allowed border-dashed border-border bg-card"
                        : mode === "L"
                        ? "border-primary bg-primary/10 text-foreground"
                        : "border-border bg-card text-muted-foreground hover:bg-accent"
                    )}
                  >
                    <span className="text-xs font-bold text-foreground">Mode L (Localize)</span>
                    <span className="text-[10px] text-muted-foreground leading-tight mt-0.5">
                      Giữ clip gốc + lồng tiếng & khung thương hiệu.
                    </span>
                    {isReferenceOnly && (
                      <span className="absolute -top-2 right-2 rounded bg-amber-500/20 px-1.5 py-0.5 text-[9px] font-semibold text-amber-600 dark:text-amber-400">
                        Khóa
                      </span>
                    )}
                  </button>
                </div>
                {isReferenceOnly && (
                  <p className="mt-1.5 text-[11px] text-amber-600 dark:text-amber-400 flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3 shrink-0" />
                    Nguồn là "Chỉ tham khảo". Để mở Mode L, vui lòng đổi bản quyền sang Sở hữu/Được phép.
                  </p>
                )}
              </div>

              {/* Style Selection */}
              <div>
                <label className="text-xs font-semibold text-foreground">Phong cách viết lại</label>
                <div className="mt-1.5 grid grid-cols-3 gap-1.5">
                  {(["faithful", "hook_boost", "character"] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setStyle(s)}
                      className={cn(
                        "rounded-lg border px-2 py-1.5 text-xs font-medium capitalize transition-colors text-center",
                        style === s
                          ? "border-primary bg-primary/10 text-primary font-bold"
                          : "border-border bg-card text-muted-foreground hover:bg-accent"
                      )}
                    >
                      {s === "faithful" ? "Sát ý" : s === "hook_boost" ? "Hook 3s" : "Sóc Nhỏ"}
                    </button>
                  ))}
                </div>
              </div>

              {/* Voice Selection */}
              <div>
                <label className="text-xs font-semibold text-foreground">Giọng đọc lồng tiếng (TTS)</label>
                <div className="mt-1.5">
                  <VoiceSelectorWithClone
                    value={voiceId}
                    onChange={setVoiceId}
                    projectId={projectId}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Platforms */}
              <div>
                <label className="text-xs font-semibold text-foreground">Nền tảng xuất bản</label>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {["tiktok", "reels", "shorts", "youtube"].map((p) => {
                    const active = platforms.includes(p);
                    return (
                      <button
                        key={p}
                        type="button"
                        onClick={() => togglePlatform(p)}
                        className={cn(
                          "rounded-lg border px-2.5 py-1 text-xs font-medium capitalize",
                          active
                            ? "border-primary bg-primary text-primary-foreground font-semibold"
                            : "border-border bg-card text-muted-foreground hover:bg-accent"
                        )}
                      >
                        {p}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Bottom Actions & Result */}
            <div className="border-t border-border pt-4 space-y-3">
              {localizeResult && (
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-600 dark:text-emerald-400">
                  <div className="flex items-center gap-1.5 font-bold">
                    <Check className="h-4 w-4" /> Bản địa hoá & Đã gửi render!
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[11px]">
                    <span>Job ID: {localizeResult.render_job_id}</span>
                    <Link
                      href="/templates"
                      className="font-bold underline inline-flex items-center gap-0.5"
                    >
                      Xem kết quả render <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              )}

              <button
                type="button"
                disabled={submitting}
                onClick={handleStartLocalize}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-xs font-bold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50"
              >
                <Wand2 className={submitting ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
                {submitting ? "Đang xử lý (ASR, Dịch, TTS)..." : "Bản địa hoá & Kết xuất video"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
