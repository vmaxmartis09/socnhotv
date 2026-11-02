const task = await claimTaskSpace(4);
const page = task.page("p2");

// 1. Close the video player
console.log("Closing video player...");
await page.evaluate(() => {
  const backBtn = document.querySelector('button[aria-label="Nút quay lại để quay về trang trước"]') ||
                  document.querySelector('button[aria-label="Đã chỉnh sửa xong cảnh"]');
  if (backBtn) backBtn.click();
});

await page.waitForTimeout(2000);

// 2. Find old Gobi card and delete it
console.log("Looking for old Gobi card...");
const deleted = await page.evaluate(async () => {
  const names = Array.from(document.querySelectorAll('.character-tile-name'));
  const oldGobi = names.find(c => c.textContent.trim() === "Gobi");
  if (!oldGobi) return { error: "Old Gobi not found" };
  
  const tile = oldGobi.closest('flow-grid-tile-container') || oldGobi;
  const rect = tile.getBoundingClientRect();
  
  // Right click
  tile.dispatchEvent(new MouseEvent('contextmenu', {
    bubbles: true,
    cancelable: true,
    clientX: rect.x + rect.width / 2,
    clientY: rect.y + rect.height / 2
  }));
  
  return { success: true, rect };
});
console.log("Right click result:", deleted);

await page.waitForTimeout(1000);

// Click delete in menu
await page.evaluate(() => {
  const items = Array.from(document.querySelectorAll('[role="menuitem"], .mat-mdc-menu-item'));
  const delItem = items.find(i => i.textContent.includes("Xoá") || i.textContent.includes("delete"));
  if (delItem) {
    delItem.click();
  }
});

await page.waitForTimeout(1000);

// Check if a confirm dialog appeared
await page.evaluate(() => {
  const confirmBtn = Array.from(document.querySelectorAll('button')).find(b => 
    b.textContent.trim() === "Xoá" || b.textContent.trim() === "Xoá bỏ" || b.textContent.trim() === "Delete"
  );
  if (confirmBtn) {
    confirmBtn.click();
  }
});

await page.waitForTimeout(2000);
await page.screenshot({ path: "shots/ego_after_delete_old_gobi.png" });
console.log("Screenshot saved to shots/ego_after_delete_old_gobi.png");

// List remaining characters
const remaining = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('.character-tile-name')).map(el => el.textContent.trim());
});
console.log("Remaining characters:", remaining);
