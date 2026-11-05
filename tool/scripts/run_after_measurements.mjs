import path from "node:path";
import fs from "node:fs/promises";

// Script executed by ego-browser nodejs
const baseUrl = "http://localhost:3200";
const responsiveDir = "D:/socnhotv/ai/plans/2026-11-roadmap/session-P-ui-perf/responsive";

await fs.mkdir(responsiveDir, { recursive: true });

const viewports = [
  { name: "375x812", width: 375, height: 812, mobile: true },
  { name: "768x1024", width: 768, height: 1024, mobile: false },
  { name: "1024x768", width: 1024, height: 768, mobile: false },
  { name: "1440x900", width: 1440, height: 900, mobile: false },
  { name: "1920x1080", width: 1920, height: 1080, mobile: false },
];

const task = await taskSpace("measure_after");
const page = task.page("p1");

const metrics = {
  bundle: {
    studioFirstLoadJs: "314 kB",
    studioRouteSize: "84.3 kB",
    sharedJs: "103 kB",
    rootFirstLoadJs: "209 kB",
  },
  layoutIssues: [],
  smallButtons: [],
  interactions: {},
  canvas: {},
};

console.log("Navigating to Studio...");
await page.goto(`${baseUrl}/vi/studio`, { waitUntil: "domcontentloaded", timeout: 15000 });
await new Promise((r) => setTimeout(r, 600));

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
      await new Promise((r) => setTimeout(r, 400));

      // Inspect layout issues
      const pageAudit = await page.evaluate(() => {
        const docW = document.documentElement.scrollWidth;
        const winW = window.innerWidth;
        const hasHorizontalOverflow = docW > winW + 2;

        const smallBtns = [];
        const buttons = document.querySelectorAll("button");
        buttons.forEach((b) => {
          const rect = b.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0 && (rect.width < 32 || rect.height < 32)) {
            smallBtns.push({
              tag: b.tagName,
              aria: b.getAttribute("aria-label") || b.getAttribute("title") || b.innerText?.slice(0, 15) || "unnamed",
              size: `${Math.round(rect.width)}x${Math.round(rect.height)}`,
            });
          }
        });

        return {
          hasHorizontalOverflow,
          docW,
          winW,
          smallButtonsCount: smallBtns.length,
        };
      });

      if (pageAudit.hasHorizontalOverflow) {
        metrics.layoutIssues.push({ viewport: vp.name, page: p.id, docW: pageAudit.docW, winW: pageAudit.winW });
      }

      const imgPath = path.join(responsiveDir, `${p.id}_${vp.name}.png`);
      const imgBuffer = await page.screenshot({ fullPage: false });
      await fs.writeFile(imgPath, imgBuffer);
      console.log(`Saved screenshot: ${imgPath}`);
    } catch (err) {
      console.error(`Error capturing ${p.id} on ${vp.name}:`, err.message);
    }
  }
}

// Reset emulation
await page.cdp("Emulation.clearDeviceMetricsOverride");

const resultJson = path.join(responsiveDir, "../after_metrics.json");
await fs.writeFile(resultJson, JSON.stringify(metrics, null, 2));
console.log(`Finished after measurements! Saved to ${resultJson}`);
