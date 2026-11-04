"use client";

import React, { useState, useEffect } from "react";
import type { Product, VideoBlueprint, GeneratorType, GeneratedScriptResponse } from "@/lib/api/intel";
import { intelApi } from "@/lib/api/intel";
import { videoApi, Platform } from "@/lib/api/video";
import { Sparkles, Brain, Wand2, ArrowRight, CheckCircle, AlertCircle, ShoppingBag } from "./icons";
import { X, Loader2, Check, AlertTriangle } from "@/components/ui/icons";

interface ScriptWizardModalProps {
  isOpen: boolean;
  projectId: string;
  blueprint?: VideoBlueprint | null;
  initialProductId?: string | null;
  onClose: () => void;
}

export function ScriptWizardModal({
  isOpen,
  projectId,
  blueprint,
  initialProductId,
  onClose,
}: ScriptWizardModalProps) {
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Data
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);

  // Form selections
  const [selectedProductId, setSelectedProductId] = useState<string>("");
  const [characterName, setCharacterName] = useState("LyLy");
  const [voiceId, setVoiceId] = useState("soc-nho");
  const [generatorType, setGeneratorType] = useState<GeneratorType>("koc_review");
  const [platforms, setPlatforms] = useState<Platform[]>(["tiktok", "reels", "shorts"]);

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedScript, setGeneratedScript] = useState<GeneratedScriptResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Render state
  const [isSubmittingRender, setIsSubmittingRender] = useState(false);
  const [renderJobId, setRenderJobId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setLoadingProducts(true);
      intelApi
        .fetchProducts(projectId)
        .then((prods) => {
          setProducts(prods);
          if (initialProductId && prods.some((p) => p.id === initialProductId)) {
            setSelectedProductId(initialProductId);
          } else if (prods.length > 0 && !selectedProductId) {
            setSelectedProductId(prods[0].id);
          }
        })
        .finally(() => setLoadingProducts(false));
    } else {
      setStep(1);
      setGeneratedScript(null);
      setRenderJobId(null);
      setError(null);
    }
  }, [isOpen, projectId, initialProductId]);

  if (!isOpen) return null;

  const handleNextStep1 = () => {
    if (!selectedProductId) {
      setError("Vui lòng chọn 1 sản phẩm.");
      return;
    }
    setError(null);
    setStep(2);
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const res = await intelApi.generateScript(projectId, {
        product_id: selectedProductId,
        blueprint_id: blueprint?.id,
        generator_type: generatorType,
        character_name: characterName,
        voice_id: voiceId,
        platforms,
      });
      setGeneratedScript(res);
      setStep(3);
    } catch (err: any) {
      setError(`Lỗi sinh kịch bản: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmitRender = async () => {
    if (!generatedScript?.render_request) return;
    setIsSubmittingRender(true);
    setError(null);
    try {
      const job = await videoApi.submitRender(projectId, generatedScript.render_request);
      setRenderJobId(job.job_id);
    } catch (err: any) {
      setError(`Lỗi gửi render: ${err.message}`);
    } finally {
      setIsSubmittingRender(false);
    }
  };

  const togglePlatform = (p: Platform) => {
    setPlatforms((prev) =>
      prev.includes(p) ? prev.filter((item) => item !== p) : [...prev, p]
    );
  };

  const selectedProduct = products.find((p) => p.id === selectedProductId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-3xl rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150 max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                {step}
              </span>
              <h2 className="text-base font-bold text-zinc-100">
                {step === 1 && "Bước 1: Chọn sản phẩm mục tiêu"}
                {step === 2 && "Bước 2: Cấu hình KOC, Giọng đọc & Nền tảng"}
                {step === 3 && "Bước 3: Xem kịch bản & Gửi Render"}
              </h2>
            </div>
            <p className="mt-1 text-xs text-zinc-400">
              Áp cấu trúc nhịp {blueprint ? `Blueprint ${blueprint.id}` : "chuẩn"} cho sản phẩm thương mại
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Error notification */}
        {error && (
          <div className="mt-3 rounded-lg border border-rose-900/50 bg-rose-950/30 p-2.5 text-xs text-rose-300">
            {error}
          </div>
        )}

        {/* Step 1: Select Product */}
        {step === 1 && (
          <div className="mt-4 flex-1 overflow-y-auto pr-1 space-y-4">
            <span className="text-xs text-zinc-400">
              Chọn sản phẩm từ danh mục để trích xuất USP, nỗi đau và link affiliate:
            </span>

            {loadingProducts ? (
              <div className="flex h-40 items-center justify-center text-xs text-zinc-500">
                <Loader2 className="h-5 w-5 animate-spin mr-2 text-indigo-500" />
                Đang tải danh sách sản phẩm...
              </div>
            ) : products.length === 0 ? (
              <div className="rounded-xl border border-zinc-800 p-8 text-center text-zinc-500">
                <ShoppingBag className="mx-auto h-8 w-8 text-zinc-600" />
                <p className="mt-2 text-xs">Chưa có sản phẩm nào trong kho.</p>
                <p className="mt-0.5 text-[11px] text-zinc-600">
                  Hãy vào mục "Sản phẩm" để thêm sản phẩm trước khi tạo kịch bản.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {products.map((p) => {
                  const isSelected = selectedProductId === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => setSelectedProductId(p.id)}
                      className={`flex items-start gap-3 rounded-xl border p-3 cursor-pointer transition ${
                        isSelected
                          ? "border-indigo-500 bg-indigo-950/30 shadow-md"
                          : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700"
                      }`}
                    >
                      <div className="h-12 w-12 rounded-lg bg-zinc-800 shrink-0 overflow-hidden flex items-center justify-center">
                        {p.images && p.images[0] ? (
                          <img src={p.images[0]} alt={p.name} className="h-full w-full object-cover" />
                        ) : (
                          <ShoppingBag className="h-5 w-5 text-zinc-500" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-semibold text-indigo-400 truncate">
                            {p.brand || "Brand"}
                          </span>
                          {isSelected && <CheckCircle className="h-4 w-4 text-indigo-400 shrink-0" />}
                        </div>
                        <h4 className="text-xs font-bold text-zinc-100 truncate">{p.name}</h4>
                        <span className="text-xs font-semibold text-zinc-300">
                          {p.sale_price || p.price
                            ? new Intl.NumberFormat("vi-VN").format(p.sale_price || p.price || 0) + " đ"
                            : "—"}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="mt-6 flex justify-end pt-3 border-t border-zinc-800">
              <button
                type="button"
                disabled={!selectedProductId}
                onClick={handleNextStep1}
                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                Tiếp tục <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Characters, Voices, Generator */}
        {step === 2 && (
          <div className="mt-4 flex-1 overflow-y-auto pr-1 space-y-4">
            {/* Selected Product Banner */}
            {selectedProduct && (
              <div className="flex items-center justify-between rounded-xl bg-zinc-900/70 p-3 border border-zinc-800">
                <div className="flex items-center gap-2">
                  <ShoppingBag className="h-4 w-4 text-indigo-400" />
                  <span className="text-xs font-semibold text-zinc-200">{selectedProduct.name}</span>
                </div>
                <button
                  onClick={() => setStep(1)}
                  className="text-[11px] text-indigo-400 hover:underline"
                >
                  Thay đổi
                </button>
              </div>
            )}

            {/* Generator Type */}
            <div>
              <label className="text-xs font-semibold text-zinc-300">Kiểu kịch bản</label>
              <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2">
                {[
                  {
                    id: "koc_review",
                    name: "KOC Review",
                    desc: "Ngôi thứ nhất, có ưu + nhược điểm thật, chân thực",
                  },
                  {
                    id: "tiktok_sales",
                    name: "TikTok Sales",
                    desc: "Hook 3s giật gân, nỗi đau, demo & ưu đãi giỏ hàng",
                  },
                  {
                    id: "affiliate_compare",
                    name: "So sánh Affiliate",
                    desc: "So sánh 2-3 dòng, bảng tiêu chí, chốt mua",
                  },
                ].map((t) => (
                  <div
                    key={t.id}
                    onClick={() => setGeneratorType(t.id as GeneratorType)}
                    className={`rounded-xl border p-3 cursor-pointer transition ${
                      generatorType === t.id
                        ? "border-indigo-500 bg-indigo-950/40"
                        : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-zinc-100">{t.name}</span>
                      {generatorType === t.id && (
                        <CheckCircle className="h-3.5 w-3.5 text-indigo-400" />
                      )}
                    </div>
                    <p className="mt-1 text-[11px] text-zinc-400 leading-tight">{t.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Character & Voice */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-zinc-300">Nhân vật KOC</label>
                <select
                  value={characterName}
                  onChange={(e) => setCharacterName(e.target.value)}
                  className="mt-1.5 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="LyLy">LyLy (KOC Nữ Thời trang / Mỹ phẩm)</option>
                  <option value="Neau">Neau (KOC Nam Công nghệ / Đời sống)</option>
                  <option value="Sóc Nhỏ (Bi)">Sóc Nhỏ (Bi) - 100cm Hoạt hình</option>
                  <option value="Koala">Bạn Koala - 150cm Hoạt hình</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-zinc-300">Giọng đọc (Voiceover)</label>
                <select
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                  className="mt-1.5 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="soc-nho">soc-nho (OmniVoice SOTA Sóc Nhỏ)</option>
                  <option value="vi-VN-HoaiMyNeural">vi-VN-HoaiMyNeural (Nữ miền Bắc, truyền cảm)</option>
                  <option value="vi-VN-NamMinhNeural">vi-VN-NamMinhNeural (Nam miền Bắc, ấm áp)</option>
                </select>
              </div>
            </div>

            {/* Platforms */}
            <div>
              <label className="text-xs font-semibold text-zinc-300">Nền tảng xuất bản</label>
              <div className="mt-2 flex flex-wrap gap-2">
                {(["tiktok", "reels", "shorts", "facebook", "youtube"] as Platform[]).map((p) => {
                  const active = platforms.includes(p);
                  return (
                    <button
                      key={p}
                      type="button"
                      onClick={() => togglePlatform(p)}
                      className={`rounded-lg px-3 py-1.5 text-xs font-semibold capitalize transition ${
                        active
                          ? "bg-indigo-600 text-white"
                          : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
                      }`}
                    >
                      {p}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="mt-6 flex items-center justify-between pt-3 border-t border-zinc-800">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="rounded-lg border border-zinc-700 px-3 py-2 text-xs font-medium text-zinc-300 hover:bg-zinc-800"
              >
                Quay lại
              </button>
              <button
                type="button"
                disabled={isGenerating}
                onClick={handleGenerate}
                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {isGenerating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Wand2 className="h-4 w-4" />
                )}
                Tạo kịch bản AI
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Script Review & Submit Render */}
        {step === 3 && generatedScript && (
          <div className="mt-4 flex-1 overflow-y-auto pr-1 space-y-4">
            {/* Compliance Banner */}
            <div
              className={`rounded-xl p-3 border ${
                generatedScript.compliance_warnings.length === 0
                  ? "border-emerald-950/60 bg-emerald-950/20 text-emerald-300"
                  : "border-amber-950/60 bg-amber-950/20 text-amber-300"
              }`}
            >
              <div className="flex items-center gap-2 font-bold text-xs">
                {generatedScript.compliance_warnings.length === 0 ? (
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                )}
                Bộ lọc tuân thủ chính sách thương mại:{" "}
                {generatedScript.compliance_warnings.length === 0 ? "ĐẠT CHUẨN" : "CÓ CẢNH BÁO"}
              </div>
              {generatedScript.compliance_warnings.length > 0 && (
                <ul className="mt-2 list-disc list-inside text-[11px] space-y-0.5 text-zinc-300">
                  {generatedScript.compliance_warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              )}
            </div>

            {/* Script Details */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">
                    Mã kịch bản & Template
                  </span>
                  <h3 className="text-sm font-bold text-zinc-100">
                    {generatedScript.script_id} • {generatedScript.template_id}
                  </h3>
                </div>
                <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                  Ý tưởng: {generatedScript.content_idea_id}
                </span>
              </div>

              {/* Lines / Beats */}
              <div>
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                  Các phân cảnh kịch bản
                </span>
                <div className="mt-2 space-y-2">
                  {generatedScript.lines.map((line, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-2.5 text-xs"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-semibold text-indigo-300 uppercase">
                          {line.role}
                        </span>
                        {line.visual_hint && (
                          <span className="text-zinc-500 italic">{line.visual_hint}</span>
                        )}
                      </div>
                      <p className="mt-1 text-zinc-200 leading-relaxed font-medium">"{line.text}"</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Full Text */}
              <div className="rounded-lg bg-zinc-950 p-3 border border-zinc-800/80">
                <span className="text-[10px] font-bold text-zinc-400 uppercase">
                  Toàn văn lời thoại (Voiceover)
                </span>
                <p className="mt-1 text-xs text-zinc-300 whitespace-pre-line leading-relaxed">
                  {generatedScript.full_text}
                </p>
              </div>
            </div>

            {/* Render Job Success Card */}
            {renderJobId && (
              <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/30 p-4 text-center">
                <CheckCircle className="mx-auto h-8 w-8 text-emerald-400" />
                <h4 className="mt-2 text-sm font-bold text-emerald-300">
                  Đã gửi lệnh render thành công!
                </h4>
                <p className="mt-1 text-xs text-zinc-300">
                  Mã tiến trình render: <span className="font-mono text-emerald-400">{renderJobId}</span>
                </p>
                <p className="mt-0.5 text-[11px] text-zinc-400">
                  HeyGen HyperFrames đang tự động biên tập video HTML5/GSAP 9:16 chuẩn TikTok Safe Zone.
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="mt-6 flex items-center justify-between pt-3 border-t border-zinc-800">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="rounded-lg border border-zinc-700 px-3 py-2 text-xs font-medium text-zinc-300 hover:bg-zinc-800"
              >
                Cấu hình lại
              </button>

              {!renderJobId ? (
                <button
                  type="button"
                  disabled={isSubmittingRender}
                  onClick={handleSubmitRender}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-emerald-500/25 hover:from-emerald-600 hover:to-teal-700 disabled:opacity-50"
                >
                  {isSubmittingRender ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                  Gửi Render (HeyGen HyperFrames)
                </button>
              ) : (
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-lg bg-zinc-800 px-4 py-2 text-xs font-bold text-zinc-200 hover:bg-zinc-700"
                >
                  Đóng
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
