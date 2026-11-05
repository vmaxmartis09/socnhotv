import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "../dashboard");

function walk(dir) {
  let files = [];
  for (const f of fs.readdirSync(dir)) {
    const full = path.join(dir, f);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      if (f !== "node_modules" && f !== ".next" && f !== ".next-build") {
        files = files.concat(walk(full));
      }
    } else if (f.endsWith(".tsx") || f.endsWith(".ts")) {
      files.push(full);
    }
  }
  return files;
}

const files = walk(root);
const violations = [];

for (const file of files) {
  const rel = path.relative(root, file);
  if (rel.includes("__tests__") || rel.includes(".test.") || rel.includes(".spec.")) continue;

  const content = fs.readFileSync(file, "utf-8");

  // 1. Direct lucide-react import
  if (content.includes('from "lucide-react"') || content.includes("from 'lucide-react'")) {
    violations.push({ file: rel, line: 1, rule: "PROHIBIT_LUCIDE_REACT", message: "Do not import from 'lucide-react' directly; use '@/components/ui/icons'" });
  }

  // 2. Native window.confirm()
  if (/\bwindow\.confirm\s*\(/.test(content)) {
    violations.push({ file: rel, line: 1, rule: "NO_NATIVE_CONFIRM", message: "Do not use window.confirm(); use confirm() from '@/lib/confirm'" });
  }

  // 3. useStudioStore() without selector
  if (/useStudioStore\s*\(\s*\)/.test(content)) {
    violations.push({ file: rel, line: 1, rule: "STORE_SELECTOR_REQUIRED", message: "Do not call useStudioStore() without narrow selector" });
  }

  // 4. HTML <img> tags missing loading="lazy" (skip Img.tsx)
  if (!rel.includes("Img.tsx")) {
    const imgMatches = content.matchAll(/<img\b([^>]*?)>/gs);
    for (const match of imgMatches) {
      const attrs = match[1];
      if (!attrs.includes('loading="lazy"') && !attrs.includes("loading='lazy'")) {
        violations.push({
          file: rel,
          line: 1,
          rule: "IMG_LAZY_REQUIRED",
          message: `HTML <img> missing loading="lazy": <img ${attrs.slice(0, 30)}...>`,
        });
      }
    }
  }

  // 5. Native alert() calls (line by line to ignore comments)
  const lines = content.split("\n");
  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("//") || trimmed.startsWith("/*") || trimmed.startsWith("*")) return;
    if (/\balert\s*\([^)]*\)/.test(trimmed) && !trimmed.includes("showAlert") && !rel.includes("lib\\confirm.ts") && !rel.includes("lib/confirm.ts")) {
      violations.push({ file: rel, line: idx + 1, rule: "NO_NATIVE_ALERT", message: "Do not use native alert(); use showAlert() from '@/lib/confirm'" });
    }
  });
}

if (violations.length > 0) {
  console.error(`\x1b[31m[FAIL] Found ${violations.length} UI style violations:\x1b[0m`);
  for (const v of violations) {
    console.error(`  ${v.file}:${v.line} [${v.rule}]: ${v.message}`);
  }
  process.exit(1);
} else {
  console.log(`\x1b[32m[PASS] All ${files.length} UI files adhere strictly to ui-rules.md style constraints.\x1b[0m`);
  process.exit(0);
}
