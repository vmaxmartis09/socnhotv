import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardDir = path.resolve(__dirname, "../dashboard");

function walk(dir, fileList = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    if (e.name.startsWith(".") || e.name === "node_modules" || e.name === ".next" || e.name === ".next-build" || e.name === "dist") continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full, fileList);
    else if (/\.(tsx?|jsx?)$/.test(e.name)) fileList.push(full);
  }
  return fileList;
}

const files = walk(dashboardDir);

for (const f of files) {
  const content = fs.readFileSync(f, "utf8");
  const rel = path.relative(dashboardDir, f).replace(/\\/g, "/");
  
  // Find lines around useStudioStore()
  const lines = content.split(/\r?\n/);
  lines.forEach((line, i) => {
    if (/useStudioStore\(\s*\)/.test(line)) {
      // Print context lines
      const start = Math.max(0, i - 5);
      const end = Math.min(lines.length, i + 2);
      console.log(`\n=== ${rel}:${i + 1} ===`);
      console.log(lines.slice(start, end).join("\n"));
    }
  });
}
