import { CORE_URL } from "@/lib/repositories/core";
import type { Platform } from "@/lib/api/video";

export interface Product {
  id: string;
  name: string;
  brand?: string;
  category?: string;
  price?: number;
  sale_price?: number;
  currency?: string;
  affiliate_links?: {
    tiktok_shop?: string;
    shopee?: string;
    lazada?: string;
    other?: string;
    [k: string]: string | undefined;
  };
  usp?: string[];
  pain_points?: string[];
  specs?: Record<string, any>;
  images?: string[];
  videos?: string[];
  target_audience?: string;
  compliance_notes?: string;
  created_at?: string;
  updated_at?: string;
}

export type BeatRole =
  | "hook"
  | "problem"
  | "agitate"
  | "reveal"
  | "demo"
  | "proof"
  | "compare"
  | "offer"
  | "urgency"
  | "cta";

export interface BlueprintBeat {
  t_start: number;
  t_end: number;
  role: BeatRole | string;
  summary: string;
  visual?: string;
  on_screen_text?: string;
}

export interface VideoBlueprint {
  id: string;
  source_ref: string;
  duration_s: number;
  platform: string;
  hook: string;
  beats: BlueprintBeat[];
  cta: string;
  pacing_cuts_per_10s: number;
  suggested_template_id?: string;
  created_at?: string;
}

export interface PatternSummary {
  sample_count: number;
  median_hook_duration_sec: number;
  common_role_sequences: string[][];
  common_hook_formulas: string[];
  common_cta_formulas: string[];
}

export type GeneratorType = "koc_review" | "tiktok_sales" | "affiliate_compare";

export interface GenerateScriptRequest {
  product_id: string;
  blueprint_id?: string;
  generator_type?: GeneratorType;
  character_name?: string;
  voice_id?: string;
  platforms?: Platform[];
}

export interface ScriptLine {
  role: string;
  text: string;
  visual_hint?: string;
  duration_s?: number;
}

export interface GeneratedScriptResponse {
  script_id: string;
  content_idea_id: string;
  template_id: string;
  lines: ScriptLine[];
  full_text: string;
  compliance_warnings: string[];
  render_request: any;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${CORE_URL}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      // fallback
    }
    throw new Error(errorDetail || `HTTP error ${res.status}`);
  }

  return res.json();
}

export const intelApi = {
  // Products
  fetchProducts: async (pid: string): Promise<Product[]> => {
    return request<Product[]>(`/projects/${pid}/products`);
  },

  getProduct: async (pid: string, id: string): Promise<Product> => {
    return request<Product>(`/projects/${pid}/products/${id}`);
  },

  createProduct: async (pid: string, product: Product): Promise<Product> => {
    return request<Product>(`/projects/${pid}/products`, {
      method: "POST",
      body: JSON.stringify(product),
    });
  },

  updateProduct: async (pid: string, id: string, product: Product): Promise<Product> => {
    return request<Product>(`/projects/${pid}/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(product),
    });
  },

  deleteProduct: async (pid: string, id: string): Promise<{ status: string; message: string }> => {
    return request<{ status: string; message: string }>(`/projects/${pid}/products/${id}`, {
      method: "DELETE",
    });
  },

  importProductFromUrl: async (pid: string, url: string): Promise<Partial<Product>> => {
    return request<Partial<Product>>(`/projects/${pid}/products/import-url`, {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  },

  // Video Blueprints
  analyzeVideo: async (pid: string, sourceId: string): Promise<VideoBlueprint> => {
    return request<VideoBlueprint>(`/projects/${pid}/intel/analyze/${sourceId}`, {
      method: "POST",
    });
  },

  fetchBlueprints: async (pid: string): Promise<VideoBlueprint[]> => {
    return request<VideoBlueprint[]>(`/projects/${pid}/intel/blueprints`);
  },

  fetchBlueprint: async (pid: string, id: string): Promise<VideoBlueprint> => {
    return request<VideoBlueprint>(`/projects/${pid}/intel/blueprints/${id}`);
  },

  fetchPatterns: async (pid: string, niche?: string): Promise<PatternSummary> => {
    const qs = niche ? `?niche=${encodeURIComponent(niche)}` : "";
    return request<PatternSummary>(`/projects/${pid}/intel/patterns${qs}`);
  },

  // Script Generator
  generateScript: async (
    pid: string,
    req: GenerateScriptRequest
  ): Promise<GeneratedScriptResponse> => {
    return request<GeneratedScriptResponse>(`/projects/${pid}/intel/generate-script`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },
};
