import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardDir = path.resolve(__dirname, "../dashboard");

// 1. RunStatusBar.tsx
const runStatusFile = path.join(dashboardDir, "components/canvas/RunStatusBar.tsx");
let rs = fs.readFileSync(runStatusFile, "utf8").replace(/\r\n/g, "\n");

// Add startedAt to RunStateInfo
rs = rs.replace(
  "  elapsedSec?: number;\n  error?: string;",
  "  elapsedSec?: number;\n  startedAt?: number;\n  error?: string;"
);

// Add isolated ticker inside RunStatusBar
const oldElapsedCalc = `  const currentNodes = activeRun?.nodes || [];
  const status = activeRun?.status || (isRunning ? "running" : "idle");
  const progressPct = Math.min(100, Math.max(0, activeRun?.progressPct ?? (activeRun?.progress ? Math.round(activeRun.progress * 100) : 0)));
  const elapsed = Math.round(activeRun?.elapsedSec || 0);
  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  const timeStr = \`\${minutes.toString().padStart(2, "0")}:\${seconds.toString().padStart(2, "0")}\`;`;

const newElapsedCalc = `  const currentNodes = activeRun?.nodes || [];
  const status = activeRun?.status || (isRunning ? "running" : "idle");
  const progressPct = Math.min(100, Math.max(0, activeRun?.progressPct ?? (activeRun?.progress ? Math.round(activeRun.progress * 100) : 0)));

  // Isolated local ticker: only re-renders RunStatusBar each second, never canvas
  const [now, setNow] = React.useState(Date.now());
  React.useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [isRunning]);

  const elapsed = React.useMemo(() => {
    if (activeRun?.startedAt) {
      return Math.max(0, Math.floor((now - activeRun.startedAt) / 1000));
    }
    return Math.round(activeRun?.elapsedSec || 0);
  }, [activeRun?.startedAt, activeRun?.elapsedSec, now]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  const timeStr = \`\${minutes.toString().padStart(2, "0")}:\${seconds.toString().padStart(2, "0")}\`;`;

rs = rs.replace(oldElapsedCalc, newElapsedCalc);
fs.writeFileSync(runStatusFile, rs, "utf8");
console.log("Updated RunStatusBar.tsx");

// 2. StudioCanvas.tsx
const canvasFile = path.join(dashboardDir, "components/canvas/StudioCanvas.tsx");
let sc = fs.readFileSync(canvasFile, "utf8").replace(/\r\n/g, "\n");

// Set startedAt on restore active run
sc = sc.replace(
  "setActiveRunState(active);",
  "setActiveRunState({ ...active, startedAt: Date.now() - (active.elapsedSec || 0) * 1000 });"
);

// Set startedAt on start run
sc = sc.replace(
  "elapsedSec: 0,\n      nodes: initialRunNodes,",
  "elapsedSec: 0,\n      startedAt: Date.now(),\n      nodes: initialRunNodes,"
);

// Remove the canvas-level interval that caused canvas re-renders every 1s
const canvasIntervalCode = `  // Bộ đếm thời gian cho phiên chạy đang hoạt động
  useEffect(() => {
    if (!isRunningGraph) return;
    const interval = setInterval(() => {
      setActiveRunState((prev) => (prev ? { ...prev, elapsedSec: (prev.elapsedSec || 0) + 1 } : prev));
    }, 1000);
    return () => clearInterval(interval);
  }, [isRunningGraph]);`;

sc = sc.replace(canvasIntervalCode, "  // Canvas timer isolated to RunStatusBar (P-04)");
fs.writeFileSync(canvasFile, sc, "utf8");
console.log("Updated StudioCanvas.tsx - removed canvas-level ticking interval");

// 3. JobsCostTab.tsx
const jobsTabFile = path.join(dashboardDir, "components/studio/tabs/JobsCostTab.tsx");
let jc = fs.readFileSync(jobsTabFile, "utf8").replace(/\r\n/g, "\n");

const oldJobsInterval = `  useEffect(() => {
    if (activeProjectId) {
      fetchJobs();
      const interval = setInterval(fetchJobs, 3000);
      return () => clearInterval(interval);
    }
  }, [activeProjectId]);`;

const newJobsInterval = `  useEffect(() => {
    if (!activeProjectId) return;
    fetchJobs();

    let timeoutId: NodeJS.Timeout | null = null;
    let cancelled = false;
    let delay = 3000;

    const tick = async () => {
      if (cancelled) return;
      if (typeof document !== "undefined" && document.hidden) {
        timeoutId = setTimeout(tick, 5000);
        return;
      }
      await fetchJobs();
      if (cancelled) return;

      const hasActive = jobs.some((j) => j.status === "running" || j.status === "queued");
      delay = hasActive ? 3000 : Math.min(delay * 1.5, 10000);
      timeoutId = setTimeout(tick, delay);
    };

    timeoutId = setTimeout(tick, delay);

    const onVisibilityChange = () => {
      if (!document.hidden && !cancelled) {
        delay = 3000;
        fetchJobs();
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      cancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [activeProjectId]);`;

jc = jc.replace(oldJobsInterval, newJobsInterval);
fs.writeFileSync(jobsTabFile, jc, "utf8");
console.log("Updated JobsCostTab.tsx - added backoff and document.hidden pause");

console.log("P-04 Timer patching complete.");
