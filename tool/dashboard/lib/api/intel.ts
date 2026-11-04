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

// B4: Channel Intelligence & Ideas
export interface ChannelMeta {
  id: string;
  url: string;
  name: string;
  uploader_id?: string;
  avatar?: string;
  video_count: number;
  top_ingested_sources?: string[];
  updated_at?: string;
}

export interface ChannelPillar {
  name: string;
  video_count: number;
  video_pct: number;
  total_views: number;
  view_pct: number;
  avg_views: number;
}

export interface ChannelAnalysisResponse {
  blueprint: any;
  channel_meta: ChannelMeta;
  stats: {
    total_videos: number;
    median_views: number;
    avg_views: number;
    avg_duration_s: number;
    shorts_ratio: number;
    longs_ratio: number;
    upload_cadence: string;
    avg_title_length: number;
    emoji_ratio: number;
    number_ratio: number;
  };
  pillars: ChannelPillar[];
  schedule_heatmap: number[][]; // 7 days x 24 hours
  top_outliers: Array<{
    id: string;
    title: string;
    view_count: number;
    outlier_score: number;
    thumbnail: string;
    url: string;
  }>;
  title_patterns: string[];
}

export interface ChannelStrategy {
  project_id: string;
  reference_channels: string[];
  differentiation: string;
  our_pillars: Array<{
    id: string;
    name: string;
    description: string;
    target_ratio: number;
  }>;
  title_rules: string[];
  thumbnail_rules: string[];
  publishing_schedule: Record<string, string>;
  format_mix: Record<string, number>;
  kpi_30d: Record<string, any>;
  guardrails: string[];
}

export type IdeaStatus = "new" | "scripted" | "rendered" | "scheduled" | "dropped";

export interface ContentIdea {
  id: string;
  project_id: string;
  title: string;
  platform_targets: string[];
  template_id?: string;
  blueprint_ref?: string;
  priority: number;
  status: IdeaStatus;
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

  // B4: Channel Intelligence
  ingestChannel: async (
    pid: string,
    url: string,
    maxVideos: number = 50
  ): Promise<ChannelAnalysisResponse> => {
    return request<ChannelAnalysisResponse>(`/projects/${pid}/intel/channels`, {
      method: "POST",
      body: JSON.stringify({ url, max_videos: maxVideos }),
    });
  },

  listChannels: async (pid: string): Promise<ChannelMeta[]> => {
    return request<ChannelMeta[]>(`/projects/${pid}/intel/channels`);
  },

  getChannelAnalysis: async (
    pid: string,
    channelId: string
  ): Promise<ChannelAnalysisResponse> => {
    return request<ChannelAnalysisResponse>(`/projects/${pid}/intel/channels/${channelId}`);
  },

  // Strategy
  generateStrategy: async (
    pid: string,
    channelIds: string[]
  ): Promise<ChannelStrategy> => {
    return request<ChannelStrategy>(`/projects/${pid}/intel/strategy`, {
      method: "POST",
      body: JSON.stringify({ channel_ids: channelIds }),
    });
  },

  getStrategy: async (pid: string): Promise<ChannelStrategy> => {
    return request<ChannelStrategy>(`/projects/${pid}/intel/strategy`);
  },

  // Content Ideas & Kanban
  generateIdeas: async (pid: string, count: number = 30): Promise<ContentIdea[]> => {
    return request<ContentIdea[]>(`/projects/${pid}/intel/ideas/generate?count=${count}`, {
      method: "POST",
    });
  },

  listIdeas: async (pid: string, status?: string): Promise<ContentIdea[]> => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return request<ContentIdea[]>(`/projects/${pid}/intel/ideas${qs}`);
  },

  updateIdea: async (
    pid: string,
    ideaId: string,
    data: { status?: string; priority?: number }
  ): Promise<ContentIdea> => {
    return request<ContentIdea>(`/projects/${pid}/intel/ideas/${ideaId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  promoteIdea: async (
    pid: string,
    ideaId: string,
    data?: { product_id?: string; character_name?: string; voice_id?: string }
  ): Promise<any> => {
    return request<any>(`/projects/${pid}/intel/ideas/${ideaId}/promote`, {
      method: "POST",
      body: JSON.stringify(data || {}),
    });
  },

  scheduleIdea: async (pid: string, ideaId: string): Promise<any> => {
    return request<any>(`/projects/${pid}/intel/ideas/${ideaId}/schedule`, {
      method: "POST",
    });
  },
};
