const task = await claimTaskSpace(4);
const page = task.page("p2");

console.log("Setting up download listener...");
const downloadPromise = page.waitForEvent("download", { timeout: 30000 });

// 1. Click download button in the top toolbar
await page.evaluate(() => {
  const btn = document.querySelector('button[aria-label="Tải nội dung nghe nhìn xuống"]');
  if (btn) btn.click();
});

await page.waitForTimeout(1000);

// 2. Click "720p Kích thước gốc" or "1080p Đã tăng độ phân giải"
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
  console.log("Download event received!");
  console.log("URL:", download.url());
  console.log("Suggested filename:", download.suggestedFilename());
  
  const targetPath = "./assets/samples/sample_video/output/gobi_official_speaking_video_1.mp4";
  await download.saveAs(targetPath);
  console.log("Video saved successfully to:", targetPath);
} catch (e) {
  console.log("Download error:", e.message);
}
