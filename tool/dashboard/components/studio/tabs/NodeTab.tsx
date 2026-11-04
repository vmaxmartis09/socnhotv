"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import { FALLBACK_NODE_TYPES, estimateNodeCostUsd } from "@/lib/core-api";
import { Pin, Check } from "@/components/ui/icons";
import { cn } from "@/lib/utils";
import {
  NodeTextInput,
  NodeImageInput,
  NodeScriptInput,
  NodeVoiceInput,
  NodeImageGenInput,
  NodeExportInput,
  NodeCharacterSelect,
  NodeCaptionsInput,
} from "@/components/canvas/NodeInputs";

export function NodeTab() {
  const t = useTranslations("nodeTab");
  const c = useTranslations("canvas");
  const {
    nodes,
    edges,
    selectedNodeId,
    nodeCatalog,
    characters,
    isMockMode,
    updateNodeParams,
    pinNodeGeneration,
    activeProjectId,
  } = useStudioStore();

  const node =
    nodes.find((n) => n.id === selectedNodeId) ||
    nodes.find((n) => n.selected) ||
    null;

  if (!node) {
    return (
      <div className="p-4 text-xs text-muted-foreground leading-relaxed">
        {t("noSelection")}
      </div>
    );
  }

  const def =
    nodeCatalog.find((d) => d.typeName === node.data.nodeType) ||
    FALLBACK_NODE_TYPES.find((d) => d.typeName === node.data.nodeType) ||
    FALLBACK_NODE_TYPES[0];

  const params = node.data.params || {};
  const estCost = estimateNodeCostUsd(def.typeName, params, isMockMode);

  const isConnected = (portName: string) =>
    edges.some((e) => e.target === node.id && e.targetHandle === portName);

  return (
    <div className="p-3.5 space-y-4 text-xs">
      {/* Header summary */}
      <div className="border-b border-border pb-3 space-y-1">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">
            {def.displayName}
          </h3>
          <span className="rounded border border-border bg-muted px-1.5 py-0.5 text-[13px] text-muted-foreground">
            {c(`categories.${def.category}` as any)}
          </span>
        </div>
        <p className="text-[13px] text-muted-foreground">{def.description}</p>
        <div className="flex items-center justify-between pt-1 text-[13px] tnum">
          <span className="text-muted-foreground">
            {t("statusLabel")}:{" "}
            <strong className="font-medium text-foreground">
              {c(
                `status.${
                  node.data.isStale ? "stale" : node.data.status || "idle"
                }` as any
              )}
            </strong>
          </span>
          <span className="text-muted-foreground">
            {t("costLabel")}:{" "}
            <strong className="font-medium text-foreground">
              ${estCost.toFixed(2)} USD
            </strong>
          </span>
        </div>
      </div>

      {/* DÙNG CHUNG CÁC COMPONENT NHẬP LIỆU CỐT LÕI (Unified with canvas card) */}
      <section className="space-y-3 border-b border-border pb-3.5">
        <h4 className="font-semibold text-foreground">{t("paramsTitle")}</h4>

        {def.typeName === "text" && (
          <NodeTextInput
            nodeId={node.id}
            content={params.content || ""}
            connected={isConnected("text")}
            isDetailed
          />
        )}

        {(def.typeName === "image" ||
          def.typeName === "character_image" ||
          def.typeName === "scene") && (
          <NodeImageInput
            nodeId={node.id}
            uri={params.uri}
            name={params.name}
            nodeType={def.typeName}
            previewUrl={node.data.previewUrl}
          />
        )}

        {def.typeName === "script" && (
          <NodeScriptInput
            nodeId={node.id}
            mode={params.mode}
            rawScript={params.rawScript}
            ideaText={params.text || params.content}
            targetSceneCount={params.targetSceneCount}
            targetDurationSec={params.targetDurationSec}
            connectedText={isConnected("text")}
          />
        )}

        {def.typeName === "voice_tts" && (
          <NodeVoiceInput
            nodeId={node.id}
            text={params.text}
            voiceId={params.voiceId}
            tempo={params.tempo}
            connectedText={isConnected("text")}
          />
        )}

        {(def.typeName === "image_gen" || def.typeName === "image_edit") && (
          <NodeImageGenInput
            nodeId={node.id}
            prompt={params.prompt}
            referenceImages={params.referenceImages}
            aspectRatio={params.aspectRatio}
            model={params.model}
            connectedPrompt={isConnected("prompt")}
          />
        )}

        {def.typeName === "character" && (
          <NodeCharacterSelect
            nodeId={node.id}
            characterId={params.characterId || "soc_nho"}
          />
        )}

        {def.typeName === "captions" && (
          <NodeCaptionsInput
            nodeId={node.id}
            style={params.style}
            language={params.language}
          />
        )}

        {def.typeName === "export" && (
          <NodeExportInput
            nodeId={node.id}
            outputFileName={params.outputFileName}
            platforms={params.platforms}
            previewUrl={node.data.previewUrl}
          />
        )}

        {/* CÁC THÔNG SỐ NÂNG CAO CHO CÁC NODE KHÁC */}
        {/* Model selector */}
        {"model" in (def.defaultParams || {}) &&
          def.typeName !== "image_gen" &&
          def.typeName !== "image_edit" && (
            <label className="block space-y-1">
              <span className="text-muted-foreground">{t("modelLabel")}</span>
              <select
                value={params.model || def.defaultParams.model}
                onChange={(e) =>
                  updateNodeParams(node.id, { model: e.target.value })
                }
                className="h-8 w-full rounded-md border border-border bg-card px-2 font-mono text-xs text-foreground"
              >
                {def.typeName === "video_gen" ? (
                  <>
                    <option value="google-veo-2">google-veo-2</option>
                    <option value="fal-ltx-video">fal-ltx-video</option>
                  </>
                ) : (
                  <>
                    <option value="gemini-2.5-flash-image">
                      gemini-2.5-flash-image
                    </option>
                    <option value="imagen-3.0-generate">
                      imagen-3.0-generate
                    </option>
                  </>
                )}
              </select>
            </label>
          )}

        {/* Quality check threshold & criteria */}
        {def.typeName === "quality_check" && (
          <div className="space-y-2">
            <label className="block space-y-1">
              <span className="text-muted-foreground">
                {t("thresholdLabel")}
              </span>
              <input
                type="number"
                step="0.05"
                min="0.1"
                max="1.0"
                value={params.thresholdScore ?? 0.85}
                onChange={(e) =>
                  updateNodeParams(node.id, {
                    thresholdScore: Number(e.target.value) || 0.85,
                  })
                }
                className="h-8 w-full rounded-md border border-border bg-card px-2 text-xs tnum text-foreground"
              />
            </label>
            <label className="block space-y-1">
              <span className="text-muted-foreground">
                {t("criteriaLabel")}
              </span>
              <textarea
                rows={2}
                value={params.criteria ?? def.defaultParams.criteria ?? ""}
                onChange={(e) =>
                  updateNodeParams(node.id, { criteria: e.target.value })
                }
                className="w-full rounded-md border border-border bg-card p-2 text-xs text-foreground"
              />
            </label>
          </div>
        )}
      </section>

      {/* Ports status */}
      <section className="space-y-2 border-b border-border pb-3.5">
        <h4 className="font-semibold text-foreground">{t("portsTitle")}</h4>
        <div className="grid grid-cols-2 gap-2 text-[13px]">
          <div>
            <span className="mb-1 block font-medium text-muted-foreground">
              {t("inputsLabel")}
            </span>
            <ul className="space-y-1">
              {def.inputPorts.map((p) => {
                const wired = isConnected(p.name);
                return (
                  <li key={p.name} className="flex items-center justify-between">
                    <span className="font-mono">{p.name}</span>
                    <span
                      className={cn(
                        wired ? "text-foreground" : "text-muted-foreground"
                      )}
                    >
                      {wired ? c("portConnected") : c("portDisconnected")}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
          <div>
            <span className="mb-1 block font-medium text-muted-foreground">
              {t("outputsLabel")}
            </span>
            <ul className="space-y-1">
              {def.outputPorts.map((p) => {
                const wired = edges.some(
                  (e) => e.source === node.id && e.sourceHandle === p.name
                );
                return (
                  <li key={p.name} className="flex items-center justify-between">
                    <span className="font-mono">{p.name}</span>
                    <span
                      className={cn(
                        wired ? "text-foreground" : "text-muted-foreground"
                      )}
                    >
                      {wired ? c("portConnected") : c("portDisconnected")}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      </section>

      {/* Generations history & Pin */}
      <section className="space-y-2">
        <h4 className="font-semibold text-foreground tnum">
          {t("generationsTitle", {
            count: node.data.generations?.length || 0,
          })}
        </h4>
        {!node.data.generations || node.data.generations.length === 0 ? (
          <p className="text-[13px] text-muted-foreground">
            {t("noGenerations")}
          </p>
        ) : (
          <ul className="space-y-2">
            {node.data.generations.map((gen, idx) => {
              const isPinned =
                node.data.pinnedGenerationId === gen.id ||
                (!node.data.pinnedGenerationId && idx === 0);
              return (
                <li
                  key={gen.id}
                  className={cn(
                    "rounded-md border p-2.5 space-y-1.5",
                    isPinned
                      ? "border-foreground bg-accent/40"
                      : "border-border bg-card"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[13px] text-foreground tnum">
                      #{node.data.generations.length - idx} · $
                      {gen.costUsd.toFixed(2)}
                    </span>
                    {isPinned ? (
                      <span className="inline-flex items-center gap-1 rounded bg-accent px-1.5 py-0.5 text-xs font-medium text-foreground">
                        <Check className="h-2.5 w-2.5" />
                        {t("pinnedBadge")}
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => pinNodeGeneration(node.id, gen.id)}
                        className="inline-flex items-center gap-1 rounded border border-border bg-card px-1.5 py-0.5 text-xs text-foreground hover:bg-accent"
                      >
                        <Pin className="h-2.5 w-2.5" />
                        {t("pinBtn")}
                      </button>
                    )}
                  </div>
                  {gen.summaryText && (
                    <p className="text-[13px] text-muted-foreground">
                      {gen.summaryText}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
