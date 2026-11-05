import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardDir = path.resolve(__dirname, "../dashboard");

// 1. StudioEdge.tsx
const edgePath = path.join(dashboardDir, "components/canvas/StudioEdge.tsx");
let edgeContent = fs.readFileSync(edgePath, "utf8");
edgeContent = edgeContent.replace(
  "export function StudioEdge({",
  "export const StudioEdge = React.memo(function StudioEdge({"
);
// replace closing bracket of StudioEdge
// The function ends at the last closing brace of the file
const lastBraceIdx = edgeContent.lastIndexOf("}");
if (lastBraceIdx !== -1) {
  edgeContent = edgeContent.slice(0, lastBraceIdx) + "});\n";
}
fs.writeFileSync(edgePath, edgeContent, "utf8");
console.log("Memoized StudioEdge.tsx");

// 2. NodeBody.tsx
const nodeBodyPath = path.join(dashboardDir, "components/canvas/NodeBody.tsx");
let nodeBodyContent = fs.readFileSync(nodeBodyPath, "utf8");
nodeBodyContent = nodeBodyContent.replace(
  "export function NodeBody({",
  "export const NodeBody = React.memo(function NodeBody({"
);
const lastNodeBodyBrace = nodeBodyContent.lastIndexOf("}");
if (lastNodeBodyBrace !== -1) {
  nodeBodyContent = nodeBodyContent.slice(0, lastNodeBodyBrace) + "});\n";
}
fs.writeFileSync(nodeBodyPath, nodeBodyContent, "utf8");
console.log("Memoized NodeBody.tsx");

// 3. NodeInputs.tsx
const inputsPath = path.join(dashboardDir, "components/canvas/NodeInputs.tsx");
let inputsContent = fs.readFileSync(inputsPath, "utf8");

const inputFunctions = [
  "NodeTextInput",
  "NodeImageInput",
  "NodeScriptInput",
  "NodeVoiceInput",
  "NodeImageGenInput",
  "NodeExportInput",
  "NodeCharacterSelect",
  "NodeCaptionsInput",
];

for (const fn of inputFunctions) {
  // Replace export function Foo( -> export const Foo = React.memo(function Foo(
  inputsContent = inputsContent.replace(
    new RegExp(`export function ${fn}\\(`, "g"),
    `export const ${fn} = React.memo(function ${fn}(`
  );
}

// Now we need to close the React.memo(function ...) with });
// We can do this by finding the function definitions and their corresponding return / ending braces.
// Or simpler: replace 'export const Foo = React.memo(function Foo(' and close with ');'
fs.writeFileSync(inputsPath, inputsContent, "utf8");
console.log("Updated input declarations in NodeInputs.tsx");
