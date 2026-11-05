import path from "path";
import fs from "fs";

/** Gốc repo (dashboard chạy tại tool/dashboard). */
export const REPO_ROOT = path.resolve(process.cwd(), "../..");
export const DATA_DIR = path.join(REPO_ROOT, "data");
export const SHARED_DIR = path.join(DATA_DIR, "shared");
export const INBOX_DIR = path.join(SHARED_DIR, "toolbox", "inbox");

/** true nếu `p` nằm trong `root` (chống ../). */
export function isInside(root: string, p: string): boolean {
  const rel = path.relative(path.resolve(root), path.resolve(p));
  return !!rel && !rel.startsWith("..") && !path.isAbsolute(rel);
}

export function safeName(name: string): string {
  const base = path.basename(name).replace(/[^\w.\-]+/g, "_").replace(/^\.+/, "");
  return base.slice(0, 80) || "file";
}

function readWorkspace(): any {
  try {
    return JSON.parse(fs.readFileSync(path.join(DATA_DIR, "workspace.json"), "utf-8"));
  } catch {
    return {};
  }
}

export function readProjects(): { id: string; name: string }[] {
  return (readWorkspace().projects || []).map((p: any) => ({ id: String(p.id), name: String(p.name || p.id) }));
}

export function readActiveProject(): string | null {
  return readWorkspace().active_project || null;
}

export function readCharacters(projectId: string): { id: string; name: string }[] {
  const dir = path.join(DATA_DIR, "projects", projectId, "characters");
  if (!fs.existsSync(dir)) return [];
  const names: Record<string, string> = {};
  try {
    const j = JSON.parse(fs.readFileSync(path.join(dir, "studio_characters.json"), "utf-8"));
    for (const c of j.characters || []) names[c.id] = c.name;
  } catch {}
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && /^[a-z0-9_-]+$/i.test(d.name) && !d.name.startsWith("_"))
    .map((d) => ({ id: d.name, name: names[d.name] || d.name }));
}
