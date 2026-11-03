"use client";

import { enterOnce } from "@/lib/motion";
import React, { memo, useState } from "react";
import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { useStudioStore } from "@/store";
import {
  PORT_TYPE_COLORS,
  type StudioNodeData,
} from "@/store/slices/canvasSlice";
import {
  FALLBACK_NODE_TYPES,
  estimateNodeCostUsd,
  isPortCompatible,
} from "@/lib/core-api";
import { useCanvasInteraction } from "@/components/canvas/CanvasContext";
import { NodeBody } from "./NodeBody";
import { CharacterCard } from "@/components/canvas/CharacterCard";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Plus,
  ChevronDown,
  ChevronUp,
  ChevronsDown,
  Sliders,
  Loader2,
  Circle,
  CircleDot,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  FileText,
  Users,
  Layers,
  Sparkles,
  Volume2,
  ShieldCheck,
  Film,
  Download,
} from "@/components/ui/icons";

export type StudioCardNodeType = Node<StudioNodeData, "studioCard">;
export type StudioNodeType = StudioCardNodeType;
export type DataType = string;
export type { StudioNodeData };

export const StudioNode = memo(function StudioNode({
  id,
  data,
  selected,
}: NodeProps<StudioCardNodeType>) {
  const t = useTranslations("canvas");
  const {
    nodeCatalog,
    isMockMode,
    characters,
    flashingNodeId,
    setSelectedNodeId,
  } = useStudioStore();
  const {
    activeDragPort,
    connectedPorts,
    nodeIssues,
    onOpenQuickAdd,
    onRequestRun,
    onOpenNodeInspector,
  } = useCanvasInteraction();


  const def =
    nodeCatalog.find((d) => d.typeName === data.nodeType) ||
    FALLBACK_NODE_TYPES.find((d) => d.typeName === data.nodeType) ||
    FALLBACK_NODE_TYPES[0];

  const categoryLabel = t(`categories.${def.category}` as any);

  // Compute state key: idle, ready, running, succeeded, failed, stale
  const hasAllRequiredInputs = def.inputPorts
    .filter((p) => p.required)
    .every(
      (p) =>
        connectedPorts.has(`${id}:in:${p.name}`) ||
        (data.params &&
          data.params[p.name] !== undefined &&
          data.params[p.name] !== "")
    );

  const stateKey = data.isStale
    ? "stale"
    : data.status === "idle" && hasAllRequiredInputs
    ? "ready"
    : data.status || "idle";

  const stateLabel = t(`status.${stateKey}` as any);
  const estCost = estimateNodeCostUsd(
    def.typeName,
    data.params || {},
    isMockMode
  );
  const issues = nodeIssues[id] || [];
  const isFlashing = flashingNodeId === id;

  // Compact parameter summary
  const compactParams: string[] = [];
  const p = data.params || {};
  if (def.typeName === "character") {
    const ch = characters.find((c) => c.id === p.characterId);
    if (ch) {
      compactParams.push(`${ch.name} (${ch.heightCm} cm)`);
      compactParams.push(ch.voiceId);
    } else if (p.characterId) {
      compactParams.push(String(p.characterId));
    }
  } else {
    if (p.model) compactParams.push(String(p.model));
    if (p.aspectRatio) compactParams.push(String(p.aspectRatio));
    if (p.durationSec) compactParams.push(`${p.durationSec}s`);
    if (p.voiceId) compactParams.push(String(p.voiceId));
    if (p.tempo) compactParams.push(`${p.tempo}x`);
    if (p.targetSceneCount) compactParams.push(`${p.targetSceneCount} cảnh`);
    if (p.thresholdScore) compactParams.push(`>= ${p.thresholdScore}`);
    if (p.template) compactParams.push(String(p.template));
    if (p.outputFileName) compactParams.push(String(p.outputFileName));
  }

  const contentPreview =
    typeof p.content === "string" && p.content.trim() ? p.content.trim() : null;

  // Character reference preview if node is character
  const boundChar =
    def.typeName === "character"
      ? characters.find((c) => c.id === p.characterId)
      : undefined;

  const pinnedIdx = data.pinnedGenerationId
    ? data.generations.findIndex((g) => g.id === data.pinnedGenerationId) + 1
    : data.generations.length;

  const [open, setOpen] = useState(false);
  const expanded = Boolean(selected) || open;

  const CategoryIcon =
    {
      Input: FileText,
      Identity: Users,
      Structure: Layers,
      Intelligence: Sparkles,
      Generation: Sparkles,
      Audio: Volume2,
      Quality: ShieldCheck,
      Composition: Film,
      Output: Download,
    }[def.category as string] || Layers;

  const StatusIcon =
    stateKey === "running"
      ? Loader2
      : stateKey === "succeeded" || stateKey === "completed"
      ? CheckCircle2
      : stateKey === "failed"
      ? AlertTriangle
      : stateKey === "stale"
      ? RotateCcw
      : stateKey === "ready"
      ? CircleDot
      : Circle;
  const statusColor =
    stateKey === "running"
      ? "text-brand"
      : stateKey === "failed"
      ? "text-semantic-danger"
      : stateKey === "succeeded" || stateKey === "completed"
      ? "text-semantic-success"
      : stateKey === "stale"
      ? "text-semantic-warning"
      : stateKey === "ready"
      ? "text-foreground"
      : "text-muted-foreground";

  const summary = compactParams.join(" · ") || contentPreview || def.description;
  const hasError = Boolean(data.errorMessage) || issues.length > 0 || data.status === "failed";

  // Cổng đặt cố định theo px để dây nối không dịch chuyển khi node mở rộng/thu gọn
  const portTop = (i: number) => 56 + i * 22;
  const minH = 48 + Math.max(def.inputPorts.length, def.outputPorts.length, 1) * 22 + 8;

  const portHandle = (
    port: (typeof def.inputPorts)[number],
    index: number,
    side: "in" | "out"
  ) => {
    const isIn = side === "in";
    const portColor = PORT_TYPE_COLORS[port.portType] || "#737373";
    const drag = activeDragPort;
    const other = drag && drag.nodeId !== id && drag.handleType === (isIn ? "source" : "target");
    const compatible =
      other &&
      (isIn
        ? isPortCompatible(drag!.portType, port.portType)
        : isPortCompatible(port.portType, drag!.portType));
    const connected = connectedPorts.has(`${id}:${side}:${port.name}`);
    const missing = isIn && port.required && !connected;
    return (
      <React.Fragment key={`${side}:${port.name}`}>
        <Handle
          id={port.name}
          type={isIn ? "target" : "source"}
          position={isIn ? Position.Left : Position.Right}
          title={`${port.name} · ${t(`portTypes.${port.portType}` as any)}${port.required ? " *" : ""}`}
          aria-label={`${port.name} (${t(`portTypes.${port.portType}` as any)})`}
          style={{
            top: portTop(index),
            [isIn ? "left" : "right"]: -8,
            width: compatible ? 16 : 14,
            height: compatible ? 16 : 14,
            borderRadius: isIn ? "50%" : 4,
            backgroundColor: portColor,
            border: compatible
              ? "2px solid hsl(var(--brand))"
              : missing
              ? "2px solid hsl(var(--danger))"
              : "2px solid hsl(var(--card))",
            boxShadow: missing ? "0 0 0 2px hsl(var(--danger) / 0.25)" : undefined,
            opacity: other && !compatible ? 0.3 : 1,
            transition: "all 150ms",
          }}
        />
        {/* Nhãn cổng hiện khi rê chuột vào card */}
        <span
          style={{ top: portTop(index) - 9, [isIn ? "right" : "left"]: "calc(100% + 12px)" }}
          className="pointer-events-none absolute z-10 whitespace-nowrap rounded border border-border bg-card px-1.5 py-0.5 text-[10px] text-foreground opacity-0 transition-opacity group-hover/node:opacity-100"
        >
          {port.name}
          {port.required ? " *" : ""}
        </span>
      </React.Fragment>
    );
  };

  const IconBtn = ({
    label,
    onClick,
    children,
    className,
  }: {
    label: string;
    onClick: () => void;
    children: React.ReactNode;
    className?: string;
  }) => (
    <button
      type="button"
      title={label}
      aria-label={label}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className={cn(
        "nodrag flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground active:scale-90",
        className
      )}
    >
      {children}
    </button>
  );

  return (
    <motion.div
      tabIndex={0}
      role="group"
      aria-label={`${def.displayName} (${stateLabel})`}
      initial={enterOnce(`node:${id}`, { opacity: 0 })}
      animate={{ opacity: 1, width: expanded ? 366 : 270 }}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          e.stopPropagation();
          onRequestRun("single_node", id);
        }
      }}
      className={cn(
        "group/node relative rounded-[10px] border bg-card text-foreground select-none transition-colors",
        stateKey === "stale" && "opacity-80",
        stateKey === "running" && "node-running",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        isFlashing
          ? "border-brand bg-brand/5"
          : hasError
          ? "border-semantic-danger"
          : selected
          ? "border-foreground"
          : "border-border hover:border-foreground/40"
      )}
      style={{ boxShadow: "none", minHeight: minH }}
    >
      {stateKey === "running" && (
        <div className="pointer-events-none absolute inset-x-2 bottom-0 h-0.5 overflow-hidden rounded-full bg-muted">
          <motion.div
            className="h-full bg-brand"
            animate={{ width: typeof data.progressPct === "number" ? `${Math.max(4, data.progressPct)}%` : ["10%", "90%", "10%"] }}
            transition={typeof data.progressPct === "number" ? { duration: 0.3 } : { repeat: Infinity, duration: 1.6, ease: "easeInOut" }}
          />
        </div>
      )}
      {def.inputPorts.map((p, i) => portHandle(p, i, "in"))}
      {def.outputPorts.map((p, i) => portHandle(p, i, "out"))}

      {/* Dòng đầu: biểu tượng loại, tên, trạng thái, chạy, mở rộng */}
      <div className="flex h-11 items-center gap-2 px-3">
        <span
          title={categoryLabel}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent text-foreground"
        >
          <CategoryIcon className="h-3.5 w-3.5" />
        </span>
        <span className="min-w-0 flex-1 truncate text-[15px] font-semibold" title={def.displayName}>
          {def.displayName}
        </span>
        <span title={`${stateLabel}${stateKey === "running" && typeof data.progressPct === "number" ? ` ${Math.round(data.progressPct)}%` : ""}`} className={cn("flex h-6 w-6 items-center justify-center", statusColor)}>
          <StatusIcon className={cn("h-3.5 w-3.5", stateKey === "running" && "animate-spin")} />
        </span>
        <IconBtn label={t("runNode")} onClick={() => onRequestRun("single_node", id)}>
          <Play className="h-3 w-3" />
        </IconBtn>
        <IconBtn label={expanded ? "Thu gọn" : "Mở rộng"} onClick={() => setOpen((v) => !v)}>
          {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </IconBtn>
      </div>

      {/* Tóm tắt một dòng khi thu gọn */}
      {!expanded && (
        <div className="px-3 pb-3">
          <p className="truncate text-[13px] text-muted-foreground" title={summary}>
            {summary}
          </p>
          {boundChar?.referenceImages?.[0] && (
            <div className="mt-1.5 flex items-center gap-1.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={boundChar.referenceImages[0]}
                alt={boundChar.name}
                className="h-7 w-7 rounded border border-border object-cover object-top"
              />
              <span className="truncate text-xs text-foreground">{boundChar.name}</span>
            </div>
          )}
        </div>
      )}

      {/* Phần mở rộng: thuộc tính, cổng, xem trước, chạy */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="space-y-2 border-t border-border/70 px-2.5 py-2">
              <p className="text-xs text-muted-foreground">{def.description}</p>

              <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                <div className="space-y-1">
                  {def.inputPorts.map((port) => {
                    const connected = connectedPorts.has(`${id}:in:${port.name}`);
                    return (
                      <div key={port.name} className="flex items-center gap-1 text-xs">
                        <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: PORT_TYPE_COLORS[port.portType] || "#737373" }} />
                        <span className={cn("truncate", connected ? "text-foreground" : port.required ? "text-brand" : "text-muted-foreground")} title={`${t(`portTypes.${port.portType}` as any)} · ${port.required ? t("portRequired") : t("portOptional")}`}>
                          {port.name}{port.required && !connected ? " *" : ""}
                        </span>
                        <button
                          type="button"
                          title={t("addUpstreamPort")}
                          aria-label={`${t("addUpstreamPort")}: ${port.name}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenQuickAdd({ anchorNodeId: id, direction: "before", portName: port.name, portType: port.portType });
                          }}
                          className="nodrag ml-auto flex h-4 w-4 shrink-0 items-center justify-center rounded border border-border text-muted-foreground hover:bg-accent hover:text-foreground"
                        >
                          <Plus className="h-2.5 w-2.5" />
                        </button>
                      </div>
                    );
                  })}
                </div>
                <div className="space-y-1">
                  {def.outputPorts.map((port) => (
                    <div key={port.name} className="flex items-center justify-end gap-1 text-xs">
                      <button
                        type="button"
                        title={t("addDownstreamPort")}
                        aria-label={`${t("addDownstreamPort")}: ${port.name}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenQuickAdd({ anchorNodeId: id, direction: "after", portName: port.name, portType: port.portType });
                        }}
                        className="nodrag mr-auto flex h-4 w-4 shrink-0 items-center justify-center rounded border border-border text-muted-foreground hover:bg-accent hover:text-foreground"
                      >
                        <Plus className="h-2.5 w-2.5" />
                      </button>
                      <span className={cn("truncate", connectedPorts.has(`${id}:out:${port.name}`) ? "text-foreground" : "text-muted-foreground")} title={t(`portTypes.${port.portType}` as any)}>
                        {port.name}
                      </span>
                      <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: PORT_TYPE_COLORS[port.portType] || "#737373" }} />
                    </div>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNodeId(id);
                  onOpenNodeInspector(id);
                }}
                title={t("editInNodeTab")}
                className="nodrag flex w-full items-center justify-between gap-2 rounded-md border border-border px-2 py-1.5 text-left transition-colors hover:bg-accent/50"
              >
                <span className="min-w-0 flex-1">
                  {compactParams.length > 0 && (
                    <span className="block truncate font-mono text-xs tnum text-foreground">{compactParams.join(" · ")}</span>
                  )}
                </span>
                <Sliders className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              </button>

              <NodeBody
                nodeType={def.typeName}
                nodeId={id}
                data={data}
                character={boundChar}
                connectedInputs={def.inputPorts.filter((pt) => connectedPorts.has(`${id}:in:${pt.name}`)).map((pt) => pt.name)}
              />

              {data.summaryText && (
                <p className="line-clamp-2 rounded border border-border/70 bg-muted/20 px-2 py-1 text-xs text-foreground">{data.summaryText}</p>
              )}

              {hasError && (
                <p className="rounded border border-semantic-danger/40 px-2 py-1 text-xs text-semantic-danger">
                  {data.errorMessage || issues[0]}
                </p>
              )}

              <div className="relative flex items-center justify-between text-xs text-muted-foreground tnum">
                <span className="truncate">
                  {data.generations.length > 0
                    ? t("pinnedGen", { index: Math.max(1, pinnedIdx), total: data.generations.length })
                    : data.nextStepHint || t("noGenYet")}
                </span>
                <span className="flex shrink-0 items-center gap-1">
                  <span title={t("estimatedCost", { cost: estCost.toFixed(2) })}>${estCost.toFixed(2)}</span>
                  <IconBtn label={t("runFromHere")} onClick={() => onRequestRun("downstream", id)}>
                    <ChevronsDown className="h-3.5 w-3.5" />
                  </IconBtn>
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
});
