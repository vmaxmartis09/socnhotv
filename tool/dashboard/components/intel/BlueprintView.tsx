"use client";

import React, { useState } from "react";
import type { VideoBlueprint, BlueprintBeat } from "@/lib/api/intel";
import { ScriptWizardModal } from "./ScriptWizardModal";
import {
  Brain,
  Sparkles,
  Gauge,
  Clock,
  Layers,
  Wand2,
  Film,
  CheckCircle,
} from "./icons";

interface BlueprintViewProps {
  blueprint: VideoBlueprint;
  projectId: string;
}

const ROLE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  hook: { bg: "bg-rose-500", text: "text-rose-400", border: "border-rose-500/40" },
  problem: { bg: "bg-amber-500", text: "text-amber-400", border: "border-amber-500/40" },
  agitate: { bg: "bg-orange-500", text: "text-orange-400", border: "border-orange-500/40" },
  reveal: { bg: "bg-violet-500", text: "text-violet-400", border: "border-violet-500/40" },
  demo: { bg: "bg-blue-500", text: "text-blue-400", border: "border-blue-500/40" },
  proof: { bg: "bg-emerald-500", text: "text-emerald-400", border: "border-emerald-500/40" },
  compare: { bg: "bg-yellow-500", text: "text-yellow-400", border: "border-yellow-500/40" },
  offer: { bg: "bg-fuchsia-500", text: "text-fuchsia-400", border: "border-fuchsia-500/40" },
  urgency: { bg: "bg-red-600", text: "text-red-400", border: "border-red-600/40" },
  cta: { bg: "bg-indigo-500", text: "text-indigo-400", border: "border-indigo-500/40" },
};

function getRoleStyle(role: string) {
  return (
    ROLE_COLORS[role.toLowerCase()] || {
      bg: "bg-zinc-500",
      text: "text-zinc-400",
      border: "border-zinc-500/40",
    }
  );
}

function formatSec(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export function BlueprintView({ blueprint, projectId }: BlueprintViewProps) {
  const [selectedBeatIndex, setSelectedBeatIndex] = useState<number | null>(null);
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  const totalDuration = blueprint.duration_s || 1;
  const hookDuration =
    blueprint.beats.length > 0
      ? blueprint.beats[0].t_end - blueprint.beats[0].t_start
      : 3.0;
  const ctaStart =
    blueprint.beats.length > 1
      ? blueprint.beats[blueprint.beats.length - 1].t_start
      : totalDuration * 0.85;

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-xl space-y-6">
      {/* Header & Quick Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-indigo-500/20 px-2 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/30">
              {blueprint.id}
            </span>
            <span className="text-xs text-zinc-400">
              Nguồn: <span className="font-mono text-zinc-300">{blueprint.source_ref}</span>
            </span>
            <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] uppercase font-bold text-zinc-400">
              {blueprint.platform}
            </span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-zinc-100 flex items-center gap-2">
            <Brain className="h-5 w-5 text-indigo-400" />
            Cấu trúc Video & Phân tích Nhịp điệu
          </h2>
        </div>

        <button
          onClick={() => setIsWizardOpen(true)}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-500/20 hover:from-indigo-600 hover:to-purple-700 transition"
        >
          <Sparkles className="h-4 w-4" />
          Áp cho sản phẩm...
        </button>
      </div>

      {/* Pacing Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-3">
          <div className="flex items-center gap-1.5 text-xs text-zinc-400">
            <Gauge className="h-3.5 w-3.5 text-indigo-400" />
            <span>Tần số Cut</span>
          </div>
          <div className="mt-1 text-base font-bold text-zinc-100">
            {(blueprint.pacing_cuts_per_10s || 0).toFixed(1)}{" "}
            <span className="text-xs font-normal text-zinc-400">cut/10s</span>
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-3">
          <div className="flex items-center gap-1.5 text-xs text-zinc-400">
            <Clock className="h-3.5 w-3.5 text-rose-400" />
            <span>Thời lượng Hook</span>
          </div>
          <div className="mt-1 text-base font-bold text-zinc-100">
            {hookDuration.toFixed(1)}s
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-3">
          <div className="flex items-center gap-1.5 text-xs text-zinc-400">
            <Clock className="h-3.5 w-3.5 text-emerald-400" />
            <span>Vị trí CTA</span>
          </div>
          <div className="mt-1 text-base font-bold text-zinc-100">
            {formatSec(ctaStart)}
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-3">
          <div className="flex items-center gap-1.5 text-xs text-zinc-400">
            <Layers className="h-3.5 w-3.5 text-amber-400" />
            <span>Số lượng Beats</span>
          </div>
          <div className="mt-1 text-base font-bold text-zinc-100">
            {blueprint.beats.length} phân cảnh
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-3">
          <div className="flex items-center gap-1.5 text-xs text-zinc-400">
            <Wand2 className="h-3.5 w-3.5 text-purple-400" />
            <span>Template gợi ý</span>
          </div>
          <div className="mt-1 text-xs font-semibold text-indigo-300 truncate">
            {blueprint.suggested_template_id || "koc-review-v1"}
          </div>
        </div>
      </div>

      {/* Interactive Timeline Bar */}
      <div>
        <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
          <span className="font-semibold text-zinc-200">Dòng thời gian phân cảnh (Beat Timeline)</span>
          <span>Tổng: {formatSec(totalDuration)} ({blueprint.beats.length} beats)</span>
        </div>

        {/* Proportional Segment Bar */}
        <div className="relative h-10 w-full overflow-hidden rounded-xl bg-zinc-900 p-1 flex gap-0.5 border border-zinc-800">
          {blueprint.beats.map((beat, idx) => {
            const beatDur = Math.max(beat.t_end - beat.t_start, 0.5);
            const widthPct = Math.max((beatDur / totalDuration) * 100, 2);
            const style = getRoleStyle(beat.role);
            const isSelected = selectedBeatIndex === idx;

            return (
              <div
                key={idx}
                onClick={() => setSelectedBeatIndex(isSelected ? null : idx)}
                style={{ width: `${widthPct}%` }}
                title={`${beat.role.toUpperCase()}: ${formatSec(beat.t_start)} - ${formatSec(beat.t_end)} (${beat.summary})`}
                className={`group relative h-full rounded cursor-pointer transition-all ${style.bg} ${
                  isSelected ? "ring-2 ring-white scale-105 z-10 brightness-110" : "opacity-85 hover:opacity-100 hover:scale-[1.02]"
                }`}
              >
                <div className="absolute inset-0 flex items-center justify-center overflow-hidden px-1">
                  <span className="text-[10px] font-bold text-white uppercase drop-shadow truncate">
                    {beat.role}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="mt-2.5 flex flex-wrap items-center gap-3 text-[11px] text-zinc-400">
          {Object.entries(ROLE_COLORS).map(([r, c]) => (
            <div key={r} className="flex items-center gap-1.5">
              <span className={`h-2.5 w-2.5 rounded-full ${c.bg}`} />
              <span className="capitalize">{r}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Beat Cards Grid */}
      <div>
        <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-3">
          Chi tiết từng Beat trong Video
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {blueprint.beats.map((beat, idx) => {
            const style = getRoleStyle(beat.role);
            const isSelected = selectedBeatIndex === idx;
            const dur = Math.max(beat.t_end - beat.t_start, 0.1);

            return (
              <div
                key={idx}
                onClick={() => setSelectedBeatIndex(idx)}
                className={`rounded-xl border p-3 cursor-pointer transition-all ${
                  isSelected
                    ? "border-indigo-500 bg-indigo-950/20 shadow-md ring-1 ring-indigo-500/50"
                    : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-zinc-400">
                    {formatSec(beat.t_start)} - {formatSec(beat.t_end)} ({dur.toFixed(1)}s)
                  </span>
                  <span
                    className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase border ${style.border} ${style.text} bg-zinc-950`}
                  >
                    {beat.role}
                  </span>
                </div>

                <p className="mt-2 text-xs font-medium text-zinc-200 line-clamp-2">
                  {beat.summary}
                </p>

                {beat.on_screen_text && (
                  <div className="mt-2 rounded bg-zinc-950/80 px-2 py-1 text-[11px] text-zinc-400 border border-zinc-800/80">
                    <span className="font-semibold text-zinc-500">Text: </span>
                    "{beat.on_screen_text}"
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Script Wizard Modal */}
      <ScriptWizardModal
        isOpen={isWizardOpen}
        projectId={projectId}
        blueprint={blueprint}
        onClose={() => setIsWizardOpen(false)}
      />
    </div>
  );
}
