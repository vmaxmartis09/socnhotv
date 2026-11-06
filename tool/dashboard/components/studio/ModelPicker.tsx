"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import {
  fetchModels,
  formatTierBadge,
  type ModelItem,
} from "@/lib/api/models";
import {
  ChevronDown,
  Check,
  Sparkles,
  AlertTriangle,
  ExternalLink,
  Plus,
  X,
  Zap,
  Info,
} from "@/components/ui/icons";

export interface ModelPickerProps {
  kind: "image" | "video" | "text";
  value?: string;
  onChange: (modelKey: string) => void;
  fallbackModels?: string[];
  onFallbackChange?: (models: string[]) => void;
  allowFallback?: boolean;
  disabled?: boolean;
  compact?: boolean;
  className?: string;
}

export function ModelPicker({
  kind,
  value,
  onChange,
  fallbackModels = [],
  onFallbackChange,
  allowFallback = true,
  disabled = false,
  compact = false,
  className,
}: ModelPickerProps) {
  const locale = useLocale();
  const [models, setModels] = useState<ModelItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [showFallbackSelector, setShowFallbackSelector] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Nạp danh sách model từ Core
  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchModels(kind).then((data) => {
      if (!active) return;
      setModels(data);
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [kind]);

  // Đóng dropdown khi click ngoài
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setShowFallbackSelector(false);
      }
    }
    if (isOpen || showFallbackSelector) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, showFallbackSelector]);

  // Model hiện tại được chọn
  const selectedModel = useMemo(() => {
    return models.find((m) => m.key === value || m.model_id === value);
  }, [models, value]);

  // Danh sách model free hoặc local hợp lệ để làm fallback (tuyệt đối không chứa model paid)
  const eligibleFallbackModels = useMemo(() => {
    return models.filter(
      (m) =>
        (m.tier === "free" || m.tier === "local") &&
        m.key !== value &&
        m.model_id !== value
    );
  }, [models, value]);

  const selectedTier = selectedModel ? formatTierBadge(selectedModel.tier, selectedModel.pricing) : null;

  return (
    <div className={cn("space-y-1.5 text-xs", className)} ref={containerRef}>
      {/* Nút chọn model chính */}
      <div className="relative">
        <button
          type="button"
          disabled={disabled || loading}
          onClick={() => setIsOpen(!isOpen)}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          className={cn(
            "w-full flex items-center justify-between gap-2 rounded-md border border-border bg-card px-2.5 py-1.5 text-left transition-colors hover:bg-muted/40",
            disabled && "opacity-50 cursor-not-allowed",
            compact ? "h-8 py-1" : "min-h-[36px]"
          )}
        >
          <div className="flex-1 min-w-0 flex items-center gap-1.5 flex-wrap">
            {loading ? (
              <span className="text-muted-foreground animate-pulse">Đang tải danh sách model...</span>
            ) : selectedModel ? (
              <>
                <span className="font-medium text-foreground truncate">
                  {selectedModel.display_name || selectedModel.key}
                </span>

                {/* Badge tier */}
                {selectedTier && (
                  <span
                    className={cn(
                      "text-[10px] font-semibold px-1.5 py-0.5 rounded border leading-none",
                      selectedTier.colorClass
                    )}
                  >
                    {locale === "vi" ? selectedTier.labelVi : selectedTier.labelEn}
                  </span>
                )}

                {/* Biểu tượng nhận ảnh DNA tham chiếu */}
                {selectedModel.supports_reference && (
                  <span
                    title="Hỗ trợ nạp ảnh mẫu DNA nhân vật"
                    className="inline-flex items-center gap-0.5 text-[10px] text-brand bg-brand/10 px-1 py-0.5 rounded font-mono"
                  >
                    <Sparkles className="h-2.5 w-2.5" />
                    Ref
                  </span>
                )}

                {/* Trạng thái key */}
                {!selectedModel.available && (
                  <span
                    title="Thiếu API key cho model này"
                    className="inline-flex items-center gap-0.5 text-[10px] text-amber-600 dark:text-amber-400 bg-amber-500/10 px-1 py-0.5 rounded"
                  >
                    <AlertTriangle className="h-2.5 w-2.5" />
                    Thiếu key
                  </span>
                )}
              </>
            ) : (
              <span className="text-muted-foreground font-mono truncate">
                {value || "Chọn model..."}
              </span>
            )}
          </div>

          <ChevronDown
            className={cn("h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform", isOpen && "rotate-180")}
          />
        </button>

        {/* Menu danh sách Model */}
        {isOpen && (
          <div className="absolute left-0 top-full mt-1 w-full min-w-[280px] max-w-sm rounded-lg border bg-popover/95 p-1.5 text-popover-foreground shadow-xl backdrop-blur-md z-50 animate-in fade-in-50 zoom-in-95 max-h-72 overflow-y-auto">
            <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center justify-between">
              <span>Model {kind.toUpperCase()}</span>
              <Link
                href={`/${locale}/settings`}
                className="text-brand hover:underline flex items-center gap-0.5 font-normal capitalize"
                onClick={() => setIsOpen(false)}
              >
                Cài đặt key <ExternalLink className="h-2.5 w-2.5" />
              </Link>
            </div>

            <div className="space-y-1 pt-1">
              {models.map((m) => {
                const isSelected = m.key === value || m.model_id === value;
                const tier = formatTierBadge(m.tier, m.pricing);
                return (
                  <div
                    key={m.key}
                    onClick={() => {
                      onChange(m.key);
                      setIsOpen(false);
                    }}
                    className={cn(
                      "flex flex-col gap-1 rounded-md p-2 cursor-pointer transition-colors hover:bg-muted/60",
                      isSelected && "bg-muted/80 font-medium",
                      !m.available && "opacity-75"
                    )}
                  >
                    <div className="flex items-center justify-between gap-1.5">
                      <div className="flex items-center gap-1.5 min-w-0">
                        {isSelected ? (
                          <Check className="h-3.5 w-3.5 text-brand shrink-0" />
                        ) : (
                          <span className="h-3.5 w-3.5 shrink-0" />
                        )}
                        <span className="font-semibold text-foreground text-xs truncate">
                          {m.display_name || m.key}
                        </span>
                      </div>

                      <div className="flex items-center gap-1 shrink-0">
                        {/* Tier */}
                        <span
                          className={cn(
                            "text-[10px] font-semibold px-1.5 py-0.5 rounded border leading-none",
                            tier.colorClass
                          )}
                        >
                          {locale === "vi" ? tier.labelVi : tier.labelEn}
                        </span>

                        {/* Ref */}
                        {m.supports_reference && (
                          <span
                            title="Hỗ trợ nạp ảnh mẫu DNA nhân vật"
                            className="inline-flex items-center text-[10px] text-brand bg-brand/10 px-1 py-0.5 rounded font-mono"
                          >
                            <Sparkles className="h-2.5 w-2.5" />
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Dòng phụ: Nhà cung cấp, ghi chú quota, key */}
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground pl-5 pr-1">
                      <span className="capitalize">{m.provider}</span>

                      {!m.available ? (
                        <Link
                          href={`/${locale}/settings`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setIsOpen(false);
                          }}
                          className="text-amber-600 dark:text-amber-400 hover:underline flex items-center gap-0.5 font-medium"
                        >
                          <AlertTriangle className="h-2.5 w-2.5" />
                          Chưa có key
                        </Link>
                      ) : m.quota_note ? (
                        <span className="truncate max-w-[140px] text-[10px]" title={m.quota_note}>
                          {m.quota_note}
                        </span>
                      ) : (
                        <span className="text-emerald-600 dark:text-emerald-400 text-[10px] flex items-center gap-0.5">
                          <Check className="h-2.5 w-2.5" /> Sẵn sàng
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Phần chuỗi dự phòng (Fallback models) - Chỉ áp dụng model Free / Local */}
      {allowFallback && onFallbackChange && (
        <div className="rounded-md border border-dashed border-border/80 bg-muted/20 p-2 space-y-1.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-muted-foreground flex items-center gap-1">
              <Zap className="h-3 w-3 text-amber-500" />
              <span>Dự phòng khi hết hạn mức (chỉ nguồn $0):</span>
            </span>

            <button
              type="button"
              disabled={disabled || eligibleFallbackModels.length === 0}
              onClick={() => setShowFallbackSelector(!showFallbackSelector)}
              className="text-brand hover:underline flex items-center gap-0.5 font-medium disabled:opacity-50"
            >
              <Plus className="h-3 w-3" />
              Thêm
            </button>
          </div>

          {/* Danh sách fallback đã chọn */}
          {fallbackModels.length > 0 ? (
            <div className="flex flex-wrap gap-1 pt-0.5">
              {fallbackModels.map((fbKey) => {
                const fbModel = models.find((m) => m.key === fbKey || m.model_id === fbKey);
                const name = fbModel?.display_name || fbKey;
                return (
                  <span
                    key={fbKey}
                    className="inline-flex items-center gap-1 rounded bg-background px-1.5 py-0.5 text-[10px] font-mono border border-border text-foreground shadow-xs"
                  >
                    <span>{name}</span>
                    <button
                      type="button"
                      onClick={() => {
                        onFallbackChange(fallbackModels.filter((k) => k !== fbKey));
                      }}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-2.5 w-2.5" />
                    </button>
                  </span>
                );
              })}
            </div>
          ) : (
            <p className="text-[10px] text-muted-foreground italic">
              Chưa chọn model dự phòng (tự động bỏ qua nếu lỗi hạn mức)
            </p>
          )}

          {/* Menu chọn thêm fallback */}
          {showFallbackSelector && (
            <div className="mt-1 rounded-md border bg-popover p-1.5 shadow-md space-y-1">
              <div className="text-[10px] font-semibold text-muted-foreground px-1">
                Chọn nguồn Free / Local dự phòng:
              </div>
              {eligibleFallbackModels.length === 0 ? (
                <div className="text-[10px] text-muted-foreground px-1 py-0.5">
                  Không còn model $0 khả dụng
                </div>
              ) : (
                eligibleFallbackModels.map((em) => {
                  const isChecked = fallbackModels.includes(em.key);
                  return (
                    <button
                      key={em.key}
                      type="button"
                      onClick={() => {
                        if (isChecked) {
                          onFallbackChange(fallbackModels.filter((k) => k !== em.key));
                        } else {
                          onFallbackChange([...fallbackModels, em.key]);
                        }
                      }}
                      className={cn(
                        "w-full flex items-center justify-between rounded px-2 py-1 text-left text-[11px] transition-colors hover:bg-muted",
                        isChecked && "bg-brand/10 text-brand font-medium"
                      )}
                    >
                      <span>{em.display_name || em.key}</span>
                      {isChecked ? (
                        <Check className="h-3 w-3 text-brand" />
                      ) : (
                        <span className="text-[10px] text-muted-foreground capitalize">{em.tier}</span>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
