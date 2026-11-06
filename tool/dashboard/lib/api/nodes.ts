import { CORE_URL } from "../repositories/core";

export interface UploadResult {
  id: string;
  kind: "image" | "video";
  url: string;
  uri: string;
  name: string;
}

export interface LibraryItem {
  id?: string;
  name: string;
  url: string;
  uri?: string;
}

export interface ParsedScene {
  sceneNumber: number;
  title: string;
  imagePrompt: string;
  videoPrompt: string;
  dialogue: string;
  durationSec: number;
}

/** Tải tệp lên thư viện dự án (POST /projects/{pid}/library/upload) */
export async function uploadNodeFile(
  projectId: string,
  file: File
): Promise<UploadResult> {
  const data: string = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });

  const res = await fetch(`${CORE_URL}/data/projects/${projectId}/library/upload`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: file.name, data }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Upload failed (${res.status}): ${errText}`);
  }

  const result = (await res.json()) as UploadResult;
  if (!result.uri && result.url) {
    // Nếu API chỉ trả url, trích xuất uri tương đối
    const match = result.url.match(/assets\/[^?#]+/);
    result.uri = match ? match[0] : `assets/${file.name}`;
  }
  return result;
}

/** Lấy danh sách ảnh từ Thư viện media của dự án */
export async function fetchProjectLibraryImages(
  projectId: string
): Promise<LibraryItem[]> {
  try {
    const res = await fetch(`${CORE_URL}/data/projects/${projectId}/library`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    const imgs = Array.isArray(data.images) ? data.images : [];
    return imgs.map((img: any) => ({
      name: img.name || "image.png",
      url: img.url.startsWith("http") ? img.url : `${CORE_URL}${img.url}`,
      uri: img.uri || (img.url ? img.url.replace(/^.*\/files\//, "") : ""),
    }));
  } catch {
    return [];
  }
}

export interface ScriptEpisode {
  id: string;
  title: string;
}

export interface ScriptFacet {
  id: string;
  label: string;
  type: "text" | "scenes" | "script";
}

export interface ScriptShot {
  id: string;
  scene: number;
  sceneTitle: string;
  speaker: string;
  dialogue: string;
  /** Nhân vật của dự án ghép được với người nói (null = chưa ghép được) */
  characterId?: string | null;
}

/** Các tập có kịch bản trong dự án (để chọn làm nội dung đầu vào) */
export async function fetchProjectScriptEpisodes(projectId: string): Promise<ScriptEpisode[]> {
  try {
    const res = await fetch(`${CORE_URL}/data/projects/${projectId}/library`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    const withScript = new Set<string>((data.scripts || []).map((s: any) => s.episodeId));
    return (data.episodes || [])
      .filter((e: any) => withScript.has(e.id))
      .map((e: any) => ({ id: e.id, title: e.title || e.id }));
  } catch {
    return [];
  }
}

/** Kịch bản tập có cấu trúc: danh mục facet + danh sách shot (GET .../script-data/{episode}) */
export async function fetchScriptData(
  projectId: string,
  episodeId: string
): Promise<{ facets: ScriptFacet[]; shotFacets: { id: string; label: string }[]; shots: ScriptShot[] } | null> {
  try {
    const res = await fetch(`${CORE_URL}/data/projects/${projectId}/script-data/${encodeURIComponent(episodeId)}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export type LibraryKind = "image" | "video" | "audio";

/** Kho tư liệu dự án theo loại (ảnh / video / âm thanh) để chọn làm đầu vào node */
export async function fetchProjectLibrary(projectId: string, kind: LibraryKind): Promise<LibraryItem[]> {
  try {
    const res = await fetch(`${CORE_URL}/data/projects/${projectId}/library`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    const key = kind === "image" ? "images" : kind === "video" ? "videos" : "audios";
    const items = Array.isArray(data[key]) ? data[key] : [];
    return items.map((it: any) => ({
      name: it.name || `${kind}`,
      url: it.url.startsWith("http") ? it.url : `${CORE_URL}${it.url}`,
      uri: it.uri || (it.url ? it.url.replace(/^.*\/files\//, "") : ""),
    }));
  } catch {
    return [];
  }
}

/** Chuyển đổi URI tương đối dự án (ví dụ assets/abc.png) thành URL đầy đủ */
export function resolveNodeFileUrl(
  projectId: string,
  uriOrUrl?: string
): string | undefined {
  if (!uriOrUrl) return undefined;
  if (
    uriOrUrl.startsWith("http://") ||
    uriOrUrl.startsWith("https://") ||
    uriOrUrl.startsWith("blob:") ||
    uriOrUrl.startsWith("data:")
  ) {
    return uriOrUrl;
  }
  if (uriOrUrl.startsWith("/projects/") || uriOrUrl.startsWith("/data/")) {
    return `${CORE_URL}${uriOrUrl}`;
  }
  return `${CORE_URL}/projects/${projectId}/files/${uriOrUrl.replace(/^\/+/, "")}`;
}

/** Phân tích kịch bản tất định chạy ngay phía client (tương đương logic backend script_parser.py) */
export function parseScriptClient(
  rawScript: string,
  targetSceneCount = 6,
  targetDurationSec = 45
): ParsedScene[] {
  if (!rawScript || !rawScript.trim()) return [];

  const text = rawScript.trim();
  const headerRegex =
    /^(?:[#*>\s]*)(?:(?:Cảnh|Phân cảnh|Hồi|Scene|Part|Segment)\s+(\d+|[IVXLCDM]+)[\s:.-]*(.*))$/gim;

  const chunks: { headerTitle?: string; content: string }[] = [];
  const matches = [...text.matchAll(headerRegex)];

  if (matches.length >= 2 || (matches.length === 1 && matches[0].index === 0)) {
    for (let i = 0; i < matches.length; i++) {
      const match = matches[i];
      const start = match.index!;
      const end = i + 1 < matches.length ? matches[i + 1].index! : text.length;
      const rawChunk = text.slice(start, end).trim();
      const firstLineBreak = rawChunk.indexOf("\n");
      let headerLine = rawChunk;
      let content = "";
      if (firstLineBreak !== -1) {
        headerLine = rawChunk.slice(0, firstLineBreak).trim();
        content = rawChunk.slice(firstLineBreak + 1).trim();
      }
      const headerTitle = headerLine.replace(/^[#*>\s]+/, "").trim();
      chunks.push({ headerTitle, content });
    }
  } else if (/^[ \t]*[-=_*~]{3,}[ \t]*$/m.test(text)) {
    const rawParts = text.split(/^[ \t]*[-=_*~]{3,}[ \t]*$/m);
    for (const p of rawParts) {
      if (p.trim()) chunks.push({ content: p.trim() });
    }
  } else if (text.includes("\n\n")) {
    const rawParts = text.split(/\n\s*\n+/);
    for (const p of rawParts) {
      if (p.trim()) chunks.push({ content: p.trim() });
    }
  } else {
    // Kịch bản 1 đoạn dài không có ngắt đoạn kép -> tách theo câu
    const sentences = text
      .split(/(?<=[.!?…])\s+(?=[A-Z\u00C0-\u1EF90-9])/g)
      .map((s) => s.trim())
      .filter(Boolean);
    const target = Math.max(1, Math.min(targetSceneCount, sentences.length));
    if (target > 1 && sentences.length >= target) {
      const chunkSize = sentences.length / target;
      for (let idx = 0; idx < target; idx++) {
        const sIdx = Math.floor(idx * chunkSize);
        const eIdx =
          idx < target - 1
            ? Math.floor((idx + 1) * chunkSize)
            : sentences.length;
        const grouped = sentences.slice(sIdx, eIdx).join(" ").trim();
        if (grouped) chunks.push({ content: grouped });
      }
    } else {
      chunks.push({ content: text });
    }
  }

  if (chunks.length === 0) {
    chunks.push({ content: text });
  }

  const directivePrefixes = new Set([
    "mô tả",
    "hinh anh",
    "hình ảnh",
    "visual",
    "image",
    "image prompt",
    "prompt",
    "video",
    "camera",
    "action",
    "hành động",
    "góc quay",
    "bối cảnh",
    "note",
    "ghi chú",
  ]);

  const dialoguePattern =
    /^(?:[#*>\s-]*)(?:\[([^\]]+)\]|([A-Za-z0-9_\u00C0-\u1EF9\s]+?))\s*[:：]\s*(.+)$/;

  const scenes: ParsedScene[] = [];

  chunks.forEach((chunk, idx) => {
    const sceneNum = idx + 1;
    const lines = chunk.content
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    const dialogues: string[] = [];
    const visualParts: string[] = [];
    const cameraParts: string[] = [];

    for (const line of lines) {
      if (
        (line.startsWith("(") && line.endsWith(")")) ||
        (line.startsWith("[") && line.endsWith("]"))
      ) {
        const inner = line.slice(1, -1).trim();
        const low = inner.toLowerCase();
        if (
          ["camera", "goc quay", "góc quay", "zoom", "pan", "dolly"].some((k) =>
            low.startsWith(k)
          )
        ) {
          cameraParts.push(inner);
        } else {
          visualParts.push(inner);
        }
        continue;
      }

      const m = line.match(dialoguePattern);
      if (m) {
        const speaker = (m[1] || m[2] || "").trim();
        const content = m[3].trim();
        const lowSpeaker = speaker.toLowerCase();

        if (directivePrefixes.has(lowSpeaker)) {
          if (["camera", "góc quay", "video"].includes(lowSpeaker)) {
            cameraParts.push(content);
          } else {
            visualParts.push(content);
          }
        } else {
          dialogues.push(`${speaker}: ${content}`);
        }
      } else {
        visualParts.push(line);
      }
    }

    const title = chunk.headerTitle || `Cảnh ${sceneNum}`;
    const fullDialogue = dialogues.join("\n");
    let imagePrompt = visualParts.join(". ");
    if (!imagePrompt) {
      imagePrompt = fullDialogue
        ? `Cảnh hoạt hình 3D: ${dialogues[0]}`
        : `Phân cảnh hoạt hình 3D cho ${title}`;
    }
    const videoPrompt =
      cameraParts.join(". ") ||
      `Camera góc trung chuyển động mượt mà, diễn hoạt sinh động theo nội dung ${title}`;

    const words = fullDialogue ? fullDialogue.split(/\s+/).length : 0;
    const durationSec =
      words > 0
        ? Math.max(3.5, Math.min(Number((words / 3.0 + 1.2).toFixed(1)), 15.0))
        : 6.0;

    scenes.push({
      sceneNumber: sceneNum,
      title,
      imagePrompt,
      videoPrompt,
      dialogue: fullDialogue,
      durationSec,
    });
  });

  if (scenes.length > 0 && targetDurationSec > 0) {
    const total = scenes.reduce((sum, s) => sum + s.durationSec, 0);
    if (total > 0 && Math.abs(total - targetDurationSec) > 10) {
      const scale = targetDurationSec / total;
      scenes.forEach((s) => {
        s.durationSec = Math.max(
          3.0,
          Math.min(Number((s.durationSec * scale).toFixed(1)), 20.0)
        );
      });
    }
  }

  return scenes;
}
