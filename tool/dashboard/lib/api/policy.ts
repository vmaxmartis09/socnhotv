import { CORE_URL } from "@/lib/repositories/core";

export interface PolicyRule {
  id: string;
  category: string;
  label: string;
  severity: "block" | "warn";
  enabled: boolean;
  terms: string[];
  note?: string;
}

export interface ContentPolicy {
  name: string;
  mode: "strict" | "standard";
  scopes: { dialogue: boolean; caption: boolean; script: boolean; prompt: boolean };
  allowlist: string[];
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
