import { CORE_URL } from "./core";

/** Upload/xóa ảnh DNA và mẫu giọng qua Core (chỉ có khi Core đang chạy). */

function toBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",")[1] ?? "");
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
