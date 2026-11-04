"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { PageBar } from "@/components/studio/PageBar";
import {
  Brain,
  Sparkles,
  BarChart3,
  Layers,
  Tv,
  Target,
  Plus,
} from "@/components/intel/icons";
import { useStudioStore } from "@/store";
import {
  intelApi,
  VideoBlueprint,
  PatternSummary,
  ChannelMeta,
  ChannelAnalysisResponse,
} from "@/lib/api/intel";
import { BlueprintView } from "@/components/intel/BlueprintView";
import { ScriptWizardModal } from "@/components/intel/ScriptWizardModal";
import { ChannelDetailView } from "@/components/intel/ChannelDetailView";
import { StrategyView } from "@/components/intel/StrategyView";
import { IdeaBoard } from "@/components/intel/IdeaBoard";
import { AddChannelModal } from "@/components/intel/AddChannelModal";
import { Loader2 } from "@/components/ui/icons";

export default function IntelPage() {
  const t = useTranslations("intel");
  const { activeProjectId } = useStudioStore();
  const searchParams = useSearchParams();
  const initialProductId = searchParams.get("productId");

  const [activeTab, setActiveTab] = useState<"blueprints" | "channels" | "strategy" | "ideas">("blueprints");

  // Video Blueprints
  const [blueprints, setBlueprints] = useState<VideoBlueprint[]>([]);
  const [selectedBlueprintId, setSelectedBlueprintId] = useState<string | null>(null);
  const [patterns, setPatterns] = useState<PatternSummary | null>(null);
  const [loadingBlueprints, setLoadingBlueprints] = useState(true);
  const [isStandaloneWizardOpen, setIsStandaloneWizardOpen] = useState(Boolean(initialProductId));

  // Channels
  const [channels, setChannels] = useState<ChannelMeta[]>([]);
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null);
  const [channelAnalysis, setChannelAnalysis] = useState<ChannelAnalysisResponse | null>(null);
  const [loadingChannel, setLoadingChannel] = useState(false);
  const [isAddChannelOpen, setIsAddChannelOpen] = useState(false);

  const projectId = activeProjectId || "soc-nho-tv";

  // Load Blueprints
  useEffect(() => {
    setLoadingBlueprints(true);
    Promise.all([
      intelApi.fetchBlueprints(projectId),
      intelApi.fetchPatterns(projectId).catch(() => null),
    ])
      .then(([bps, pat]) => {
        setBlueprints(bps);
        if (bps.length > 0 && !selectedBlueprintId) {
          setSelectedBlueprintId(bps[0].id);
        }
        if (pat) setPatterns(pat);
      })
      .finally(() => setLoadingBlueprints(false));
  }, [projectId]);

  // Load Channels
  useEffect(() => {
    intelApi.listChannels(projectId).then((chans) => {
      setChannels(chans);
      if (chans.length > 0 && !selectedChannelId) {
        setSelectedChannelId(chans[0].id);
      }
    });
  }, [projectId]);

  // Load selected channel analysis
  useEffect(() => {
    if (selectedChannelId) {
      setLoadingChannel(true);
      intelApi
        .getChannelAnalysis(projectId, selectedChannelId)
        .then(setChannelAnalysis)
        .catch((e) => console.error(e))
        .finally(() => setLoadingChannel(false));
    } else {
      setChannelAnalysis(null);
    }
  }, [projectId, selectedChannelId]);

  const activeBlueprint = blueprints.find((b) => b.id === selectedBlueprintId) || blueprints[0];

  return (
    <div className="relative h-full w-full overflow-clip">
      <PageBar page="intel" />
      <div className="scroll-quiet h-full overflow-y-auto">
        <div className="mx-auto max-w-[1200px] space-y-6 px-6 pb-12 pt-16 md:pr-16">
          {/* Header & Tab navigation */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="flex items-center gap-2 text-lg font-bold text-foreground">
                <Brain className="h-5 w-5 text-indigo-400" />
                {t("title")}
              </h1>
              <p className="text-xs text-muted-foreground">{t("description")}</p>
            </div>

            {/* Main Tabs */}
            <div className="flex rounded-xl bg-zinc-900 p-1 border border-zinc-800">
              {[
                { id: "blueprints", label: "Video Blueprints", icon: Brain },
                { id: "channels", label: "Học Kênh Đối Thủ", icon: Tv },
                { id: "strategy", label: "Chiến Lược Kênh", icon: Target },
                { id: "ideas", label: "Bảng Ý Tưởng", icon: Layers },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      isActive
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/25"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* TAB 1: Video Blueprints */}
          {activeTab === "blueprints" && (
            <div className="space-y-6">
              {/* Patterns Summary Card */}
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

              {/* Blueprint Selector */}
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
              {loadingBlueprints ? (
                <div className="flex h-64 items-center justify-center text-zinc-500">
                  <Loader2 className="h-6 w-6 animate-spin text-indigo-500 mr-2" />
                  <span className="text-xs">Đang tải dữ liệu Blueprint...</span>
                </div>
              ) : activeBlueprint ? (
                <BlueprintView blueprint={activeBlueprint} projectId={projectId} />
              ) : (
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-12 text-center text-zinc-500">
                  <Brain className="mx-auto h-12 w-12 text-zinc-700" />
                  <h3 className="mt-4 text-sm font-semibold text-zinc-300">{t("empty")}</h3>
                  <p className="mt-1 text-xs text-zinc-500 max-w-md mx-auto">
                    Vào trang "Nguồn video", mở chi tiết một video nguồn bất kỳ và bấm nút "Phân tích cấu trúc Blueprint" để giải mã nhịp điệu và visual cues.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Channels Intelligence */}
          {activeTab === "channels" && (
            <div className="space-y-6">
              {/* Channel List & Add Channel Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2 overflow-x-auto pb-1">
                  <span className="text-xs font-semibold text-zinc-400 mr-1 shrink-0">Kênh đã học:</span>
                  {channels.map((ch) => {
                    const isSelected = selectedChannelId === ch.id;
                    return (
                      <button
                        key={ch.id}
                        onClick={() => setSelectedChannelId(ch.id)}
                        className={`rounded-xl px-3 py-1.5 text-xs font-medium transition shrink-0 ${
                          isSelected
                            ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                            : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
                        }`}
                      >
                        {ch.name} ({ch.video_count} vids)
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => setIsAddChannelOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-xs font-bold text-white shadow-lg hover:bg-indigo-500 shrink-0"
                >
                  <Plus className="h-4 w-4" />
                  Học kênh mới
                </button>
              </div>

              {/* Selected Channel Analysis */}
              {loadingChannel ? (
                <div className="flex h-64 items-center justify-center text-zinc-500">
                  <Loader2 className="h-6 w-6 animate-spin text-indigo-500 mr-2" />
                  <span className="text-xs">Đang tải phân tích kênh đối thủ...</span>
                </div>
              ) : channelAnalysis ? (
                <ChannelDetailView analysis={channelAnalysis} projectId={projectId} />
              ) : (
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-12 text-center text-zinc-500">
                  <Tv className="mx-auto h-12 w-12 text-zinc-700" />
                  <h3 className="mt-4 text-sm font-semibold text-zinc-300">
                    Chưa có kênh đối thủ nào được phân tích
                  </h3>
                  <p className="mt-1 text-xs text-zinc-500 max-w-sm mx-auto">
                    Dán đường dẫn một kênh YouTube hoặc TikTok để bóc tách chủ đề pillars, lịch đăng và video đột biến lượt xem.
                  </p>
                  <button
                    onClick={() => setIsAddChannelOpen(true)}
                    className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg hover:bg-indigo-500"
                  >
                    <Plus className="h-4 w-4" /> Thêm Kênh Đầu Tiên
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Strategy */}
          {activeTab === "strategy" && (
            <StrategyView
              projectId={projectId}
              onGoToIdeas={() => setActiveTab("ideas")}
            />
          )}

          {/* TAB 4: Ideas Kanban */}
          {activeTab === "ideas" && <IdeaBoard projectId={projectId} />}

          {/* Standalone Wizard Modal */}
          <ScriptWizardModal
            isOpen={isStandaloneWizardOpen}
            projectId={projectId}
            initialProductId={initialProductId}
            blueprint={activeBlueprint}
            onClose={() => setIsStandaloneWizardOpen(false)}
          />

          {/* Add Channel Modal */}
          <AddChannelModal
            isOpen={isAddChannelOpen}
            projectId={projectId}
            onClose={() => setIsAddChannelOpen(false)}
            onSuccess={(analysisRes) => {
              intelApi.listChannels(projectId).then(setChannels);
              setSelectedChannelId(analysisRes.channel_meta.id);
              setChannelAnalysis(analysisRes);
            }}
          />
        </div>
      </div>
    </div>
  );
}
