import { CORE_URL } from "./core";

/** Upload/xóa ảnh DNA và mẫu giọng qua Core (chỉ có khi Core đang chạy). */

export function toBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",")[1] ?? "");
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
}

export function toDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result));
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
}

async function call(path: string, init: RequestInit): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${CORE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    throw new Error(`Core không phản hồi: ${e instanceof Error ? e.message : String(e)}`);
  }
  if (!res.ok) throw new Error(`Core ${res.status}: ${await res.text()}`);
}

export async function uploadCharacterImage(projectId: string, characterId: string, file: File) {
  await call(`/data/projects/${projectId}/characters/${characterId}/images`, {
    method: "POST",
    body: JSON.stringify({ name: file.name, data: await toBase64(file) }),
  });
}

export async function deleteCharacterImage(projectId: string, characterId: string, filename: string) {
  await call(
    `/data/projects/${projectId}/characters/${characterId}/images/${encodeURIComponent(filename)}`,
    { method: "DELETE" }
  );
}

export async function uploadVoiceSample(voiceId: string, file: File) {
  await call(`/data/voices/${voiceId}/samples`, {
    method: "POST",
    body: JSON.stringify({ name: file.name, data: await toBase64(file) }),
  });
}

export async function cloneCharacterVoice(
  projectId: string,
  params: {
    voiceId: string;
    characterId?: string;
    file?: File;
    sourceFile?: string;
    dialect?: "north" | "south" | "central";
    consentConfirmed: boolean;
  }
) {
  let audioData: string | undefined = undefined;
  let filename: string | undefined = undefined;
  if (params.file) {
    audioData = await toBase64(params.file);
    filename = params.file.name;
  }
  const res = await fetch(`${CORE_URL}/projects/${projectId}/voice/clone`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      voiceId: params.voiceId,
      characterId: params.characterId,
      audioData,
      filename,
      sourceFile: params.sourceFile,
      dialect: params.dialect || "south",
      consentConfirmed: params.consentConfirmed,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Không thể nhân bản giọng nói");
  }
  return res.json();
}

export interface CharacterDraft {
  name: string;
  role: "main" | "supporting";
  heightCm: number;
  description: string;
  personality: string;
  promptLock: string;
  catchphrases?: string[];
  habits?: string[];
}

/** Nhờ AI (Gemini khi có khóa, ngược lại bản nháp theo quy tắc) dựng hồ sơ nhân vật từ mô tả. */
export async function generateCharacterDraft(
  projectId: string,
  prompt: string,
  mockMode: boolean
): Promise<{ draft: CharacterDraft; mode: "gemini" | "mock" }> {
  let res: Response;
  try {
    res = await fetch(`${CORE_URL}/data/projects/${projectId}/ai/character`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, mockMode }),
    });
  } catch (e) {
    throw new Error(`Core không phản hồi: ${e instanceof Error ? e.message : String(e)}`);
  }
  if (!res.ok) throw new Error(`Core ${res.status}: ${await res.text()}`);
  return res.json();
}
