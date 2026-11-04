import fs from "node:fs/promises";
import path from "node:path";

function cleanFacebookUrl(rawUrl) {
  if (!rawUrl) return null;
  try {
    const parsed = new URL(rawUrl);
    if (parsed.hostname.includes("l.facebook.com") && parsed.pathname.includes("/l.php")) {
      const target = parsed.searchParams.get("u");
      if (target) return cleanFacebookUrl(target);
    }
    // Remove fbclid and other tracking params
    parsed.searchParams.delete("fbclid");
    parsed.searchParams.delete("__tn__");
    parsed.searchParams.delete("mibextid");
    return parsed.toString();
  } catch (e) {
    return rawUrl;
  }
}

function classifyKind(url) {
  if (!url) return "note";
  if (url.includes("/share/r/") || url.includes("/reel/")) return "fb_reel";
  if (url.includes("/share/v/") || url.includes("/watch/") || url.includes("facebook.com/video")) return "fb_video";
  if (url.includes("/share/p/") || url.includes("/posts/")) return "fb_post";
  if (url.includes("youtube.com") || url.includes("youtu.be")) return "youtube";
  if (url.includes("tiktok.com")) return "tiktok";
  if (url.includes("messenger_media")) return "image";
  return "external_tool";
}

async function run() {
  const task = await taskSpace(25);
  const page = task.page("p1");

  console.log("Navigating fresh to Messenger thread...");
  await page.goto("https://www.facebook.com/messages/t/100014084354965", { waitUntil: "domcontentloaded" });
  await new Promise(r => setTimeout(r, 4000));

  console.log("Starting full harvest...");

  // We want to capture from bottom (newest) to top (oldest).
  // First, scroll to bottom
  await page.evaluate(() => {
    const s = document.querySelector(".x78zum5.xdt5ytf.x1iyjqo2.x6ikm8r.x1odjw0f.x8du1vd.x16o0dkt") ||
              Array.from(document.querySelectorAll("div")).find(d => d.scrollHeight > d.clientHeight && d.clientHeight > 300);
    if (s) s.scrollTop = s.scrollHeight;
  });
  await new Promise(r => setTimeout(r, 1500));

  // Map to hold items. Key = cleaned URL or unique note key
  // We will preserve chronological / reverse-chronological order
  const rawItems = [];
  const seenUrls = new Set();

  let prevScrollHeight = 0;
  let noChangeCount = 0;
  let totalSteps = 0;
  const MAX_STEPS = 35; // sufficient to cover 24 months

  while (totalSteps < MAX_STEPS && noChangeCount < 3) {
    totalSteps++;
    const batch = await page.evaluate(() => {
      const scrollable = document.querySelector(".x78zum5.xdt5ytf.x1iyjqo2.x6ikm8r.x1odjw0f.x8du1vd.x16o0dkt") ||
                         Array.from(document.querySelectorAll("div")).find(d => d.scrollHeight > d.clientHeight && d.clientHeight > 300);
      if (!scrollable) return null;

      const container = document.querySelector(".x78zum5.xdt5ytf.x1iyjqo2.x2lah0s.xl56j7k.x121v3j4");
      if (!container) return null;

      const captured = [];
      Array.from(container.children).forEach(child => {
        const text = child.innerText.trim();
        const links = Array.from(child.querySelectorAll("a[href]")).map(a => ({
          href: a.href,
          text: a.innerText.trim().replace(/\n+/g, " "),
          ariaLabel: a.getAttribute("aria-label")
        }));

        const timeLabels = Array.from(child.querySelectorAll("[aria-label]"))
          .map(el => el.getAttribute("aria-label"))
          .filter(l => l && (l.includes("lúc") || l.includes("trước") || l.includes("ngày") || l.includes("tháng") || l.includes("năm")));

        captured.push({ text, links, timeLabels });
      });

      const h = scrollable.scrollHeight;
      const t = scrollable.scrollTop;
      scrollable.scrollTop = 0; // scroll up to load older
      return { captured, h, t };
    });

    if (!batch) break;

    batch.captured.forEach(entry => {
      if (entry.links.length > 0) {
        entry.links.forEach(l => {
          if (l.href.includes("/messages/") || l.href.match(/facebook\.com\/\d+\/?$/)) return;
          const cleaned = cleanFacebookUrl(l.href);
          if (!seenUrls.has(cleaned)) {
            seenUrls.add(cleaned);
            rawItems.push({
              url: cleaned,
              raw_url: l.href,
              preview_title: l.text || l.ariaLabel || "",
              time_labels: entry.timeLabels,
              context_text: entry.text,
              order_found: rawItems.length
            });
          }
        });
      } else if (entry.text.length > 10 && !entry.text.includes("Đang tải")) {
        const noteKey = "note:" + entry.text.slice(0, 40);
        if (!seenUrls.has(noteKey)) {
          seenUrls.add(noteKey);
          rawItems.push({
            url: null,
            raw_url: null,
            preview_title: entry.text.slice(0, 60),
            time_labels: entry.timeLabels,
            context_text: entry.text,
            is_note: true,
            order_found: rawItems.length
          });
        }
      }
    });

    console.log(`Step ${totalSteps}: total unique items = ${rawItems.length}, height = ${batch.h}`);

    if (batch.h === prevScrollHeight) {
      noChangeCount++;
    } else {
      noChangeCount = 0;
    }
    prevScrollHeight = batch.h;
    await new Promise(r => setTimeout(r, 2000));
  }

  console.log(`Harvest complete. Total items discovered: ${rawItems.length}`);

  // Now, sort items from NEWEST to OLDEST.
  // Note: Since we started scanning from the bottom, the first items captured were the newest!
  // Let's verify and assign seq = 1..N
  const queue = rawItems.map((item, idx) => {
    const kind = item.is_note ? "note" : classifyKind(item.url);
    const message_time = item.time_labels && item.time_labels.length > 0 
      ? item.time_labels[0].replace(/^Nhập,\s*/, "").replace(/^Tin nhắn do Bạn gửi\s*/, "") 
      : "recent";
    
    // Separate user note if present in context_text
    let user_note = "";
    if (item.context_text && item.context_text.length > 0) {
      const lines = item.context_text.split("\n").map(l => l.trim()).filter(Boolean);
      // If lines contain something other than preview title or "Bạn đã gửi"
      user_note = lines.filter(l => !l.includes("Bạn đã gửi") && !l.includes("Facebook") && !l.includes(item.preview_title)).join(" | ");
    }

    return {
      seq: idx + 1,
      message_time,
      raw_url: item.raw_url || item.url,
      clean_url: item.url,
      kind,
      preview_title: item.preview_title,
      preview_source: item.preview_title.includes("Facebook") ? "Facebook" : (item.url ? new URL(item.url).hostname : ""),
      user_note: user_note || null,
      context_text: item.context_text
    };
  });

  const harvestDir = "/Volumes/Data/socnhotv/data/shared/knowledge/video_craft/harvest";
  await fs.mkdir(harvestDir, { recursive: true });

  const queueLines = queue.map(q => JSON.stringify(q)).join("\n");
  await fs.writeFile(path.join(harvestDir, "queue.jsonl"), queueLines + "\n", "utf-8");

  const state = {
    indexed_at: new Date().toISOString(),
    total_indexed: queue.length,
    newest_seq: 1,
    oldest_seq: queue.length,
    cursor_seq: 1,
    status: "indexed"
  };
  await fs.writeFile(path.join(harvestDir, "state.json"), JSON.stringify(state, null, 2), "utf-8");

  console.log(`Saved queue.jsonl and state.json with ${queue.length} items.`);
}

run().catch(console.error);
