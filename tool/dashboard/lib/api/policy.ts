import { CORE_URL } from "@/lib/repositories/core";

export interface PolicyRule {
  id: string;
  category: string;
  label: string;
  severity: "block" | "warn";
  enabled: boolean;
  terms: string[];
  note?: string;
  /** Nguồn quy tắc: pack-<gói> hoặc upload-<tệp>; trống = tự tạo */
  source?: string;
}

export interface PolicyReference {
  url: string;
  title?: string;
  kind?: string;
  fetchedAt?: string;
  excerpt?: string;
}

export interface PolicyPack {
  id: string;
  name: string;
  platform: string;
  sourceUrl: string;
  description: string;
  ruleCount: number;
}

export interface ContentPolicy {
  name: string;
  mode: "strict" | "standard";
  scopes: { dialogue: boolean; caption: boolean; script: boolean; prompt: boolean };
  allowlist: string[];
  references?: PolicyReference[];
  rules: PolicyRule[];
}

export interface PolicyViolation {
  source: string;
  ruleId: string;
  category: string;
  label: string;
  severity: "block" | "warn";
  term: string;
  snippet: string;
  note?: string;
}

export interface PolicyReport {
  passed: boolean;
  violations: PolicyViolation[];
  blockCount: number;
  warnCount: number;
  checkedSources: string[];
}

const base = (projectId: string) => `${CORE_URL}/data/projects/${encodeURIComponent(projectId)}/policy`;

export async function fetchProjectPolicy(projectId: string): Promise<ContentPolicy | null> {
  try {
    const res = await fetch(base(projectId), { cache: "no-store" });
    return res.ok ? ((await res.json()) as ContentPolicy) : null;
  } catch {
    return null;
  }
}

export async function saveProjectPolicy(projectId: string, policy: ContentPolicy): Promise<ContentPolicy> {
  const res = await fetch(base(projectId), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policy),
  });
  if (!res.ok) throw new Error((await res.text()) || "Lưu chính sách thất bại");
  return (await res.json()) as ContentPolicy;
}

export async function checkPolicyText(projectId: string, texts: Record<string, string>): Promise<PolicyReport | null> {
  try {
    const res = await fetch(`${base(projectId)}/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts }),
    });
    return res.ok ? ((await res.json()) as PolicyReport) : null;
  } catch {
    return null;
  }
}

export async function fetchPolicyPacks(): Promise<PolicyPack[]> {
  try {
    const res = await fetch(`${CORE_URL}/data/policy-packs`, { cache: "no-store" });
    return res.ok ? ((await res.json()) as PolicyPack[]) : [];
  } catch {
    return [];
  }
}

async function post<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!res.ok) {
    let msg = "";
    try {
      msg = (await res.json()).detail || "";
    } catch {
      msg = await res.text();
    }
    throw new Error(msg || `Lỗi ${res.status}`);
  }
  return (await res.json()) as T;
}

export const importPolicyPack = (projectId: string, packId: string) =>
  post<ContentPolicy>(`${base(projectId)}/import-pack`, { packId });

export const importPolicyFile = (projectId: string, name: string, text: string) =>
  post<{ policy: ContentPolicy; added: number; terms: number }>(`${base(projectId)}/import`, { name, text });

export const fetchPolicyUrl = (projectId: string, url: string) =>
  post<{ policy: ContentPolicy; page: { title: string; chars: number; text: string } }>(`${base(projectId)}/fetch-url`, { url });
