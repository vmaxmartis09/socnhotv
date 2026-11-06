import type { Node, Edge } from "@xyflow/react";
import type { StudioNodeData } from "@/store/slices/canvasSlice";
import type { TemplateMeta, Platform } from "@/lib/api/video";
import type { Graph } from "@/lib/core-contracts";
import { autoLayout } from "@/lib/graph-layout";

export interface TemplateGraphOptions {
  projectId: string;
  template: TemplateMeta;
  topic: string;
  scriptText?: string;
  characterId?: string;
  voiceId?: string;
  platforms?: Platform[];
  slotValues?: Record<string, any>;
  productInfo?: {
    title?: string;
    name?: string;
    price?: string;
    usp?: string;
    image?: string;
  };
}

export interface GeneratedGraphBundle {
  reactFlowGraph: {
    nodes: Node<StudioNodeData>[];
    edges: Edge[];
  };
  coreGraph: Graph;
}

/**
 * Sinh đồ thị node tự động chuẩn cho 8 mẫu template:
 * text -> script -> voice_tts -> template_render -> platform_export
 * Kèm node character nối vào voice_tts.
 */
export function generateTemplateGraph(opts: TemplateGraphOptions): GeneratedGraphBundle {
  const {
    projectId,
    template,
    topic,
    scriptText = "",
    characterId = "soc_nho",
    voiceId = template.voice?.default_voice_id || "soc-nho",
    platforms = [template.default_platform || "tiktok"],
    slotValues = {},
    productInfo,
  } = opts;

  const targetPlatforms = platforms.length > 0 ? platforms : [template.default_platform || "tiktok"];
  const mergedSlots: Record<string, any> = { ...slotValues };
  if (productInfo && (productInfo.title || productInfo.name)) {
    mergedSlots.product = {
      title: productInfo.title || productInfo.name,
      name: productInfo.name || productInfo.title,
      price: productInfo.price || "",
      usp: productInfo.usp || "",
      image: productInfo.image || "",
    };
  }

  const nodes: Node<StudioNodeData>[] = [
    {
      id: "node_text",
      type: "studioCard",
      position: { x: 80, y: 150 },
      data: {
        nodeType: "text",
        status: "idle",
        params: {
          content: scriptText.trim() || topic.trim() || "Ý tưởng video mới",
        },
        generations: [],
        nextStepHint: "Bước 1: Chủ đề / Ý tưởng kịch bản",
      },
    },
    {
      id: "node_character",
      type: "studioCard",
      position: { x: 80, y: 460 },
      data: {
        nodeType: "character",
        status: "idle",
        params: {
          characterId: characterId || "soc_nho",
        },
        generations: [],
        nextStepHint: "Hồ sơ DNA nhân vật Sóc Nhỏ",
      },
    },
    {
      id: "node_script",
      type: "studioCard",
      position: { x: 420, y: 150 },
      data: {
        nodeType: "script",
        status: "idle",
        params: {
          targetSceneCount: template.scenes?.length || 4,
          targetDurationSec: Math.round(template.duration?.min || 30),
        },
        generations: [],
        nextStepHint: "Bước 2: Phân tách kịch bản thành phân cảnh và lời thoại",
      },
    },
    {
      id: "node_voice",
      type: "studioCard",
      position: { x: 740, y: 150 },
      data: {
        nodeType: "voice_tts",
        status: "idle",
        params: {
          voiceId: voiceId || "soc-nho",
          tempo: 1.1,
          mastering: true,
        },
        generations: [],
        nextStepHint: "Bước 3: Lồng tiếng chuẩn TikTok -14 LUFS",
      },
    },
    {
      id: "node_template_render",
      type: "studioCard",
      position: { x: 1060, y: 150 },
      data: {
        nodeType: "template_render",
        status: "idle",
        params: {
          template_id: template.id,
          platforms: targetPlatforms,
          slot_mapping: mergedSlots,
        },
        generations: [],
        nextStepHint: `Bước 4: Dựng video HyperFrames theo mẫu ${template.name}`,
      },
    },
    {
      id: "node_platform_export",
      type: "studioCard",
      position: { x: 1380, y: 150 },
      data: {
        nodeType: "platform_export",
        status: "idle",
        params: {
          target_platforms: targetPlatforms,
          fit_strategy: "cover",
        },
        generations: [],
        nextStepHint: "Bước 5: Xuất định dạng đa nền tảng tự động",
      },
    },
  ];

  const edges: Edge[] = [
    {
      id: "e_text_script",
      source: "node_text",
      sourceHandle: "text",
      target: "node_script",
      targetHandle: "text",
      type: "studioSmooth",
    },
    {
      id: "e_char_voice",
      source: "node_character",
      sourceHandle: "character",
      target: "node_voice",
      targetHandle: "character",
      type: "studioSmooth",
    },
    {
      id: "e_script_voice",
      source: "node_script",
      sourceHandle: "dialogue",
      target: "node_voice",
      targetHandle: "text",
      type: "studioSmooth",
    },
    {
      id: "e_voice_render",
      source: "node_voice",
      sourceHandle: "audio",
      target: "node_template_render",
      targetHandle: "audio",
      type: "studioSmooth",
    },
    {
      id: "e_render_export",
      source: "node_template_render",
      sourceHandle: "video",
      target: "node_platform_export",
      targetHandle: "video",
      type: "studioSmooth",
    },
  ];

  // Đặt template = 1 Group node chứa toàn bộ flow (thay flow cũ)
  const groupId = `group_${template.id}`;
  const coreNodes = nodes.map((n) => ({ ...n }));
  const grouped = autoLayout(
    [
      {
        id: groupId,
        type: "templateGroup",
        position: { x: 40, y: 40 },
        selectable: true,
        zIndex: -1,
        data: { nodeType: "group", label: template.name, templateId: template.id, count: nodes.length, status: "idle", params: {}, generations: [] },
      } as any,
      ...nodes.map((n) => ({ ...n, parentId: groupId, extent: "parent" as const })),
    ],
    edges
  );

  const coreGraph: Graph = {
    id: `graph_${projectId}_${Date.now()}`,
    projectId,
    nodes: coreNodes.map((n) => ({
      id: n.id,
      type: n.data.nodeType,
      position: n.position,
      params: n.data.params,
      isStale: false,
      inputs: {},
      state: "idle" as any,
    })),
    edges: edges.map((e) => ({
      id: e.id,
      sourceNodeId: e.source,
      sourcePort: e.sourceHandle || "text",
      targetNodeId: e.target,
      targetPort: e.targetHandle || "text",
    })),
    updatedAt: new Date().toISOString(),
  };

  return {
    reactFlowGraph: { nodes: grouped as any, edges },
    coreGraph,
  };
}
