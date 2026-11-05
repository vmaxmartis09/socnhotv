import fs from "fs";
import path from "path";

const SHOTS_DIR = "/Volumes/Data/socnhotv/data/projects/soc-nho-tv/shots";
fs.mkdirSync(SHOTS_DIR, { recursive: true });

export async function runHubVerification(task) {
  const page = task.page("p1");

  // Set 1440px desktop
  await page.cdp("Emulation.setDeviceMetricsOverride", {
    width: 1440,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false,
  });

  const results = [];

  // Helper to check issues overlay
  async function checkOverlay() {
    return await page.evaluate(() => {
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
      return { issuesCount, overlayText };
    });
  }

  // 1. Visit Studio and open Publish tab
  console.log("Testing Studio Publish Tab...");
  await page.goto("http://localhost:3000/vi/studio", { waitUntil: "load" });
  await new Promise((r) => setTimeout(r, 1500));

  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll("button"));
    const publishBtn = btns.find((b) =>
      b.getAttribute("aria-label")?.includes("Lịch đăng") ||
      b.innerText?.includes("Lịch đăng")
    );
    if (publishBtn) publishBtn.click();
  });
  await new Promise((r) => setTimeout(r, 1000));

  const publishOverlay = await checkOverlay();
  results.push({
    view: "Studio [tab: Lịch đăng]",
    issuesCount: publishOverlay.issuesCount,
    overlayText: publishOverlay.overlayText,
  });

  const shotPublish = await page.cdp("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(path.join(SHOTS_DIR, "S2_publish_tab.png"), Buffer.from(shotPublish.data, "base64"));
  console.log("Saved S2_publish_tab.png");

  // 2. Test each Social Hub view
  const views = [
    { id: "overview", label: "Tổng quan", shot: "S2_hub_overview.png" },
    { id: "library", label: "Kho video", shot: "S2_hub_library.png" },
    { id: "queue", label: "Hàng đợi", shot: "S2_hub_queue.png" },
    { id: "calendar", label: "Lịch", shot: "S2_hub_calendar.png" },
    { id: "accounts", label: "Tài khoản", shot: "S2_hub_accounts.png" },
    { id: "templates", label: "Mẫu nội dung", shot: "S2_hub_templates.png" },
  ];

  for (const v of views) {
    console.log(`Testing Social Hub: ${v.label} (?hub=social&view=${v.id})...`);
    await page.goto(`http://localhost:3000/vi/studio?hub=social&view=${v.id}`, {
      waitUntil: "load",
    });
    await new Promise((r) => setTimeout(r, 1500));

    const overlay = await checkOverlay();
    results.push({
      view: `Social Hub [${v.label}]`,
      issuesCount: overlay.issuesCount,
      overlayText: overlay.overlayText,
    });

    const shot = await page.cdp("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(path.join(SHOTS_DIR, v.shot), Buffer.from(shot.data, "base64"));
    console.log(`Saved ${v.shot}`);
  }

  // 3. Test Mobile 375px
  console.log("Testing Mobile 375px...");
  await page.cdp("Emulation.setDeviceMetricsOverride", {
    width: 375,
    height: 812,
    deviceScaleFactor: 2,
    mobile: true,
  });
  await page.goto("http://localhost:3000/vi/studio?hub=social&view=overview", {
    waitUntil: "load",
  });
  await new Promise((r) => setTimeout(r, 1200));

  const mobileOverlay = await checkOverlay();
  results.push({
    view: "Social Hub [Mobile 375px]",
    issuesCount: mobileOverlay.issuesCount,
    overlayText: mobileOverlay.overlayText,
  });

  const shotMobile = await page.cdp("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(path.join(SHOTS_DIR, "S2_hub_mobile_375.png"), Buffer.from(shotMobile.data, "base64"));
  console.log("Saved S2_hub_mobile_375.png");

  return results;
}
