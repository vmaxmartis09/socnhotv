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

export interface VoiceVaultItem {
  id: string;
  name: string;
  dialect: string;
  engine: string;
  durationSec?: number;
  transcript?: string;
  createdAt?: string;
  hasSample?: boolean;
  sampleUrl?: string | null;
  usedBy?: Array<{ projectId: string; characterId: string; name: string }>;
}

export async function fetchVoiceVault(): Promise<VoiceVaultItem[]> {
  try {
    const res = await fetch(`${CORE_URL}/voices`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export interface VoiceCloneParams {
  voiceId: string;
  projectId?: string;
  characterId?: string;
  file?: File;
  sourceFile?: string;
  dialect?: "north" | "south" | "central";
  consentConfirmed: boolean;
}

export interface VoiceCloneResult {
  status: string;
  voiceId: string;
  name: string;
  dialect: string;
  durationSec?: number;
  transcript?: string;
  sampleUrl: string;
  vaultPath: string;
  mastering: string;
}

export async function cloneCharacterVoice(
  projectIdOrParams: string | VoiceCloneParams,
  paramsMaybe?: VoiceCloneParams
): Promise<VoiceCloneResult> {
  const isFirstParamString = typeof projectIdOrParams === "string";
  const projectId = isFirstParamString ? projectIdOrParams : projectIdOrParams.projectId;
  const params = isFirstParamString ? (paramsMaybe as VoiceCloneParams) : projectIdOrParams;

  let audioData: string | undefined = undefined;
  let filename: string | undefined = undefined;
  if (params.file) {
    audioData = await toBase64(params.file);
    filename = params.file.name;
  }

  const endpoint = projectId
    ? `${CORE_URL}/projects/${projectId}/voice/clone`
    : `${CORE_URL}/voices/clone`;

  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      voiceId: params.voiceId,
      projectId: projectId || params.projectId,
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
