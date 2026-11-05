import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardDir = path.resolve(__dirname, "../dashboard");

// 1. StudioEdge.tsx
const edgeFile = path.join(dashboardDir, "components/canvas/StudioEdge.tsx");
let edgeText = fs.readFileSync(edgeFile, "utf8").replace(/\r\n/g, "\n");
if (!edgeText.includes("export const StudioEdge = React.memo")) {
  edgeText = edgeText.replace(
    "export function StudioEdge({",
    "export const StudioEdge = React.memo(function StudioEdge({"
  );
  const lastBrace = edgeText.lastIndexOf("}");
  edgeText = edgeText.slice(0, lastBrace) + "});\n";
  fs.writeFileSync(edgeFile, edgeText, "utf8");
  console.log("Memoized StudioEdge.tsx");
}

// 2. NodeBody.tsx
const bodyFile = path.join(dashboardDir, "components/canvas/NodeBody.tsx");
let bodyText = fs.readFileSync(bodyFile, "utf8").replace(/\r\n/g, "\n");
if (!bodyText.includes("export const NodeBody = React.memo")) {
  bodyText = bodyText.replace(
    "export function NodeBody({",
    "export const NodeBody = React.memo(function NodeBody({"
  );
  const lastBrace = bodyText.lastIndexOf("}");
  bodyText = bodyText.slice(0, lastBrace) + "});\n";
  fs.writeFileSync(bodyFile, bodyText, "utf8");
  console.log("Memoized NodeBody.tsx");
}

// 3. NodeInputs.tsx
const inputsFile = path.join(dashboardDir, "components/canvas/NodeInputs.tsx");
let inputsText = fs.readFileSync(inputsFile, "utf8").replace(/\r\n/g, "\n");

const inputFunctions = [
  { name: "NodeTextInput", endPattern: "\n}\n\n// ============================================================================\n// 2. IMAGE INPUT" },
  { name: "NodeImageInput", endPattern: "\n}\n\n// ============================================================================\n// 3. SCRIPT INPUT" },
  { name: "NodeScriptInput", endPattern: "\n}\n\n// ============================================================================\n// 4. VOICE INPUT" },
  { name: "NodeVoiceInput", endPattern: "\n}\n\n// ============================================================================\n// 5. IMAGE GEN INPUT" },
  { name: "NodeImageGenInput", endPattern: "\n}\n\n// ============================================================================\n// 6. EXPORT INPUT" },
  { name: "NodeExportInput", endPattern: "\n}\n\n// ============================================================================\n// 7. CHARACTER SELECT" },
  { name: "NodeCharacterSelect", endPattern: "\n}\n\n// ============================================================================\n// 8. CAPTIONS INPUT" },
  { name: "NodeCaptionsInput", endPattern: "\n}\n" },
];

for (const fn of inputFunctions) {
  if (inputsText.includes(`export function ${fn.name}(`)) {
    inputsText = inputsText.replace(
      `export function ${fn.name}(`,
      `export const ${fn.name} = React.memo(function ${fn.name}(`
    );
    if (fn.endPattern === "\n}\n") {
      const lastIdx = inputsText.lastIndexOf("\n}\n");
      inputsText = inputsText.slice(0, lastIdx) + "\n});\n";
    } else {
      inputsText = inputsText.replace(fn.endPattern, "\n});\n\n" + fn.endPattern.trimStart().replace(/^\}\n\n/, ""));
    }
    console.log(`Memoized ${fn.name}`);
  }
}
fs.writeFileSync(inputsFile, inputsText, "utf8");

// 4. StudioCanvas.tsx
const canvasFile = path.join(dashboardDir, "components/canvas/StudioCanvas.tsx");
let canvasText = fs.readFileSync(canvasFile, "utf8").replace(/\r\n/g, "\n");

// Add nodeIdsKey memoization and replace in stepInfo and nodeIssues
if (!canvasText.includes("nodeIdsKey")) {
  const targetStepInfo = "  const stepInfo = useMemo(() => analyzeGraph(nodes, edges), [nodes, edges]);";
  const replacementStepInfo = `  const nodeIdsKey = useMemo(() => nodes.map((n) => n.id).join(","), [nodes]);\n  const stepInfo = useMemo(() => analyzeGraph(nodes, edges), [nodeIdsKey, edges]);`;
  canvasText = canvasText.replace(targetStepInfo, replacementStepInfo);

  // nodeIssues: change [validationResult, nodes] to [validationResult, nodeIdsKey]
  canvasText = canvasText.replace(
    "  }, [validationResult, nodes]);",
    "  }, [validationResult, nodeIdsKey]);"
  );

  // onOpenQuickAdd in contextValue: make it a useCallback
  const targetContext = `  const contextValue = useMemo(
    () => ({
      activeDragPort,
      connectedPorts,
      nodeIssues,
      onOpenQuickAdd: (req: QuickAddRequest) => setQuickAddReq(req),
      onRequestRun: handleRequestRun,
      onOpenNodeInspector: (nodeId: string) => {
        setSelectedNodeId(nodeId);
        setActiveRightTab("node");
      },`;

  const replacementContext = `  const onOpenQuickAdd = useCallback((req: QuickAddRequest) => setQuickAddReq(req), []);
  const onOpenNodeInspector = useCallback(
    (nodeId: string) => {
      setSelectedNodeId(nodeId);
      setActiveRightTab("node");
    },
    [setSelectedNodeId, setActiveRightTab]
  );

  const contextValue = useMemo(
    () => ({
      activeDragPort,
      connectedPorts,
      nodeIssues,
      onOpenQuickAdd,
      onRequestRun: handleRequestRun,
      onOpenNodeInspector,`;

  canvasText = canvasText.replace(targetContext, replacementContext);
  fs.writeFileSync(canvasFile, canvasText, "utf8");
  console.log("Optimized StudioCanvas memoization and context stability");
}

console.log("P-03 Memoization script completed.");
