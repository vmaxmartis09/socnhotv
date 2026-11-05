import fs from "fs";

export async function runAudit(task) {
  const page = task.page("p1");
  const routes = [
    "/vi",
    "/vi/projects",
    "/vi/characters",
    "/vi/jobs",
    "/vi/settings",
    "/vi/studio"
  ];

  const viewports = [
    { name: "1440px", width: 1440, height: 900, mobile: false },
    { name: "1024px", width: 1024, height: 768, mobile: false },
    { name: "375px", width: 375, height: 667, mobile: true }
  ];

  const results = [];

  for (const vp of viewports) {
    await page.cdp("Emulation.setDeviceMetricsOverride", {
      width: vp.width,
      height: vp.height,
      deviceScaleFactor: 1,
      mobile: vp.mobile
    });

    for (const route of routes) {
      const url = `http://localhost:3000${route}`;
      await page.goto(url, { waitUntil: "load" });
      await new Promise(r => setTimeout(r, 1200));

      const pageErrors = await page.evaluate(() => {
        const portal = document.querySelector("nextjs-portal");
        let issuesCount = 0;
        let overlayText = "";
        if (portal && portal.shadowRoot) {
          const toast = portal.shadowRoot.querySelector("[data-nextjs-toast]");
          if (toast) {
            overlayText = toast.innerText || "";
            const match = overlayText.match(/(\d+)\s+Issues?/i);
            if (match) issuesCount = parseInt(match[1], 10);
          }
          const dialog = portal.shadowRoot.querySelector("[data-nextjs-dialog-overlay]");
          if (dialog) {
            overlayText += " " + (dialog.innerText || "");
            issuesCount = Math.max(issuesCount, 1);
          }
        }
        return {
          title: document.title,
          issuesCount,
          overlayText: overlayText.slice(0, 300)
        };
      });

      results.push({
        viewport: vp.name,
        route,
        issuesCount: pageErrors.issuesCount,
        overlayText: pageErrors.overlayText
      });
    }
  }

  // Now test right panel tabs on studio at 1440px
  await page.cdp("Emulation.setDeviceMetricsOverride", {
    width: 1440,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false
  });
  await page.goto("http://localhost:3000/vi/studio", { waitUntil: "load" });
  await new Promise(r => setTimeout(r, 1500));

  const tabs = ["project", "characters", "chat", "publish", "jobs", "node", "shortcuts"];
  for (const tab of tabs) {
    // Click dock button or set active tab
    const tabResult = await page.evaluate(async (tabName) => {
      // Find the tab button in FloatingPanels or RightPanel
      // Or use window API if available, or click matching button
      const btns = Array.from(document.querySelectorAll("button"));
      // check aria-label or text
      const targetBtn = btns.find(b => b.getAttribute("aria-label")?.toLowerCase().includes(tabName) || b.innerText?.toLowerCase().includes(tabName));
      if (targetBtn) targetBtn.click();
      
      await new Promise(r => setTimeout(r, 600));

      const portal = document.querySelector("nextjs-portal");
      let issuesCount = 0;
      let overlayText = "";
      if (portal && portal.shadowRoot) {
        const toast = portal.shadowRoot.querySelector("[data-nextjs-toast]");
        if (toast) {
          overlayText = toast.innerText || "";
          const match = overlayText.match(/(\d+)\s+Issues?/i);
          if (match) issuesCount = parseInt(match[1], 10);
        }
        const dialog = portal.shadowRoot.querySelector("[data-nextjs-dialog-overlay]");
        if (dialog) {
          overlayText += " " + (dialog.innerText || "");
          issuesCount = Math.max(issuesCount, 1);
        }
      }
      return { tab: tabName, issuesCount, overlayText };
    }, tab);

    results.push({
      viewport: "1440px",
      route: `/vi/studio [tab: ${tab}]`,
      issuesCount: tabResult.issuesCount,
      overlayText: tabResult.overlayText
    });
  }

  return results;
}
