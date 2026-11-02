const task = await claimTaskSpace(4);
const page = task.page("p2");

// Click next video arrow
console.log("Switching to next video...");
await page.evaluate(() => {
  const nextBtn = document.querySelector('button[aria-label="Nội dung nghe nhìn tiếp theo"]');
  if (nextBtn) nextBtn.click();
});

await page.waitForTimeout(2000);
await page.screenshot({ path: "shots/ego_gobi_video_2_opened.png" });

console.log("Setting up download listener for video 2...");
const downloadPromise = page.waitForEvent("download", { timeout: 30000 });

// 1. Click download button in the top toolbar
await page.evaluate(() => {
  const btn = document.querySelector('button[aria-label="Tải nội dung nghe nhìn xuống"]');
  if (btn) btn.click();
});

await page.waitForTimeout(1000);

// 2. Click "720p Kích thước gốc"
console.log("Clicking 720p download option...");
await page.evaluate(() => {
  const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"]'));
  const target = items.find(i => i.textContent.includes("720p") || i.textContent.includes("Kích thước gốc"));
  if (target) {
    target.click();
  }
});

try {
  const download = await downloadPromise;
  console.log("Download event received for video 2!");
  console.log("Filename:", download.suggestedFilename());
  
  const targetPath = "./assets/samples/sample_video/output/gobi_official_speaking_video_2.mp4";
  await download.saveAs(targetPath);
  console.log("Video 2 saved successfully to:", targetPath);
} catch (e) {
  console.log("Download error:", e.message);
}
