#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardDir = path.resolve(__dirname, "../dashboard");
const iconsFile = path.resolve(dashboardDir, "components/ui/icons.ts");

if (!fs.existsSync(iconsFile)) {
  console.error(`Icons file not found: ${iconsFile}`);
  process.exit(1);
}

// 1. Get all exported names from icons.ts
const iconsContent = fs.readFileSync(iconsFile, "utf-8");
const exportedNames = new Set();

// Match: export const Foo = ...
for (const match of iconsContent.matchAll(/export\s+const\s+([A-Za-z0-9_]+)/g)) {
  exportedNames.add(match[1]);
}
// Match: export function Foo ...
for (const match of iconsContent.matchAll(/export\s+function\s+([A-Za-z0-9_]+)/g)) {
  exportedNames.add(match[1]);
}
// Match: export { Foo, Bar as Baz } ...
for (const match of iconsContent.matchAll(/export\s+\{([^}]+)\}/g)) {
  const block = match[1];
  for (const part of block.split(",")) {
    const trimmed = part.trim();
    if (!trimmed) continue;
    // Handle 'type Foo' or 'Foo as Bar'
    const clean = trimmed.replace(/^type\s+/, "");
    const parts = clean.split(/\s+as\s+/);
    const exportedAs = (parts[1] || parts[0]).trim();
    if (exportedAs) {
      exportedNames.add(exportedAs);
    }
  }
}

// 2. Scan all files in dashboard
function walkDir(dir, fileList = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.name.startsWith(".") || entry.name === "node_modules" || entry.name === ".next" || entry.name === ".next-build" || entry.name === "dist") {
      continue;
    }
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkDir(fullPath, fileList);
    } else if (/\.(ts|tsx|js|jsx)$/.test(entry.name)) {
      fileList.push(fullPath);
    }
  }
  return fileList;
}

const allFiles = walkDir(dashboardDir);
const missingImports = []; // { file, specifier, line }

// Regex to capture import { ... } from "...icons"
const importRegex = /import\s+(?:type\s+)?\{([^}]+)\}\s+from\s+["']([^"']*icons?)["']/g;

for (const file of allFiles) {
  if (file === iconsFile) continue;
  const content = fs.readFileSync(file, "utf-8");
  for (const match of content.matchAll(importRegex)) {
    const rawSpecifiers = match[1];
    const importSource = match[2];
    // check if it targets icons
    if (!importSource.endsWith("icons") && !importSource.endsWith("icons.ts")) {
      continue;
    }
    const specifiers = rawSpecifiers.split(",").map(s => s.trim()).filter(Boolean);
    for (const spec of specifiers) {
      const clean = spec.replace(/^type\s+/, "");
      // if 'Original as Local', original is what icons.ts must export
      const original = clean.split(/\s+as\s+/)[0].trim();
      if (!exportedNames.has(original)) {
        missingImports.push({ file: path.relative(dashboardDir, file), name: original });
      }
    }
  }
}

if (missingImports.length > 0) {
  console.error(`\x1b[31m[ERROR] Found ${missingImports.length} missing icon exports from '@/components/ui/icons':\x1b[0m`);
  const grouped = {};
  for (const item of missingImports) {
    grouped[item.name] = grouped[item.name] || [];
    grouped[item.name].push(item.file);
  }
  for (const [name, files] of Object.entries(grouped)) {
    console.error(`  - \x1b[33m${name}\x1b[0m (used in: ${files.join(", ")})`);
  }
  process.exit(1);
} else {
  console.log(`\x1b[32m[OK] All icon imports are cleanly exported by icons.ts (${exportedNames.size} exports checked).\x1b[0m`);
  process.exit(0);
}
