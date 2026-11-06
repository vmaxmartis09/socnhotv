#!/usr/bin/env node
// vm — chạy Dashboard (3000) + Core API (8000) cùng lúc. Mac/Win/Linux, chạy từ bất kỳ đâu trong repo.
// Dùng: vm run [--keep] | vm stop | vm api | vm web | vm install
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync, chmodSync } from "node:fs";
import path from "node:path";
import os from "node:os";
import net from "node:net";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const WIN = process.platform === "win32";
const DASH = path.join(ROOT, "tool", "dashboard");
const cmd = process.argv[2] || "run";

function venvBin(name) {
  const p = WIN ? path.join(ROOT, ".venv", "Scripts", name + ".exe") : path.join(ROOT, ".venv", "bin", name);
  return existsSync(p) ? p : null;
}

function start(label, color, command, args, opts) {
  const child = spawn(command, args, { ...opts, shell: WIN && !command.endsWith(".exe"), stdio: ["inherit", "pipe", "pipe"] });
  const tag = `\x1b[${color}m[${label}]\x1b[0m `;
  const pipe = (s, out) => s.on("data", (d) => out.write(String(d).replace(/^(?=.)/gm, tag)));
  pipe(child.stdout, process.stdout);
  pipe(child.stderr, process.stderr);
  child.on("error", (e) => console.error(tag + "lỗi khởi chạy: " + e.message));
  return child;
}

function api() {
  const uv = venvBin("uvicorn");
  const env = { ...process.env, PYTHONPATH: path.join(ROOT, "tool", "src") + (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : "") };
  if (uv) return start("api:8000", "36", uv, ["socnhotv.core.api.app:app", "--port", "8000", "--reload", "--reload-dir", path.join(ROOT, "tool", "src")], { cwd: ROOT, env });
  console.error("Không thấy .venv (uvicorn). Chạy setup trước (mac: uv sync / win: setup.ps1). Thử dùng uvicorn trong PATH...");
  return start("api:8000", "36", "uvicorn", ["socnhotv.core.api.app:app", "--port", "8000"], { cwd: ROOT, env });
}

function web() {
  if (!existsSync(path.join(DASH, "node_modules"))) {
    console.error("Thiếu node_modules — chạy: cd tool/dashboard && npm install");
  }
  const next = path.join(DASH, "node_modules", ".bin", WIN ? "next.cmd" : "next");
  return start("web:3000", "32", existsSync(next) ? next : "npx", existsSync(next) ? ["dev", "-p", "3000"] : ["next", "dev", "-p", "3000"], { cwd: DASH, env: process.env });
}

const inUse = (port) => new Promise((res) => {
  const c = net.connect({ port, host: "127.0.0.1" });
  c.on("connect", () => { c.destroy(); res(true); });
  c.on("error", () => res(false));
});

function stopPorts() {
  for (const port of [3000, 8000]) {
    try {
      if (WIN) {
        const out = execSync(`netstat -ano | findstr :${port} | findstr LISTENING`, { encoding: "utf8" });
        for (const pid of new Set(out.split("\n").map((l) => l.trim().split(/\s+/).pop()).filter(Boolean))) execSync(`taskkill /PID ${pid} /T /F`);
      } else {
        const pids = execSync(`lsof -ti tcp:${port} -sTCP:LISTEN`, { encoding: "utf8" }).trim().split("\n").filter(Boolean);
        pids.forEach((p) => process.kill(Number(p), "SIGTERM"));
      }
      console.log(`Đã dừng tiến trình ở cổng ${port}`);
    } catch { console.log(`Cổng ${port} không có tiến trình`); }
  }
}

function install() {
  const target = path.join(ROOT, "scripts", "vm.mjs");
  if (WIN) {
    const dir = path.join(process.env.USERPROFILE || os.homedir(), ".socnhotv", "bin");
    mkdirSync(dir, { recursive: true });
    writeFileSync(path.join(dir, "vm.cmd"), `@echo off\r\nnode "${target}" %*\r\n`);
    const ps = `$d='${dir}';$p=[Environment]::GetEnvironmentVariable('Path','User');if(($p -split ';') -notcontains $d){[Environment]::SetEnvironmentVariable('Path',($p.TrimEnd(';')+';'+$d),'User')}`;
    spawn("powershell", ["-NoProfile", "-Command", ps], { stdio: "inherit" }).on("exit", () =>
      console.log(`Đã cài vm vào ${dir}. Mở terminal MỚI rồi gõ: vm run`));
  } else {
    const dir = path.join(os.homedir(), ".local", "bin");
    mkdirSync(dir, { recursive: true });
    const f = path.join(dir, "vm");
    writeFileSync(f, `#!/bin/sh\nexec node "${target}" "$@"\n`);
    chmodSync(f, 0o755);
    console.log(`Đã cài vm vào ${f}.`);
    if (!(process.env.PATH || "").split(":").includes(dir))
      console.log(`Thêm vào ~/.zshrc:  export PATH="$HOME/.local/bin:$PATH"  (rồi mở terminal mới)`);
    else console.log("Gõ: vm run");
  }
}

if (cmd === "install") install();
else if (cmd === "api") api();
else if (cmd === "web") web();
else if (cmd === "stop") stopPorts();
else if (cmd === "run" || cmd === "dev" || cmd === "up") {
  const keep = process.argv.includes("--keep");
  const kids = [];
  if (!keep) {
    // Mỗi lần run = bản mới: dừng bản cũ ở 3000/8000 rồi khởi động lại
    if ((await inUse(8000)) || (await inUse(3000))) { stopPorts(); await new Promise((r) => setTimeout(r, 1500)); }
  }
  // Bước đã có thì bỏ qua: chỉ cài deps khi thiếu
  if (!existsSync(path.join(DASH, "node_modules"))) {
    console.log("[setup] cài npm dependencies...");
    execSync("npm install", { cwd: DASH, stdio: "inherit" });
  }
  if (await inUse(8000)) console.log("[api:8000] đang chạy (--keep) — dùng lại"); else kids.push(api());
  if (await inUse(3000)) console.log("[web:3000] đang chạy (--keep) — dùng lại"); else kids.push(web());
  if (!kids.length) process.exit(0);
  const stop = () => kids.forEach((k) => { try { WIN ? spawn("taskkill", ["/pid", String(k.pid), "/T", "/F"]) : k.kill("SIGTERM"); } catch {} });
  process.on("SIGINT", () => { stop(); process.exit(0); });
  process.on("SIGTERM", () => { stop(); process.exit(0); });
  kids.forEach((k) => k.on("exit", (c) => { if (c) { console.error(`tiến trình thoát mã ${c}, dừng tất cả`); stop(); process.exit(c); } }));
  console.log("Dashboard http://localhost:3000 · Core API http://127.0.0.1:8000 (Ctrl+C để dừng)");
} else {
  console.log("Dùng: vm run [--keep] | vm stop | vm api | vm web | vm install");
}
