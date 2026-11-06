export * from "./template-graphs";

import type { Node, Edge } from "@xyflow/react";
import type { StudioNodeData } from "@/store/slices/canvasSlice";
import type { Graph } from "@/lib/core-contracts";
import type { GeneratedGraphBundle } from "./template-graphs";

/**
 * Preset "Tập hoạt hình (tái dùng)" — Session G (G4).
 *
 * Kịch bản (episode) → Dàn diễn viên (đọc thoại + ảnh DNA) → Keyframe theo shot (image_gen)
 *   → Video theo shot (video_gen, perShot) → Dựng HyperFrames 16:9 → Xuất (tên tệp tự theo tập, C6)
 * Kiểm định chính sách chặn trước khi dựng.
 *
 * - Đổi tập: chỉ đổi `episodeId` ở node Kịch bản; đồ thị giữ nguyên, dàn diễn viên & tên tệp tự đổi.
 * - Mức A: video_gen để `clipSource: "manual"` → chỉ dùng clip làm tay có sẵn trong
 *   content/episodes/<tập>/clips/<shot>.mp4 (C5), không gọi model video nào, $0. Không có clip thì giữ ảnh.
 * - Mức B: đổi `clipSource` sang "auto" (có clip tay thì dùng, không có thì sinh AI tối đa `maxClips`).
 * - Id node cố định (n_script, n_cast, n_keyframes, n_video, n_quality, n_render, n_export) để
 *   scripts/video/verify_episode.py tìm đúng snapshot cổng ra.
 */
export const EPISODE_PRESET_ID = "episode-animation-reusable";
export const EPISODE_PRESET_NAME = "Tập hoạt hình (tái dùng)";

export interface EpisodePresetOptions {
  projectId: string;
  episodeId: string;
  /** Model ảnh keyframe, mặc định nguồn free chính của G1 */
  imageModel?: string;
  /** Model video cho Mức B */
  videoModel?: string;
  /** "manual" = Mức A (chỉ clip làm tay), "auto" = Mức B */
  clipSource?: "manual" | "auto" | "ai";
  maxClips?: number;
}

export const EPISODE_PRESET_DEFAULTS = {
  imageModel: "pollinations-flux",
  videoModel: "mock-video",
  clipSource: "manual" as const,
  maxClips: 5,
};

type NodeSpec = { id: string; type: string; x: number; y: number; name: string; params: Record<string, any>; hint?: string };

export function buildEpisodeAnimationPreset(opts: EpisodePresetOptions): GeneratedGraphBundle {
  const o = { ...EPISODE_PRESET_DEFAULTS, ...opts };
  const specs: NodeSpec[] = [
    {
      id: "n_script", type: "script", x: 60, y: 160, name: "Kịch bản tập",
      params: { mode: "episode", episodeId: o.episodeId, granularity: "shot", targetSceneCount: 30, targetDurationSec: 600 },
      hint: "Chọn tập ở đây — cả flow tự theo tập",
    },
    {
      id: "n_cast", type: "cast", x: 420, y: 40, name: "Dàn diễn viên",
      params: { speak: { enabled: true }, include: [], exclude: [], onMissingVoice: "stop" },
      hint: "Giọng thật OmniVoice từng câu + ảnh DNA",
    },
    {
      id: "n_quality", type: "quality_check", x: 420, y: 320, name: "Kiểm định chính sách",
      params: { blockOnFail: true, policyAutoScan: true },
    },
    {
      id: "n_keyframes", type: "image_gen", x: 780, y: 160, name: "Keyframe theo shot",
      params: { model: o.imageModel, aspectRatio: "16:9", resolution: "1080p", n: 1, prompt: "" },
      hint: "1 ảnh/shot, tham chiếu ảnh DNA nhân vật",
    },
    {
      id: "n_video", type: "video_gen", x: 1140, y: 160, name: "Video theo shot",
      params: {
        model: o.videoModel, perShot: true, maxClips: o.maxClips, shotIds: [], clipSource: o.clipSource,
        durationSec: 5, aspectRatio: "16:9", hasAudio: false,
      },
      hint: o.clipSource === "manual" ? "Mức A: chỉ clip làm tay (clips/<shot>.mp4), không tốn tiền" : "Mức B: clip AI cho shot chính",
    },
    {
      id: "n_render", type: "hyperframes_render", x: 1500, y: 160, name: "Dựng HyperFrames 16:9",
      params: {
        aspectRatio: "16:9", platform: "youtube", template: "default_cartoon", templateId: "default_cartoon",
        timing: "script", gapSec: 0.35, requireHyperFrames: true,
      },
    },
    {
      id: "n_export", type: "export", x: 1860, y: 160, name: "Xuất (tên theo tập)",
      params: { platforms: ["youtube"], outputFileName: "" },
      hint: "Để trống tên tệp → output/<tập>/<tập>.mp4",
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
    id: `graph_${o.projectId}`,
    projectId: o.projectId,
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
