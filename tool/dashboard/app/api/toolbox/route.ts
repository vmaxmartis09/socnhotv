import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

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

      return NextResponse.json({ ok: true, vaults: { cutouts, audios, voices } });
    }

    return NextResponse.json({ ok: false, error: "Unknown action" }, { status: 400 });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { toolId, inData } = body;

    if (!toolId) {
      return NextResponse.json({ ok: false, error: "Missing toolId" }, { status: 400 });
    }

    const tmpIn = path.join(REPO_ROOT, "tool", "toolbox", "tools", toolId, "tests", "ui_in.json");
    const tmpOut = path.join(REPO_ROOT, "tool", "toolbox", "tools", toolId, "tests", "ui_out.json");

    fs.mkdirSync(path.dirname(tmpIn), { recursive: true });
    fs.writeFileSync(tmpIn, JSON.stringify(inData || {}, null, 2), "utf-8");

    const cliPath = path.join(REPO_ROOT, "tool", "toolbox", "toolbox_cli", "cli.py");
    const cmd = `py -3.11 "${cliPath}" run ${toolId} --in "${tmpIn}" --out "${tmpOut}"`;

    const { stdout, stderr } = await execAsync(cmd, { cwd: REPO_ROOT });

    if (fs.existsSync(tmpOut)) {
      const outData = JSON.parse(fs.readFileSync(tmpOut, "utf-8"));
      return NextResponse.json({ ok: true, result: outData });
    }

    return NextResponse.json({ ok: false, error: stderr || "Execution produced no output" }, { status: 500 });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}
