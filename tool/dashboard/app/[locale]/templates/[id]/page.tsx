"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { PageBar } from "@/components/studio/PageBar";
import { SlotField } from "@/components/templates/SlotField";
import { VoiceSelectorWithClone } from "@/components/voice/VoiceSelectorWithClone";
import { videoApi, type Platform, type TemplateMeta } from "@/lib/api/video";
import { CORE_URL } from "@/lib/repositories/core";
import { useStudioStore } from "@/store";
import { Film, Play, Check, ShieldCheck, Loader2, ArrowRight } from "@/components/ui/icons";

export default function TemplateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = String(params?.id || "");
  const t = useTranslations("video");

  const activeProjectId = useStudioStore((state) => state.activeProjectId || "soc-nho-tv");

  const [template, setTemplate] = useState<TemplateMeta | null>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [voiceId, setVoiceId] = useState<string>("soc-nho");
  const [scriptText, setScriptText] = useState<string>("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>(["tiktok"]);
  const [previewPlatform, setPreviewPlatform] = useState<Platform>("tiktok");
  const [showSafeZone, setShowSafeZone] = useState<boolean>(true);
  const [autoDraft, setAutoDraft] = useState<boolean>(true);

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [rendering, setRendering] = useState<boolean>(false);
  const [quickPreviewLoading, setQuickPreviewLoading] = useState<boolean>(false);

  // Load template
  useEffect(() => {
    if (!templateId) return;
    let isMounted = true;
    async function loadTemplate() {
      try {
        setLoading(true);
        const data = await videoApi.fetchTemplate(templateId);
        if (isMounted) {
          setTemplate(data);
          setPreviewPlatform(data.default_platform || "tiktok");
          setSelectedPlatforms([data.default_platform || "tiktok"]);
          if (data.voice?.default_voice_id) {
            setVoiceId(data.voice.default_voice_id);
          }

          // Nạp dữ liệu mặc định từ slots
          const initialData: Record<string, any> = {};
          data.slots.forEach((s) => {
            if (s.default !== undefined) {
              initialData[s.key] = s.default;
            }
          });
          setFormData(initialData);
        }
      } catch (e) {
        console.error("Lỗi nạp template:", e);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadTemplate();
    return () => {
      isMounted = false;
    };
  }, [templateId]);

  // Realtime validate khi formData thay đổi
  useEffect(() => {
    if (!template) return;
    const timer = setTimeout(async () => {
      try {
        const res = await videoApi.validateTemplateData(template.id, formData);
        const errMap: Record<string, string> = {};
        if (!res.valid) {
          res.errors.forEach((err) => {
            // Map lỗi tới slot tương ứng
            const match = err.match(/'([^']+)'/);
            if (match && match[1]) {
              errMap[match[1]] = err;
            }
          });
        }
        setValidationErrors(errMap);
      } catch (e) {
        // bỏ qua
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [formData, template]);

  const handleSlotChange = (key: string, val: any) => {
    setFormData((prev) => ({ ...prev, [key]: val }));
  };

  const handleTogglePlatform = (plat: Platform) => {
    setSelectedPlatforms((prev) =>
      prev.includes(plat) ? (prev.length > 1 ? prev.filter((p) => p !== plat) : prev) : [...prev, plat]
    );
  };

  const handleQuickPreview = async () => {
    if (!template) return;
    try {
      setQuickPreviewLoading(true);
      await videoApi.previewTemplate(template.id);
      alert("Đã tạo bản xem nhanh 540p thành công!");
    } catch (e: any) {
      alert(`Lỗi xem nhanh: ${e.message}`);
    } finally {
      setQuickPreviewLoading(false);
    }
  };

  const handleStartRender = async () => {
    if (!template) return;
    try {
      setRendering(true);
      const reqPayload = {
        project_id: activeProjectId,
        template_id: template.id,
        platforms: selectedPlatforms,
        data: {
          ...formData,
          auto_draft: autoDraft,
          title: formData.title || formData.hook_text || template.name,
        },
        voice: {
          voice_id: voiceId,
          script: scriptText || undefined,
        },
        output_name: `${template.id}_${Date.now()}`,
      };

      const job = await videoApi.submitRender(activeProjectId, reqPayload);
      router.push("/renders");
    } catch (e: any) {
      alert(`Lỗi gửi yêu cầu render: ${e.message}`);
    } finally {
      setRendering(false);
    }
  };

  if (loading || !template) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-slate-950 text-slate-400">
        <Loader2 className="h-6 w-6 animate-spin text-sky-400" />
      </div>
    );
  }

  const previewJpg = `${CORE_URL}/video/templates/${template.id}/preview.jpg`;
  const is916 = previewPlatform !== "youtube" && previewPlatform !== "facebook";

  return (
    <div className="relative h-full w-full overflow-clip bg-slate-950 text-slate-100">
      <PageBar page="templates" />
      <div className="scroll-quiet h-full overflow-y-auto">
        <div className="mx-auto max-w-7xl space-y-6 px-4 pb-16 pt-16 md:px-8">
          {/* Header */}
          <div className="flex flex-col gap-2 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2 text-xs text-sky-400 font-semibold uppercase">
              <span>{template.category}</span>
              <span>•</span>
              <span>Phiên bản {template.version}</span>
            </div>
            <h1 className="text-2xl font-bold text-white">{template.name}</h1>
          </div>

          {/* Hai cột: Trái (Form Slots) - Phải (Preview & Safe Zone) */}
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
            {/* Cột trái: Form cấu hình slots (lg:col-span-7) */}
            <div className="flex flex-col gap-5 lg:col-span-7">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
                <h2 className="text-sm font-bold text-slate-200">Dữ liệu nội dung (Slots)</h2>

                <div className="flex flex-col gap-4">
                  {template.slots.map((slot) => (
                    <SlotField
                      key={slot.key}
                      slot={slot}
                      value={formData[slot.key]}
                      onChange={(val) => handleSlotChange(slot.key, val)}
                      error={validationErrors[slot.key]}
                      projectId={activeProjectId}
                    />
                  ))}
                </div>
              </div>

              {/* Cấu hình Giọng đọc & Kịch bản */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
                <h2 className="text-sm font-bold text-slate-200">🎙️ Giọng đọc & Kịch bản</h2>

                <div className="space-y-3">
                  <label className="text-xs font-semibold text-slate-300">Giọng đọc OmniVoice</label>
                  <VoiceSelectorWithClone
                    value={voiceId}
                    onChange={setVoiceId}
                    projectId={activeProjectId}
                  />

                  <div className="flex flex-col gap-1.5 pt-2">
                    <label className="text-xs font-semibold text-slate-300">Kịch bản thoại (tự đo thời lượng)</label>
                    <textarea
                      rows={3}
                      value={scriptText}
                      onChange={(e) => setScriptText(e.target.value)}
                      placeholder="Nhập kịch bản để tự động tạo audio đọc cho video..."
                      className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-xs text-slate-200 outline-none focus:border-sky-500"
                    />
                  </div>
                </div>
              </div>

              {/* Khối chọn nền tảng xuất & Nút Render */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 space-y-4">
                <h2 className="text-sm font-bold text-slate-200">Xuất bản đa nền tảng</h2>

                <div className="flex flex-wrap gap-2">
                  {template.platforms.map((plat) => {
                    const isChecked = selectedPlatforms.includes(plat);
                    return (
                      <button
                        key={plat}
                        type="button"
                        onClick={() => handleTogglePlatform(plat)}
                        className={`flex items-center gap-2 rounded-xl border px-3.5 py-2 text-xs font-bold uppercase transition-all ${
                          isChecked
                            ? "border-sky-500 bg-sky-500/20 text-sky-300 shadow-md shadow-sky-500/10"
                            : "border-slate-800 bg-slate-950 text-slate-500 hover:text-slate-300"
                        }`}
                      >
                        <span
                          className={`flex h-4 w-4 items-center justify-center rounded border ${
                            isChecked ? "border-sky-400 bg-sky-500 text-white" : "border-slate-700"
                          }`}
                        >
                          {isChecked && <Check className="h-3 w-3" />}
                        </span>
                        {plat}
                      </button>
                    );
                  })}
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="auto-draft"
                    checked={autoDraft}
                    onChange={(e) => setAutoDraft(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-sky-500 focus:ring-0"
                  />
                  <label htmlFor="auto-draft" className="text-xs font-medium text-slate-300">
                    {t("autoDraft")}
                  </label>
                </div>

                <button
                  type="button"
                  onClick={handleStartRender}
                  disabled={rendering}
                  className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 py-3 text-sm font-bold text-white shadow-lg shadow-sky-500/25 transition-all hover:opacity-95 disabled:opacity-50"
                >
                  {rendering ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> {t("rendering")}
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-white" /> {t("renderButton")} ({selectedPlatforms.length} nền tảng)
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Cột phải: Preview khung hình & Safe Zone (lg:col-span-5) */}
            <div className="flex flex-col gap-4 lg:col-span-5">
              <div className="sticky top-20 flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                {/* Preview controls */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-1.5">
                    {template.platforms.map((plat) => (
                      <button
                        key={plat}
                        type="button"
                        onClick={() => setPreviewPlatform(plat)}
                        className={`rounded-lg px-2.5 py-1 text-[11px] font-bold uppercase transition-colors ${
                          previewPlatform === plat
                            ? "bg-slate-200 text-slate-950"
                            : "bg-slate-950 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {plat}
                      </button>
                    ))}
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowSafeZone(!showSafeZone)}
                    className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                      showSafeZone
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                        : "bg-slate-950 text-slate-500"
                    }`}
                  >
                    <ShieldCheck className="h-3.5 w-3.5" /> Safe-zone
                  </button>
                </div>

                {/* Simulated Device Screen with Safe-zone Overlay */}
                <div className="flex items-center justify-center py-2">
                  <div
                    className={`relative overflow-hidden rounded-2xl border border-slate-700 bg-black shadow-2xl transition-all ${
                      previewPlatform === "youtube"
                        ? "aspect-video w-full"
                        : previewPlatform === "facebook"
                        ? "aspect-[4/5] w-72"
                        : "aspect-[9/16] w-64"
                    }`}
                  >
                    <img
                      src={previewJpg}
                      alt="Preview"
                      className="h-full w-full object-cover"
                    />

                    {/* Safe Zone Overlay */}
                    {showSafeZone && (
                      <div className="pointer-events-none absolute inset-0 z-30">
                        {/* Header Safe Zone (top) */}
                        <div className="absolute top-0 left-0 right-0 h-[10%] bg-rose-500/20 border-b border-dashed border-rose-500 flex items-center justify-center">
                          <span className="text-[10px] font-mono font-bold text-rose-300">TOP SAFE ZONE</span>
                        </div>
                        {/* Bottom Safe Zone (cart / tabs) */}
                        <div className="absolute bottom-0 left-0 right-0 h-[16%] bg-rose-500/20 border-t border-dashed border-rose-500 flex items-center justify-center">
                          <span className="text-[10px] font-mono font-bold text-rose-300">BOTTOM SAFE ZONE</span>
                        </div>
                        {/* Right interaction column */}
                        {is916 && (
                          <div className="absolute top-[20%] right-0 bottom-[20%] w-[12%] bg-amber-500/15 border-l border-dashed border-amber-500 flex items-center justify-center">
                            <span className="text-[9px] font-mono font-bold text-amber-300 -rotate-90">BUTTONS</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Nút Xem nhanh 540p */}
                <button
                  type="button"
                  onClick={handleQuickPreview}
                  disabled={quickPreviewLoading}
                  className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-slate-700 bg-slate-950 py-2.5 text-xs font-semibold text-slate-300 transition-colors hover:bg-slate-800 disabled:opacity-50"
                >
                  {quickPreviewLoading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <span>⚡ Xem nhanh (540p)</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
