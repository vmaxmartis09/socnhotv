import type { Node, Edge } from "@xyflow/react";
import type { StudioNodeData } from "@/store/slices/canvasSlice";
import type { Graph } from "@/lib/core-contracts";
import type { GeneratedGraphBundle } from "./template-graphs";

export const SHORT_VIDEO_PRESET_ID = "short-video-preset";
export const SHORT_VIDEO_PRESET_NAME = "Video ngắn (30–90s)";

export interface ShortVideoPresetOptions {
  projectId: string;
  topic: string;
  characterId?: string;
  characterName?: string;
  durationSec?: number;
  aspectRatio?: "9:16" | "16:9";
  mode?: "static" | "ai_clip";
  imageModel?: string;
  videoModel?: string;
  maxClips?: number;
  rawScript?: string;
  outputSlug?: string;
}

export const SHORT_VIDEO_DEFAULTS = {
  characterId: "soc_nho",
  characterName: "Sóc Nhỏ",
  durationSec: 30,
  aspectRatio: "9:16" as const,
  mode: "static" as const,
  imageModel: "pollinations-flux",
  videoModel: "mock-video",
  maxClips: 5,
};

const MODEL_RATES_PER_SEC: Record<string, number> = {
  "mock-video": 0.0,
  "fal-ltx-video": 0.05,
  "fal-kling-v3-std": 0.084,
  "google-veo-2": 0.15,
  "google-veo-3.1-fast": 0.4,
};

export function estimateShortVideoCost(opts: {
  mode: "static" | "ai_clip";
  durationSec: number;
  shotCount: number;
  videoModel?: string;
  maxClips?: number;
}) {
  const { mode, durationSec, shotCount, videoModel = "google-veo-2", maxClips = 5 } = opts;
  if (mode === "static") {
    return {
      totalUsd: 0.0,
      breakdown: {
        imageCostUsd: 0.0,
        voiceCostUsd: 0.0,
        videoAiCostUsd: 0.0,
        renderCostUsd: 0.0,
      },
      isFree: true,
      spendGuardRequired: false,
      note: "Miễn phí 100% ($0.00). Dùng ảnh keyframe Pollinations, giọng OmniVoice và camera GSAP.",
    };
  }

  const clipsToGen = Math.min(shotCount, maxClips);
  const clipDur = Math.min(6.0, durationSec / Math.max(1, shotCount));
  const rate = MODEL_RATES_PER_SEC[videoModel] ?? 0.15;
  const videoCost = Number((clipsToGen * clipDur * rate).toFixed(2));

  return {
    totalUsd: videoCost,
    breakdown: {
      imageCostUsd: 0.0,
      voiceCostUsd: 0.0,
      videoAiCostUsd: videoCost,
      renderCostUsd: 0.0,
    },
    isFree: videoCost === 0,
    spendGuardRequired: videoCost > 0,
    note: `Ước tính $${videoCost.toFixed(2)} (${clipsToGen} clips qua ${videoModel} @ $${rate}/s). Cần xác nhận qua SpendGuard trước khi gọi thật.`,
  };
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[đĐ]/g, "d")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 36) || "short-video";
}

type NodeSpec = {
  id: string;
  type: string;
  x: number;
  y: number;
  name: string;
  params: Record<string, any>;
  hint?: string;
};

export function buildShortVideoPreset(opts: ShortVideoPresetOptions): GeneratedGraphBundle {
  const o = { ...SHORT_VIDEO_DEFAULTS, ...opts };
  const slug = o.outputSlug || `short-${slugify(o.topic)}`;
  const isStatic = o.mode === "static";
  const platform = o.aspectRatio === "9:16" ? "tiktok" : "youtube";

  const shotCount = o.durationSec <= 35 ? 5 : o.durationSec <= 50 ? 6 : o.durationSec <= 70 ? 7 : 9;

  const defaultRawScript = o.rawScript || [
    `Cảnh 1: Hook giữ chân`,
    `(Camera: push-in)`,
    `Hình ảnh: Tiền cảnh lá sồi mờ bokeh, trung cảnh Sóc Nhỏ Bi lông cam mắt to ngạc nhiên, hậu cảnh rừng thông nắng sớm`,
    `${o.characterName}: Đừng bỏ qua điều kỳ diệu về ${o.topic} nếu các bạn chưa nghe qua trải nghiệm này của ${o.characterName} nha!`,
    ``,
    `Cảnh 2: Vấn đề cần giải quyết`,
    `(Camera: pan-left)`,
    `Hình ảnh: Sóc Nhỏ đứng suy tư gãi đầu, bối cảnh khu rừng ấm áp chiều thu`,
    `${o.characterName}: Trước đây ${o.characterName} cũng rất băn khoăn tìm cách khám phá ${o.topic} sao cho trọn vẹn nhất.`,
    ``,
    `Cảnh 3: Khám phá điểm sáng`,
    `(Camera: dolly-out)`,
    `Hình ảnh: Sóc Nhỏ vui sướng cầm trên tay phát hiện mới, ánh nắng vàng rực rỡ chiếu qua kẽ lá`,
    `${o.characterName}: Và đây chính là điều bất ngờ nhất, mọi thứ diễn ra vô cùng tự nhiên và sống động!`,
    ``,
    `Cảnh 4: Trải nghiệm & Đánh giá`,
    `(Camera: ken-burns)`,
    `Hình ảnh: Sóc Nhỏ mỉm cười gật gù hài lòng, giơ ngón tay cái chấm điểm tuyệt đối`,
    `${o.characterName}: Cảm giác thực tế phải nói là cực kỳ ưng ý, ${o.characterName} chấm ngay 10 trên 10 nha!`,
    ``,
    `Cảnh 5: Kêu gọi hành động`,
    `(Camera: push-in)`,
    `Hình ảnh: Sóc Nhỏ tươi cười vẫy tay chào khán giả, góc quay cận cảnh tràn ngập năng lượng tích cực`,
    `${o.characterName}: Hãy cùng theo dõi hành trình của ${o.characterName} để khám phá thêm nhiều điều thú vị nhé!`,
  ].join("\n");

  const specs: NodeSpec[] = [
    {
      id: "n_script",
      type: "script",
      x: 60,
      y: 160,
      name: "Kịch bản video ngắn",
      params: {
        mode: "paste",
        rawScript: defaultRawScript,
        targetSceneCount: shotCount,
        targetDurationSec: o.durationSec,
        text: o.topic,
        slug,
      },
      hint: `${shotCount} shot (${o.durationSec}s), kịch bản chuẩn TikTok Safe Zone`,
    },
    {
      id: "n_cast",
      type: "cast",
      x: 420,
      y: 40,
      name: "Dàn diễn viên",
      params: {
        speak: { enabled: true },
        include: [o.characterId],
        voiceOverrides: { [o.characterId]: "soc-nho" },
        onMissingVoice: "stop",
      },
      hint: `Nhân vật ${o.characterName} + Giọng OmniVoice $0`,
    },
    {
      id: "n_quality",
      type: "quality_check",
      x: 420,
      y: 320,
      name: "Kiểm định chính sách",
      params: { blockOnFail: true, policyAutoScan: true },
      hint: "Cổng lọc từ khoá cấm & an toàn nội dung",
    },
    {
      id: "n_keyframes",
      type: "image_gen",
      x: 780,
      y: 160,
      name: "Keyframe theo shot",
      params: {
        model: o.imageModel,
        aspectRatio: o.aspectRatio,
        resolution: "1080p",
        n: 1,
        prompt: "",
      },
      hint: "Ảnh 3-layer depth tham chiếu DNA nhân vật",
    },
    {
      id: "n_video",
      type: "video_gen",
      x: 1140,
      y: 160,
      name: "Video theo shot",
      params: {
        model: isStatic ? "mock-video" : o.videoModel,
        perShot: true,
        maxClips: isStatic ? 0 : Math.min(o.maxClips, shotCount),
        shotIds: [],
        clipSource: isStatic ? "manual" : "auto",
        durationSec: 5,
        aspectRatio: o.aspectRatio,
        hasAudio: false,
      },
      hint: isStatic ? "Chế độ ảnh tĩnh ($0.00)" : `Clip AI perShot (${o.videoModel})`,
    },
    {
      id: "n_render",
      type: "hyperframes_render",
      x: 1500,
      y: 160,
      name: `Dựng HyperFrames ${o.aspectRatio}`,
      params: {
        aspectRatio: o.aspectRatio,
        platform,
        template: "tiktok_safe_zone",
        templateId: "tiktok_safe_zone",
        timing: "script",
        gapSec: 0.35,
        requireHyperFrames: true,
        titleBadge: "SÓC NHỎ TV • SHORT",
      },
      hint: "Render HTML5/GSAP chuẩn Safe Zone",
    },
    {
      id: "n_export",
      type: "export",
      x: 1860,
      y: 160,
      name: "Xuất video ngắn",
      params: {
        platforms: [platform],
        outputSlug: slug,
        outputFileName: `${slug}.mp4`,
      },
      hint: `output/${slug}/${slug}.mp4`,
    },
  ];

  const wires: Array<[string, string, string, string]> = [
    ["n_script", "lines", "n_cast", "lines"],
    ["n_script", "scenes", "n_cast", "scenes"],
    ["n_script", "scenes", "n_quality", "scenes"],
    ["n_script", "lines", "n_quality", "text"],
    ["n_script", "scenes", "n_keyframes", "scenes"],
    ["n_cast", "reference_images", "n_keyframes", "references"],
    ["n_keyframes", "scenes", "n_video", "scenes"],
    ["n_video", "scenes", "n_render", "scenes"],
    ["n_cast", "voice", "n_render", "voice_clips"],
    ["n_quality", "pass_fail", "n_render", "gate"],
    ["n_render", "video", "n_export", "video"],
  ];

  const nodes: Node<StudioNodeData>[] = specs.map((s) => ({
    id: s.id,
    type: "studioCard",
    position: { x: s.x, y: s.y },
    data: {
      nodeType: s.type,
      status: "idle",
      params: { ...s.params, _customName: s.name },
      generations: [],
      ...(s.hint ? { nextStepHint: s.hint } : {}),
    },
  }));

  const edges: Edge[] = wires.map(([src, sp, dst, dp]) => ({
    id: `e_${src}_${sp}__${dst}_${dp}`,
    source: src,
    sourceHandle: sp,
    target: dst,
    targetHandle: dp,
  }));

  const coreGraph: Graph = {
    id: `graph_short_${slug}`,
    projectId: o.projectId,
    name: `Video Ngắn: ${o.topic.slice(0, 30)}`,
    nodes: specs.map((s) => ({
      id: s.id,
      type: s.type,
      position: { x: s.x, y: s.y },
      params: { ...s.params, _customName: s.name },
      isStale: false,
      inputs: {},
      state: "idle" as any,
    })),
    edges: wires.map(([src, sp, dst, dp]) => ({
      id: `e_${src}_${sp}__${dst}_${dp}`,
      sourceNodeId: src,
      sourcePort: sp,
      targetNodeId: dst,
      targetPort: dp,
    })),
    updatedAt: new Date().toISOString(),
  } as Graph;

  return { reactFlowGraph: { nodes, edges }, coreGraph };
}
