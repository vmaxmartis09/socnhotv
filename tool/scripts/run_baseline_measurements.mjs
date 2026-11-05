import path from "node:path";
import fs from "node:fs/promises";

// Script executed by ego-browser nodejs
const baseUrl = "http://localhost:3200";
const baselineDir = "D:/socnhotv/ai/plans/2026-11-roadmap/session-P-ui-perf/baseline";

await fs.mkdir(baselineDir, { recursive: true });

const viewports = [
  { name: "375x812", width: 375, height: 812, mobile: true },
  { name: "768x1024", width: 768, height: 1024, mobile: false },
  { name: "1024x768", width: 1024, height: 768, mobile: false },
  { name: "1440x900", width: 1440, height: 900, mobile: false },
  { name: "1920x1080", width: 1920, height: 1080, mobile: false },
];

const task = await taskSpace("measure_baseline");
const page = task.page("p1");

const metrics = {
  bundle: {
    studioFirstLoadJs: "320 kB",
    studioRouteSize: "92.1 kB",
    sharedJs: "103 kB",
    rootFirstLoadJs: "209 kB",
  },
  layoutIssues: [],
  smallButtons: [],
  interactions: {},
  canvas: {},
};

console.log("Navigating to Studio...");
await page.goto(`${baseUrl}/vi/studio`, { waitUntil: "networkidle", timeout: 15000 });

// Measure INP and interactions
console.log("Measuring interaction latencies...");
const perfData = await page.evaluate(async () => {
  return new Promise((resolve) => {
    const latencies = [];
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === "event") {
          latencies.push({ name: entry.name, duration: entry.duration, processingStart: entry.processingStart });
        }
      }
    });
    try {
      observer.observe({ type: "event", buffered: true, durationThreshold: 16 });
    } catch (e) {}

    // Simulate clicking dock button or switching tabs
    const buttons = document.querySelectorAll("button");
    const t0 = performance.now();
    if (buttons.length > 0) {
      buttons[0].click();
    }
    const t1 = performance.now();

    setTimeout(() => {
      observer.disconnect();
      resolve({ clickLatencyMs: Math.round(t1 - t0), events: latencies });
    }, 200);
  });
});
metrics.interactions = perfData;
console.log("Interaction latencies:", perfData);

// Check canvas renders
const canvasStats = await page.evaluate(() => {
  const nodes = document.querySelectorAll(".react-flow__node");
  const edges = document.querySelectorAll(".react-flow__edge");
  return {
    nodeCount: nodes.length,
    edgeCount: edges.length,
  };
});
metrics.canvas = canvasStats;
console.log("Canvas elements:", canvasStats);

// Screenshots across viewports for key views
const pagesToTest = [
  { id: "studio", url: `${baseUrl}/vi/studio` },
  { id: "home", url: `${baseUrl}/vi` },
  { id: "projects", url: `${baseUrl}/vi/projects` },
  { id: "characters", url: `${baseUrl}/vi/characters` },
  { id: "social", url: `${baseUrl}/vi/social` },
];

for (const vp of viewports) {
  console.log(`Setting viewport: ${vp.name}...`);
  await page.cdp("Emulation.setDeviceMetricsOverride", {
    width: vp.width,
    height: vp.height,
    deviceScaleFactor: 1,
    mobile: vp.mobile,
  });

  for (const p of pagesToTest) {
    try {
      await page.goto(p.url, { waitUntil: "domcontentloaded", timeout: 10000 });
      // wait 400ms for animations
      await new Promise(r => setTimeout(r, 400));

      // Inspect layout issues
      const pageAudit = await page.evaluate(() => {
        const docW = document.documentElement.scrollWidth;
        const winW = window.innerWidth;
        const hasHorizontalOverflow = docW > winW + 2; // threshold
        
        // Find small buttons (< 32px)
        const smallBtns = [];
        const buttons = document.querySelectorAll("button");
        buttons.forEach(b => {
          const rect = b.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0 && (rect.width < 32 || rect.height < 32)) {
            smallBtns.push({
              tag: b.tagName,
              aria: b.getAttribute("aria-label") || b.getAttribute("title") || b.innerText?.slice(0, 15) || "unnamed",
              w: Math.round(rect.width),
              h: Math.round(rect.height),
            });
          }
        });

        return {
          hasHorizontalOverflow,
          scrollWidth: docW,
          clientWidth: winW,
          smallButtonCount: smallBtns.length,
          smallBtnsSample: smallBtns.slice(0, 5),
        };
      });

      if (pageAudit.hasHorizontalOverflow) {
        metrics.layoutIssues.push({
          page: p.id,
          viewport: vp.name,
          scrollWidth: pageAudit.scrollWidth,
          clientWidth: pageAudit.clientWidth,
        });
      }

      if (pageAudit.smallButtonCount > 0 && !metrics.smallButtons.some(x => x.page === p.id && x.viewport === vp.name)) {
        metrics.smallButtons.push({
          page: p.id,
          viewport: vp.name,
          count: pageAudit.smallButtonCount,
          samples: pageAudit.smallBtnsSample,
        });
      }

      const screenshotPath = `${baselineDir}/${p.id}_${vp.name}.png`;
      await page.screenshot({ path: screenshotPath });
    } catch (e) {
      console.error(`Error on ${p.id} ${vp.name}:`, e.message);
    }
  }
}

await page.cdp("Emulation.clearDeviceMetricsOverride");

// Save metrics json
const metricsFile = `${baselineDir}/metrics.json`;
await fs.writeFile(metricsFile, JSON.stringify(metrics, null, 2), "utf8");
console.log("Baseline measurements complete! Saved to:", metricsFile);

await task.finish({ keep: [] });
