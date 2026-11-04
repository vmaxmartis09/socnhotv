"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { Film, Trash2, Activity, Info, ShieldCheck, AlertTriangle } from "@/components/ui/icons";
import { cn } from "@/lib/utils";
import type { SourceItem } from "@/lib/api/sources";
import { getSourceFileUrl } from "@/lib/api/sources";

interface SourceCardProps {
  source: SourceItem;
  projectId: string;
  onSelect: (source: SourceItem) => void;
  onDelete: (sourceId: string, e: React.MouseEvent) => void;
}

export function SourceCard({ source, projectId, onSelect, onDelete }: SourceCardProps) {
  const t = useTranslations("sources");

  // Rights badge styling
  const rightsBadge = () => {
    switch (source.rights) {
      case "owned":
        return {
          label: t("rights.owned"),
          classes: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
          icon: ShieldCheck,
        };
      case "licensed":
      case "permission":
        return {
          label: t(`rights.${source.rights}`),
          classes: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
          icon: ShieldCheck,
        };
      case "reference_only":
      default:
        return {
          label: t("rights.reference_only"),
          classes: "bg-zinc-500/15 text-zinc-600 dark:text-zinc-400 border-zinc-500/30",
          icon: AlertTriangle,
        };
    }
  };

  const badge = rightsBadge();
  const BadgeIcon = badge.icon;
  const thumbUrl = source.files.thumb ? getSourceFileUrl(projectId, source.id, "thumb.jpg") : null;

  const formatDuration = (sec: number) => {
    if (!sec) return "0:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <div
      onClick={() => onSelect(source)}
      className="group relative flex cursor-pointer flex-col overflow-hidden rounded-xl border border-border bg-card transition-all hover:border-foreground/30 hover:shadow-md"
    >
      {/* Thumbnail */}
      <div className="relative aspect-[9/16] max-h-[220px] w-full overflow-hidden bg-muted">
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={source.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            <Film className="h-8 w-8 opacity-40" />
          </div>
        )}

        {/* Platform tag */}
        <span className="absolute left-2 top-2 rounded-md bg-black/60 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wider text-white backdrop-blur-sm">
          {source.platform}
        </span>

        {/* Duration */}
        {source.duration_s > 0 && (
          <span className="absolute bottom-2 right-2 flex items-center gap-1 rounded bg-black/70 px-1.5 py-0.5 text-[11px] font-medium text-white backdrop-blur-sm tnum">
            {formatDuration(source.duration_s)}
          </span>
        )}

        {/* Delete action button */}
        <button
          type="button"
          onClick={(e) => onDelete(source.id, e)}
          title={t("confirmTrash")}
          className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/60 text-white opacity-0 transition-opacity hover:bg-rose-600 group-hover:opacity-100"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Card Info */}
      <div className="flex flex-1 flex-col p-3">
        <h3 className="line-clamp-2 text-xs font-semibold leading-snug text-foreground" title={source.title}>
          {source.title || "Không có tiêu đề"}
        </h3>

        <div className="mt-1 flex items-center justify-between text-[11px] text-muted-foreground">
          <span className="truncate max-w-[120px]">{source.author || "Khuyết danh"}</span>
          {source.stats.views > 0 && (
            <span className="flex items-center gap-1 tnum">
              <Activity className="h-3 w-3" />
              {source.stats.views.toLocaleString()}
            </span>
          )}
        </div>

        {/* Rights badge */}
        <div className="mt-3 flex items-center justify-between">
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium",
              badge.classes
            )}
          >
            <BadgeIcon className="h-3 w-3" />
            {badge.label}
          </span>

          {source.status === "failed" && (
            <span className="text-[10px] font-medium text-rose-500">Lỗi tải</span>
          )}
        </div>
      </div>
    </div>
  );
}
