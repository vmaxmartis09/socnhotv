import fs from "fs";
import path from "path";

const root = path.resolve("tool/dashboard");

function replaceIn(rel, from, to) {
  const p = path.join(root, rel);
  let c = fs.readFileSync(p, "utf-8");
  if (c.includes(from)) {
    c = c.replace(from, to);
    fs.writeFileSync(p, c, "utf-8");
    console.log(`Updated ${rel}`);
  } else {
    console.log(`Not found in ${rel}`);
  }
}

// 1. StudioCanvas.tsx
replaceIn(
  "components/canvas/StudioCanvas.tsx",
  'className="z-40 w-[340px] rounded-lg border',
  'className="z-40 w-[min(340px,calc(100vw-32px))] rounded-lg border'
);

// 2. StudioNode.tsx
replaceIn(
  "components/canvas/StudioNode.tsx",
  'className="nodrag nowheel absolute z-30 w-[380px] rounded-xl border',
  'className="nodrag nowheel absolute z-30 w-[min(380px,calc(100vw-32px))] rounded-xl border'
);

// 3. UserBubble.tsx
replaceIn(
  "components/navigation/UserBubble.tsx",
  '? "w-[316px] max-h-[70dvh]',
  '? "w-[min(316px,calc(100vw-24px))] max-h-[70dvh]'
);
replaceIn(
  "components/navigation/UserBubble.tsx",
  ': "fixed md:absolute z-50 w-[300px] max-h-[82dvh]',
  ': "fixed md:absolute z-50 w-[min(300px,calc(100vw-24px))] max-h-[82dvh]'
);

console.log("Responsive adjustments applied.");
