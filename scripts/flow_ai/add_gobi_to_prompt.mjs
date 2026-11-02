const task = await claimTaskSpace(4);
const page = task.page("p2");

// 1. Right-click on Gobi (ADN Mới)
const res = await page.evaluate(() => {
  const nameEl = document.querySelector('.character-tile-name');
  if (!nameEl) return { error: "No character-tile-name" };
  const tile = nameEl.closest('flow-grid-tile-container') || nameEl;
  const rect = tile.getBoundingClientRect();
  tile.dispatchEvent(new MouseEvent('contextmenu', {
    bubbles: true,
    cancelable: true,
    clientX: rect.x + rect.width / 2,
    clientY: rect.y + rect.height / 2
  }));
  return { success: true, text: nameEl.textContent };
});
console.log("Right click:", res);

await page.waitForTimeout(1000);

// 2. Click "Thêm vào câu lệnh"
const clickedAdd = await page.evaluate(() => {
  const items = Array.from(document.querySelectorAll('[role="menuitem"], .mat-mdc-menu-item'));
  const addItem = items.find(i => i.textContent.includes("Thêm vào câu lệnh"));
  if (addItem) {
    addItem.click();
    return true;
  }
  return false;
});
console.log("Clicked 'Thêm vào câu lệnh':", clickedAdd);

await page.waitForTimeout(1000);
await page.screenshot({ path: "shots/ego_gobi_added_to_prompt.png" });

// Inspect the prompt box
const promptBox = await page.evaluate(() => {
  const textBox = document.querySelector('[contenteditable="true"]');
  return {
    html: textBox ? textBox.innerHTML : null,
    text: textBox ? textBox.textContent : null
  };
});
console.log("Prompt box after add:", JSON.stringify(promptBox, null, 2));
