const spaces = await listTaskSpaces();
const flowSpace = spaces.find(s => s.name && (s.name.includes("Flow") || s.name.includes("google"))) || spaces[0];
console.log("Using space:", flowSpace?.id);

const task = await claimTaskSpace(flowSpace.id);
const tabs = await task.tabs();

const flowTab = tabs.find(t => t.url && t.url.includes("flow.google.com")) || tabs.find(t => t.active);
const page = flowTab.label ? task.page(flowTab.label) : await task.adopt(flowTab.page);
console.log("Operating page:", page.label, "URL:", await page.url());

// 1. Click on the first card on canvas (True DNA Video 1)
console.log("Clicking on Card 1 (True DNA Video)...");
await page.evaluate(() => {
  const cards = Array.from(document.querySelectorAll('flow-grid-tile-container'));
  console.log("Total cards:", cards.length);
  if (cards.length > 0) {
    cards[0].click();
  }
});

await page.waitForTimeout(2000);

try {
  await page.screenshot({ path: "shots/ego_gobi_dna_card1_opened.png" });
} catch (e) {
  console.log("Screenshot note:", e.message);
}

console.log("Setting up download for Card 1...");
const downloadPromise1 = page.waitForEvent("download", { timeout: 30000 });

// Click download button
await page.evaluate(() => {
  const btn = document.querySelector('button[aria-label="Tải nội dung nghe nhìn xuống"]');
  if (btn) btn.click();
});

await page.waitForTimeout(1000);

// Click 720p or original size
await page.evaluate(() => {
  const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"]'));
  const target = items.find(i => i.textContent.includes("720p") || i.textContent.includes("Kích thước gốc"));
  if (target) target.click();
});

try {
  const download1 = await downloadPromise1;
  const path1 = "shots/ego_gobi_dna_card2_opened.png" });
} catch (e) {
  console.log("Screenshot note:", e.message);
}

console.log("Setting up download for Card 2...");
const downloadPromise2 = page.waitForEvent("download", { timeout: 30000 });

// Click download button
await page.evaluate(() => {
  const btn = document.querySelector('button[aria-label="Tải nội dung nghe nhìn xuống"]');
  if (btn) btn.click();
});

await page.waitForTimeout(1000);

// Click 720p
await page.evaluate(() => {
  const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"]'));
  const target = items.find(i => i.textContent.includes("720p") || i.textContent.includes("Kích thước gốc"));
  if (target) target.click();
});

try {
  const download2 = await downloadPromise2;
  const path2 = "./assets/samples/sample_video/output/gobi_true_dna_video_2.mp4";
  await download2.saveAs(path2);
  console.log("Card 2 saved successfully to:", path2);
} catch (e) {
  console.log("Card 2 download error:", e.message);
}
