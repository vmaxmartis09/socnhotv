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
  "components/studio/tabs/PortsEditor.tsx",
  "components/canvas/PortValueInput.tsx",
];

for (const rel of files) {
  const fullPath = path.join(dashboardDir, rel);
  if (!fs.existsSync(fullPath)) continue;
  let content = fs.readFileSync(fullPath, "utf8");

  // Replace (s: any) => with (s: StudioStore) =>
  content = content.replace(/\(s:\s*any\)\s*=>/g, "(s: StudioStore) =>");

  // Ensure StudioStore is imported from "@/store"
  if (content.includes("StudioStore") && !content.includes("type StudioStore") && !content.includes("StudioStore,")) {
    if (content.includes('import { useStudioStore } from "@/store";')) {
      content = content.replace(
        'import { useStudioStore } from "@/store";',
        'import { useStudioStore, type StudioStore } from "@/store";'
      );
    } else if (content.includes('from "@/store"')) {
      content = content.replace('from "@/store"', 'type StudioStore } from "@/store"').replace('import {', 'import { ');
    }
  }

  fs.writeFileSync(fullPath, content, "utf8");
  console.log(`Fixed types in: ${rel}`);
}
