const fs = await import("node:fs/promises");
const root = "/Volumes/Data/socnhotv/";
const prof = JSON.parse(await fs.readFile(root + "assets/soc_nho/soc_nho_profile.json", "utf8"));
const shots = [...prof.shot_list.sheet_1, ...prof.shot_list.sheet_2];
const BATCH = __BATCH__;
const task = await takeOverTaskSpace(1);
const page = task.page("p1");
const cnt = () => page.evaluate(() => [...document.querySelectorAll("img")].filter(i=>i.naturalWidth>=512).length);
for (const n of BATCH) {
  const before = await cnt();
  const p = `Tạo MỘT ảnh DUY NHẤT, chất lượng tuyệt đối, KHÔNG chia bảng, tỉ lệ 16:9. Nhân vật (giữ đúng tuyệt đối thông số): ${prof.prompt_lock}. Tư thế/góc máy: ${shots[n-1]}.`;
  await page.click("css=div[contenteditable=true]");
  await page.keyboard.insertText(p);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(8000);
  await page.waitForFunction((b) => [...document.querySelectorAll("img")].filter(i=>i.naturalWidth>=512).length > b && !!document.querySelector("button[aria-label*='giọng nói']"), before, { timeout: 150000 }).catch(()=>console.log("timeout", n));
  await page.waitForTimeout(3000);
  const r = await page.evaluate(() => { const a=[...document.querySelectorAll("img")].filter(i=>i.naturalWidth>=512); const i=a[a.length-1]; const c=document.createElement("canvas"); c.width=i.naturalWidth; c.height=i.naturalHeight; c.getContext("2d").drawImage(i,0,0); return {w:c.width,h:c.height,d:c.toDataURL("image/png").split(",")[1]}; });
  await fs.writeFile(root + `assets/soc_nho/soc_nho_${String(n).padStart(2,"0")}.png`, Buffer.from(r.d,"base64"));
  console.log(n, shots[n-1], r.w, r.h);
}
