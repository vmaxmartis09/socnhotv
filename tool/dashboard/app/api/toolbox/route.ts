import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import os from "os";
import { execFile } from "child_process";
import { promisify } from "util";
import { readProjects, readCharacters, readActiveProject } from "@/lib/toolbox-paths";

const execFileAsync = promisify(execFile);

// Path resolution to repo root
const REPO_ROOT = path.resolve(process.cwd(), "../..");
const TOOLS_DIR = path.join(REPO_ROOT, "tool", "toolbox", "tools");
const TEMPLATE_DIR = path.join(REPO_ROOT, "tool", "toolbox", "_template");
const SHARED_DIR = path.join(REPO_ROOT, "data", "shared");

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action") || "list";

  try {
    if (action === "list") {
      const tools: any[] = [];
      if (fs.existsSync(TOOLS_DIR)) {
        const dirs = fs.readdirSync(TOOLS_DIR);
        for (const d of dirs) {
          const mPath = path.join(TOOLS_DIR, d, "tool.json");
          if (fs.existsSync(mPath)) {
            try {
              const manifest = JSON.parse(fs.readFileSync(mPath, "utf-8"));
              tools.push(manifest);
            } catch {}
          }
        }
      }
      return NextResponse.json({ ok: true, tools });
    }

    if (action === "vaults") {
      // 1. Cutouts
      const cutoutsIndex = path.join(SHARED_DIR, "assets", "cutouts", "index.jsonl");
      const cutouts: any[] = [];
      if (fs.existsSync(cutoutsIndex)) {
        const lines = fs.readFileSync(cutoutsIndex, "utf-8").split("\n");
        for (const l of lines) {
          if (l.trim()) {
            try { cutouts.push(JSON.parse(l.trim())); } catch {}
          }
        }
      }

      // 2. Audio Timings
      const audioIndex = path.join(SHARED_DIR, "assets", "audio", "index.jsonl");
      const audios: any[] = [];
      if (fs.existsSync(audioIndex)) {
        const lines = fs.readFileSync(audioIndex, "utf-8").split("\n");
        for (const l of lines) {
          if (l.trim()) {
            try { audios.push(JSON.parse(l.trim())); } catch {}
          }
        }
      }

      // 3. Voices
      const voiceIndex = path.join(SHARED_DIR, "voice_vault", "index.jsonl");
      const voices: any[] = [];
      if (fs.existsSync(voiceIndex)) {
        const lines = fs.readFileSync(voiceIndex, "utf-8").split("\n");
        for (const l of lines) {
          if (l.trim()) {
            try { voices.push(JSON.parse(l.trim())); } catch {}
          }
        }
      }

      // index.jsonl là append-only nên có thể trùng id: giữ bản mới nhất, mới lên trước
      const dedupe = (rows: any[]) => {
        const m = new Map<string, any>();
        for (const r of rows) m.set(String(r.id), r);
        return Array.from(m.values()).reverse();
      };
      return NextResponse.json({
        ok: true,
        vaults: { cutouts: dedupe(cutouts), audios: dedupe(audios), voices: dedupe(voices) },
      });
    }

    if (action === "targets") {
      const projects = readProjects();
      const characters: Record<string, { id: string; name: string }[]> = {};
      for (const p of projects) characters[p.id] = readCharacters(p.id);
      return NextResponse.json({ ok: true, projects, characters, active: readActiveProject(), sharedDir: SHARED_DIR });
    }

    return NextResponse.json({ ok: false, error: "Unknown action" }, { status: 400 });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  let tmpIn = "";
  let tmpOut = "";
  try {
    const { toolId, inData } = await request.json();

    // toolId đi vào dòng lệnh → chỉ nhận dạng slug và phải là tool đang có trên đĩa
    if (typeof toolId !== "string" || !/^[a-z0-9][a-z0-9-]*$/.test(toolId) || !fs.existsSync(path.join(TOOLS_DIR, toolId, "tool.json"))) {
      return NextResponse.json({ ok: false, error: "toolId không hợp lệ" }, { status: 400 });
    }

    // Đầu vào phải nằm trong data/ (không cho đọc file tùy ý trên máy)
    const dataRoot = path.join(REPO_ROOT, "data");
    const inputs: string[] = [];
    for (const raw of (inData?.inputs as string[]) || []) {
      const abs = path.resolve(REPO_ROOT, String(raw));
      const rel = path.relative(dataRoot, abs);
      if (rel.startsWith("..") || path.isAbsolute(rel) || !fs.existsSync(abs)) {
        return NextResponse.json({ ok: false, error: `Đầu vào không hợp lệ hoặc không tồn tại: ${raw}` }, { status: 400 });
      }
      inputs.push(abs);
    }

    const stamp = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const dir = path.join(os.tmpdir(), "socnhotv-toolbox");
    fs.mkdirSync(dir, { recursive: true });
    tmpIn = path.join(dir, `${toolId}_${stamp}_in.json`);
    tmpOut = path.join(dir, `${toolId}_${stamp}_out.json`);
    fs.writeFileSync(tmpIn, JSON.stringify({ ...(inData || {}), inputs }, null, 2), "utf-8");

    const cliPath = path.join(REPO_ROOT, "tool", "toolbox", "toolbox_cli", "cli.py");
    let stderr = "";
    try {
      const r = await execFileAsync("py", ["-3.11", cliPath, "run", toolId, "--in", tmpIn, "--out", tmpOut], {
        cwd: REPO_ROOT,
        timeout: 15 * 60 * 1000,
        maxBuffer: 16 * 1024 * 1024,
      });
      stderr = r.stderr;
    } catch (e: any) {
      stderr = e.stderr || e.message; // tool thoát mã khác 0 vẫn có thể đã ghi out.json chứa lỗi
    }

    if (fs.existsSync(tmpOut)) {
      const outData = JSON.parse(fs.readFileSync(tmpOut, "utf-8"));
      return NextResponse.json({ ok: outData.ok !== false, result: outData, error: outData.error?.message });
    }
    return NextResponse.json({ ok: false, error: stderr || "Tool không tạo ra kết quả" }, { status: 500 });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  } finally {
    for (const f of [tmpIn, tmpOut]) if (f) try { fs.unlinkSync(f); } catch {}
  }
}
