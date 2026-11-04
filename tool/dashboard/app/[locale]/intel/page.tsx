"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { PageBar } from "@/components/studio/PageBar";
import { Brain, Sparkles, BarChart3, Layers } from "@/components/intel/icons";
import { useStudioStore } from "@/store";
import { intelApi, VideoBlueprint, PatternSummary } from "@/lib/api/intel";
import { BlueprintView } from "@/components/intel/BlueprintView";
import { ScriptWizardModal } from "@/components/intel/ScriptWizardModal";
import { Loader2 } from "@/components/ui/icons";

export default function IntelPage() {
  const t = useTranslations("intel");
  const { activeProjectId } = useStudioStore();
  const searchParams = useSearchParams();
  const initialProductId = searchParams.get("productId");

  const [blueprints, setBlueprints] = useState<VideoBlueprint[]>([]);
  const [selectedBlueprintId, setSelectedBlueprintId] = useState<string | null>(null);
  const [patterns, setPatterns] = useState<PatternSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [isStandaloneWizardOpen, setIsStandaloneWizardOpen] = useState(Boolean(initialProductId));

  const projectId = activeProjectId || "soc-nho-tv";

  useEffect(() => {
    setLoading(true);
    Promise.all([
      intelApi.fetchBlueprints(projectId),
      intelApi.fetchPatterns(projectId).catch(() => null),
    ])
      .then(([bps, pat]) => {
        setBlueprints(bps);
        if (bps.length > 0 && !selectedBlueprintId) {
          setSelectedBlueprintId(bps[0].id);
        }
        if (pat) {
          setPatterns(pat);
        }
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  const activeBlueprint = blueprints.find((b) => b.id === selectedBlueprintId) || blueprints[0];

  return (
    <div className="relative h-full w-full overflow-clip">
      <PageBar page="intel" />
      <div className="scroll-quiet h-full overflow-y-auto">
        <div className="mx-auto max-w-[1200px] space-y-6 px-6 pb-12 pt-16 md:pr-16">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="flex items-center gap-2 text-lg font-bold text-foreground">
                <Brain className="h-5 w-5 text-indigo-400" />
                {t("title")}
              </h1>
              <p className="text-xs text-muted-foreground">{t("description")}</p>
            </div>

            <button
              onClick={() => setIsStandaloneWizardOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-500 transition"
            >
              <Sparkles className="h-4 w-4" />
              Tạo Kịch bản Bán hàng
            </button>
          </div>

          {/* Patterns Summary Card if available */}
          {patterns && patterns.sample_count > 0 && (
            <div className="rounded-2xl border border-indigo-950/60 bg-gradient-to-r from-indigo-950/30 to-purple-950/20 p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-indigo-400" />
                  <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
                    Công thức Viral từ {patterns.sample_count} video mẫu
                  </h3>
                </div>
                <span className="text-xs text-zinc-400">
                  Hook trung vị:{" "}
                  <span className="font-bold text-indigo-300">
                    {patterns.median_hook_duration_sec.toFixed(1)}s
                  </span>
                </span>
              </div>

              {patterns.common_hook_formulas.length > 0 && (
                <div className="mt-3">
                  <span className="text-[11px] font-semibold text-zinc-400">
                    Khuôn mẫu Hook phổ biến:
                  </span>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {patterns.common_hook_formulas.map((f, i) => (
                      <span
                        key={i}
                        className="rounded-lg bg-zinc-900/80 px-2.5 py-1 text-xs text-zinc-300 border border-zinc-800"
                      >
                        "{f}"
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Blueprint Selector Tabs */}
          {blueprints.length > 0 && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              <span className="text-xs font-semibold text-zinc-400 mr-1 shrink-0">
                Danh sách Blueprint:
              </span>
              {blueprints.map((bp) => {
                const isActive = bp.id === activeBlueprint?.id;
                return (
                  <button
                    key={bp.id}
                    onClick={() => setSelectedBlueprintId(bp.id)}
                    className={`rounded-xl px-3 py-1.5 text-xs font-medium transition shrink-0 ${
                      isActive
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                        : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
                    }`}
                  >
                    #{bp.id} ({bp.beats.length} beats)
                  </button>
                );
              })}
            </div>
          )}

          {/* Main Blueprint View */}
          {loading ? (
            <div className="flex h-64 items-center justify-center text-zinc-500">
              <Loader2 className="h-6 w-6 animate-spin text-indigo-500 mr-2" />
              <span className="text-xs">Đang tải dữ liệu Blueprint...</span>
            </div>
          ) : activeBlueprint ? (
            <BlueprintView blueprint={activeBlueprint} projectId={projectId} />
          ) : (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-12 text-center text-zinc-500">
              <Brain className="mx-auto h-12 w-12 text-zinc-700" />
              <h3 className="mt-4 text-sm font-semibold text-zinc-300">
                {t("empty")}
              </h3>
              <p className="mt-1 text-xs text-zinc-500 max-w-md mx-auto">
                Vào trang "Nguồn video", mở chi tiết một video nguồn bất kỳ và bấm nút "Phân tích cấu trúc Blueprint" để giải mã nhịp điệu và visual cues.
              </p>
            </div>
          )}

          {/* Standalone Wizard Modal */}
          <ScriptWizardModal
            isOpen={isStandaloneWizardOpen}
            projectId={projectId}
            initialProductId={initialProductId}
            blueprint={activeBlueprint}
            onClose={() => setIsStandaloneWizardOpen(false)}
          />
        </div>
      </div>
    </div>
  );
}
