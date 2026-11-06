import type { Edge, Node } from "@xyflow/react";

export interface StepInfo {
  /** Thứ tự chạy (1 = chạy trước) */
  step: number;
  /** Cột (lớp) trái → phải */
  layer: number;
  /** Nằm trên trục chính (chuỗi dài nhất từ đầu tới thành phẩm) */
  main: boolean;
}

const GROUP_TYPE = "templateGroup";
const GROUP_PAD = 32;
const GROUP_HEAD = 64;
const NODE_W = 300;
const COL_GAP = 110;
const ROW_GAP = 56;
const FALLBACK_H = 380;
/** Chiều cao ước lượng khi thẻ chưa được đo (lúc mới tải): thẻ nhân vật có ảnh lớn nên cao hơn hẳn */
const FALLBACK_H_BY_TYPE: Record<string, number> = {
  character: 720,
  image_gen: 480,
  voice_tts: 340,
};

function heightOf(n: Node): number {
  const nodeType = (n.data as { nodeType?: string } | undefined)?.nodeType || "";
  return n.measured?.height ?? n.height ?? FALLBACK_H_BY_TYPE[nodeType] ?? FALLBACK_H;
}

/** Phân lớp theo đường dài nhất từ nguồn; trả về thứ tự bước và trục chính. */
export function analyzeGraph(allNodes: Node[], edges: Edge[]): Record<string, StepInfo> {
  const nodes = allNodes.filter((n) => n.type !== GROUP_TYPE);
  const ids = nodes.map((n) => n.id);
  const idSet = new Set(ids);
  const preds = new Map<string, string[]>(ids.map((i) => [i, []]));
  const succs = new Map<string, string[]>(ids.map((i) => [i, []]));
  for (const e of edges) {
    if (!idSet.has(e.source) || !idSet.has(e.target) || e.source === e.target) continue;
    preds.get(e.target)!.push(e.source);
    succs.get(e.source)!.push(e.target);
  }

  // Sắp xếp topo (Kahn), chống vòng bằng cách bỏ qua phần còn lại
  const indeg = new Map(ids.map((i) => [i, preds.get(i)!.length]));
  const queue = ids.filter((i) => indeg.get(i) === 0);
  const order: string[] = [];
  const layer = new Map<string, number>(ids.map((i) => [i, 0]));
  const depth = new Map<string, number>(ids.map((i) => [i, 1])); // độ dài chuỗi dài nhất kết thúc tại node
  const parent = new Map<string, string | null>(ids.map((i) => [i, null]));
  while (queue.length) {
    const u = queue.shift()!;
    order.push(u);
    for (const v of succs.get(u)!) {
      layer.set(v, Math.max(layer.get(v)!, layer.get(u)! + 1));
      if (depth.get(u)! + 1 > depth.get(v)!) {
        depth.set(v, depth.get(u)! + 1);
        parent.set(v, u);
      }
      indeg.set(v, indeg.get(v)! - 1);
      if (indeg.get(v) === 0) queue.push(v);
    }
  }
  for (const i of ids) if (!order.includes(i)) order.push(i);

  // Trục chính: truy ngược từ node có chuỗi dài nhất
  const main = new Set<string>();
  let tail = ids[0];
  for (const i of ids) if (depth.get(i)! > depth.get(tail)!) tail = i;
  for (let cur: string | null | undefined = tail; cur; cur = parent.get(cur)) main.add(cur);

  // Bước = thứ tự theo (lớp, vị trí dọc hiện tại)
  const y = new Map(nodes.map((n) => [n.id, n.position.y]));
  const ranked = [...ids].sort(
    (a, b) => layer.get(a)! - layer.get(b)! || (y.get(a) ?? 0) - (y.get(b) ?? 0)
  );
  const out: Record<string, StepInfo> = {};
  ranked.forEach((id, idx) => {
    out[id] = { step: idx + 1, layer: layer.get(id)!, main: main.has(id) };
  });
  return out;
}

/** Xếp các node thành cột trái → phải theo thứ tự chạy; trục chính nằm giữa. */
export function autoLayout<N extends Node>(allNodes: N[], edges: Edge[]): N[] {
  if (allNodes.length === 0) return allNodes;
  const groups = allNodes.filter((n) => n.type === GROUP_TYPE);
  if (groups.length > 0) return layoutWithGroups(allNodes, groups, edges);
  return layoutFlat(allNodes, edges);
}

/** Mỗi group tự xếp con bên trong (toạ độ tương đối) và co khung vừa nội dung. */
function layoutWithGroups<N extends Node>(allNodes: N[], groups: N[], edges: Edge[]): N[] {
  const out = new Map<string, N>();
  let cursorY = 40;
  for (const g of groups) {
    const kids = allNodes.filter((n) => n.parentId === g.id);
    const kidIds = new Set(kids.map((k) => k.id));
    const laid = layoutFlat(kids, edges.filter((e) => kidIds.has(e.source) && kidIds.has(e.target)));
    let maxX = 0;
    let maxY = 0;
    for (const k of laid) {
      const pos = { x: k.position.x - 40 + GROUP_PAD, y: k.position.y - 40 + GROUP_HEAD };
      out.set(k.id, { ...k, position: pos });
      maxX = Math.max(maxX, pos.x + NODE_W);
      maxY = Math.max(maxY, pos.y + heightOf(k));
    }
    const width = maxX + GROUP_PAD;
    const height = maxY + GROUP_PAD;
    out.set(g.id, { ...g, position: { x: 40, y: cursorY }, width, height, style: { ...(g.style || {}), width, height } });
    cursorY += height + 80;
  }
  const loose = allNodes.filter((n) => n.type !== GROUP_TYPE && !n.parentId);
  if (loose.length) {
    const xs = [...out.values()].filter((n) => n.type === GROUP_TYPE).map((n) => n.position.x + (n.width ?? 0));
    const offsetX = (xs.length ? Math.max(...xs) : 0) + 120;
    layoutFlat(loose, edges).forEach((n) => out.set(n.id, { ...n, position: { x: n.position.x + offsetX, y: n.position.y } }));
  }
  return allNodes.map((n) => out.get(n.id) ?? n);
}

function layoutFlat<N extends Node>(nodes: N[], edges: Edge[]): N[] {
  if (nodes.length === 0) return nodes;
  const info = analyzeGraph(nodes, edges);
  const maxLayer = Math.max(...Object.values(info).map((i) => i.layer));
  const columns: string[][] = Array.from({ length: maxLayer + 1 }, () => []);
  const byId = new Map(nodes.map((n) => [n.id, n]));
  for (const n of nodes) columns[info[n.id].layer].push(n.id);

  const parents = new Map<string, string[]>(nodes.map((n) => [n.id, []]));
  for (const e of edges) if (parents.has(e.target) && byId.has(e.source)) parents.get(e.target)!.push(e.source);

  // Thứ tự trong cột: trục chính trước, rồi theo trung bình vị trí cha để giảm chéo dây
  const rowIndex = new Map<string, number>();
  columns.forEach((col, ci) => {
    col.sort((a, b) => {
      const bary = (id: string) => {
        const ps = parents.get(id)!.filter((p) => rowIndex.has(p));
        return ps.length ? ps.reduce((s, p) => s + rowIndex.get(p)!, 0) / ps.length : (byId.get(id)!.position.y / 400);
      };
      return bary(a) - bary(b) || (byId.get(a)!.position.y - byId.get(b)!.position.y);
    });
    // trục chính lên giữa: đẩy node main về giữa cột
    if (ci > 0) {
      const mainIdx = col.findIndex((id) => info[id].main);
      if (mainIdx > 0) {
        const mid = Math.floor((col.length - 1) / 2);
        const [m] = col.splice(mainIdx, 1);
        col.splice(Math.min(mid, col.length), 0, m);
      }
    }
    col.forEach((id, i) => rowIndex.set(id, i));
  });

  const pos = new Map<string, { x: number; y: number }>();
  const heights = columns.map((col) => col.reduce((s, id) => s + heightOf(byId.get(id)!), 0) + ROW_GAP * Math.max(0, col.length - 1));
  const tallest = Math.max(...heights);
  columns.forEach((col, ci) => {
    let y = 40 + (tallest - heights[ci]) / 2;
    for (const id of col) {
      pos.set(id, { x: 40 + ci * (NODE_W + COL_GAP), y });
      y += heightOf(byId.get(id)!) + ROW_GAP;
    }
  });
  return nodes.map((n) => (pos.has(n.id) ? { ...n, position: pos.get(n.id)! } : n));
}

const MIN_GAP = 28;

/**
 * Khi một thẻ giãn ra (mở panel, thêm dòng…) thì đẩy các thẻ nằm chồng bên dưới xuống để không đè/cắt nhau.
 * Chỉ dịch thẻ bị chồng theo chiều dọc, theo thứ tự từ trên xuống; trả lại đúng mảng cũ nếu không có gì chồng.
 */
export function resolveOverlaps<N extends Node>(allNodes: N[]): N[] {
  const items = allNodes
    .filter((n) => n.type !== GROUP_TYPE && !n.parentId && n.measured?.height)
    .map((n) => ({ id: n.id, x: n.position.x, y: n.position.y, h: n.measured!.height as number, w: n.measured?.width ?? NODE_W }))
    .sort((a, b) => a.y - b.y || a.x - b.x);
  let moved = false;
  for (let j = 1; j < items.length; j++) {
    const b = items[j];
    for (let i = 0; i < j; i++) {
      const a = items[i];
      const overlapX = a.x < b.x + b.w && b.x < a.x + a.w;
      if (overlapX && b.y < a.y + a.h + MIN_GAP && b.y + b.h > a.y) {
        b.y = a.y + a.h + MIN_GAP;
        moved = true;
      }
    }
  }
  if (!moved) return allNodes;
  const newY = new Map(items.map((it) => [it.id, it.y]));
  return allNodes.map((n) => {
    const y = newY.get(n.id);
    return y !== undefined && Math.abs(y - n.position.y) > 0.5 ? { ...n, position: { ...n.position, y } } : n;
  });
}
