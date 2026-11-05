import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardDir = path.resolve(__dirname, "../dashboard");

const files = [
  "components/canvas/StudioCanvas.tsx",
  "components/navigation/Sidebar.tsx",
  "components/navigation/UserBubble.tsx",
  "components/navigation/WorkspaceBootstrap.tsx",
  "components/studio/CreateVideoModal.tsx",
  "components/studio/StudioBreadcrumb.tsx",
  "components/studio/tabs/ChatTab.tsx",
  "components/studio/tabs/JobsCostTab.tsx",
  "components/studio/tabs/NodeTab.tsx",
  "components/studio/tabs/ProjectTab.tsx",
];

for (const rel of files) {
  const fullPath = path.join(dashboardDir, rel);
  const raw = fs.readFileSync(fullPath, "utf8");
  const isCrlf = raw.includes("\r\n");
  let content = raw.replace(/\r\n/g, "\n");

  const match = content.match(/const\s+\{([^}]+)\}\s*=\s*useStudioStore\(\)/);
  if (!match) {
    console.log(`No match in ${rel}`);
    continue;
  }

  const rawFields = match[1]
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const parsedFields = rawFields.map((f) => {
    if (f.includes(":")) {
      const parts = f.split(":").map((p) => p.trim());
      return { key: parts[0], alias: parts[1] };
    }
    return { key: f, alias: f };
  });

  const selectorMapping = parsedFields
    .map((p) => (p.key === p.alias ? `      ${p.key}: s.${p.key},` : `      ${p.alias}: s.${p.key},`))
    .join("\n");

  const replacement = `const {
${parsedFields.map((p) => (p.key === p.alias ? `    ${p.key},` : `    ${p.key}: ${p.alias},`)).join("\n")}
  } = useStudioStore(
    useShallow((s: any) => ({
${selectorMapping}
    }))
  )`;

  content = content.replace(match[0], replacement);

  if (!content.includes("useShallow")) {
    content = `import { useShallow } from "zustand/react/shallow";\n` + content;
  }

  const output = isCrlf ? content.replace(/\n/g, "\r\n") : content;
  fs.writeFileSync(fullPath, output, "utf8");
  console.log(`Successfully selector-ized: ${rel}`);
}
