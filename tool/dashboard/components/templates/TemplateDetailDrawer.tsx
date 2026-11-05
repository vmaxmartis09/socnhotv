"use client";

import { useShallow } from "zustand/react/shallow";
import React, { useState } from "react";
import type { TemplateV2Data } from "./TemplateV2Card";
import {
  Film,
  Play,
  Wrench,
  Key,
  Zap,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  Layers,
  Sparkles,
  X,
} from "@/components/ui/icons";
import { Button } from "@/components/ui/Button";
import { confirm } from "@/lib/confirm";
import { cn } from "@/lib/utils";
import { useRouter } from "@/i18n/routing";
import { useStudioStore } from "@/store";
import { generateTemplateGraph } from "@/lib/template-graphs";

interface TemplateDetailDrawerProps {
  template: TemplateV2Data;
  onClose?: () => void;
}

export function TemplateDetailDrawer({ template, onClose }: TemplateDetailDrawerProps) {
  const router = useRouter();
  const { activeProjectId, setNodesAndEdges } = useStudioStore(
    useShallow((s) => ({ activeProjectId: s.activeProjectId, setNodesAndEdges: s.setNodesAndEdges }))
  );
  const [safeZone, setSafeZone] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);

  const isAvailable = template.is_available !== false;
  const isLandscape = template.outputs?.aspect?.includes("16:9");
  const previewMp4Url = template.preview_mp4_url || `/core/video/templates/${template.id}/preview.mp4`;
  const previewJpgUrl = template.preview_jpg_url || `/core/video/templates/${template.id}/preview.jpg`;

  const handleApplyToStudio = async () => {
    if (!isAvailable) {
      await confirm({
        tone: "warning",
        title: "Template chưa đủ điều kiện",
        message: `Mẫu này đang thiếu:\n${(template.missing_requirements || []).join("\n")}\n\nBạn vẫn muốn dựng khung đồ thị để xem trước cấu trúc?`,
        confirmLabel: "Vẫn dựng khung",
        cancelLabel: "Hủy",
      });
    }

    setIsBuilding(true);
    try {
      // Dựng đồ thị bằng generator
      const bundle = generateTemplateGraph({
        projectId: activeProjectId || "soc-nho-tv",
        template: template as any,
        topic: template.name,
      });

      // Ghi đồ thị vào ReactFlow canvas store
      if (bundle.reactFlowGraph) {
        setNodesAndEdges(bundle.reactFlowGraph.nodes as any, bundle.reactFlowGraph.edges as any);
      }

      onClose?.();
      router.push("/studio");
    } catch (err: any) {
      await confirm({
        tone: "danger",
        title: "Lỗi dựng đồ thị",
        message: err.message || "Không thể khởi tạo đồ thị từ template này.",
      });
    } finally {
      setIsBuilding(false);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-y-auto scroll-quiet p-4 space-y-4 text-left">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 border-b border-border pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-bold uppercase text-primary border border-primary/20">
              Tier {template.tier}
            </span>
            <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold text-muted-foreground uppercase">
              {template.kind}
            </span>
            <span className="text-[11px] font-medium text-muted-foreground capitalize">
              • {template.category}
            </span>
          </div>
          <h2 className="mt-1 text-base font-bold text-foreground">
            {template.name}
          </h2>
        </div>
        {onClose && (
          <button
            type="button"
            title="Đóng xem trước"
            aria-label="Đóng xem trước"
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-border text-muted-foreground hover:bg-accent hover:text-foreground active:scale-95 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Video Preview Player */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span className="font-semibold uppercase tracking-wider text-[10px]">
            Xem trước Video mẫu
          </span>
          {!isLandscape && (
            <button
              type="button"
              onClick={() => setSafeZone((v) => !v)}
              className={cn(
                "rounded px-1.5 py-0.5 text-[10px] font-medium transition-colors border",
                safeZone
                  ? "border-primary bg-primary/15 text-primary"
                  : "border-border text-muted-foreground hover:bg-muted"
              )}
            >
              Safe Zone 9:16
            </button>
          )}
        </div>

        <div
          className={cn(
            "relative mx-auto overflow-hidden rounded-xl bg-black border border-border flex items-center justify-center",
            isLandscape ? "aspect-[16/9] w-full" : "aspect-[9/16] max-h-[360px]"
          )}
        >
          <video
            src={previewMp4Url}
            poster={previewJpgUrl}
            controls
            playsInline
            className="h-full w-full object-contain"
          />

          {/* TikTok Safe Zone Overlay */}
          {safeZone && !isLandscape && (
            <div className="pointer-events-none absolute inset-0 z-20 flex flex-col justify-between">
              <div className="h-[9.4%] w-full border-b border-dashed border-red-500/60 bg-red-500/10 flex items-center justify-center">
                <span className="text-[9px] font-bold text-red-400">Header Zone (180px)</span>
              </div>
              <div className="h-[16.7%] w-full border-t border-dashed border-red-500/60 bg-red-500/10 flex items-center justify-center">
                <span className="text-[9px] font-bold text-red-400">Cart & Captions (320px)</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Cảnh báo thiếu điều kiện nếu có */}
      {!isAvailable && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-destructive">
          <div className="flex items-center gap-1.5 font-bold text-xs">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>Thiếu điều kiện môi trường:</span>
          </div>
          <ul className="mt-1.5 list-disc list-inside space-y-0.5 text-[11px] text-destructive/90">
            {template.missing_requirements?.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Recipe Graph Flow */}
      <div className="rounded-xl border border-border bg-card/60 p-3 space-y-2">
        <span className="block font-semibold uppercase tracking-wider text-[10px] text-muted-foreground">
          Công thức Studio Graph ({template.recipe?.nodes?.length || 0} bước)
        </span>
        <div className="flex flex-wrap items-center gap-1.5">
          {template.recipe?.nodes?.map((node, i) => (
            <React.Fragment key={i}>
              <span className="rounded-md border border-border bg-muted/60 px-2 py-1 text-[11px] font-mono text-foreground font-semibold">
                {node}
              </span>
              {i < (template.recipe.nodes.length - 1) && (
                <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
              )}
            </React.Fragment>
          ))}
        </div>
        {template.recipe?.description && (
          <p className="text-[11px] text-muted-foreground pt-1">
            {template.recipe.description}
          </p>
        )}
      </div>

      {/* Slots Input Fields Summary */}
      <div className="rounded-xl border border-border bg-card/60 p-3 space-y-2">
        <span className="block font-semibold uppercase tracking-wider text-[10px] text-muted-foreground">
          Các ô dữ liệu đầu vào (Slots - {template.slots?.length || 0})
        </span>
        <div className="grid grid-cols-1 gap-1.5 max-h-40 overflow-y-auto scroll-quiet">
          {template.slots?.map((s, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between rounded-lg border border-border/70 bg-background/50 px-2.5 py-1.5 text-xs"
            >
              <div className="flex items-center gap-1.5 truncate">
                <span className="font-semibold text-foreground truncate">
                  {s.label || s.key}
                </span>
                {s.required && (
                  <span className="text-[10px] font-bold text-destructive">*bắt buộc</span>
                )}
              </div>
              <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground uppercase">
                {s.type}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Yêu cầu hệ thống & Giấy phép */}
      <div className="rounded-xl border border-border bg-card/60 p-3 space-y-2 text-xs">
        <span className="block font-semibold uppercase tracking-wider text-[10px] text-muted-foreground">
          Hạ tầng & Nguồn học hỏi
        </span>
        <div className="space-y-1.5 text-[11px]">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Công cụ Toolbox:</span>
            <span className="font-semibold text-foreground">
              {template.requires?.tools?.length ? template.requires.tools.join(", ") : "Không yêu cầu"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Khoá API ngoài:</span>
            <span className="font-semibold text-foreground">
              {template.requires?.providers?.length ? template.requires.providers.join(", ") : "Chạy hoàn toàn Offline"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Yêu cầu GPU:</span>
            <span className="font-semibold text-foreground">
              {template.requires?.gpu ? "Cần GPU NVIDIA" : "CPU Standard"}
            </span>
          </div>
          {template.learned_from && template.learned_from.length > 0 && (
            <div className="flex items-center justify-between pt-1 border-t border-border/60">
              <span className="text-muted-foreground">Thẻ Video Craft:</span>
              <span className="font-mono text-primary font-medium">
                {template.learned_from.join(", ")}
              </span>
            </div>
          )}
          {template.sources && template.sources.length > 0 && (
            <div className="pt-1 border-t border-border/60">
              <span className="text-muted-foreground block mb-1">Nguồn & Giấy phép:</span>
              {template.sources.map((src, i) => (
                <div key={i} className="flex items-center justify-between text-[10px] text-muted-foreground">
                  <span className="font-semibold text-foreground">{src.name}</span>
                  <span className="rounded bg-muted px-1.5 py-0.2">{src.license}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Nút Hành Động Chính (Rule 19: Một nút chính duy nhất) */}
      <div className="pt-2">
        <Button
          onClick={handleApplyToStudio}
          disabled={isBuilding}
          className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-bold shadow-md active:scale-98"
        >
          <Sparkles className="h-4 w-4" />
          <span>{isBuilding ? "Đang dựng đồ thị..." : "Dựng đồ thị vào Studio"}</span>
        </Button>
      </div>
    </div>
  );
}
