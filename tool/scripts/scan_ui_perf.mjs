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
console.log("Total TS/TSX files scanned:", files.length);

const fileLines = files.map(f => ({
  f: path.relative(dashboardDir, f).replace(/\\/g, "/"),
  lines: fs.readFileSync(f, "utf8").split("\n").length
}));
fileLines.sort((a, b) => b.lines - a.lines);

console.log("\n--- TOP 10 LARGEST FILES ---");
fileLines.slice(0, 10).forEach(x => console.log(`${x.lines.toString().padStart(5)} lines: ${x.f}`));

let storeNoSel = 0;
const storeNoSelLocations = [];
let memoCount = 0;
let dynamicCount = 0;
let imgCount = 0;
let imgLazyCount = 0;
let intervalCount = 0;
let timeoutCount = 0;
let abortControllerCount = 0;
let fetchCount = 0;
let useEffectCount = 0;
let keyIndexCount = 0;
let alertCount = 0;
const alertLocations = [];
let windowConfirmCount = 0;
const confirmLocations = [];
let overflowHiddenCount = 0;
let overflowClipCount = 0;
let overflowYAutoCount = 0;
let scrollQuietCount = 0;
let fixedWidthCount = 0;
let smallButtonCount = 0;
let buttonCount = 0;
let buttonWithAriaCount = 0;
let hardcodedColorsCount = 0;
const hardcodedColorLocations = [];

for (const f of files) {
  const content = fs.readFileSync(f, "utf8");
  const rel = path.relative(dashboardDir, f).replace(/\\/g, "/");

  // useStudioStore() without selector
  const storeMatches = [...content.matchAll(/useStudioStore\(\s*\)/g)];
  if (storeMatches.length > 0) {
    storeNoSel += storeMatches.length;
    storeNoSelLocations.push({ file: rel, count: storeMatches.length });
  }

  // React.memo or memo(
  const memoMatches = [...content.matchAll(/\b(React\.)?memo\s*\(/g)];
  memoCount += memoMatches.length;

  // dynamic or lazy
  const dynMatches = [...content.matchAll(/\b(dynamic|React\.lazy)\s*\(/g)];
  dynamicCount += dynMatches.length;

  // img tags
  const imgs = [...content.matchAll(/<img\b([^>]*)>/g)];
  imgCount += imgs.length;
  for (const img of imgs) {
    if (/loading\s*=\s*['"]lazy['"]/.test(img[1])) imgLazyCount++;
  }

  // intervals and timeouts
  const intervals = [...content.matchAll(/\bsetInterval\s*\(/g)];
  intervalCount += intervals.length;
  const timeouts = [...content.matchAll(/\bsetTimeout\s*\(/g)];
  timeoutCount += timeouts.length;

  // AbortController, fetch, useEffect
  abortControllerCount += [...content.matchAll(/\bAbortController\b/g)].length;
  fetchCount += [...content.matchAll(/\bfetch\s*\(/g)].length;
  useEffectCount += [...content.matchAll(/\buseEffect\s*\(/g)].length;

  // key with index/idx/i
  const keyMatches = [...content.matchAll(/key\s*=\s*\{[^\}]*\b(index|idx|i)\b[^\}]*\}/g)];
  keyIndexCount += keyMatches.length;

  // alert(
  const alerts = [...content.matchAll(/\balert\s*\(/g)];
  if (alerts.length > 0) {
    alertCount += alerts.length;
    alertLocations.push({ file: rel, count: alerts.length });
  }

  // window.confirm or confirm( (if not importing confirm from @/lib/confirm)
  const winConfirms = [...content.matchAll(/\bwindow\.confirm\s*\(/g)];
  if (winConfirms.length > 0) {
    windowConfirmCount += winConfirms.length;
    confirmLocations.push({ file: rel, count: winConfirms.length });
  }

  // overflow
  overflowHiddenCount += [...content.matchAll(/\boverflow-hidden\b/g)].length;
  overflowClipCount += [...content.matchAll(/\boverflow-clip\b/g)].length;
  overflowYAutoCount += [...content.matchAll(/\boverflow-y-auto\b/g)].length;
  scrollQuietCount += [...content.matchAll(/\bscroll-quiet\b/g)].length;

  // Fixed widths like w-[123px] or min-w-[123px]
  const fwMatches = [...content.matchAll(/\b(min-)?w-\[\d+px\]/g)];
  fixedWidthCount += fwMatches.length;

  // buttons and accessibility
  const buttons = [...content.matchAll(/<button\b([^>]*)>/g)];
  buttonCount += buttons.length;
  for (const b of buttons) {
    const attr = b[1];
    if (/\b(aria-label|data-tip|title)\s*=/i.test(attr)) {
      buttonWithAriaCount++;
    }
  }

  // hardcoded hex colors #fff, #123456, or bg-red-500, etc. (excluding tailwind opacity / arbitrary values)
  const hexMatches = [...content.matchAll(/#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b/g)];
  // also check literal colors like bg-red-500, text-green-600, etc.
  const rawColorMatches = [...content.matchAll(/\b(bg|text|border)-(red|green|blue|yellow|amber|purple|pink|indigo|emerald)-(400|500|600|700)\b/g)];
  const totalColors = hexMatches.length + rawColorMatches.length;
  if (totalColors > 0 && !rel.includes("icons.ts") && !rel.includes("tailwind.config")) {
    hardcodedColorsCount += totalColors;
    hardcodedColorLocations.push({ file: rel, count: totalColors });
  }
}

console.log("\n--- DETAILED METRICS SCAN ---");
console.log({
  storeNoSel,
  memoCount,
  dynamicCount,
  imgCount,
  imgLazyCount,
  intervalCount,
  timeoutCount,
  abortControllerCount,
  fetchCount,
  useEffectCount,
  keyIndexCount,
  alertCount,
  windowConfirmCount,
  overflowHiddenCount,
  overflowClipCount,
  overflowYAutoCount,
  scrollQuietCount,
  fixedWidthCount,
  buttonCount,
  buttonWithAriaCount,
  hardcodedColorsCount
});

console.log("\n--- STORE NO SELECTOR LOCATIONS (" + storeNoSelLocations.length + " files) ---");
storeNoSelLocations.forEach(x => console.log(`  ${x.count}x: ${x.file}`));

console.log("\n--- ALERT LOCATIONS ---");
alertLocations.forEach(x => console.log(`  ${x.count}x: ${x.file}`));

console.log("\n--- WINDOW CONFIRM LOCATIONS ---");
confirmLocations.forEach(x => console.log(`  ${x.count}x: ${x.file}`));
