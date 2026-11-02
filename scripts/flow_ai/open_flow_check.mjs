const task = await taskSpace("AI Flow Video Production");
const page = task.page("p1");

// Go to Google Flow project
console.log("Navigating to Google Flow...");
await page.goto("https://flow.google.com/u/1/project/905a28b7-ceb4-4cf9-b92d-443050bd2d43");
await page.waitForLoadState("domcontentloaded");
await page.waitForTimeout(5000);

await page.screenshot({ path: "shots/ego_flow_current.png" });
console.log("Saved screenshot to shots/ego_flow_current.png");

// Also check what tools/menus exist for an image on canvas
const pageInfo = await page.evaluate(() => {
  return {
    title: document.title,
    url: window.location.href,
    buttons: Array.from(document.querySelectorAll('button')).map(b => ({
      ariaLabel: b.getAttribute('aria-label'),
      text: b.textContent.trim()
    })).filter(b => b.ariaLabel || b.text)
  };
});
console.log("Page info:", JSON.stringify(pageInfo, null, 2));
