const task = await claimTaskSpace(4);
const page = task.page("p2");

// Take screenshot of current state
await page.screenshot({ path: "shots/ego_gobi_new_adn_render_status.png" });

// Inspect the video cards on canvas
const cards = await page.evaluate(() => {
  const containers = Array.from(document.querySelectorAll('flow-grid-tile-container, .cdk-drag')).map(el => {
    const playIcon = el.querySelector('.play-icon, [data-mat-icon-name="play_circle"], mat-icon');
    const img = el.querySelector('img');
    const label = el.querySelector('.footer-left, .video-title, span');
    const progress = el.querySelector('mat-progress-bar, .progress-bar, mat-spinner');
    return {
      tagName: el.tagName,
      hasPlay: !!playIcon,
      imgSrc: img ? img.src : null,
      labelText: label ? label.textContent.trim() : null,
      hasProgress: !!progress,
      rect: el.getBoundingClientRect()
    };
  });
  return containers;
});

console.log("Canvas cards count:", cards.length);
console.log("Canvas cards summary:", JSON.stringify(cards.slice(0, 5), null, 2));
