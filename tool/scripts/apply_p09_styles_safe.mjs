import fs from "fs";
import path from "path";

const root = path.resolve("tool/dashboard");

function walk(dir) {
  let files = [];
  for (const f of fs.readdirSync(dir)) {
    const full = path.join(dir, f);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      if (f !== "node_modules" && f !== ".next" && f !== ".next-build") {
        files = files.concat(walk(full));
      }
    } else if (f.endsWith(".tsx")) {
      files.push(full);
    }
  }
  return files;
}

const files = walk(root);
let modifiedCount = 0;

for (const f of files) {
  let content = fs.readFileSync(f, "utf-8");
  let updated = content;

  // 1. Add scroll-quiet to scroll containers
  updated = updated.replace(/className=(["'])([^"']*?\boverflow-y-auto\b[^"']*?)\1/g, (match, quote, cls) => {
    if (!cls.includes("scroll-quiet") && !cls.includes("no-scrollbar")) {
      return `className=${quote}${cls} scroll-quiet${quote}`;
    }
    return match;
  });

  // 2. Modals and drawers: replace overflow-hidden with overflow-clip on outer container
  if (
    f.includes("Modal") ||
    f.includes("Dialog") ||
    f.includes("Sheet") ||
    f.includes("Drawer") ||
    f.includes("Floating") ||
    f.includes("UserBubble")
  ) {
    updated = updated
      .replace(/rounded-([23]?xl|lg)\s+([^"']*?\b)overflow-hidden\b/g, "rounded-$1 $2overflow-clip")
      .replace(/\boverflow-hidden\b\s+rounded-([23]?xl|lg)/g, "overflow-clip rounded-$1");
  }

  // 3. Normalize common color classes to semantic tokens
  updated = updated
    .replace(/\btext-rose-500\b/g, "text-semantic-danger")
    .replace(/\btext-red-500\b/g, "text-semantic-danger")
    .replace(/\btext-emerald-500\b/g, "text-semantic-success")
    .replace(/\btext-green-500\b/g, "text-semantic-success")
    .replace(/\btext-amber-500\b/g, "text-semantic-warning")
    .replace(/\btext-yellow-500\b/g, "text-semantic-warning")
    .replace(/\btext-sky-500\b/g, "text-semantic-info")
    .replace(/\btext-blue-500\b/g, "text-semantic-info");

  if (content !== updated) {
    fs.writeFileSync(f, updated, "utf-8");
    modifiedCount++;
    console.log(`Updated styles in: ${path.relative(root, f)}`);
  }
}

console.log(`Updated ${modifiedCount} files safely.`);
