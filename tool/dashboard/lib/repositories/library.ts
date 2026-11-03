import { CORE_URL } from "./core";

export interface LibraryItem {
  id: string;
  name: string;
  url: string;
  source: "artifact" | "episode";
  episodeId?: string;
  aspect?: string | null;
  durationSec?: number | null;
  provider?: string | null;
  model?: string | null;
  createdAt: string;
}

export interface LibraryScript {
  id: string;
  name: string;
  episodeId: string;
  url: string;
  preview: string;
  updatedAt: string;
}

export interface LibraryEpisode {
  id: string;
  title: string;
  videoCount: number;
  imageCount: number;
  scriptCount: number;
  updatedAt: string;
}

export interface ProjectLibrary {
  videos: LibraryItem[];
  images: LibraryItem[];
  scripts: LibraryScript[];
  episodes: LibraryEpisode[];
}

const abs = <T extends { url: string }>(x: T): T => ({ ...x, url: CORE_URL + x.url });

export async function fetchProjectLibrary(projectId: string): Promise<ProjectLibrary> {
  const res = await fetch(`${CORE_URL}/data/projects/${projectId}/library`);
  if (!res.ok) throw new Error(`Core ${res.status}`);
  const d = (await res.json()) as ProjectLibrary;
  return {
    videos: d.videos.map(abs),
    images: d.images.map(abs),
    scripts: d.scripts.map(abs),
    episodes: d.episodes,
  };
}

export async function fetchText(url: string): Promise<string> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

export async function createProject(input: { id: string; name: string; description?: string }): Promise<void> {
  const res = await fetch(`${CORE_URL}/data/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error(`Core ${res.status}: ${await res.text()}`);
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${CORE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    throw new Error(`Core không phản hồi: ${e instanceof Error ? e.message : String(e)}`);
  }
  if (!res.ok) throw new Error(`Core ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const createEpisodeFolder = (projectId: string, title: string) =>
  post<{ id: string; title: string }>(`/data/projects/${projectId}/episodes`, { title });

export const saveScript = (projectId: string, title: string, content: string, episodeId?: string) =>
  post<{ episodeId: string; name: string }>(`/data/projects/${projectId}/scripts`, { title, content, episodeId });

export const generateScriptDraft = (projectId: string, prompt: string, mockMode: boolean) =>
  post<{ mode: "gemini" | "mock"; markdown: string }>(`/data/projects/${projectId}/ai/script`, { prompt, mockMode });

export async function uploadLibraryFile(projectId: string, file: File): Promise<void> {
  const data: string = await new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",")[1] ?? "");
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
  await post(`/data/projects/${projectId}/library/upload`, { name: file.name, data });
}
