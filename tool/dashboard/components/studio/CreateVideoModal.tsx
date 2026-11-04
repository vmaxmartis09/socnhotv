"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useStudioStore } from "@/store";
import { videoApi, type TemplateMeta, type Platform, type PlatformPreset } from "@/lib/api/video";
import { generateTemplateGraph } from "@/lib/template-graphs";
import { validateGraphWithCore, runGraphOnCore } from "@/lib/core-api";
import { CORE_URL } from "@/lib/repositories/core";
import { SlotField } from "@/components/templates/SlotField";
import { VoiceSelectorWithClone } from "@/components/voice/VoiceSelectorWithClone";
import {
  X,
  Sparkles,
  Film,
  Check,
  ChevronRight,
  Layers,
  Wand2,
  Loader2,
  Video,
  Play,
  RotateCcw,
} from "@/components/ui/icons";
import { cn } from "@/lib/utils";

interface CreateVideoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CATEGORY_CHIPS = [
  { id: "all", label: "Tất cả mẫu" },
  { id: "sales", label: "Bán hàng TikTok" },
  { id: "review", label: "KOC Review" },
  { id: "animation", label: "Hoạt hình 3D" },
  { id: "education", label: "Khám phá / Fact" },
  { id: "affiliate", label: "Affiliate So sánh" },
  { id: "story", label: "Truyện kể" },
  { id: "reup", label: "Bản địa hoá" },
];

export function CreateVideoModal({ isOpen, onClose }: CreateVideoModalProps) {
  const {
    activeProjectId,
    nodeCatalog,
    isMockMode,
    createEpisode,
    selectEpisode,
    addJob,
    updateJob,
  } = useStudioStore();

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [templates, setTemplates] = useState<TemplateMeta[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateMeta | null>(null);
  const [hoveredTemplateId, setHoveredTemplateId] = useState<string | null>(null);

  // Step 2: Content
  const [topic, setTopic] = useState("");
  const [isGeneratingScript, setIsGeneratingScript] = useState(false);
  const [scriptText, setScriptText] = useState("");
  const [slotValues, setSlotValues] = useState<Record<string, any>>({});
  const [productInfo, setProductInfo] = useState({
    title: "",
    name: "",
    price: "",
    usp: "",
    image: "",
  });
  const [selectedCharacterId, setSelectedCharacterId] = useState("soc_nho");
  const [selectedVoiceId, setSelectedVoiceId] = useState("soc-nho");

  // Batch toggle
  const [isBatchMode, setIsBatchMode] = useState(false);
  const [batchTopicsText, setBatchTopicsText] = useState("");

  // Step 3: Export
  const [platforms, setPlatforms] = useState<Platform[]>(["tiktok"]);
  const [platformPresets, setPlatformPresets] = useState<PlatformPreset[]>([]);
  const [qualityLevel, setQualityLevel] = useState<"standard" | "high">("standard");
  const [isEstimating, setIsEstimating] = useState(false);
  const [estimatedCost, setEstimatedCost] = useState<number>(0.0);
  const [isCreating, setIsCreating] = useState(false);
  const [createProgressText, setCreateProgressText] = useState("");

  const videoRefs = useRef<Record<string, HTMLVideoElement | null>>({});

  // Load templates and platforms on mount
  useEffect(() => {
    if (!isOpen) return;
    async function loadData() {
      try {
        const [tpls, plats] = await Promise.all([
          videoApi.fetchTemplates().catch(() => []),
          videoApi.fetchPlatforms().catch(() => []),
        ]);
        setTemplates(tpls);
        setPlatformPresets(plats);
        if (tpls.length > 0 && !selectedTemplate) {
          setSelectedTemplate(tpls[0]);
          setPlatforms([tpls[0].default_platform || "tiktok"]);
        }
      } catch (err) {
        console.error("Failed to load templates:", err);
      }
    }
    loadData();
  }, [isOpen]);

  // When selectedTemplate changes, update defaults
  useEffect(() => {
    if (selectedTemplate) {
      setPlatforms([selectedTemplate.default_platform || "tiktok"]);
      setSelectedVoiceId(selectedTemplate.voice?.default_voice_id || "soc-nho");
      // Pre-fill default slots
      const initialSlots: Record<string, any> = {};
      selectedTemplate.slots.forEach((s) => {
        if (s.default !== undefined && s.default !== null) {
          initialSlots[s.key] = s.default;
        }
      });
      setSlotValues(initialSlots);
    }
  }, [selectedTemplate]);

  // Estimate cost when reaching step 3
  useEffect(() => {
    if (step === 3 && selectedTemplate) {
      estimateCost();
    }
  }, [step, selectedTemplate, isBatchMode, batchTopicsText]);

  const estimateCost = async () => {
    if (!selectedTemplate) return;
    setIsEstimating(true);
    try {
      const topicCount = isBatchMode
        ? Math.max(1, batchTopicsText.split("\n").filter((l) => l.trim().length > 0).length)
        : 1;

      const dummyBundle = generateTemplateGraph({
        projectId: activeProjectId,
        template: selectedTemplate,
        topic: topic || "Video mới",
        scriptText,
        characterId: selectedCharacterId,
        voiceId: selectedVoiceId,
        platforms,
        slotValues,
        productInfo,
      });

      const res = await fetch(`${CORE_URL}/projects/${activeProjectId}/estimate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ graph: dummyBundle.coreGraph, mockMode: isMockMode }),
      });
      if (res.ok) {
        const data = await res.json();
        setEstimatedCost((data.totalEstimatedCostUsd || 0.0) * topicCount);
      }
    } catch {
      setEstimatedCost(0.0);
    } finally {
      setIsEstimating(false);
    }
  };

  const handleGenerateScript = async () => {
    const currentTopic = topic.trim();
    if (!currentTopic) return;
    setIsGeneratingScript(true);
    try {
      const res = await fetch(`${CORE_URL}/projects/${activeProjectId}/ai/script`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: currentTopic, mockMode: isMockMode }),
      });
      if (res.ok) {
        const data = await res.json();
        const md = data.markdown || "";
        setScriptText(md);

        // Auto-fill template slots from generated content
        const updatedSlots = { ...slotValues };
        if (selectedTemplate) {
          selectedTemplate.slots.forEach((s) => {
            if (s.key.includes("title") || s.key.includes("question") || s.key === "item_a") {
              updatedSlots[s.key] = currentTopic;
            }
          });
        }
        setSlotValues(updatedSlots);
      }
    } catch (err) {
      console.error("Generate script failed:", err);
    } finally {
      setIsGeneratingScript(false);
    }
  };

  const handleCreateVideos = async () => {
    if (!selectedTemplate) return;
    setIsCreating(true);

    const topicsList: string[] = isBatchMode
      ? batchTopicsText
          .split("\n")
          .map((t) => t.trim())
          .filter((t) => t.length > 0)
      : [topic.trim() || selectedTemplate.name];

    if (topicsList.length === 0) {
      topicsList.push(selectedTemplate.name);
    }

    try {
      for (let i = 0; i < topicsList.length; i++) {
        const itemTopic = topicsList[i];
        setCreateProgressText(
          `Đang tạo video ${i + 1}/${topicsList.length}: "${itemTopic.slice(0, 30)}..."`
        );

        // 1. Generate graph bundle
        const bundle = generateTemplateGraph({
          projectId: activeProjectId,
          template: selectedTemplate,
          topic: itemTopic,
          scriptText: isBatchMode ? "" : scriptText,
          characterId: selectedCharacterId,
          voiceId: selectedVoiceId,
          platforms,
          slotValues,
          productInfo,
        });

        // 2. Create episode in store
        const isLast = i === topicsList.length - 1;
        const newEp = createEpisode(itemTopic, {
          customGraph: bundle.reactFlowGraph,
          autoSelect: isLast,
        });

        // 3. Validate with core
        await validateGraphWithCore(activeProjectId, bundle.coreGraph, nodeCatalog);

        // 4. Submit run to core & add to jobs
        const jobId = `job_${Date.now()}_${i}`;
        addJob({
          id: jobId,
          projectId: activeProjectId,
          type: "render",
          model: selectedTemplate.id,
          status: "running",
          progress: 10,
          estimatedCostUsd: isMockMode ? 0.0 : 0.05,
          actualCostUsd: 0.0,
          createdAt: new Date().toISOString(),
          logs: [`Bắt đầu render mẫu ${selectedTemplate.name} cho tập ${newEp.title}`],
        });

        // Fire run on core (non-blocking in queue)
        runGraphOnCore(activeProjectId, {
          graph: bundle.coreGraph,
          mode: "all" as any,
          mockMode: isMockMode,
        })
          .then((summary) => {
            if (summary) {
              updateJob(jobId, {
                status: summary.isSuccess ? "completed" : "failed",
                progress: 100,
                actualCostUsd: summary.totalCostUsd || 0.0,
                completedAt: new Date().toISOString(),
                outputUrl: `${CORE_URL}/data/projects/${activeProjectId}/output/final_render.mp4`,
              });
            }
          })
          .catch((err) => {
            updateJob(jobId, {
              status: "failed",
              logs: [String(err)],
            });
          });
      }

      onClose();
    } catch (err) {
      console.error("Create video batch failed:", err);
    } finally {
      setIsCreating(false);
      setCreateProgressText("");
    }
  };

  const filteredTemplates = templates.filter((t) => {
    if (selectedCategory === "all") return true;
    return t.category === selectedCategory;
  });

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-background/80 backdrop-blur-sm"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96 }}
        className="relative flex flex-col w-full max-w-4xl max-h-[90vh] rounded-2xl border border-border bg-card shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-3.5 shrink-0 bg-accent/30">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                Tạo video tự động trong Studio
                <span className="text-[11px] font-normal text-muted-foreground">
                  (Bước {step}/3)
                </span>
              </h2>
              <p className="text-xs text-muted-foreground">
                {step === 1 && "Chọn mẫu kịch bản & visual định sẵn"}
                {step === 2 && "Tự sinh lời thoại hoặc tuỳ biến nội dung"}
                {step === 3 && "Xem trước chuẩn nền tảng & tạo đồ thị"}
              </p>
            </div>
          </div>

          {/* Step Breadcrumbs */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs">
            <button
              onClick={() => setStep(1)}
              className={cn(
                "px-2.5 py-1 rounded-md transition-colors",
                step === 1
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:bg-accent"
              )}
            >
              1. Mẫu
            </button>
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
            <button
              onClick={() => selectedTemplate && setStep(2)}
              disabled={!selectedTemplate}
              className={cn(
                "px-2.5 py-1 rounded-md transition-colors",
                step === 2
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:bg-accent disabled:opacity-40"
              )}
            >
              2. Nội dung
            </button>
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
            <button
              onClick={() => selectedTemplate && setStep(3)}
              disabled={!selectedTemplate}
              className={cn(
                "px-2.5 py-1 rounded-md transition-colors",
                step === 3
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:bg-accent disabled:opacity-40"
              )}
            >
              3. Xuất
            </button>
          </div>

          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 scroll-quiet">
          {/* STEP 1: CHỌN MẪU */}
          {step === 1 && (
            <div className="space-y-4">
              {/* Category Filter Chips */}
              <div className="flex flex-wrap gap-1.5 pb-1">
                {CATEGORY_CHIPS.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={cn(
                      "px-3 py-1 rounded-full text-xs font-medium transition-colors",
                      selectedCategory === cat.id
                        ? "bg-foreground text-background"
                        : "border border-border text-muted-foreground hover:bg-accent hover:text-foreground"
                    )}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>

              {/* Template Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {filteredTemplates.map((tpl) => {
                  const isSelected = selectedTemplate?.id === tpl.id;
                  const isHovered = hoveredTemplateId === tpl.id;
                  const previewJpgUrl = `${CORE_URL}/video/templates/${tpl.id}/preview.jpg`;
                  const previewMp4Url = `${CORE_URL}/video/templates/${tpl.id}/preview.mp4`;

                  return (
                    <div
                      key={tpl.id}
                      onClick={() => setSelectedTemplate(tpl)}
                      onMouseEnter={() => {
                        setHoveredTemplateId(tpl.id);
                        const v = videoRefs.current[tpl.id];
                        if (v) {
                          v.currentTime = 0;
                          v.play().catch(() => {});
                        }
                      }}
                      onMouseLeave={() => {
                        setHoveredTemplateId(null);
                        const v = videoRefs.current[tpl.id];
                        if (v) v.pause();
                      }}
                      className={cn(
                        "group relative flex flex-col rounded-xl border p-2 cursor-pointer transition-all duration-200 select-none",
                        isSelected
                          ? "border-primary bg-primary/5 ring-2 ring-primary/30"
                          : "border-border bg-card/60 hover:border-primary/50 hover:bg-accent/40"
                      )}
                    >
                      {/* Thumbnail Container */}
                      <div className="relative aspect-[9/16] w-full overflow-hidden rounded-lg bg-black/40">
                        <img
                          src={previewJpgUrl}
                          alt={tpl.name}
                          className={cn(
                            "h-full w-full object-cover transition-opacity duration-300",
                            isHovered ? "opacity-0" : "opacity-100"
                          )}
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                          }}
                        />

                        {/* Hover Video Preview */}
                        <video
                          ref={(el) => {
                            videoRefs.current[tpl.id] = el;
                          }}
                          src={previewMp4Url}
                          muted
                          loop
                          playsInline
                          className={cn(
                            "absolute inset-0 h-full w-full object-cover transition-opacity duration-300",
                            isHovered ? "opacity-100" : "opacity-0 pointer-events-none"
                          )}
                        />

                        {/* Badges */}
                        <div className="absolute top-1.5 left-1.5 flex gap-1 z-10">
                          <span className="rounded bg-black/70 px-1.5 py-0.5 text-[9px] font-medium uppercase text-white backdrop-blur-sm">
                            {tpl.category}
                          </span>
                        </div>

                        <div className="absolute bottom-1.5 right-1.5 z-10">
                          <span className="rounded bg-black/70 px-1.5 py-0.5 text-[9px] font-mono text-white/90 backdrop-blur-sm">
                            {tpl.duration?.min}s - {tpl.duration?.max}s
                          </span>
                        </div>

                        {isSelected && (
                          <div className="absolute top-1.5 right-1.5 z-10 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground shadow">
                            <Check className="h-3 w-3" />
                          </div>
                        )}
                      </div>

                      {/* Meta */}
                      <div className="mt-2 flex flex-col gap-0.5">
                        <h4 className="line-clamp-2 text-xs font-semibold text-foreground group-hover:text-primary transition-colors">
                          {tpl.name}
                        </h4>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {tpl.platforms.map((p) => (
                            <span
                              key={p}
                              className="rounded bg-accent px-1 py-0.2 text-[9px] font-medium uppercase text-muted-foreground"
                            >
                              {p}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 2: NỘI DUNG & KỊCH BẢN */}
          {step === 2 && selectedTemplate && (
            <div className="space-y-5">
              {/* Batch Mode Switch */}
              <div className="flex items-center justify-between rounded-xl border border-border bg-accent/30 p-3">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <Layers className="h-4 w-4 text-primary" />
                    Chế độ Hàng loạt (Batch Video)
                  </span>
                  <p className="text-[11px] text-muted-foreground">
                    Tạo N video cùng lúc với các chủ đề khác nhau dùng chung mẫu & giọng
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isBatchMode}
                    onChange={(e) => setIsBatchMode(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-10 h-5 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-background after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-background after:border-border after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                </label>
              </div>

              {isBatchMode ? (
                /* Batch Inputs */
                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-foreground">
                    Danh sách chủ đề (Mỗi dòng 1 video, hoặc ngăn cách bằng "---"):
                  </label>
                  <textarea
                    rows={6}
                    value={batchTopicsText}
                    onChange={(e) => setBatchTopicsText(e.target.value)}
                    placeholder={`Chủ đề 1: Review kem chống nắng Sóc Nhỏ đi biển\nChủ đề 2: Thử thách tìm hạt dẻ kỳ diệu cùng Koala\nChủ đề 3: Khám phá bí ẩn rừng xanh`}
                    className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground outline-none focus:border-primary font-mono leading-relaxed"
                  />
                  <p className="text-[11px] text-muted-foreground">
                    Số lượng video dự kiến:{" "}
                    <span className="font-semibold text-primary">
                      {batchTopicsText.split("\n").filter((l) => l.trim().length > 0).length}
                    </span>
                  </p>
                </div>
              ) : (
                /* Single Video Script & Topic */
                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-foreground">
                        Chủ đề / Ý tưởng video:
                      </label>
                      <button
                        type="button"
                        onClick={handleGenerateScript}
                        disabled={isGeneratingScript || !topic.trim()}
                        className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors shadow-2xs"
                      >
                        {isGeneratingScript ? (
                          <>
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            <span>Đang viết kịch bản...</span>
                          </>
                        ) : (
                          <>
                            <Wand2 className="h-3.5 w-3.5" />
                            <span>Tự viết kịch bản</span>
                          </>
                        )}
                      </button>
                    </div>
                    <input
                      type="text"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder="Nhập ý tưởng (vd: Sóc Nhỏ review kem chống nắng, Câu chuyện hạt dẻ thần kỳ...)"
                      className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-xs text-foreground outline-none focus:border-primary"
                    />
                  </div>

                  {scriptText && (
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <label className="text-xs font-semibold text-foreground">
                          Kịch bản chi tiết (sửa trực tiếp nếu muốn):
                        </label>
                        <span className="text-[11px] text-muted-foreground">
                          Đã tự điền vào các slot bên dưới
                        </span>
                      </div>
                      <textarea
                        rows={4}
                        value={scriptText}
                        onChange={(e) => setScriptText(e.target.value)}
                        className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground outline-none focus:border-primary font-mono leading-relaxed"
                      />
                    </div>
                  )}

                  {/* Template Slots Editing */}
                  <div className="space-y-3 pt-2 border-t border-border">
                    <h4 className="text-xs font-semibold text-foreground">
                      Các trường nội dung của mẫu ({selectedTemplate.slots.length} trường):
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {selectedTemplate.slots.map((slot) => (
                        <SlotField
                          key={slot.key}
                          slot={slot}
                          value={slotValues[slot.key]}
                          onChange={(val) =>
                            setSlotValues((prev) => ({ ...prev, [slot.key]: val }))
                          }
                          projectId={activeProjectId}
                        />
                      ))}
                    </div>
                  </div>

                  {/* In-form Product slot if applicable */}
                  {(selectedTemplate.category === "sales" ||
                    selectedTemplate.category === "review" ||
                    selectedTemplate.category === "affiliate") && (
                    <div className="space-y-2 rounded-xl border border-border bg-accent/20 p-3.5">
                      <span className="text-xs font-semibold text-foreground">
                        🛍️ Thông tin sản phẩm gắn kèm (nhập trực tiếp):
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <input
                          type="text"
                          placeholder="Tên sản phẩm..."
                          value={productInfo.title}
                          onChange={(e) =>
                            setProductInfo((prev) => ({
                              ...prev,
                              title: e.target.value,
                              name: e.target.value,
                            }))
                          }
                          className="rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground outline-none focus:border-primary"
                        />
                        <input
                          type="text"
                          placeholder="Giá sản phẩm (vd: 199.000đ)..."
                          value={productInfo.price}
                          onChange={(e) =>
                            setProductInfo((prev) => ({ ...prev, price: e.target.value }))
                          }
                          className="rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground outline-none focus:border-primary"
                        />
                        <input
                          type="text"
                          placeholder="Điểm nổi bật / USP..."
                          value={productInfo.usp}
                          onChange={(e) =>
                            setProductInfo((prev) => ({ ...prev, usp: e.target.value }))
                          }
                          className="rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground outline-none focus:border-primary"
                        />
                        <input
                          type="text"
                          placeholder="URL ảnh sản phẩm (tuỳ chọn)..."
                          value={productInfo.image}
                          onChange={(e) =>
                            setProductInfo((prev) => ({ ...prev, image: e.target.value }))
                          }
                          className="rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground outline-none focus:border-primary"
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Character & Voice */}
              <div className="space-y-2.5 pt-2 border-t border-border">
                <span className="text-xs font-semibold text-foreground">
                  Nhân vật & Giọng đọc:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] text-muted-foreground">Nhân vật:</label>
                    <select
                      value={selectedCharacterId}
                      onChange={(e) => setSelectedCharacterId(e.target.value)}
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
                    >
                      <option value="soc_nho">Sóc Nhỏ (Bi) — 100cm, Áo vàng</option>
                      <option value="koala">Bạn Koala — 150cm, Bác sĩ</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] text-muted-foreground">Giọng lồng tiếng:</label>
                    <VoiceSelectorWithClone
                      value={selectedVoiceId}
                      onChange={setSelectedVoiceId}
                      projectId={activeProjectId}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: XUẤT ĐỊNH DẠNG & THÔNG SỐ */}
          {step === 3 && selectedTemplate && (
            <div className="space-y-5">
              {/* Platform Selection */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground">
                  Nền tảng xuất bản (tự áp chuẩn Safe-Zone & Tỷ lệ):
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {(["tiktok", "shorts", "reels", "youtube"] as Platform[]).map((plat) => {
                    const checked = platforms.includes(plat);
                    return (
                      <button
                        key={plat}
                        type="button"
                        onClick={() => {
                          if (checked && platforms.length > 1) {
                            setPlatforms(platforms.filter((p) => p !== plat));
                          } else if (!checked) {
                            setPlatforms([...platforms, plat]);
                          }
                        }}
                        className={cn(
                          "flex items-center gap-2 rounded-xl border p-3 text-xs font-medium transition-all text-left",
                          checked
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border bg-background text-muted-foreground hover:bg-accent"
                        )}
                      >
                        <div
                          className={cn(
                            "flex h-4 w-4 shrink-0 items-center justify-center rounded border",
                            checked ? "border-primary bg-primary text-white" : "border-border"
                          )}
                        >
                          {checked && <Check className="h-3 w-3" />}
                        </div>
                        <span className="capitalize">{plat}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Quality level */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground">Chất lượng video:</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setQualityLevel("standard")}
                    className={cn(
                      "flex flex-col gap-0.5 rounded-xl border p-3 text-left transition-all",
                      qualityLevel === "standard"
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-background text-muted-foreground hover:bg-accent"
                    )}
                  >
                    <span className="text-xs font-semibold">Chuẩn (1080p Standard)</span>
                    <span className="text-[11px] text-muted-foreground">
                      Tối ưu tốc độ render, chuẩn TikTok & Reels
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setQualityLevel("high")}
                    className={cn(
                      "flex flex-col gap-0.5 rounded-xl border p-3 text-left transition-all",
                      qualityLevel === "high"
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-background text-muted-foreground hover:bg-accent"
                    )}
                  >
                    <span className="text-xs font-semibold">Cao (1080p High Bitrate)</span>
                    <span className="text-[11px] text-muted-foreground">
                      Bitrate cao, chuẩn phát YouTube 4K/FHD
                    </span>
                  </button>
                </div>
              </div>

              {/* Automatic Specs Summary (No technical inputs!) */}
              <div className="rounded-xl border border-border bg-accent/30 p-4 space-y-2 text-xs">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Film className="h-4 w-4 text-primary" />
                  Thông số kỹ thuật tự động hoá (từ preset chuẩn):
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] pt-1">
                  <div className="space-y-0.5">
                    <span className="text-muted-foreground">Kích thước:</span>
                    <p className="font-semibold text-foreground">
                      {selectedTemplate.default_platform === "youtube" ? "1920×1080 (16:9)" : "1080×1920 (9:16)"}
                    </p>
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-muted-foreground">Âm thanh:</span>
                    <p className="font-semibold text-foreground">-14 LUFS (TikTok SOTA)</p>
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-muted-foreground">Safe Zone:</span>
                    <p className="font-semibold text-foreground">Top 180px · Bottom 320px</p>
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-muted-foreground">Codec & FPS:</span>
                    <p className="font-semibold text-foreground">H.264 / AAC @ 30fps</p>
                  </div>
                </div>
              </div>

              {/* Estimate Cost Card */}
              <div className="flex items-center justify-between rounded-xl border border-border bg-card p-3.5">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold text-foreground">
                    Ước tính chi phí sản xuất:
                  </span>
                  <p className="text-[11px] text-muted-foreground">
                    {isMockMode
                      ? "Chế độ Chạy thử (Mock mode: 0 USD)"
                      : "Dựa trên mô hình AI đã chọn"}
                  </p>
                </div>
                <div className="text-right">
                  {isEstimating ? (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  ) : (
                    <span className="text-base font-bold text-primary font-mono">
                      ${estimatedCost.toFixed(2)} USD
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-border px-5 py-3 shrink-0 bg-accent/20">
          <div>
            {step > 1 && (
              <button
                type="button"
                onClick={() => setStep((s) => (s - 1) as 1 | 2)}
                disabled={isCreating}
                className="rounded-lg border border-border px-3.5 py-1.5 text-xs font-semibold text-foreground hover:bg-accent disabled:opacity-40 transition-colors"
              >
                Quay lại
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            {step < 3 ? (
              <button
                type="button"
                onClick={() => setStep((s) => (s + 1) as 2 | 3)}
                disabled={!selectedTemplate}
                className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors shadow-2xs"
              >
                <span>Tiếp tục</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleCreateVideos}
                disabled={isCreating}
                className="flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors shadow"
              >
                {isCreating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>{createProgressText || "Đang khởi tạo đồ thị..."}</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>
                      {isBatchMode
                        ? `Tạo ${Math.max(
                            1,
                            batchTopicsText.split("\n").filter((l) => l.trim().length > 0).length
                          )} video hàng loạt`
                        : "Tạo video ngay"}
                    </span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
