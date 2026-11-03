// Chụp dữ liệu từ Core đang chạy (mặc định http://127.0.0.1:8000) thành bản tĩnh chỉ-đọc cho bản deploy Vercel.
// Chạy: node scripts/build-snapshot.mjs   (cần Core đang chạy). Kết quả: public/snapshot/** (JSON + tệp tham chiếu).
import fs from "node:fs";
import path from "node:path";

const CORE = (process.env.CORE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const OUT = path.resolve("public/snapshot");
const MAX_FILE = Number(process.env.SNAPSHOT_MAX_FILE_MB || 6) * 1024 * 1024;
const skipped = [];
let files = 0, bytes = 0;

const get = async (p) => {
  const r = await fetch(CORE + p);
  return r.ok ? r : null;
};
const save = (rel, data) => {
  const f = path.join(OUT, rel);
  fs.mkdirSync(path.dirname(f), { recursive: true });
  fs.writeFileSync(f, data);
};
const urls = new Set();
const scan = (v) => {
  if (typeof v === "string") { if (/^\/(data\/)?projects\/[^/]+\/files\/.+/.test(v)) urls.add(v); }
  else if (Array.isArray(v)) v.forEach(scan);
  else if (v && typeof v === "object") Object.values(v).forEach(scan);
};

fs.rmSync(OUT, { recursive: true, force: true });
const json = async (p) => {
  const r = await get(p);
  if (!r) { console.warn("bỏ qua", p); return null; }
  const d = await r.json();
  save(p.replace(/^\//, "") + ".json", JSON.stringify(d));
  scan(d);
  return d;
};

for (const p of ["/health", "/models", "/providers", "/node-types", "/projects", "/settings/api-keys", "/data/projects"]) await json(p);
const list = (await (await get("/data/projects")).json());
const ids = (Array.isArray(list) ? list : list.projects ?? []).map((x) => x.id);
for (const id of ids) {
  for (const p of [`/data/projects/${id}`, `/data/projects/${id}/characters`, `/data/projects/${id}/library`, `/data/projects/${id}/channels`,
    `/projects/${id}/graph`, `/projects/${id}/publishing`, `/projects/${id}/spend`, `/projects/${id}/characters`]) await json(p);
}

// Tệp tham chiếu (ảnh, âm thanh, video nhỏ). Tệp quá lớn bỏ qua và ghi vào báo cáo.
for (const u of urls) {
  const clean = decodeURI(u);
  const r = await get(u.startsWith("/data/") ? u : "/data" + u);
  if (!r) { skipped.push([u, "không tải được"]); continue; }
  const buf = Buffer.from(await r.arrayBuffer());
  if (buf.length > MAX_FILE) { skipped.push([u, `${(buf.length / 1048576).toFixed(1)} MB`]); continue; }
  save(path.join("files", clean.replace(/^\/(data\/)?/, "")), buf);
  files++; bytes += buf.length;
}
save("_report.json", JSON.stringify({ projects: ids, files, mb: +(bytes / 1048576).toFixed(1), skipped }, null, 1));
console.log(`projects=${ids.length} files=${files} ${(bytes / 1048576).toFixed(1)}MB skipped=${skipped.length}`);
skipped.forEach(([u, why]) => console.log("  bỏ:", u, why));
