import type {
  NodeDefinition,
  PortType,
  Graph,
  GraphValidationResult,
  GraphRunSummary,
  RunMode,
  RunPolicy,
} from "./core-contracts";
import { CORE_URL } from "./repositories/core";

/**
 * Quy tắc tương thích cổng kết nối (đồng bộ 100% với is_port_compatible trong types.py).
 */
export function isPortCompatible(
  sourceType: PortType,
  targetType: PortType
): boolean {
  if (sourceType === targetType) return true;
  if (sourceType === "image" && targetType === "image[]") return true;
  // Lời thoại có cấu trúc nối được vào cổng văn bản (Core ghép thành "Tên: câu")
  if (sourceType === "dialogue" && targetType === "text") return true;
  return false;
}

/**
 * Danh mục 13 loại node chuẩn từ Core (dùng làm bản dự phòng khi Core chưa bật).
 * Khi Core chạy, giao diện luôn lấy trực tiếp từ GET /node-types.
 */
export const FALLBACK_NODE_TYPES: NodeDefinition[] = [
  {
    typeName: "text",
    displayName: "Văn bản / Prompt",
    category: "Input",
    description: "Nhập văn bản tự do, ý tưởng hoặc prompt tùy chỉnh",
    inputPorts: [],
    outputPorts: [
      { name: "text", portType: "text", description: "Văn bản đầu ra", required: true },
    ],
    defaultParams: { content: "" },
    mockable: true,
  },
  {
    typeName: "image",
    displayName: "Tải ảnh / Thư viện",
    category: "Input",
    description: "Tải ảnh lên hoặc chọn ảnh từ thư viện tài nguyên",
    inputPorts: [],
    outputPorts: [
      { name: "image", portType: "image", description: "Ảnh đã chọn", required: true },
    ],
    defaultParams: { uri: "/demo/scenes/canh_01.jpg" },
    mockable: true,
  },
  {
    typeName: "character",
    displayName: "Nhân vật (Character Bible)",
    category: "Identity",
    description: "Chọn nhân vật của dự án (DNA ảnh tham chiếu, prompt lock, voiceId, bộ nhớ)",
    inputPorts: [],
    outputPorts: [
      { name: "character", portType: "character", description: "Dữ liệu hồ sơ nhân vật", required: true },
      { name: "reference_images", portType: "image[]", description: "Danh sách ảnh tham chiếu DNA", required: true },
    ],
    defaultParams: { characterId: "soc_nho" },
    mockable: true,
  },
  {
    typeName: "script",
    displayName: "Kịch bản phân cảnh",
    category: "Structure",
    description: "Biến kịch bản thành danh sách cảnh có prompt ảnh, chuyển động và lời thoại",
    inputPorts: [
      { name: "text", portType: "text", description: "Ý tưởng hoặc cốt truyện", required: true },
    ],
    outputPorts: [
      { name: "scenes", portType: "scenes", description: "Danh sách phân cảnh cấu trúc", required: true },
      { name: "prompt", portType: "text", description: "Prompt tạo ảnh/video theo cảnh", required: true },
      { name: "dialogue", portType: "text", description: "Lời thoại theo cảnh", required: true },
      { name: "lines", portType: "dialogue", description: "Lời thoại có người nói: từng câu kèm nhân vật, shot, mốc thời gian", required: true },
    ],
    defaultParams: { targetSceneCount: 6, targetDurationSec: 45 },
    mockable: true,
  },
  {
    typeName: "vision_analyze",
    displayName: "Phân tích Video / Ảnh",
    category: "Intelligence",
    description: "Phân tích cấu trúc video, góc quay, nhịp cảnh và lời thoại qua model nhìn",
    inputPorts: [
      { name: "video", portType: "video", description: "Video nguồn để phân tích", required: false },
      { name: "image", portType: "image", description: "Ảnh nguồn để phân tích", required: false },
    ],
    outputPorts: [
      { name: "script", portType: "script", description: "Kịch bản cấu trúc trích xuất", required: true },
      { name: "scenes", portType: "scenes", description: "Danh sách phân cảnh trích xuất", required: true },
    ],
    defaultParams: { goal: "extract_scenes_and_dialogue" },
    mockable: true,
  },
  {
    typeName: "quality_check",
    displayName: "Kiểm tra chất lượng (Gate)",
    category: "Quality",
    description: "Chấm điểm ảnh trước khi tốn tiền tạo video",
    inputPorts: [
      { name: "media", portType: "image", description: "Ảnh hoặc video cần thẩm định", required: false },
      { name: "criteria", portType: "text", description: "Tiêu chí thẩm định", required: false },
      { name: "text", portType: "text", description: "Lời nói / kịch bản / prompt cần kiểm chính sách", required: false },
      { name: "captions", portType: "captions", description: "Caption cần kiểm chính sách", required: false },
      { name: "scenes", portType: "scenes", description: "Danh sách cảnh cần kiểm", required: false },
      { name: "policy", portType: "policy", description: "Chính sách riêng (mặc định: chính sách của dự án)", required: false },
    ],
    outputPorts: [
      { name: "media", portType: "image", description: "Media đã qua kiểm duyệt", required: true },
      { name: "pass_fail", portType: "text", description: "Kết quả đạt/không đạt + điểm + vi phạm chính sách", required: true },
      { name: "violations", portType: "text", description: "Danh sách từ ngữ vi phạm chính sách", required: false },
    ],
    defaultParams: {
      thresholdScore: 0.85,
      maxRetries: 2,
      policyAutoScan: true,
      criteria: "Nhân vật Sóc Nhỏ 100cm, áo phông vàng, quần short đen, đuôi xù lớn, không chữ lạ",
    },
    mockable: true,
  },
  {
    typeName: "policy",
    displayName: "Chính sách nội dung",
    category: "Quality",
    description: "Chính sách của dự án (từ cấm, mức vi phạm) — nối vào node Kiểm tra chất lượng hoặc để mặc định theo dự án",
    inputPorts: [],
    outputPorts: [{ name: "policy", portType: "policy", description: "Chính sách nội dung đang áp dụng", required: true }],
    defaultParams: { extraTerms: [], extraSeverity: "block" },
    mockable: true,
  },
  {
    typeName: "image_gen",
    displayName: "Tạo ảnh AI",
    category: "Generation",
    description: "Tạo ảnh từ prompt mô tả kết hợp các ảnh tham chiếu nhận diện nhân vật",
    inputPorts: [
      { name: "prompt", portType: "text", description: "Prompt mô tả cảnh", required: true },
      { name: "references", portType: "image[]", description: "Ảnh tham chiếu DNA", required: false },
      { name: "scenes", portType: "scenes", description: "Lặp theo cảnh: nối danh sách cảnh để tạo mỗi cảnh 1 ảnh", required: false },
    ],
    outputPorts: [
      { name: "images", portType: "image[]", description: "Danh sách ảnh sinh ra", required: true },
      { name: "image", portType: "image", description: "Ảnh đại diện / khung đầu tiên sinh ra", required: true },
      { name: "scenes", portType: "scenes", description: "Danh sách cảnh đã gắn ảnh (khi lặp theo cảnh)", required: false },
    ],
    defaultParams: {
      model: "gemini-2.5-flash-image",
      aspectRatio: "9:16",
      resolution: "1080p",
      n: 1,
      seed: null,
    },
    mockable: true,
  },
  {
    typeName: "image_edit",
    displayName: "Sửa ảnh / Tách trang phục",
    category: "Generation",
    description: "Chỉnh sửa chi tiết hoặc thay đổi trang phục trên ảnh gốc",
    inputPorts: [
      { name: "image", portType: "image", description: "Ảnh gốc cần sửa", required: true },
      { name: "references", portType: "image[]", description: "Ảnh tham chiếu mới", required: false },
      { name: "prompt", portType: "text", description: "Mô tả chỉnh sửa", required: false },
    ],
    outputPorts: [
      { name: "image", portType: "image", description: "Ảnh kết quả sau sửa", required: true },
    ],
    defaultParams: { model: "gemini-2.5-flash-image", aspectRatio: "9:16" },
    mockable: true,
  },
  {
    typeName: "video_gen",
    displayName: "Tạo video chuyển động",
    category: "Generation",
    description: "Biến ảnh khung đầu thành video chuyển động 3D qua model Veo / LTX",
    inputPorts: [
      { name: "first_frame", portType: "image", description: "Ảnh khung đầu (First frame)", required: false },
      { name: "image", portType: "image", description: "Ảnh khung đầu (alias)", required: false },
      { name: "prompt", portType: "text", description: "Prompt chuyển động camera", required: false },
      { name: "references", portType: "image[]", description: "Ảnh tham chiếu phụ", required: false },
    ],
    outputPorts: [
      { name: "video", portType: "video", description: "Clip video sinh ra", required: true },
    ],
    defaultParams: {
      model: "google-veo-2",
      durationSec: 8,
      aspectRatio: "9:16",
      hasAudio: false,
    },
    mockable: true,
  },
  {
    typeName: "voice_tts",
    displayName: "Văn bản thành giọng nói",
    category: "Audio",
    description: "Đọc lời thoại kịch bản bằng giọng Sóc Nhỏ (soc-nho) chuẩn ngữ điệu cảm xúc",
    inputPorts: [
      { name: "text", portType: "text", description: "Lời thoại cần đọc", required: true },
      { name: "character", portType: "character", description: "Hồ sơ nhân vật chứa voiceId", required: false },
    ],
    outputPorts: [
      { name: "audio", portType: "audio", description: "Tệp âm thanh MP3 đã master -14 LUFS", required: true },
    ],
    defaultParams: {
      voiceId: "soc-nho",
      tempo: 1.1,
      mastering: true,
    },
    mockable: true,
  },
  {
    typeName: "captions",
    displayName: "Phụ đề Karaoke (Whisper)",
    category: "Audio",
    description: "Trích xuất phụ đề từng từ khớp mốc thời gian (Word-level timestamps)",
    inputPorts: [
      { name: "audio", portType: "audio", description: "Tệp âm thanh thoại", required: true },
      { name: "text", portType: "text", description: "Text đối chiếu chuẩn", required: false },
    ],
    outputPorts: [
      { name: "captions", portType: "captions", description: "Dữ liệu phụ đề mốc thời gian", required: true },
    ],
    defaultParams: { language: "vi", style: "kinetic_karaoke" },
    mockable: true,
  },
  {
    typeName: "hyperframes_render",
    displayName: "Dựng phim HyperFrames",
    category: "Composition",
    description: "Ghép các phân cảnh, chạy phụ đề karaoke, chèn BGM ducking chuẩn Safe Zone 9:16",
    inputPorts: [
      { name: "scenes", portType: "scenes", description: "Cấu trúc các cảnh", required: false },
      { name: "video", portType: "video", description: "Video clip đầu vào", required: false },
      { name: "audio", portType: "audio", description: "Thoại chính voiceover", required: false },
      { name: "captions", portType: "captions", description: "Phụ đề karaoke", required: false },
      { name: "bgm", portType: "audio", description: "Nhạc nền BGM", required: false },
    ],
    outputPorts: [
      { name: "video", portType: "video", description: "Video thành phẩm MP4", required: true },
    ],
    defaultParams: {
      aspectRatio: "9:16",
      template: "default_cartoon",
      safeZonePaddingTop: 180,
      safeZonePaddingBottom: 320,
      duckingLevel: 0.25,
    },
    mockable: true,
  },
  {
    typeName: "export",
    displayName: "Xuất & Phân phối",
    category: "Output",
    description: "Xuất video hoàn chỉnh vào thư mục output/ và tạo manifest đóng gói",
    inputPorts: [
      { name: "video", portType: "video", description: "Video cần xuất bản", required: true },
    ],
    outputPorts: [
      { name: "manifest", portType: "composition", description: "Manifest thành phẩm", required: true },
    ],
    defaultParams: {
      platforms: ["tiktok", "youtube"],
      outputFileName: "soc_nho_tap_01.mp4",
    },
    mockable: true,
  },
  {
    typeName: "character_image",
    displayName: "Nhân vật từ ảnh",
    category: "Identity",
    description: "Dùng một ảnh bất kỳ làm nhân vật tham chiếu, không cần tạo hồ sơ đầy đủ",
    inputPorts: [],
    outputPorts: [
      { name: "image", portType: "image", description: "Ảnh nhân vật", required: true },
      { name: "reference_images", portType: "image[]", description: "Ảnh tham chiếu nhân vật", required: true },
    ],
    defaultParams: { uri: "", name: "" },
    mockable: true,
  },
  {
    typeName: "scene",
    displayName: "Cảnh",
    category: "Structure",
    description: "Ghép một ảnh và lời thoại thành một cảnh để dựng phim",
    inputPorts: [
      { name: "image", portType: "image", description: "Ảnh của cảnh", required: true },
      { name: "text", portType: "text", description: "Lời thoại hoặc mô tả cảnh", required: false },
    ],
    outputPorts: [
      { name: "scenes", portType: "scenes", description: "Cảnh đã ghép", required: true },
      { name: "image", portType: "image", description: "Ảnh của cảnh", required: true },
    ],
    defaultParams: { title: "Cảnh mới", durationSec: 6 },
    mockable: true,
  },
  {
    typeName: "transition",
    displayName: "Chuyển cảnh",
    category: "Structure",
    description: "Đặt kiểu chuyển cảnh (mờ dần, trượt, cắt) giữa các cảnh",
    inputPorts: [
      { name: "scenes", portType: "scenes", description: "Các cảnh cần chuyển tiếp", required: true },
    ],
    outputPorts: [
      { name: "scenes", portType: "scenes", description: "Các cảnh kèm chuyển cảnh", required: true },
    ],
    defaultParams: { style: "fade", durationSec: 0.5 },
    mockable: true,
  }
];

export function estimateNodeCostUsd(
  typeName: string,
  params: Record<string, any>,
  isMockMode: boolean,
  runPolicy?: RunPolicy
): number {
  if (isMockMode) return 0.0;
  if (runPolicy) {
    if (typeName === "image_gen" || typeName === "image_edit") {
      if (runPolicy.image === "mock") return 0.0;
    }
    if (typeName === "video_gen") {
      if (runPolicy.video === "off" || runPolicy.video === "mock") return 0.0;
    }
    if (typeName === "tts" || typeName === "voice_clone") {
      if (runPolicy.voice === "local" || runPolicy.voice === "mock") return 0.0;
    }
  }
  const model = String(params.model || "").toLowerCase();
  // Nguồn free / local theo hợp đồng C1/C3
  if (
    model.includes("pollinations") ||
    model.includes("cloudflare") ||
    model.includes("mflux") ||
    model.includes("local") ||
    model === "mock-image" ||
    model === "mock-video"
  ) {
    return 0.0;
  }
  if (typeName === "image_gen" || typeName === "image_edit") {
    const n = Number(params.n || 1);
    const m = String(params.model || "gemini-2.5-flash-image");
    const rate = m.includes("flux-schnell")
      ? 0.003
      : m.includes("flux-pro")
        ? 0.04
        : m.includes("kontext")
          ? 0.04
          : 0.03;
    return Number((rate * n).toFixed(4));
  }
  if (typeName === "video_gen") {
    const dur = Number(params.durationSec || 8);
    const m = String(params.model || "google-veo-2");
    const rate = m.includes("ltx")
      ? 0.04
      : m.includes("kling")
        ? 0.084
        : m.includes("veo-3")
          ? 0.4
          : 0.15;
    return Number((dur * rate).toFixed(4));
  }
  if (typeName === "quality_check" || typeName === "vision_analyze") {
    return 0.005;
  }
  return 0.0;
}

export async function checkCoreHealth(): Promise<{
  online: boolean;
  version: string;
  repoRoot?: string;
  outdated?: boolean;
}> {
  try {
    const res = await fetch(`${CORE_URL}/health`, { cache: "no-store" });
    if (!res.ok) return { online: false, version: "–" };
    const data = await res.json();
    let outdated = false;
    try {
      const tmplRes = await fetch(`${CORE_URL}/video/templates`, { cache: "no-store" });
      if (!tmplRes.ok) outdated = true;
    } catch {
      outdated = true;
    }
    return {
      online: data.status === "healthy",
      version: data.version || "0.1.0",
      repoRoot: data.repo_root,
      outdated,
    };
  } catch {
    return { online: false, version: "–" };
  }
}

export async function fetchNodeTypes(): Promise<{
  definitions: NodeDefinition[];
  fromCore: boolean;
}> {
  try {
    const res = await fetch(`${CORE_URL}/node-types`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed");
    const defs = (await res.json()) as NodeDefinition[];
    if (Array.isArray(defs) && defs.length > 0) {
      return { definitions: defs, fromCore: true };
    }
  } catch {
    // Fallback to FALLBACK_NODE_TYPES
  }
  return { definitions: FALLBACK_NODE_TYPES, fromCore: false };
}

export async function fetchCustomNodeTypes(projectId: string): Promise<NodeDefinition[]> {
  try {
    const res = await fetch(`${CORE_URL}/custom-node-types?projectId=${encodeURIComponent(projectId)}`, { cache: "no-store" });
    if (!res.ok) return [];
    const list = (await res.json()) as NodeDefinition[];
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
}

export async function saveCustomNodeType(
  def: NodeDefinition,
  scope: "project" | "shared",
  projectId: string
): Promise<void> {
  const res = await fetch(
    `${CORE_URL}/custom-node-types?scope=${scope}&projectId=${encodeURIComponent(projectId)}`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(def) }
  );
  if (!res.ok) throw new Error((await res.text()) || "Lưu loại node thất bại");
}

export async function deleteCustomNodeType(typeName: string, scope: "project" | "shared", projectId: string): Promise<void> {
  await fetch(
    `${CORE_URL}/custom-node-types/${encodeURIComponent(typeName)}?scope=${scope}&projectId=${encodeURIComponent(projectId)}`,
    { method: "DELETE" }
  );
}

export async function validateGraphWithCore(
  projectId: string,
  graph: Graph,
  nodeCatalog: NodeDefinition[]
): Promise<GraphValidationResult> {
  try {
    const res = await fetch(`${CORE_URL}/graph/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph),
    });
    if (res.ok) {
      return (await res.json()) as GraphValidationResult;
    }
  } catch {
    // Local validation fallback when Core is offline
  }
  return validateGraphLocally(graph, nodeCatalog);
}

export function validateGraphLocally(
  graph: Graph,
  nodeCatalog: NodeDefinition[]
): GraphValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const defMap = new Map(nodeCatalog.map((d) => [d.typeName, d]));
  const nodeMap = new Map(graph.nodes.map((n) => [n.id, n]));
  const adj = new Map<string, string[]>();
  const inDegree = new Map<string, number>();
  const connectedTargetPorts = new Set<string>();

  for (const n of graph.nodes) {
    adj.set(n.id, []);
    inDegree.set(n.id, 0);
  }

  for (const e of graph.edges) {
    const src = nodeMap.get(e.sourceNodeId);
    const tgt = nodeMap.get(e.targetNodeId);
    if (!src || !tgt) {
      errors.push(`Dây nối '${e.id}' trỏ tới node không tồn tại.`);
      continue;
    }
    const srcDef = defMap.get(src.type);
    const tgtDef = defMap.get(tgt.type);
    const srcPort = srcDef?.outputPorts.find((p) => p.name === e.sourcePort);
    const tgtPort = tgtDef?.inputPorts.find((p) => p.name === e.targetPort);
    if (srcPort && tgtPort && !isPortCompatible(srcPort.portType, tgtPort.portType)) {
      errors.push(
        `Không tương thích kiểu cổng: '${e.sourcePort}' (${srcPort.portType}) -> '${e.targetPort}' (${tgtPort.portType}) tại node '${tgt.id}'.`
      );
    }
    adj.get(src.id)?.push(tgt.id);
    inDegree.set(tgt.id, (inDegree.get(tgt.id) || 0) + 1);
    connectedTargetPorts.add(`${tgt.id}:${e.targetPort}`);
  }

  const queue: string[] = [];
  inDegree.forEach((deg, nid) => {
    if (deg === 0) queue.push(nid);
  });
  const topo: string[] = [];
  while (queue.length > 0) {
    const u = queue.shift()!;
    topo.push(u);
    for (const v of adj.get(u) || []) {
      const nextDeg = (inDegree.get(v) || 1) - 1;
      inDegree.set(v, nextDeg);
      if (nextDeg === 0) queue.push(v);
    }
  }

  if (topo.length !== graph.nodes.length) {
    errors.push("Phát hiện chu trình (vòng lặp) trong đồ thị.");
  }

  for (const n of graph.nodes) {
    const def = defMap.get(n.type);
    if (!def) continue;
    for (const port of def.inputPorts) {
      if (!port.required) continue;
      const isConnected = connectedTargetPorts.has(`${n.id}:${port.name}`);
      const hasParam =
        n.params && n.params[port.name] !== undefined && n.params[port.name] !== "";
      if (!isConnected && !hasParam) {
        warnings.push(
          `Node '${n.id}' (${def.displayName}) chưa nối cổng bắt buộc '${port.name}'.`
        );
      }
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    topologicalOrder: topo,
  };
}

/** Chuẩn hoá đồ thị theo hợp đồng của core trước khi lưu (tránh 422): state "succeeded" -> "completed", bản sinh thiếu nodeId/artifactId. */
function normalizeGraphForCore(graph: Graph): Graph {
  return {
    ...graph,
    nodes: graph.nodes.map((n: any) => ({
      ...n,
      ...(n.state === "succeeded" ? { state: "completed" } : {}),
      ...(Array.isArray(n.generations)
        ? {
            generations: n.generations.map((g: any) => ({
              ...g,
              nodeId: g.nodeId ?? n.id,
              artifactId: g.artifactId ?? g.id,
            })),
          }
        : {}),
    })),
  } as Graph;
}

export async function saveGraphToCore(
  projectId: string,
  graph: Graph
): Promise<boolean> {
  try {
    const res = await fetch(`${CORE_URL}/projects/${projectId}/graph`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(normalizeGraphForCore(graph)),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export interface CoreCostEstimateResponse {
  projectId: string;
  mode: RunMode;
  mockMode: boolean;
  nodesToExecute: Array<{
    nodeId: string;
    nodeType: string;
    model: string;
    provider: string;
    estimatedCostUsd: number;
  }>;
  skippedNodes: string[];
  totalEstimatedCostUsd: number;
  requiresConfirmation: boolean;
  missingApiKeys: string[];
  spendStatus: Record<string, any>;
}

export async function estimateGraphOnCore(
  projectId: string,
  payload: {
    graph: Graph;
    mode: RunMode;
    targetNodeId?: string;
    spendingLimitUsd?: number;
    mockMode: boolean;
    runPolicy?: RunPolicy;
  }
): Promise<CoreCostEstimateResponse | null> {
  try {
    const res = await fetch(`${CORE_URL}/projects/${projectId}/estimate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) return null;
    return (await res.json()) as CoreCostEstimateResponse;
  } catch {
    return null;
  }
}

export async function runGraphOnCore(
  projectId: string,
  payload: {
    graph: Graph;
    mode: RunMode;
    targetNodeId?: string;
    spendingLimitUsd?: number;
    mockMode: boolean;
    runPolicy?: RunPolicy;
    confirmPaidRun?: boolean;
  }
): Promise<GraphRunSummary | null> {
  const res = await fetch(`${CORE_URL}/projects/${projectId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...payload,
      confirmPaidRun: payload.confirmPaidRun ?? true,
    }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail);
  }
  return (await res.json()) as GraphRunSummary;
}

export async function cancelRunOnCore(projectId: string): Promise<void> {
  try {
    await fetch(`${CORE_URL}/projects/${projectId}/run/cancel`, {
      method: "POST",
    });
  } catch {
    // ignore if offline
  }
}

export async function deleteRunOnCore(projectId: string, runId: string): Promise<boolean> {
  try {
    const res = await fetch(`${CORE_URL}/projects/${projectId}/runs/${encodeURIComponent(runId)}`, { method: "DELETE" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchActiveRun(projectId: string): Promise<any | null> {
  try {
    const res = await fetch(`${CORE_URL}/projects/${projectId}/runs/active`, { cache: "no-store" });
    if (res.status === 204 || !res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchProjectRuns(projectId: string, limit: number = 20): Promise<any[]> {
  try {
    const res = await fetch(`${CORE_URL}/projects/${projectId}/runs?limit=${limit}`, { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchProjectOutputs(projectId: string): Promise<any[]> {
  try {
    const res = await fetch(`${CORE_URL}/projects/${projectId}/outputs`, { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function sendChatToCore(
  projectId: string,
  prompt: string,
  context?: Record<string, unknown>
): Promise<{
  reply: string;
  mode: string;
  actions: any[];
  requiresConfirmation?: boolean;
  confirmationMeta?: any;
}> {
  try {
    const res = await fetch(`${CORE_URL}/projects/${projectId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, context }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback to client-side rule parser if Core is unreachable
  }
  return parseStudioCommandClientSide(prompt);
}

export function parseStudioCommandClientSide(prompt: string): {
  reply: string;
  mode: string;
  actions: any[];
  requiresConfirmation?: boolean;
  confirmationMeta?: any;
} {
  const p = prompt.toLowerCase().trim();
  const actions: any[] = [];
  let reply =
    "[Chế độ chạy thử — Trợ lý quy tắc] Đã ghi nhận lệnh. Bạn có thể gõ: 'thêm bước kiểm tra trước khi tạo video', 'đổi tỉ lệ sang 16:9', 'chạy từ cảnh 3', 'lên lịch đăng tập 1 lúc 19:00 lên YouTube', 'mở lịch đăng', hoặc 'xem nhân vật Koala'.";
  let requiresConfirmation = false;
  let confirmationMeta: any = null;

  if (p.includes("kiểm tra") || p.includes("quality") || p.includes("gate")) {
    actions.push({
      type: "add_node",
      nodeType: "quality_check",
      afterNodeType: "image_gen",
      beforeNodeType: "video_gen",
      summaryVi: "Đã thêm node Kiểm tra chất lượng (Gate) và nối với Tạo ảnh AI",
      summaryEn: "Added Quality Check (Gate) node and wired to AI Image Gen",
    });
    reply =
      "[Chế độ chạy thử] Đã thêm node Kiểm tra chất lượng (Gate) và nối giữa Tạo ảnh AI và Tạo video chuyển động.";
  } else if (p.includes("16:9") || p.includes("9:16") || p.includes("1:1") || p.includes("4:5")) {
    const ratio = p.includes("16:9") ? "16:9" : p.includes("1:1") ? "1:1" : p.includes("4:5") ? "4:5" : "9:16";
    actions.push({
      type: "set_aspect_ratio",
      aspectRatio: ratio,
      summaryVi: `Đã đổi tỉ lệ khung hình sang ${ratio}`,
      summaryEn: `Changed aspect ratio to ${ratio}`,
    });
    reply = `[Chế độ chạy thử] Đã chuyển tỉ lệ khung hình sang ${ratio}.`;
  } else if (p.includes("mở lịch") || p.includes("open schedule")) {
    actions.push({
      type: "open_tab",
      tab: "publish",
      summaryVi: "Đã mở tab Lịch đăng & Kênh",
      summaryEn: "Opened Schedule & Channels tab",
    });
    reply = "[Chế độ chạy thử] Đã mở tab Lịch đăng & Kênh ở khung bên phải.";
  } else if (p.includes("lên lịch") || p.includes("schedule") || p.includes("youtube") || p.includes("tiktok")) {
    const platform = p.includes("tiktok") ? "tiktok" : "youtube";
    const time = p.includes("20:00") ? "20:00" : "19:00";
    requiresConfirmation = true;
    confirmationMeta = {
      kind: "publish",
      platform,
      time,
      episodeTitle: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
    };
    actions.push({
      type: "schedule_post",
      platform,
      time,
      episodeTitle: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
      summaryVi: `Chuẩn bị lên lịch đăng Tập 1 lúc ${time} lên ${platform.toUpperCase()} (chờ xác nhận)`,
      summaryEn: `Prepared schedule for Episode 1 at ${time} on ${platform.toUpperCase()} (awaiting confirmation)`,
    });
    reply = `[Chế độ chạy thử] Lệnh lên lịch đăng bài lên ${platform.toUpperCase()} lúc ${time} cần bạn xác nhận trước khi thực hiện.`;
  } else if (p.includes("nhân vật") || p.includes("koala") || p.includes("sóc nhỏ") || p.includes("character")) {
    const characterId = p.includes("koala") ? "koala" : "soc_nho";
    actions.push({
      type: "open_character",
      tab: "project",
      characterId,
      summaryVi: `Đã mở hồ sơ nhân vật ${characterId === "koala" ? "Bác sĩ Koala" : "Sóc Nhỏ (Bi)"}`,
      summaryEn: `Opened character profile for ${characterId === "koala" ? "Dr. Koala" : "Little Squirrel (Bi)"}`,
    });
    reply = `[Chế độ chạy thử] Đã mở tab Dự án và hiển thị hồ sơ nhân vật ${characterId === "koala" ? "Bác sĩ Koala" : "Sóc Nhỏ (Bi)"}.`;
  } else if (p.includes("chạy") || p.includes("run")) {
    requiresConfirmation = true;
    confirmationMeta = {
      kind: "run",
      mode: p.includes("từ") || p.includes("from") ? "downstream" : "all",
      estimatedCostUsd: 0.0,
    };
    actions.push({
      type: "run_graph",
      mode: p.includes("từ") || p.includes("from") ? "downstream" : "all",
      summaryVi: "Yêu cầu chạy đồ thị (chờ xác nhận chi phí)",
      summaryEn: "Requested graph run (awaiting cost confirmation)",
    });
    reply = "[Chế độ chạy thử] Vui lòng xác nhận chi phí trước khi chạy đồ thị.";
  } else {
    actions.push({
      type: "add_node",
      nodeType: "quality_check",
      summaryVi: "Đã thêm node Kiểm tra chất lượng (Gate) vào đồ thị",
      summaryEn: "Added Quality Check (Gate) node to graph",
    });
  }

  return {
    reply,
    mode: "rule_based_mock",
    actions,
    requiresConfirmation,
    confirmationMeta,
  };
}

/** Đọc đồ thị đã lưu của dự án từ Core; null nếu Core không phản hồi. */
export async function fetchGraphFromCore(projectId: string): Promise<Graph | null> {
  try {
    const res = await fetch(`${CORE_URL}/projects/${projectId}/graph`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as Graph;
  } catch {
    return null;
  }
}
