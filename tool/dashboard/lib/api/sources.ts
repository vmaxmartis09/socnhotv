import { CORE_URL } from "@/lib/repositories/core";

export type PlatformType = "douyin" | "tiktok" | "youtube" | "bilibili" | "facebook" | "instagram" | "local";
export type RightsType = "owned" | "licensed" | "permission" | "reference_only";
export type SourceStatus = "queued" | "downloading" | "ready" | "failed";

export interface SourceStats {
  views: number;
  likes: number;
  comments: number;
  shares: number;
}

export interface SourceFiles {
  video?: string | null;
  audio?: string | null;
  thumb?: string | null;
  subtitle_orig?: string | null;
}

export interface SceneCut {
  scene_idx: number;
  start_s: number;
  end_s: number;
  thumb: string;
}

export interface SourceItem {
  id: string;
  project_id: string;
  platform: PlatformType;
  url: string;
  author: string;
  author_url: string;
  title: string;
  description: string;
  duration_s: number;
  published_at: string;
  stats: SourceStats;
  hashtags: string[];
  music: string;
  rights: RightsType;
  rights_note: string;
  files: SourceFiles;
  status: SourceStatus;
  error?: string | null;
  created_at: string;
}

export function getSourceFileUrl(projectId: string, sourceId: string, fileName: string): string {
  return `${CORE_URL}/projects/${projectId}/sources/${sourceId}/file/${fileName}`;
}

export async function listSources(
  projectId: string,
  filter?: { platform?: string; rights?: string; q?: string }
): Promise<SourceItem[]> {
  const params = new URLSearchParams();
  if (filter?.platform) params.set("platform", filter.platform);
  if (filter?.rights) params.set("rights", filter.rights);
  if (filter?.q) params.set("q", filter.q);

  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources?${params.toString()}`);
  if (!res.ok) throw new Error(`Lỗi tải danh sách nguồn: ${res.statusText}`);
  return res.json();
}

export async function getSource(projectId: string, sourceId: string): Promise<SourceItem> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources/${sourceId}`);
  if (!res.ok) throw new Error(`Lỗi lấy thông tin nguồn: ${res.statusText}`);
  return res.json();
}

export async function ingestUrls(
  projectId: string,
  urls: string[],
  rights: RightsType = "reference_only",
  rights_note: string = ""
): Promise<{ type: string; job_ids: string[] }> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ urls, rights, rights_note }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Lỗi nạp liên kết");
  }
  return res.json();
}

export async function ingestFile(
  projectId: string,
  file: File,
  rights: RightsType = "owned",
  rights_note: string = ""
): Promise<{ type: string; source: SourceItem }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("rights", rights);
  formData.append("rights_note", rights_note);

  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Lỗi tải lên tập tin");
  }
  return res.json();
}

export async function updateRights(
  projectId: string,
  sourceId: string,
  rights: RightsType,
  rights_note?: string,
  confirm_rights: boolean = false
): Promise<SourceItem> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources/${sourceId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rights, rights_note, confirm_rights }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Lỗi cập nhật bản quyền");
  }
  return res.json();
}

export async function deleteSource(projectId: string, sourceId: string): Promise<void> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources/${sourceId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Lỗi chuyển nguồn vào thùng rác");
}

export async function detectScenes(projectId: string, sourceId: string): Promise<SceneCut[]> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources/${sourceId}/scenes`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Lỗi phân tách cảnh");
  return res.json();
}

export async function localizeSource(
  projectId: string,
  sourceId: string,
  payload: {
    mode: "R" | "L";
    style: "faithful" | "hook_boost" | "character";
    voice_id: string;
    platforms: string[];
    template_id?: string;
    auto_draft?: boolean;
  }
): Promise<any> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources/${sourceId}/localize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Lỗi bản địa hoá");
  }
  return res.json();
}

export async function getTranscript(
  projectId: string,
  sourceId: string,
  lang: "orig" | "vi" = "vi"
): Promise<any[]> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources/${sourceId}/transcript?lang=${lang}`);
  if (!res.ok) throw new Error("Chưa có transcript");
  return res.json();
}

export async function updateTranscript(
  projectId: string,
  sourceId: string,
  segments: any[],
  lang: "orig" | "vi" = "vi"
): Promise<void> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources/${sourceId}/transcript?lang=${lang}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(segments),
  });
  if (!res.ok) throw new Error("Lỗi cập nhật transcript");
}

export async function getScript(
  projectId: string,
  sourceId: string,
  style: string = "faithful"
): Promise<any[]> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources/${sourceId}/script?style=${style}`);
  if (!res.ok) throw new Error("Chưa có kịch bản");
  return res.json();
}

export async function updateScript(
  projectId: string,
  sourceId: string,
  lines: any[],
  style: string = "faithful"
): Promise<void> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/sources/${sourceId}/script?style=${style}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(lines),
  });
  if (!res.ok) throw new Error("Lỗi cập nhật kịch bản");
}
