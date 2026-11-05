import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardDir = path.resolve(__dirname, "../dashboard");

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    if (e.name.startsWith(".") || e.name === "node_modules" || e.name === ".next" || e.name === ".next-build" || e.name === "dist") continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full);
    else if (/\.(tsx|jsx)$/.test(e.name)) {
      const raw = fs.readFileSync(full, "utf8");
      const isCrlf = raw.includes("\r\n");
      let c = raw.replace(/\r\n/g, "\n");
      if (c.includes('"use client";')) {
        const trimmed = c.trimStart();
        if (!trimmed.startsWith('"use client";')) {
          c = c.replace(/[\n]*"use client";[\n]*/g, "\n");
          c = '"use client";\n\n' + c.trimStart();
          const finalOutput = isCrlf ? c.replace(/\n/g, "\r\n") : c;
          fs.writeFileSync(full, finalOutput, "utf8");
          console.log("Fixed use client in:", path.relative(dashboardDir, full));
        }
      }
    }
  }
}

walk(dashboardDir);
console.log("Done checking use client directives.");
