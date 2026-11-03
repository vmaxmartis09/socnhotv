"use client";

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
import { CharacterCard } from "@/components/canvas/CharacterCard";
import { Play, Plus, ChevronDown, Sliders } from "@/components/ui/icons";

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

  const [runMenuOpen, setRunMenuOpen] = useState(false);

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

  return (
    <div
      tabIndex={0}
      role="group"
      aria-label={`${def.displayName} (${stateLabel})`}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          e.stopPropagation();
          onRequestRun("single_node", id);
        }
      }}
      className={cn(
        "w-[304px] rounded-[8px] border bg-card text-foreground select-none transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        isFlashing
          ? "border-brand bg-brand/5"
          : issues.length > 0 || data.status === "failed"
          ? "border-semantic-danger"
          : selected
          ? "border-foreground"
          : "border-border"
      )}
      style={{ boxShadow: "none" }}
    >
      {/* 1. Card Header (32px / h-8): Node type name, role badge from category, text state */}
      <div className="flex h-8 items-center justify-between gap-1.5 border-b border-border bg-muted/40 px-2.5">
        <div className="flex min-w-0 items-center gap-1.5">
          <span className="truncate text-xs font-semibold text-foreground">
            {def.displayName}
          </span>
          <span className="shrink-0 rounded border border-border bg-card px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
            {categoryLabel}
          </span>
        </div>
        <span
          className={cn(
            "shrink-0 text-xs font-medium tnum",
            stateKey === "running"
              ? "text-brand"
              : stateKey === "failed"
              ? "text-semantic-danger"
              : stateKey === "succeeded"
              ? "text-semantic-success"
              : stateKey === "stale"
              ? "text-semantic-warning"
              : "text-muted-foreground"
          )}
        >
          {stateLabel}
          {stateKey === "running" &&
            typeof data.progressPct === "number" &&
            ` ${Math.round(data.progressPct)}%`}
        </span>
      </div>

      {/* 2. One-line role description written for video creators */}
      <div className="border-b border-border/70 px-2.5 py-1.5">
        <p className="truncate text-[11px] text-muted-foreground" title={def.description}>
          {def.description}
        </p>
      </div>

      {/* 3. Left Input Ports & Right Output Ports columns */}
      <div className="grid grid-cols-2 divide-x divide-border/70 border-b border-border/70 text-[11px]">
        {/* Left: Input ports */}
        <div className="space-y-1.5 py-2 pl-2.5 pr-1.5">
          {def.inputPorts.length === 0 ? (
            <span className="block text-[10px] text-muted-foreground">
              —
            </span>
          ) : (
            def.inputPorts.map((port) => {
              const isConnected = connectedPorts.has(`${id}:in:${port.name}`);
              const portColor = PORT_TYPE_COLORS[port.portType] || "#737373";
              const isCompatibleTarget =
                activeDragPort &&
                activeDragPort.nodeId !== id &&
                activeDragPort.handleType === "source" &&
                isPortCompatible(activeDragPort.portType, port.portType);
              const isIncompatibleTarget =
                activeDragPort &&
                activeDragPort.nodeId !== id &&
                activeDragPort.handleType === "source" &&
                !isPortCompatible(activeDragPort.portType, port.portType);

              return (
                <div
                  key={port.name}
                  className={cn(
                    "relative flex items-center justify-between gap-1 rounded px-1 py-0.5 transition-opacity",
                    isCompatibleTarget && "bg-accent ring-1 ring-brand",
                    isIncompatibleTarget && "opacity-35"
                  )}
                >
                  <Handle
                    id={port.name}
                    type="target"
                    position={Position.Left}
                    aria-label={`${port.name} (${t(`portTypes.${port.portType}` as any)})`}
                    style={{
                      left: -11,
                      width: 10,
                      height: 10,
                      backgroundColor: portColor,
                      border: isCompatibleTarget
                        ? "2px solid hsl(var(--brand))"
                        : "2px solid hsl(var(--card))",
                    }}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1">
                      <span className="truncate font-medium text-foreground">
                        {port.name}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        · {t(`portTypes.${port.portType}` as any)}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                      <span>
                        {port.required ? t("portRequired") : t("portOptional")}
                      </span>
                      <span>·</span>
                      <span
                        className={cn(
                          isConnected
                            ? "text-foreground font-medium"
                            : port.required
                            ? "text-brand"
                            : "text-muted-foreground"
                        )}
                      >
                        {isConnected
                          ? t("portConnected")
                          : t("portDisconnected")}
                      </span>
                    </div>
                  </div>
                  {/* + Quick add upstream node button */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenQuickAdd({
                        anchorNodeId: id,
                        direction: "before",
                        portName: port.name,
                        portType: port.portType,
                      });
                    }}
                    title={t("addUpstreamPort")}
                    aria-label={`${t("addUpstreamPort")}: ${port.name}`}
                    className="nodrag flex h-4 w-4 shrink-0 items-center justify-center rounded border border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground"
                  >
                    <Plus className="h-2.5 w-2.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Right: Output ports */}
        <div className="space-y-1.5 py-2 pl-1.5 pr-2.5">
          {def.outputPorts.length === 0 ? (
            <span className="block text-right text-[10px] text-muted-foreground">
              —
            </span>
          ) : (
            def.outputPorts.map((port) => {
              const isConnected = connectedPorts.has(`${id}:out:${port.name}`);
              const portColor = PORT_TYPE_COLORS[port.portType] || "#737373";
              const isCompatibleSource =
                activeDragPort &&
                activeDragPort.nodeId !== id &&
                activeDragPort.handleType === "target" &&
                isPortCompatible(port.portType, activeDragPort.portType);
              const isIncompatibleSource =
                activeDragPort &&
                activeDragPort.nodeId !== id &&
                activeDragPort.handleType === "target" &&
                !isPortCompatible(port.portType, activeDragPort.portType);

              return (
                <div
                  key={port.name}
                  className={cn(
                    "relative flex items-center justify-between gap-1 rounded px-1 py-0.5 text-right transition-opacity",
                    isCompatibleSource && "bg-accent ring-1 ring-brand",
                    isIncompatibleSource && "opacity-35"
                  )}
                >
                  {/* + Quick add downstream node button */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenQuickAdd({
                        anchorNodeId: id,
                        direction: "after",
                        portName: port.name,
                        portType: port.portType,
                      });
                    }}
                    title={t("addDownstreamPort")}
                    aria-label={`${t("addDownstreamPort")}: ${port.name}`}
                    className="nodrag flex h-4 w-4 shrink-0 items-center justify-center rounded border border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground"
                  >
                    <Plus className="h-2.5 w-2.5" />
                  </button>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-end gap-1">
                      <span className="text-[10px] text-muted-foreground">
                        {t(`portTypes.${port.portType}` as any)} ·
                      </span>
                      <span className="truncate font-medium text-foreground">
                        {port.name}
                      </span>
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      <span
                        className={cn(
                          isConnected
                            ? "text-foreground font-medium"
                            : "text-muted-foreground"
                        )}
                      >
                        {isConnected
                          ? t("portConnected")
                          : t("portDisconnected")}
                      </span>
                    </div>
                  </div>
                  <Handle
                    id={port.name}
                    type="source"
                    position={Position.Right}
                    aria-label={`${port.name} (${t(`portTypes.${port.portType}` as any)})`}
                    style={{
                      right: -11,
                      width: 10,
                      height: 10,
                      backgroundColor: portColor,
                      border: isCompatibleSource
                        ? "2px solid hsl(var(--brand))"
                        : "2px solid hsl(var(--card))",
                    }}
                  />
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* 4. Compact primary params (clickable to edit in Node tab) */}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setSelectedNodeId(id);
          onOpenNodeInspector(id);
        }}
        title={t("editInNodeTab")}
        className="nodrag flex w-full items-center justify-between gap-2 border-b border-border/70 px-2.5 py-1.5 text-left text-[11px] hover:bg-accent/50"
      >
        <div className="min-w-0 flex-1">
          {compactParams.length > 0 && (
            <p className="truncate font-mono text-[11px] text-foreground tnum">
              {compactParams.join(" · ")}
            </p>
          )}
          {contentPreview && (
            <p className="line-clamp-2 text-[11px] text-muted-foreground">
              {contentPreview}
            </p>
          )}
          {!compactParams.length && !contentPreview && (
            <span className="text-muted-foreground">{t("editInNodeTab")}</span>
          )}
        </div>
        <Sliders className="h-3 w-3 shrink-0 text-muted-foreground" />
      </button>

      {/* 5. Real output preview when available (or Character avatar / next-step hint) */}
      <div className="px-2.5 py-2 space-y-1.5">
        {data.previewType === "image" && data.previewUrl ? (
          <div className="overflow-hidden rounded border border-border bg-muted/20">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={data.previewUrl}
              alt={def.displayName}
              className="h-28 w-full object-cover object-top"
            />
          </div>
        ) : data.previewType === "video" && data.previewUrl ? (
          <div className="overflow-hidden rounded border border-border bg-muted/20">
            <video
              src={data.previewUrl}
              controls
              preload="metadata"
              className="nodrag h-28 w-full object-cover"
            />
          </div>
        ) : data.previewType === "audio" && data.previewUrl ? (
          <div className="rounded border border-border bg-muted/20 p-1.5">
            <audio
              src={data.previewUrl}
              controls
              preload="metadata"
              className="nodrag h-7 w-full"
            />
          </div>
        ) : boundChar ? (
          <CharacterCard character={boundChar} />
        ) : null}

        {data.summaryText && (
          <p className="rounded border border-border/70 bg-muted/20 px-2 py-1 text-[11px] text-foreground line-clamp-2">
            {data.summaryText}
          </p>
        )}

        <div className="flex items-center justify-between text-[10px] text-muted-foreground tnum">
          {data.generations.length > 0 ? (
            <span>
              {t("pinnedGen", {
                index: Math.max(1, pinnedIdx),
                total: data.generations.length,
              })}
            </span>
          ) : (
            <span className="truncate">
              {data.nextStepHint || t("noGenYet")}
            </span>
          )}
        </div>

        {(data.errorMessage || issues.length > 0) && (
          <div className="rounded border border-semantic-danger/40 bg-card px-2 py-1 text-[11px] text-semantic-danger">
            {data.errorMessage || issues[0]}
          </div>
        )}
      </div>

      {/* 6. Bottom bar: Run button with menu + estimated cost */}
      <div className="relative flex h-8 items-center justify-between border-t border-border bg-muted/30 px-2.5 text-xs">
        <span className="text-[11px] text-muted-foreground tnum">
          {t("estimatedCost", { cost: estCost.toFixed(2) })}
        </span>

        <div className="relative flex items-center">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onRequestRun("single_node", id);
            }}
            className="nodrag flex h-6 items-center gap-1 rounded-l border border-border bg-card px-2 text-[11px] font-medium text-foreground hover:bg-accent"
          >
            <Play className="h-3 w-3" />
            <span>{t("runMenu")}</span>
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setRunMenuOpen((v) => !v);
            }}
            aria-label={t("runMenu")}
            aria-expanded={runMenuOpen}
            className="nodrag flex h-6 w-5 items-center justify-center rounded-r border border-l-0 border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            <ChevronDown className="h-3 w-3" />
          </button>

          {runMenuOpen && (
            <div
              onClick={(e) => e.stopPropagation()}
              className="nodrag absolute bottom-7 right-0 z-30 w-44 rounded-md border border-border bg-popover p-1 text-xs text-popover-foreground"
            >
              <button
                type="button"
                onClick={() => {
                  setRunMenuOpen(false);
                  onRequestRun("single_node", id);
                }}
                className="flex w-full items-center rounded px-2 py-1 text-left hover:bg-accent"
              >
                {t("runNode")}
              </button>
              <button
                type="button"
                onClick={() => {
                  setRunMenuOpen(false);
                  onRequestRun("downstream", id);
                }}
                className="flex w-full items-center rounded px-2 py-1 text-left hover:bg-accent"
              >
                {t("runFromHere")}
              </button>
              <button
                type="button"
                onClick={() => {
                  setRunMenuOpen(false);
                  onRequestRun("all");
                }}
                className="flex w-full items-center rounded px-2 py-1 text-left hover:bg-accent"
              >
                {t("runAll")}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});
