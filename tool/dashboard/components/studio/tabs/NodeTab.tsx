"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import { FALLBACK_NODE_TYPES, estimateNodeCostUsd } from "@/lib/core-api";
import { Pin, Check } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

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

  return (
    <div className="p-3.5 space-y-4 text-xs">
      {/* Header summary */}
      <div className="border-b border-border pb-3 space-y-1">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">
            {def.displayName}
          </h3>
          <span className="rounded border border-border bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
            {c(`categories.${def.category}` as any)}
          </span>
        </div>
        <p className="text-[11px] text-muted-foreground">{def.description}</p>
        <div className="flex items-center justify-between pt-1 text-[11px] tnum">
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

      {/* Parameters form */}
      <section className="space-y-2.5 border-b border-border pb-3.5">
        <h4 className="font-semibold text-foreground">{t("paramsTitle")}</h4>

        {/* Character selector for character node */}
        {def.typeName === "character" && (
          <label className="block space-y-1">
            <span className="text-muted-foreground">
              {t("characterSelectLabel")}
            </span>
            <select
              value={params.characterId || "soc_nho"}
              onChange={(e) =>
                updateNodeParams(node.id, { characterId: e.target.value })
              }
              className="h-8 w-full rounded-md border border-border bg-card px-2 text-xs text-foreground"
            >
              {characters.map((ch) => (
                <option key={ch.id} value={ch.id}>
                  {ch.name} ({ch.heightCm} cm · {ch.voiceId})
                </option>
              ))}
            </select>
          </label>
        )}

        {/* Text / Prompt input */}
        {(def.typeName === "text" ||
          def.typeName === "image_gen" ||
          def.typeName === "image_edit" ||
          def.typeName === "video_gen") && (
          <label className="block space-y-1">
            <span className="text-muted-foreground">{t("promptLabel")}</span>
            <textarea
              rows={3}
              value={params.content ?? params.prompt ?? ""}
              onChange={(e) =>
                updateNodeParams(
                  node.id,
                  def.typeName === "text"
                    ? { content: e.target.value }
                    : { prompt: e.target.value }
                )
              }
              className="w-full rounded-md border border-border bg-card p-2 text-xs text-foreground leading-relaxed"
            />
          </label>
        )}

        {/* Model selector */}
        {"model" in (def.defaultParams || {}) && (
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

        {/* Aspect ratio */}
        {"aspectRatio" in (def.defaultParams || {}) && (
          <label className="block space-y-1">
            <span className="text-muted-foreground">{t("aspectLabel")}</span>
            <select
              value={params.aspectRatio || "9:16"}
              onChange={(e) =>
                updateNodeParams(node.id, { aspectRatio: e.target.value })
              }
              className="h-8 w-full rounded-md border border-border bg-card px-2 text-xs tnum text-foreground"
            >
              <option value="9:16">9:16 (TikTok / Shorts)</option>
              <option value="16:9">16:9 (YouTube ngang)</option>
              <option value="1:1">1:1 (Vuông)</option>
              <option value="4:5">4:5 (Dọc vừa)</option>
            </select>
          </label>
        )}

        {/* Duration */}
        {("durationSec" in (def.defaultParams || {}) ||
          "targetDurationSec" in (def.defaultParams || {})) && (
          <label className="block space-y-1">
            <span className="text-muted-foreground">{t("durationLabel")}</span>
            <input
              type="number"
              min={2}
              max={120}
              value={params.durationSec ?? params.targetDurationSec ?? 8}
              onChange={(e) => {
                const v = Number(e.target.value) || 8;
                updateNodeParams(
                  node.id,
                  "durationSec" in (def.defaultParams || {})
                    ? { durationSec: v }
                    : { targetDurationSec: v }
                );
              }}
              className="h-8 w-full rounded-md border border-border bg-card px-2 text-xs tnum text-foreground"
            />
          </label>
        )}

        {/* Voice ID & Tempo */}
        {def.typeName === "voice_tts" && (
          <div className="grid grid-cols-2 gap-2">
            <label className="block space-y-1">
              <span className="text-muted-foreground">{t("voiceIdLabel")}</span>
              <input
                type="text"
                value={params.voiceId || "soc-nho"}
                onChange={(e) =>
                  updateNodeParams(node.id, { voiceId: e.target.value })
                }
                className="h-8 w-full rounded-md border border-border bg-card px-2 font-mono text-xs text-foreground"
              />
            </label>
            <label className="block space-y-1">
              <span className="text-muted-foreground">{t("tempoLabel")}</span>
              <input
                type="number"
                step="0.05"
                min="0.7"
                max="1.5"
                value={params.tempo || 1.1}
                onChange={(e) =>
                  updateNodeParams(node.id, {
                    tempo: Number(e.target.value) || 1.0,
                  })
                }
                className="h-8 w-full rounded-md border border-border bg-card px-2 text-xs tnum text-foreground"
              />
            </label>
          </div>
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
        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <span className="mb-1 block font-medium text-muted-foreground">
              {t("inputsLabel")}
            </span>
            <ul className="space-y-1">
              {def.inputPorts.map((p) => {
                const wired = edges.some(
                  (e) => e.target === node.id && e.targetHandle === p.name
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
          <p className="text-[11px] text-muted-foreground">
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
                    <span className="font-mono text-[11px] text-foreground tnum">
                      #{node.data.generations.length - idx} · $
                      {gen.costUsd.toFixed(2)}
                    </span>
                    {isPinned ? (
                      <span className="inline-flex items-center gap-1 rounded bg-accent px-1.5 py-0.5 text-[10px] font-medium text-foreground">
                        <Check className="h-2.5 w-2.5" />
                        {t("pinnedBadge")}
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => pinNodeGeneration(node.id, gen.id)}
                        className="inline-flex items-center gap-1 rounded border border-border bg-card px-1.5 py-0.5 text-[10px] text-foreground hover:bg-accent"
                      >
                        <Pin className="h-2.5 w-2.5" />
                        {t("pinBtn")}
                      </button>
                    )}
                  </div>
                  {gen.summaryText && (
                    <p className="text-[11px] text-muted-foreground">
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
