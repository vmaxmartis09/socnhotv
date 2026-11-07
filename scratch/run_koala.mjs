// ego-browser nodejs < file (đã thay koala/2/18). Một chat mới cho mỗi nhân vật; ảnh master tải lên làm tham chiếu.
const fs = await import("node:fs/promises");
const root = "/Volumes/Data/socnhotv/";
const CHAR = "koala", FROM = 2, TO = 18;
const dir = root + `data/projects/soc-nho-tv/characters/${CHAR}/`;
const prof = JSON.parse(await fs.readFile(dir + `${CHAR}_profile.json`, "utf8"));
const shots = JSON.parse(await fs.readFile(root + "scripts/dna/shots.json", "utf8"));
await fs.mkdir(dir + "dna", { recursive: true });
const task = await taskSpace("dna-characters");
const page = task.page("p1");
const f = (n) => dir + `dna/${CHAR}_${String(n).padStart(2,"0")}.png`;
const exists = async (p) => fs.access(p).then(()=>true,()=>false);
const srcs = () => page.evaluate(() => [...document.querySelectorAll("img")].filter(i=>i.naturalWidth>=512).map(i=>i.src));
await page.goto("https://gemini.google.com/app", {timeout:60000});
await page.waitForTimeout(3000);
const hasMaster = await exists(f(1));
if (hasMaster && FROM > 1) {
  await page.click("css=button[aria-label='Nội dung tải lên và công cụ']");
  await page.waitForSelector("loc=role:menuitem[name*='Tải tệp lên']");
  const ch = page.waitForFileChooser({ timeout: 15000 });
  await page.click("loc=role:menuitem[name*='Tải tệp lên']");
  await (await ch).setFiles(f(1));
  await page.waitForTimeout(5000);
}
let fails = 0;
for (let n = FROM; n <= TO; n++) {
  if (await exists(f(n))) { console.log("skip", n); continue; }
  const seen = new Set(await srcs());
  const p = (n === 1 && !hasMaster)
    ? `Tạo MỘT ảnh DUY NHẤT, KHÔNG chia bảng, tỉ lệ 16:9, nền trắng trơn sáng, 3D Pixar. Nhân vật (giữ đúng tuyệt đối thông số, chiều cao ${prof.height_cm}cm, tỉ lệ đầu/thân ${prof.head_body_ratio}): ${prof.prompt_lock}. Tư thế/góc máy: ${shots[0]}. Nhân vật này là master DNA cho cả loạt.`
    : `Giữ NGUYÊN 100% nhân vật ở ảnh master (cùng khuôn mặt, màu lông, trang phục, tỉ lệ cơ thể). Tạo MỘT ảnh DUY NHẤT, KHÔNG chia bảng, 16:9, nền trắng trơn sáng, 3D Pixar. Tư thế/góc máy: ${shots[n-1]}.`;
  await page.click("css=div[contenteditable=true]");
  await page.keyboard.insertText(p);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(8000);
  await page.waitForFunction((s) => [...document.querySelectorAll("img")].some(i=>i.naturalWidth>=512 && !s.includes(i.src)), seen.size ? [...seen] : [], { timeout: 150000 }).catch(()=>{});
  await page.waitForTimeout(5000);
  const r = await page.evaluate((s) => { const a=[...document.querySelectorAll("img")].filter(i=>i.naturalWidth>=512 && !s.includes(i.src)); const i=a[a.length-1]; if(!i) return null; const c=document.createElement("canvas"); c.width=i.naturalWidth; c.height=i.naturalHeight; c.getContext("2d").drawImage(i,0,0); return {w:c.width,h:c.height,d:c.toDataURL("image/png").split(",")[1]}; }, [...seen]);
  if (!r) { console.log("NO NEW IMAGE", n, await page.evaluate(() => document.body.innerText.slice(-250))); if (++fails >= 2) break; n--; continue; }
  await fs.writeFile(f(n), Buffer.from(r.d,"base64"));
  console.log("saved", CHAR, n, r.w, r.h);
}
