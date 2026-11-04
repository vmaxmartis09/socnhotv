"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  X,
  Play,
  Scissors,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Hash,
  Music,
  Activity,
  Sparkles,
  MessageSquare,
  Send,
  Wand2,
  Brain,
  Loader2,
} from "@/components/ui/icons";
import { confirm } from "@/lib/confirm";
import { cn } from "@/lib/utils";
import type { SceneCut, SourceItem, RightsType } from "@/lib/api/sources";
import { detectScenes, getSourceFileUrl, updateRights } from "@/lib/api/sources";
import { intelApi } from "@/lib/api/intel";
import { LocalizeStudio } from "./LocalizeStudio";

interface SourceDetailModalProps {
  source: SourceItem;
  projectId: string;
  onClose: () => void;
  onUpdated: (updated: SourceItem) => void;
}

export function SourceDetailModal({ source, projectId, onClose, onUpdated }: SourceDetailModalProps) {
  const router = useRouter();
  const t = useTranslations("sources");
  const [scenes, setScenes] = useState<SceneCut[]>([]);
  const [loadingScenes, setLoadingScenes] = useState(false);
  const [currentRights, setCurrentRights] = useState<RightsType>(source.rights);
  const [rightsNote, setRightsNote] = useState(source.rights_note);
  const [savingRights, setSavingRights] = useState(false);
  const [localizeOpen, setLocalizeOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const videoUrl = source.files.video ? getSourceFileUrl(projectId, source.id, "video.mp4") : null;

  const handleAnalyzeBlueprint = async () => {
    setIsAnalyzing(true);
    try {
      const bp = await intelApi.analyzeVideo(projectId, source.id);
      onClose();
      router.push(`/intel?blueprintId=${bp.id}`);
    } catch (err: any) {
      alert(`Lỗi phân tích Blueprint: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Load scenes.json if available
  useEffect(() => {
    let active = true;
    fetch(getSourceFileUrl(projectId, source.id, "scenes.json"))
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (active && Array.isArray(data)) setScenes(data);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [projectId, source.id]);

  const handleTriggerScenes = async () => {
    setLoadingScenes(true);
    try {
      const res = await detectScenes(projectId, source.id);
      setScenes(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingScenes(false);
    }
  };

  const handleSaveRights = async (newRights: RightsType) => {
    if (source.rights === "reference_only" && newRights !== "reference_only") {
      const ok = await confirm({
        title: "Xác nhận bản quyền sử dụng",
        message: t("confirmRightsChange"),
        tone: "warning",
        confirmLabel: "Tôi cam kết sở hữu bản quyền",
        cancelLabel: "Hủy",
      });
      if (!ok) return;

      setSavingRights(true);
      try {
        const updated = await updateRights(projectId, source.id, newRights, rightsNote, true);
        setCurrentRights(updated.rights);
        onUpdated(updated);
      } catch (err: any) {
        alert(err.message || "Lỗi cập nhật");
      } finally {
        setSavingRights(false);
      }
    } else {
      setSavingRights(true);
      try {
        const updated = await updateRights(projectId, source.id, newRights, rightsNote, false);
        setCurrentRights(updated.rights);
        onUpdated(updated);
      } catch (err: any) {
        alert(err.message || "Lỗi cập nhật");
      } finally {
        setSavingRights(false);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="relative flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="rounded-md bg-foreground/10 px-2 py-0.5 text-xs font-semibold uppercase text-foreground">
              {source.platform}
            </span>
            <h2 className="line-clamp-1 text-base font-semibold text-foreground">
              {source.title || "Chi tiết nguồn nội dung"}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={isAnalyzing}
              onClick={handleAnalyzeBlueprint}
              className="flex items-center gap-1.5 rounded-xl border border-indigo-500/50 bg-indigo-500/10 px-3 py-1.5 text-xs font-bold text-indigo-400 hover:bg-indigo-500/20 disabled:opacity-50"
            >
              {isAnalyzing ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Brain className="h-3.5 w-3.5" />
              )}
              Phân tích cấu trúc
            </button>
            <button
              type="button"
              onClick={() => setLocalizeOpen(true)}
              className="flex items-center gap-1.5 rounded-xl bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground hover:bg-primary/90"
            >
              <Wand2 className="h-3.5 w-3.5" />
              Bản địa hoá
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="grid flex-1 grid-cols-1 gap-6 overflow-y-auto p-6 md:grid-cols-2">
          {/* Left: Video Player & Stats */}
          <div className="flex flex-col gap-4">
            <div className="relative aspect-[9/16] max-h-[440px] w-full overflow-hidden rounded-xl bg-black">
              {videoUrl ? (
                <video
                  src={videoUrl}
                  controls
                  className="h-full w-full object-contain"
                  poster={source.files.thumb ? getSourceFileUrl(projectId, source.id, "thumb.jpg") : undefined}
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
                  {source.error ? `Lỗi: ${source.error}` : "Chưa có tập tin video"}
                </div>
              )}
            </div>

            {/* Stats row */}
            <div className="flex items-center justify-around rounded-xl border border-border bg-background p-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Activity className="h-4 w-4" /> {source.stats.views.toLocaleString()}
              </span>
              <span className="flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-rose-500" /> {source.stats.likes.toLocaleString()}
              </span>
              <span className="flex items-center gap-1.5">
                <MessageSquare className="h-4 w-4" /> {source.stats.comments.toLocaleString()}
              </span>
              <span className="flex items-center gap-1.5">
                <Send className="h-4 w-4" /> {source.stats.shares.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Right: Metadata, Rights & Scenes */}
          <div className="flex flex-col gap-5">
            {/* Rights Configuration */}
            <div className="rounded-xl border border-border bg-background p-4">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Quản lý quyền & bản quyền
              </label>
              <div className="mt-2.5 flex flex-wrap gap-2">
                {(["reference_only", "owned", "licensed", "permission"] as RightsType[]).map((r) => {
                  const active = currentRights === r;
                  return (
                    <button
                      key={r}
                      type="button"
                      disabled={savingRights}
                      onClick={() => handleSaveRights(r)}
                      className={cn(
                        "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                        active
                          ? r === "owned"
                            ? "border-emerald-500 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-semibold"
                            : r === "reference_only"
                            ? "border-zinc-500 bg-zinc-500/15 text-foreground font-semibold"
                            : "border-amber-500 bg-amber-500/15 text-amber-600 dark:text-amber-400 font-semibold"
                          : "border-border bg-card text-muted-foreground hover:bg-accent"
                      )}
                    >
                      {t(`rights.${r}`)}
                    </button>
                  );
                })}
              </div>
              <p className="mt-2 text-[11px] text-muted-foreground">
                {t("rightsNotice")}
              </p>
            </div>

            {/* Author & URL */}
            <div className="space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Tác giả:</span>
                <span className="font-medium text-foreground">{source.author || "Không rõ"}</span>
              </div>
              {source.url && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Đường dẫn:</span>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
                  >
                    Mở gốc <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              )}
            </div>

            {/* Description */}
            {source.description && (
              <div className="rounded-xl border border-border bg-background p-3 text-xs">
                <span className="mb-1 block font-semibold text-muted-foreground">Mô tả:</span>
                <p className="line-clamp-4 text-foreground whitespace-pre-wrap">{source.description}</p>
              </div>
            )}

            {/* Scenes section */}
            <div className="rounded-xl border border-border bg-background p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Scissors className="h-4 w-4 text-primary" />
                  <span className="text-xs font-semibold text-foreground">
                    Phân tách cảnh ({scenes.length})
                  </span>
                </div>
                <button
                  type="button"
                  disabled={loadingScenes}
                  onClick={handleTriggerScenes}
                  className="rounded-md border border-border bg-card px-2.5 py-1 text-[11px] font-medium text-foreground hover:bg-accent"
                >
                  {loadingScenes ? "Đang quét..." : "Quét lại cảnh"}
                </button>
              </div>

              {scenes.length > 0 ? (
                <div className="mt-3 grid grid-cols-3 gap-2 max-h-48 overflow-y-auto pr-1">
                  {scenes.map((sc) => {
                    const scThumb = sc.thumb
                      ? getSourceFileUrl(projectId, source.id, sc.thumb.replace(`raw/${source.id}/`, ""))
                      : null;
                    return (
                      <div key={sc.scene_idx} className="relative overflow-hidden rounded-lg border border-border bg-muted">
                        {scThumb && (
                          <img src={scThumb} alt={`Scene ${sc.scene_idx}`} className="h-16 w-full object-cover" />
                        )}
                        <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1 text-[9px] text-white tnum">
                          {sc.start_s}s - {sc.end_s}s
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="mt-2 text-center text-xs text-muted-foreground">Chưa có dữ liệu phân tách cảnh.</p>
              )}
            </div>
          </div>
        </div>

        {localizeOpen && (
          <LocalizeStudio
            source={source}
            projectId={projectId}
            onClose={() => setLocalizeOpen(false)}
          />
        )}
      </div>
    </div>
  );
}
