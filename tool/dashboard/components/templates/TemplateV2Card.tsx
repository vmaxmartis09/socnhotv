"use client";

import React, { useState, useRef } from "react";
import { Film, Play, AlertTriangle, ShieldCheck, Zap, Key, Wrench, CheckCircle2 } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

export interface TemplateV2Data {
  id: string;
  name: string;
  version: number | string;
  kind: string;
  category: string;
  status: "draft" | "runnable" | "verified";
  tier: "A" | "B" | "C";
  requires: {
    tools: string[];
    providers: string[];
    gpu: boolean;
    ffmpeg: boolean;
  };
  recipe: {
    nodes: string[];
    description?: string;
  };
  slots: Array<{
    key: string;
    type: string;
    label?: string;
    description?: string;
    required?: boolean;
    default?: any;
  }>;
  outputs: {
    aspect: string[];
    duration?: {
      min?: number;
      max?: number;
      default?: number;
    };
  };
  sample_output?: string | null;
  verified_on?: string | null;
  sources?: Array<{
    name: string;
    url: string;
    license: string;
    notes?: string;
  }>;
  learned_from?: string[];
  is_available?: boolean;
  missing_requirements?: string[];
  preview_mp4_url?: string;
  preview_jpg_url?: string;
}

interface TemplateV2CardProps {
  template: TemplateV2Data;
  isSelected?: boolean;
  onClick?: () => void;
  onDoubleClick?: () => void;
}

const TIER_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  A: {
    bg: "bg-emerald-500/10 dark:bg-emerald-500/20",
    text: "text-emerald-700 dark:text-emerald-400",
    border: "border-emerald-500/30",
  },
  B: {
    bg: "bg-amber-500/10 dark:bg-amber-500/20",
    text: "text-amber-700 dark:text-amber-400",
    border: "border-amber-500/30",
  },
  C: {
    bg: "bg-rose-500/10 dark:bg-rose-500/20",
    text: "text-rose-700 dark:text-rose-400",
    border: "border-rose-500/30",
  },
};

const STATUS_LABELS: Record<string, { label: string; bg: string; text: string }> = {
  verified: {
    label: "Verified",
    bg: "bg-emerald-500/20",
    text: "text-emerald-600 dark:text-emerald-300",
  },
  runnable: {
    label: "Runnable",
    bg: "bg-blue-500/20",
    text: "text-blue-600 dark:text-blue-300",
  },
  draft: {
    label: "Draft",
    bg: "bg-muted",
    text: "text-muted-foreground",
  },
};

export function TemplateV2Card({
  template,
  isSelected = false,
  onClick,
  onDoubleClick,
}: TemplateV2CardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const isAvailable = template.is_available !== false;
  const missing = template.missing_requirements || [];
  const tierStyle = TIER_COLORS[template.tier] || TIER_COLORS.A;
  const statusBadge = STATUS_LABELS[template.status] || STATUS_LABELS.draft;

  const isLandscape = template.outputs?.aspect?.includes("16:9");
  const previewJpgUrl = template.preview_jpg_url || `/core/video/templates/${template.id}/preview.jpg`;
  const previewMp4Url = template.preview_mp4_url || `/core/video/templates/${template.id}/preview.mp4`;

  const handleMouseEnter = () => {
    setIsHovered(true);
    if (videoRef.current && isAvailable) {
      videoRef.current.currentTime = 0;
      videoRef.current.play().catch(() => {});
    }
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    if (videoRef.current) {
      videoRef.current.pause();
    }
  };

  const tooltipReason = !isAvailable
    ? `Thiếu điều kiện sử dụng:\n• ${missing.join("\n• ")}`
    : `Bấm 1 lần để xem trước chi tiết\nNhấn đúp để dựng đồ thị Studio`;

  return (
    <div
      role="button"
      tabIndex={0}
      title={tooltipReason}
      data-tip={tooltipReason}
      aria-label={`${template.name} — ${template.kind} — Tier ${template.tier}`}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          onClick?.();
        }
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={cn(
        "group relative flex flex-col rounded-2xl border bg-card p-3 text-left transition-all duration-200 select-none cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-ring",
        isSelected
          ? "border-foreground shadow-lg shadow-black/10 ring-1 ring-foreground/20"
          : "border-border hover:border-foreground/30 hover:bg-accent/30",
        !isAvailable && "opacity-65 grayscale-[35%] hover:border-destructive/40"
      )}
    >
      {/* Vùng Media Poster */}
      <div
        className={cn(
          "relative w-full overflow-hidden rounded-xl bg-muted/60 flex items-center justify-center",
          isLandscape ? "aspect-[16/9]" : "aspect-[9/16]"
        )}
      >
        {/* Ảnh thumbnail tĩnh */}
        <img decoding="async" loading="lazy"
          src={previewJpgUrl}
          alt={template.name}
          className={cn(
            "h-full w-full object-cover transition-opacity duration-300",
            isHovered && isAvailable ? "opacity-0" : "opacity-100"
          )}
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />

        {/* Video preview khi hover */}
        {isAvailable && (
          <video
            ref={videoRef}
            src={previewMp4Url}
            muted
            loop
            playsInline
            className={cn(
              "absolute inset-0 h-full w-full object-cover transition-opacity duration-300 pointer-events-none",
              isHovered ? "opacity-100" : "opacity-0"
            )}
          />
        )}

        {/* Placeholder nếu ảnh lỗi */}
        <div className="absolute inset-0 -z-10 flex flex-col items-center justify-center gap-2 p-3 text-center">
          <Film className="h-8 w-8 text-muted-foreground/40" />
          <span className="text-[11px] text-muted-foreground/60 line-clamp-2">
            {template.name}
          </span>
        </div>

        {/* Huy hiệu Góc trên: Tier + Kind */}
        <div className="absolute top-2.5 left-2.5 flex flex-wrap items-center gap-1.5 z-10">
          <span
            className={cn(
              "rounded-full border px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider backdrop-blur-md shadow-xs",
              tierStyle.bg,
              tierStyle.text,
              tierStyle.border
            )}
            title={`Tier ${template.tier}: ${
              template.tier === "A"
                ? "Chạy offline CPU"
                : template.tier === "B"
                ? "Cần khóa API Cloud"
                : "Cần GPU phần cứng"
            }`}
          >
            Tier {template.tier}
          </span>
          <span className="rounded-full bg-background/85 px-2 py-0.5 text-[10px] font-semibold text-foreground/80 backdrop-blur-md border border-border/80">
            {template.kind}
          </span>
        </div>

        {/* Huy hiệu Góc trên phải: Status */}
        <div className="absolute top-2.5 right-2.5 z-10">
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider backdrop-blur-md border border-border/60",
              statusBadge.bg,
              statusBadge.text
            )}
          >
            {statusBadge.label}
          </span>
        </div>

        {/* Huy hiệu Cảnh báo nếu thiếu điều kiện */}
        {!isAvailable && (
          <div className="absolute inset-x-2 bottom-2.5 z-10 flex items-center gap-1.5 rounded-lg bg-destructive/90 px-2.5 py-1 text-[11px] font-medium text-destructive-foreground backdrop-blur-md shadow-sm">
            <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
            <span className="truncate">{missing[0] || "Thiếu điều kiện"}</span>
          </div>
        )}

        {/* Huy hiệu Thời lượng góc dưới nếu khả dụng */}
        {isAvailable && (
          <div className="absolute bottom-2.5 right-2.5 z-10">
            <span className="rounded-md bg-background/85 px-2 py-0.5 text-[11px] font-medium text-foreground backdrop-blur-sm border border-border/80">
              {template.outputs?.duration?.min || 15}s - {template.outputs?.duration?.max || 60}s
            </span>
          </div>
        )}
      </div>

      {/* Thông tin Text bên dưới */}
      <div className="mt-2.5 flex flex-col gap-1">
        <div className="flex items-start justify-between gap-1">
          <h3 className="line-clamp-1 text-[13px] font-bold text-foreground group-hover:text-foreground/80 transition-colors">
            {template.name}
          </h3>
        </div>

        {/* Chuỗi tóm tắt Recipe & Công cụ */}
        <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
          <span className="truncate">
            {template.recipe?.nodes ? `${template.recipe.nodes.length} bước đồ thị` : "Dựng tự động"}
          </span>
          <span>•</span>
          <span className="shrink-0 uppercase font-semibold text-[10px]">
            {template.category}
          </span>
        </div>

        {/* Icon yêu cầu: Tool, Provider, GPU */}
        <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
          {template.requires?.tools?.length > 0 && (
            <span
              className="inline-flex items-center gap-1 rounded bg-muted/80 px-1.5 py-0.5 text-[10px] text-muted-foreground"
              title={`Cần công cụ Toolbox: ${template.requires.tools.join(", ")}`}
            >
              <Wrench className="h-2.5 w-2.5 text-foreground/70" />
              <span>{template.requires.tools.length} tool</span>
            </span>
          )}
          {template.requires?.providers?.length > 0 && (
            <span
              className="inline-flex items-center gap-1 rounded bg-muted/80 px-1.5 py-0.5 text-[10px] text-muted-foreground"
              title={`Cần khóa API: ${template.requires.providers.join(", ")}`}
            >
              <Key className="h-2.5 w-2.5 text-amber-500" />
              <span>{template.requires.providers.join(", ")}</span>
            </span>
          )}
          {template.requires?.gpu && (
            <span
              className="inline-flex items-center gap-1 rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] text-rose-600 dark:text-rose-400"
              title="Yêu cầu GPU NVIDIA"
            >
              <Zap className="h-2.5 w-2.5" />
              <span>GPU</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
