"use client";

import { enterOnce } from "@/lib/motion";
import React, { memo, useEffect, useRef, useState } from "react";
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

  const hasError = Boolean(data.errorMessage) || issues.length > 0 || data.status === "failed";

  // Bố cục 3 vùng: NHẬN (trên) · LÀM (giữa) · TRẢ (dưới). Cổng bám theo hàng của vùng tương ứng.
  const HEADER = 44;
  const LABEL = 22;
  const ROW = 22;
  const FOOTER = 30;
  const inTop = (i: number) => HEADER + LABEL + i * ROW + ROW / 2;
  const outBottom = (i: number) =>
    FOOTER + 6 + (def.outputPorts.length - 1 - i) * ROW + ROW / 2;

  const [guide, setGuide] = useState<"in" | "out" | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!guide) return;
    const close = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as globalThis.Node)) setGuide(null);
    };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, [guide]);
  useEffect(() => {
    if (!selected) setGuide(null);
  }, [selected]);

  const typeLabel = (pt: string) => t(`portTypes.${pt}` as any);

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
    const pos = isIn
      ? { top: inTop(index), transform: "translate(-50%, -50%)" }
      : { top: "auto", bottom: outBottom(index), transform: "translate(50%, 50%)" };
    return (
      <Handle
        key={`${side}:${port.name}`}
        id={port.name}
        type={isIn ? "target" : "source"}
        position={isIn ? Position.Left : Position.Right}
        title={`${port.name} · ${typeLabel(port.portType)}${port.required ? " *" : ""}`}
        aria-label={`${port.name} (${typeLabel(port.portType)})`}
        style={{
          ...pos,
          [isIn ? "left" : "right"]: -1,
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

  const zoneLabel = (text: string, hint: string) => (
    <div className="flex items-baseline justify-between px-3" style={{ height: LABEL }}>
      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{text}</span>
      <span className="text-[10px] text-muted-foreground/70">{hint}</span>
    </div>
  );

  /** Nút + nhỏ ở mép card: hiện khi rê chuột / chọn card; bấm mở hướng dẫn input hoặc output. */
  const plusBtn = (side: "in" | "out") => {
    const isIn = side === "in";
    const ports = isIn ? def.inputPorts : def.outputPorts;
    if (ports.length === 0) return null;
    const active = guide === side;
    const style: React.CSSProperties = isIn
      ? { top: HEADER + LABEL + ((ports.length * ROW) / 2 - 10), left: -34 }
      : { bottom: FOOTER + 6 + ((ports.length * ROW) / 2 - 10), right: -34 };
    return (
      <>
        <button
          type="button"
          title={isIn ? "Xem cần nhận gì" : "Xem trả ra gì & nối tiếp"}
          aria-label={isIn ? "Hướng dẫn đầu vào" : "Hướng dẫn đầu ra"}
          aria-expanded={active}
          onClick={(e) => {
            e.stopPropagation();
            setGuide(active ? null : side);
          }}
          style={style}
          className={cn(
            "nodrag absolute z-20 flex h-5 w-5 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-sm transition-all hover:scale-110 hover:text-foreground",
            active || selected
              ? "opacity-100"
              : "pointer-events-none opacity-0 group-hover/node:pointer-events-auto group-hover/node:opacity-100"
          )}
        >
          <Plus className={cn("h-3 w-3 transition-transform", active && "rotate-45")} />
        </button>
        <AnimatePresence>
          {active && (
            <motion.div
              initial={{ opacity: 0, x: isIn ? 6 : -6, scale: 0.97 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              style={isIn ? { top: HEADER, right: "calc(100% + 40px)" } : { bottom: FOOTER, left: "calc(100% + 40px)" }}
              className="nodrag nowheel absolute z-30 w-60 space-y-2 rounded-lg border border-border bg-card p-2.5 text-xs shadow-lg"
            >
              <p className="font-semibold text-foreground">
                {isIn ? "Node này cần nhận" : "Node này trả ra"}
              </p>
              {ports.map((port) => {
                const connected = connectedPorts.has(`${id}:${side}:${port.name}`);
                return (
                  <div key={port.name} className="space-y-1 rounded-md border border-border/70 p-1.5">
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: PORT_TYPE_COLORS[port.portType] || "#737373" }} />
                      <span className="font-medium text-foreground">{port.name}</span>
                      <span className="text-muted-foreground">· {typeLabel(port.portType)}</span>
                      <span className={cn("ml-auto text-[10px]", connected ? "text-semantic-success" : isIn && port.required ? "text-semantic-danger" : "text-muted-foreground")}>
                        {connected ? "đã nối" : isIn ? (port.required ? "bắt buộc" : "tuỳ chọn") : "chưa nối"}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setGuide(null);
                        onOpenQuickAdd({ anchorNodeId: id, direction: isIn ? "before" : "after", portName: port.name, portType: port.portType });
                      }}
                      className="flex w-full items-center gap-1 rounded border border-dashed border-border px-1.5 py-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                    >
                      <Plus className="h-3 w-3" />
                      {isIn ? `Thêm node cấp ${typeLabel(port.portType)}` : `Thêm node nhận ${typeLabel(port.portType)}`}
                    </button>
                  </div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </>
    );
  };

  const outputsDone = data.status === "succeeded" || data.status === "completed";

  return (
    <motion.div
      ref={rootRef}
      tabIndex={0}
      role="group"
      aria-label={`${def.displayName} (${stateLabel})`}
      initial={enterOnce(`node:${id}`, { opacity: 0 })}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          e.stopPropagation();
          onRequestRun("single_node", id);
        }
      }}
      className={cn(
        "group/node relative w-[300px] rounded-[12px] border bg-card text-foreground select-none transition-colors",
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
      style={{ boxShadow: "none" }}
    >
      {stateKey === "running" && (
        <div className="pointer-events-none absolute inset-x-2 bottom-0 h-0.5 overflow-hidden rounded-full bg-muted">
          {typeof data.progressPct === "number" ? (
            <motion.div
              className="h-full bg-brand"
              initial={false}
              animate={{ width: `${Math.max(4, Math.min(100, data.progressPct))}%` }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              style={{ willChange: "width" }}
            />
          ) : (
            <div className="h-full w-2/5 rounded-full bg-brand animate-node-indeterminate" />
          )}
        </div>
      )}
      {def.inputPorts.map((p, i) => portHandle(p, i, "in"))}
      {def.outputPorts.map((p, i) => portHandle(p, i, "out"))}
      {plusBtn("in")}
      {plusBtn("out")}

      {/* Đầu card: loại, tên, trạng thái, chạy */}
      <div className="flex items-center gap-2 px-3" style={{ height: HEADER }}>
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
      </div>

      {/* 1. NHẬN */}
      <div className="border-t border-border/70">
        {zoneLabel("Nhận", `${def.inputPorts.length} đầu vào`)}
        {def.inputPorts.length === 0 && (
          <p className="px-3 pb-1.5 text-xs text-muted-foreground" style={{ height: ROW }}>
            Không cần đầu vào — nhập trực tiếp
          </p>
        )}
        {def.inputPorts.map((port) => {
          const connected = connectedPorts.has(`${id}:in:${port.name}`);
          const filled = connected || (p[port.name] !== undefined && p[port.name] !== "");
          return (
            <div key={port.name} className="flex items-center gap-1.5 px-3 text-xs" style={{ height: ROW }}>
              <span className={cn("truncate", filled ? "text-foreground" : port.required ? "text-semantic-danger" : "text-muted-foreground")}>
                {port.name}
              </span>
              <span className="text-muted-foreground/70">· {typeLabel(port.portType)}</span>
              <span className="ml-auto">
                {filled ? <CheckCircle2 className="h-3 w-3 text-semantic-success" /> : port.required ? <span className="text-[10px] text-semantic-danger">thiếu</span> : null}
              </span>
            </div>
          );
        })}
      </div>

      {/* 2. LÀM */}
      <div className="space-y-2 border-t border-border/70 pb-2.5">
        {zoneLabel("Làm", categoryLabel)}
        <div className="space-y-2 px-2.5">
          <p className="line-clamp-2 px-0.5 text-xs text-muted-foreground" title={def.description}>
            {def.description}
          </p>
          <NodeBody
            nodeType={def.typeName}
            nodeId={id}
            data={data}
            character={boundChar}
            connectedInputs={def.inputPorts.filter((pt) => connectedPorts.has(`${id}:in:${pt.name}`)).map((pt) => pt.name)}
          />
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedNodeId(id);
              onOpenNodeInspector(id);
            }}
            title={t("editInNodeTab")}
            className="nodrag flex w-full items-center justify-between gap-2 rounded-md border border-border px-2 py-1 text-left transition-colors hover:bg-accent/50"
          >
            <span className="min-w-0 flex-1 truncate font-mono text-xs tnum text-foreground">
              {compactParams.join(" · ") || "Tuỳ chỉnh"}
            </span>
            <Sliders className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          </button>
        </div>
      </div>

      {/* 3. TRẢ */}
      <div className="border-t border-border/70">
        {zoneLabel("Trả", outputsDone ? "đã có kết quả" : "chưa chạy")}
        {def.outputPorts.map((port) => {
          const connected = connectedPorts.has(`${id}:out:${port.name}`);
          return (
            <div key={port.name} className="flex items-center justify-end gap-1.5 px-3 text-xs" style={{ height: ROW }}>
              <span className="text-muted-foreground/70">{typeLabel(port.portType)} ·</span>
              <span className={cn("truncate", connected ? "text-foreground" : "text-muted-foreground")}>{port.name}</span>
            </div>
          );
        })}
        {data.summaryText && (
          <p className="mx-2.5 mb-1 line-clamp-2 rounded border border-border/70 bg-muted/20 px-2 py-1 text-xs text-foreground">{data.summaryText}</p>
        )}
        {hasError && (
          <p className="mx-2.5 mb-1 rounded border border-semantic-danger/40 px-2 py-1 text-xs text-semantic-danger">
            {data.errorMessage || issues[0]}
          </p>
        )}
        <div className="flex items-center justify-between px-3 text-xs text-muted-foreground tnum" style={{ height: FOOTER }}>
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
  );
});
