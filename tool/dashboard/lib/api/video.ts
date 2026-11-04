import { CORE_URL } from "@/lib/repositories/core";

export type Platform = "tiktok" | "reels" | "shorts" | "youtube" | "facebook" | "douyin";

export interface SafeZone {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

export interface PlatformPreset {
  id: Platform;
  name: string;
  width: number;
  height: number;
  aspect_ratio: string;
  fps: number;
  max_duration_sec?: number | null;
  safe_zone: SafeZone;
  loudness_lufs: number;
  audio_bitrate: string;
  video_bitrate: string;
  codec: string;
  notes: string;
}

export interface Slot {
  key: string;
  type: string;
  label?: string;
  description?: string;
  required: boolean;
  default?: any;
  max_chars?: number;
  min_chars?: number;
  min?: number;
  max?: number;
}

export interface TemplateMeta {
  id: string;
  name: string;
  version: number | string;
  category: "sales" | "review" | "reup" | "animation" | "education" | "affiliate" | "story";
  platforms: Platform[];
  default_platform: Platform;
  duration: {
    mode: string;
    min: number;
    max: number;
    fixed_duration?: number | null;
  };
  slots: Slot[];
  voice: {
    required: boolean;
    default_voice_id: string;
  };
  captions: {
    style: string;
    position: string;
  };
  bgm: {
    mood: string;
    duck_db: number;
  };
  scenes: Array<{
    role: string;
    dur?: string;
    summary?: string;
  }>;
  responsive: Record<string, string>;
}

export interface RenderRequest {
  project_id: string;
  template_id: string;
  platforms: Platform[];
  data: Record<string, any>;
  voice?: {
    voice_id?: string;
    script?: string;
    audio_path?: string;
  } | null;
  source_ref?: string | null;
  output_name: string;
}

export interface RenderJob {
  job_id: string;
  project_id: string;
  status: "queued" | "rendering" | "done" | "failed";
  outputs: Partial<Record<Platform, string>>;
  error?: string | null;
  created_at: string;
}

export interface DialogueLine {
  speaker: string;
  line: string;
}

export interface ScenePlan {
  scene_id: string;
  scene_number: number;
  characters: string[];
  location: string;
  action: string;
  dialogue: DialogueLine[];
  camera: string;
  duration_est: number;
  prompt: string;
  scale_lock_prompt: string;
}

export interface EpisodePlan {
  episode_id: string;
  title: string;
  scenes: ScenePlan[];
  estimated_cost_usd: number;
  total_duration_est: number;
}

export interface EpisodeBuildStatus {
  episode_id: string;
  title: string;
  main_job_id: string;
  shorts_job_ids: string[];
  status: "planned" | "queued" | "rendering" | "done" | "failed";
  scenes_count?: number;
  estimated_cost_usd?: number;
  main_job?: RenderJob | null;
  shorts_jobs?: RenderJob[];
  chapters?: string;
  youtube_meta?: {
    title: string;
    description: string;
    tags: string[];
    category_id: string;
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${CORE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`API error (${res.status}): ${errText}`);
  }
  return res.json() as Promise<T>;
}

export const videoApi = {
  fetchPlatforms: async (): Promise<PlatformPreset[]> => {
    return request<PlatformPreset[]>("/video/platforms");
  },

  fetchTemplates: async (category?: string, platform?: string): Promise<TemplateMeta[]> => {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (platform) params.append("platform", platform);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return request<TemplateMeta[]>(`/video/templates${qs}`);
  },

  fetchTemplate: async (tid: string): Promise<TemplateMeta> => {
    return request<TemplateMeta>(`/video/templates/${tid}`);
  },

  validateTemplateData: async (tid: string, data: Record<string, any>): Promise<{ valid: boolean; errors: string[] }> => {
    return request<{ valid: boolean; errors: string[] }>(`/video/templates/${tid}/validate`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  previewTemplate: async (tid: string): Promise<{ status: string; preview_mp4: string; preview_jpg: string }> => {
    return request<{ status: string; preview_mp4: string; preview_jpg: string }>(`/video/templates/${tid}/preview`, {
      method: "POST",
    });
  },

  submitRender: async (pid: string, req: RenderRequest): Promise<RenderJob> => {
    return request<RenderJob>(`/projects/${pid}/video/render`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  fetchRenderJob: async (pid: string, jobId: string): Promise<RenderJob> => {
    return request<RenderJob>(`/projects/${pid}/video/render/${jobId}`);
  },

  listRenderJobs: async (pid: string, status?: string): Promise<RenderJob[]> => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return request<RenderJob[]>(`/projects/${pid}/video/renders${qs}`);
  },

  cancelRenderJob: async (pid: string, jobId: string): Promise<RenderJob> => {
    return request<RenderJob>(`/projects/${pid}/video/render/${jobId}/cancel`, {
      method: "POST",
    });
  },

  getRenderEventsUrl: (pid: string, jobId: string): string => {
    return `${CORE_URL}/projects/${pid}/video/render/${jobId}/events`;
  },

  planEpisode: async (pid: string, eid: string, script: string, title?: string): Promise<EpisodePlan> => {
    return request<EpisodePlan>(`/projects/${pid}/video/episodes/${eid}/plan`, {
      method: "POST",
      body: JSON.stringify({ script, title }),
    });
  },

  buildEpisode: async (pid: string, eid: string, useMock: boolean = false): Promise<EpisodeBuildStatus> => {
    return request<EpisodeBuildStatus>(`/projects/${pid}/video/episodes/${eid}/build`, {
      method: "POST",
      body: JSON.stringify({ use_mock: useMock }),
    });
  },

  fetchEpisodeStatus: async (pid: string, eid: string): Promise<EpisodeBuildStatus> => {
    return request<EpisodeBuildStatus>(`/projects/${pid}/video/episodes/${eid}/status`);
  },
};
