const task = await taskSpace("AI Flow Video Production");
const page = task.page("p2");

await page.evaluate(() => {
  const cards = Array.from(document.querySelectorAll('flow-grid-tile-container'));
  const personCard = cards.find(c => c.textContent.includes("Person talking to camera"));
  if (personCard) {
    personCard.click();
  }
});

await page.waitForTimeout(2000);
await page.screenshot({ path: "shots/ego_video_player_opened.png" });

const videoInfo = await page.evaluate(() => {
  const v = document.querySelector('video');
  const buttons = Array.from(document.querySelectorAll('button')).map(b => ({
    text: b.textContent.trim(),
    ariaLabel: b.getAttribute('aria-label'),
    title: b.getAttribute('title')
  }));
  return {
    videoSrc: v ? v.src : null,
    videoCurrentSrc: v ? v.currentSrc : null,
    videoDuration: v ? v.duration : null,
    buttons: buttons.filter(b => b.text || b.ariaLabel || b.title)
  };
});

console.log("Video info:", JSON.stringify(videoInfo, null, 2));
