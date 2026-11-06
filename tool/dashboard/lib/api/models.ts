/**
 * API client tra cứu sổ Model và Nhà cung cấp AI (Session G / Hợp đồng C2)
 */

import { CORE_URL } from "@/lib/repositories/core";

export interface ModelPricing {
  cost_per_generation?: number;
  cost_per_second?: number;
  cost_per_minute?: number;
  cost_per_1k_tokens?: number;
  cost_per_1k_chars?: number;
}

export interface ModelItem {
  key: string;
  display_name: string;
  displayName?: string;
  provider: string;
  model_id: string;
  modelId?: string;
  kind: string;
  tier: "free" | "freemium" | "paid" | "local" | string;
  supports_reference?: boolean;
  supportsReference?: boolean;
  max_references?: number;
  maxReferences?: number;
  quota_note?: string;
  quotaNote?: string;
  speed_note?: string;
  speedNote?: string;
  durations_sec?: number[];
  durationsSec?: number[];
  capabilities?: Record<string, any>;
  pricing?: ModelPricing;
  available: boolean;
}

export interface ProviderItem {
  id: string;
  label: string;
  tier: string;
  needs_key: boolean;
  configured: boolean;
  quota_note?: string;
  capabilities?: Record<string, any>;
  models?: string[];
}

export async function fetchModels(kind?: string, provider?: string): Promise<ModelItem[]> {
  try {
    const params = new URLSearchParams();
    if (kind) params.set("kind", kind);
    if (provider) params.set("provider", provider);
    const qs = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${CORE_URL}/models${qs}`, { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    console.warn("fetchModels failed:", err);
    return [];
  }
}

export async function fetchProviders(): Promise<ProviderItem[]> {
  try {
    const res = await fetch(`${CORE_URL}/providers`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.providers || [];
  } catch (err) {
    console.warn("fetchProviders failed:", err);
    return [];
  }
}

export function formatTierBadge(tier: string, pricing?: ModelPricing): {
  labelVi: string;
  labelEn: string;
  colorClass: string;
} {
  switch (tier) {
    case "free":
      return {
        labelVi: "Miễn phí",
        labelEn: "Free",
        colorClass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
      };
    case "local":
      return {
        labelVi: "Trên máy ($0)",
        labelEn: "Local ($0)",
        colorClass: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/20",
      };
    case "freemium":
      return {
        labelVi: "Free hằng ngày",
        labelEn: "Daily Free",
        colorClass: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
      };
    case "paid":
    default: {
      let costStr = "";
      if (pricing?.cost_per_generation) costStr = ` ~$${pricing.cost_per_generation}/ảnh`;
      else if (pricing?.cost_per_second) costStr = ` ~$${pricing.cost_per_second}/s`;
      return {
        labelVi: `Trả phí${costStr}`,
        labelEn: `Paid${costStr}`,
        colorClass: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
      };
    }
  }
}
