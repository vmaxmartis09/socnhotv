const spaces = await listTaskSpaces();
console.log("Current spaces:", JSON.stringify(spaces, null, 2));

const task = await taskSpace("AI Flow Video Production");
const pageList = await task.pages();

for (const p of pageList) {
  const pageUrl = await p.url();
  console.log("Inspecting page:", p.label, pageUrl);
  if (pageUrl && pageUrl.includes("flow.google.com")) {
    await p.screenshot({ path: "shots/ego_gobi_generation_status.png" });
    console.log("Saved screenshot to ego_gobi_generation_status.png");
    
    const info = await p.evaluate(() => {
      const videos = Array.from(document.querySelectorAll('video')).map(v => ({
        src: v.src,
        currentSrc: v.currentSrc,
        duration: v.duration,
        paused: v.paused,
        offsetWidth: v.offsetWidth,
        offsetHeight: v.offsetHeight
      }));
      const textNodes = Array.from(document.querySelectorAll('*'))
        .filter(el => el.children.length === 0 && el.textContent.trim().length > 0)
        .map(el => el.textContent.trim());
      const buttons = Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).filter(Boolean);
      
      return {
        title: document.title,
        videos,
        hasGenerating: textNodes.some(t => t.includes("Tư duy") || t.includes("Đang tạo") || t.includes("Generating")),
        lastText: textNodes.slice(-30),
        buttons: buttons.slice(-15)
      };
    });
    console.log("Flow page details:", JSON.stringify(info, null, 2));
  }
}
