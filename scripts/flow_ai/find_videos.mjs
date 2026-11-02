const task = await taskSpace("AI Flow Video Production");
const page = task.page("p2");

// Inspect the video cards on the canvas
const videoCards = await page.evaluate(() => {
  const containers = Array.from(document.querySelectorAll('flow-grid-tile-container, .cdk-drag, [role="button"]')).map(el => {
    const playIcon = el.querySelector('.play-icon, [data-mat-icon-name="play_circle"], mat-icon');
    const img = el.querySelector('img');
    const label = el.querySelector('.footer-left, .video-title, span');
    return {
      tagName: el.tagName,
      hasPlay: !!playIcon,
      imgSrc: img ? img.src : null,
      labelText: label ? label.textContent.trim() : null,
      rect: el.getBoundingClientRect()
    };
  }).filter(c => c.hasPlay && c.rect.width > 100);
  return videoCards = containers;
});

console.log("Video cards:", JSON.stringify(videoCards, null, 2));
