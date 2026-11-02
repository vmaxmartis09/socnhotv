const task = await claimTaskSpace(4);
const page = task.page("p2");

const promptText = `nói chuyện trực tiếp với camera: "Xin chào mọi người nha! Em là Gobi đây. Hôm nay em lên set đồ lụa kết hợp cardigan này cực kỳ tôn dáng và sang chảnh cho các nàng nhé!" Natural expressive face, elegant posture, warm eye contact, soft natural head tilt, 4K realistic cinematic fashion video, fluid continuous movement, precise lip-sync for Vietnamese.`;

// Focus the editor
await page.evaluate(() => {
  const editor = document.querySelector('.ProseMirror, [contenteditable="true"]');
  if (editor) {
    editor.focus();
    // Use execCommand to insert text cleanly without breaking TrustedHTML
    document.execCommand('insertText', false, `nói chuyện trực tiếp với camera: "Xin chào mọi người nha! Em là Gobi đây. Hôm nay em lên set đồ lụa kết hợp cardigan này cực kỳ tôn dáng và sang chảnh cho các nàng nhé!" Natural expressive face, elegant posture, warm eye contact, soft natural head tilt, 4K realistic cinematic fashion video, fluid continuous movement, precise lip-sync for Vietnamese.`);
  }
});

await page.waitForTimeout(1000);

// Check if button is enabled
const canGenerate = await page.evaluate(() => {
  const btn = document.querySelector('button[aria-label="Bắt đầu tạo"]');
  const editor = document.querySelector('.ProseMirror, [contenteditable="true"]');
  return {
    editorText: editor ? editor.textContent : null,
    btnDisabled: btn ? btn.disabled : true,
    btnFound: !!btn
  };
});
console.log("Status before submit:", JSON.stringify(canGenerate, null, 2));

// If enabled, click Generate!
if (canGenerate.btnFound && !canGenerate.btnDisabled) {
  console.log("Clicking 'Bắt đầu tạo'...");
  await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label="Bắt đầu tạo"]');
    if (btn) btn.click();
  });
  console.log("Submitted prompt!");
} else {
  console.log("Button not enabled yet, trying Enter or keyboard...");
}

await page.waitForTimeout(3000);
await page.screenshot({ path: "shots/ego_gobi_new_adn_generating.png" });
console.log("Saved screenshot to shots/ego_gobi_new_adn_generating.png");
