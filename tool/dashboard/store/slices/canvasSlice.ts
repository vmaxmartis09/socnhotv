import type { StateCreator } from "zustand";
import type { Node, Edge } from "@xyflow/react";
import type {
  NodeDefinition,
  NodeStatus,
  GraphValidationResult,
  PortType,
} from "@/lib/core-contracts";
import type { Episode } from "@/lib/repositories/types";
import { FALLBACK_NODE_TYPES, fetchGraphFromCore } from "@/lib/core-api";

export interface NodeGenerationRecord {
  id: string;
  createdAt: string;
  previewUrl?: string;
  previewType?: "image" | "video" | "audio" | "text";
  summaryText?: string;
  costUsd: number;
  seed?: number | null;
  model?: string;
}

export interface StudioNodeData extends Record<string, unknown> {
  nodeType: string;
  label?: string;
  status: NodeStatus;
  isStale?: boolean;
  params: Record<string, any>;
  progressPct?: number;
  lastLog?: string;
  errorMessage?: string;
  actualCostUsd?: number;
  previewUrl?: string;
  previewType?: "image" | "video" | "audio" | "text";
  summaryText?: string;
  generations: NodeGenerationRecord[];
  pinnedGenerationId?: string | null;
  nextStepHint?: string;
}

export const PORT_TYPE_COLORS: Record<PortType, string> = {
  text: "#737373",
  script: "#737373",
  scenes: "#737373",
  captions: "#737373",
  character: "#525252",
  image: "#1b6c80",
  "image[]": "#1b6c80",
  video: "#b4531a",
  composition: "#b4531a",
  audio: "#a86f0c",
};

/** Đồ thị mẫu 9 bước giữ nguyên cấu trúc nhưng bỏ nội dung riêng của Sóc Nhỏ khi dùng cho dự án khác. */
export function genericizeTemplate(
  tpl: { nodes: Node<StudioNodeData>[]; edges: Edge[] },
  projectId: string
): { nodes: Node<StudioNodeData>[]; edges: Edge[] } {
  if (projectId === "soc-nho-tv") return tpl;
  return {
    edges: tpl.edges,
    nodes: tpl.nodes.map((n) => {
      const params = { ...(n.data.params || {}) };
      if (n.data.nodeType === "text") params.content = "";
      if (n.data.nodeType === "character") params.characterId = "";
      if (n.data.nodeType === "export") params.outputFileName = `${projectId}_tap_01.mp4`;
      return { ...n, data: { ...n.data, params } };
    }),
  };
}

export function buildSocNhoStoryTemplate(
  catalog: NodeDefinition[] = FALLBACK_NODE_TYPES
): { nodes: Node<StudioNodeData>[]; edges: Edge[] } {
  const getDef = (t: string) =>
    catalog.find((d) => d.typeName === t) ||
    FALLBACK_NODE_TYPES.find((d) => d.typeName === t)!;

  const nodes: Node<StudioNodeData>[] = [
    {
      id: "node_text",
      type: "studioCard",
      position: { x: 20, y: 20 },
      data: {
        nodeType: "text",
        status: "idle",
        params: {
          ...getDef("text")?.defaultParams,
          content:
            "Tập 1: Sóc Nhỏ (Bi, 100cm) mê ăn kẹo dẻo hạt dẻ trước khi đi ngủ, bị đau răng sâu và được Bác sĩ Koala (150cm) khám răng, hướng dẫn đánh răng đúng cách.",
        },
        generations: [],
        nextStepHint: "Bước 1: Kiểm tra cốt truyện hoặc bấm Chạy cả chuỗi",
      },
    },
    {
      id: "node_script",
      type: "studioCard",
      position: { x: 380, y: 20 },
      data: {
        nodeType: "script",
        status: "idle",
        params: {
          ...getDef("script")?.defaultParams,
          targetSceneCount: 6,
          targetDurationSec: 45,
        },
        generations: [],
        nextStepHint: "Bước 2: Tách cốt truyện thành 6 cảnh có lời thoại",
      },
    },
    {
      id: "node_character",
      type: "studioCard",
      position: { x: 20, y: 640 },
      data: {
        nodeType: "character",
        status: "idle",
        params: {
          ...getDef("character")?.defaultParams,
          characterId: "soc_nho",
        },
        generations: [],
        nextStepHint: "Hồ sơ DNA Sóc Nhỏ (100cm) & giọng soc-nho",
      },
    },
    {
      id: "node_image_gen",
      type: "studioCard",
      position: { x: 740, y: 20 },
      data: {
        nodeType: "image_gen",
        status: "idle",
        params: {
          ...getDef("image_gen")?.defaultParams,
          model: "gemini-2.5-flash-image",
          aspectRatio: "9:16",
          n: 1,
        },
        generations: [],
        nextStepHint: "Bước 3: Sinh ảnh 3D Pixar theo DNA nhân vật",
      },
    },
    {
      id: "node_quality",
      type: "studioCard",
      position: { x: 380, y: 640 },
      data: {
        nodeType: "quality_check",
        status: "idle",
        params: {
          ...getDef("quality_check")?.defaultParams,
          thresholdScore: 0.85,
        },
        generations: [],
        nextStepHint: "Bước 4: Chấm điểm ảnh trước khi tạo video",
      },
    },
    {
      id: "node_video_gen",
      type: "studioCard",
      position: { x: 740, y: 640 },
      data: {
        nodeType: "video_gen",
        status: "idle",
        params: {
          ...getDef("video_gen")?.defaultParams,
          model: "google-veo-2",
          durationSec: 8,
          aspectRatio: "9:16",
        },
        generations: [],
        nextStepHint: "Bước 5: Tạo chuyển động video từ ảnh đạt chuẩn",
      },
    },
    {
      id: "node_voice",
      type: "studioCard",
      position: { x: 380, y: 1260 },
      data: {
        nodeType: "voice_tts",
        status: "idle",
        params: {
          ...getDef("voice_tts")?.defaultParams,
          voiceId: "soc-nho",
          tempo: 1.1,
        },
        generations: [],
        nextStepHint: "Bước 6: Đọc lời thoại bằng giọng Sóc Nhỏ (-14 LUFS)",
      },
    },
    {
      id: "node_render",
      type: "studioCard",
      position: { x: 740, y: 1260 },
      data: {
        nodeType: "hyperframes_render",
        status: "idle",
        params: {
          ...getDef("hyperframes_render")?.defaultParams,
          aspectRatio: "9:16",
          template: "default_cartoon",
        },
        generations: [],
        nextStepHint: "Bước 7: Ghép cảnh, phụ đề & nhạc nền HyperFrames",
      },
    },
    {
      id: "node_export",
      type: "studioCard",
      position: { x: 1100, y: 1260 },
      data: {
        nodeType: "export",
        status: "idle",
        params: {
          ...getDef("export")?.defaultParams,
          platforms: ["tiktok", "youtube"],
          outputFileName: "soc_nho_tap_01.mp4",
        },
        generations: [],
        nextStepHint: "Bước 8: Đóng gói MP4 & sẵn sàng lên lịch đăng",
      },
    },
  ];

  const makeEdge = (
    id: string,
    source: string,
    sourceHandle: string,
    target: string,
    targetHandle: string,
    portType: PortType
  ): Edge => ({
    id,
    source,
    sourceHandle,
    target,
    targetHandle,
    type: "default",
    style: {
      stroke: PORT_TYPE_COLORS[portType] || "#737373",
      strokeWidth: 1.75,
    },
    data: { portType },
  });

  const edges: Edge[] = [
    makeEdge("e_text_script", "node_text", "text", "node_script", "text", "text"),
    makeEdge(
      "e_script_img_prompt",
      "node_script",
      "prompt",
      "node_image_gen",
      "prompt",
      "text"
    ),
    makeEdge(
      "e_char_img_refs",
      "node_character",
      "reference_images",
      "node_image_gen",
      "references",
      "image[]"
    ),
    makeEdge(
      "e_img_quality",
      "node_image_gen",
      "image",
      "node_quality",
      "media",
      "image"
    ),
    makeEdge(
      "e_quality_vid",
      "node_quality",
      "media",
      "node_video_gen",
      "first_frame",
      "image"
    ),
    makeEdge(
      "e_script_vid_prompt",
      "node_script",
      "prompt",
      "node_video_gen",
      "prompt",
      "text"
    ),
    makeEdge(
      "e_script_voice",
      "node_script",
      "dialogue",
      "node_voice",
      "text",
      "text"
    ),
    makeEdge(
      "e_char_voice",
      "node_character",
      "character",
      "node_voice",
      "character",
      "character"
    ),
    makeEdge(
      "e_script_render_scenes",
      "node_script",
      "scenes",
      "node_render",
      "scenes",
      "scenes"
    ),
    makeEdge(
      "e_vid_render",
      "node_video_gen",
      "video",
      "node_render",
      "video",
      "video"
    ),
    makeEdge(
      "e_voice_render",
      "node_voice",
      "audio",
      "node_render",
      "audio",
      "audio"
    ),
    makeEdge(
      "e_render_export",
      "node_render",
      "video",
      "node_export",
      "video",
      "video"
    ),
  ];

  return { nodes, edges };
}

const DEFAULT_EPISODES: Episode[] = [
  {
    id: "ep_01_rang_sau",
    projectId: "soc-nho-tv",
    episodeNumber: 1,
    title: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
    status: "ready",
    nodeCount: 9,
    updatedAt: "2026-11-03T15:00:00Z",
  },
  {
    id: "ep_02_bac_si_koala",
    projectId: "soc-nho-tv",
    episodeNumber: 2,
    title: "Tập 2: Bác Sĩ Koala Khám Răng",
    status: "draft",
    nodeCount: 9,
    updatedAt: "2026-11-02T10:30:00Z",
  },
  {
    id: "ep_03_danh_rang_dung_cach",
    projectId: "soc-nho-tv",
    episodeNumber: 3,
    title: "Tập 3: Đánh Răng Sáng Tối Cùng Bi",
    status: "draft",
    nodeCount: 0,
    updatedAt: "2026-11-01T09:15:00Z",
  },
];

const INITIAL_TEMPLATE = buildSocNhoStoryTemplate(FALLBACK_NODE_TYPES);

export interface ProjectWorkspace {
  episodes: Episode[];
  activeEpisodeId: string;
  graphsByEpisode: Record<string, { nodes: Node<StudioNodeData>[]; edges: Edge[] }>;
  nodes: Node<StudioNodeData>[];
  edges: Edge[];
}

export interface CanvasSlice {
  selectedNodeId: string | null;
  aspectRatio: "9:16" | "16:9" | "1:1" | "4:5";
  zoomLevel: number;
  isMockMode: boolean;
  episodes: Episode[];
  activeEpisodeId: string;
  nodeCatalog: NodeDefinition[];
  nodeCatalogFromCore: boolean;
  nodes: Node<StudioNodeData>[];
  edges: Edge[];
  graphsByEpisode: Record<
    string,
    { nodes: Node<StudioNodeData>[]; edges: Edge[] }
  >;
  undoStack: Array<{ nodes: Node<StudioNodeData>[]; edges: Edge[] }>;
  redoStack: Array<{ nodes: Node<StudioNodeData>[]; edges: Edge[] }>;
  saveState: "saved" | "saving" | "unsaved";
  isRunningGraph: boolean;
  validationResult: GraphValidationResult | null;
  /** Mỗi dự án có không gian làm việc riêng (tập + đồ thị); chuyển dự án sẽ tráo cả canvas. */
  projectWorkspaces: Record<string, ProjectWorkspace>;
  switchProject: (projectId: string) => void;
  /** Dự án đã nạp đồ thị từ Core (hoặc xác nhận trống). Chỉ lưu tự động khi đã nạp, để không ghi đè đồ thị đã lưu bằng canvas trống. */
  loadedGraphs: Record<string, boolean>;
  loadProjectGraph: (projectId: string) => Promise<void>;
  setSelectedNodeId: (id: string | null) => void;
  setAspectRatio: (ratio: "9:16" | "16:9" | "1:1" | "4:5") => void;
  setZoomLevel: (zoom: number) => void;
  setIsMockMode: (mock: boolean) => void;
  setEpisodes: (episodes: Episode[]) => void;
  selectEpisode: (episodeId: string) => void;
  createEpisode: (title: string, opts?: { blank?: boolean }) => Episode;
  setNodeCatalog: (defs: NodeDefinition[], fromCore: boolean) => void;
  setNodesAndEdges: (
    nodes: Node<StudioNodeData>[],
    edges: Edge[],
    recordHistory?: boolean
  ) => void;
  pushUndoSnapshot: () => void;
  undoCanvas: () => void;
  redoCanvas: () => void;
  loadCanvasTemplate: (template: "soc_nho_story" | "blank") => void;
  updateNodeParams: (nodeId: string, patch: Record<string, any>) => void;
  updateNodeExecutionState: (
    nodeId: string,
    patch: Partial<StudioNodeData>
  ) => void;
  pinNodeGeneration: (nodeId: string, generationId: string) => void;
  markDownstreamStale: (sourceNodeId: string) => void;
  setSaveState: (state: "saved" | "saving" | "unsaved") => void;
  setIsRunningGraph: (running: boolean) => void;
  setValidationResult: (res: GraphValidationResult | null) => void;
}

function collectDownstreamIds(startNodeId: string, edges: Edge[]): Set<string> {
  const visited = new Set<string>();
  const queue = [startNodeId];
  while (queue.length > 0) {
    const curr = queue.shift()!;
    for (const e of edges) {
      if (e.source === curr && !visited.has(e.target)) {
        visited.add(e.target);
        queue.push(e.target);
      }
    }
  }
  return visited;
}

export const createCanvasSlice: StateCreator<
  CanvasSlice,
  [],
  [],
  CanvasSlice
> = (set, get) => ({
  selectedNodeId: "node_image_gen",
  aspectRatio: "9:16",
  zoomLevel: 1.0,
  isMockMode: true,
  episodes: DEFAULT_EPISODES,
  activeEpisodeId: "ep_01_rang_sau",
  nodeCatalog: FALLBACK_NODE_TYPES,
  nodeCatalogFromCore: false,
  nodes: INITIAL_TEMPLATE.nodes,
  edges: INITIAL_TEMPLATE.edges,
  graphsByEpisode: {
    ep_01_rang_sau: INITIAL_TEMPLATE,
    ep_02_bac_si_koala: buildSocNhoStoryTemplate(FALLBACK_NODE_TYPES),
    ep_03_danh_rang_dung_cach: { nodes: [], edges: [] },
  },
  undoStack: [],
  redoStack: [],
  saveState: "saved",
  isRunningGraph: false,
  validationResult: null,
  projectWorkspaces: {},
  loadedGraphs: {},
  loadProjectGraph: async (projectId) => {
    const g = await fetchGraphFromCore(projectId);
    if (!g) return; // Core không phản hồi: không đánh dấu đã nạp, tránh lưu đè
    const s = get() as any;
    if (s.activeProjectId !== projectId) return; // đã chuyển dự án khác trong lúc chờ
    if (g.nodes.length > 0) {
      const nodes: Node<StudioNodeData>[] = g.nodes.map((n: any) => ({
        id: n.id,
        type: "studioCard",
        position: n.position ?? { x: 0, y: 0 },
        data: {
          nodeType: n.type,
          status: (n.state || "idle") as NodeStatus,
          isStale: Boolean(n.isStale),
          params: n.params || {},
          pinnedGenerationId: n.pinnedGenerationId ?? null,
          generations: n.generations || [],
        },
      }));
      const edges: Edge[] = g.edges.map((e: any) => ({
        id: e.id,
        source: e.sourceNodeId,
        sourceHandle: e.sourcePort,
        target: e.targetNodeId,
        targetHandle: e.targetPort,
        type: "default",
      }));
      set({
        nodes,
        edges,
        graphsByEpisode: { ...s.graphsByEpisode, [s.activeEpisodeId]: { nodes, edges } },
        loadedGraphs: { ...s.loadedGraphs, [projectId]: true },
        saveState: "saved",
      } as any);
    } else {
      set({ loadedGraphs: { ...s.loadedGraphs, [projectId]: true } } as any);
    }
  },
  switchProject: (projectId) => {
    const s = get() as any;
    if (s.activeProjectId === projectId) return;
    const current: ProjectWorkspace = {
      episodes: s.episodes,
      activeEpisodeId: s.activeEpisodeId,
      graphsByEpisode: {
        ...s.graphsByEpisode,
        [s.activeEpisodeId]: { nodes: s.nodes, edges: s.edges },
      },
      nodes: s.nodes,
      edges: s.edges,
    };
    const saved = { ...s.projectWorkspaces, [s.activeProjectId]: current };
    let next: ProjectWorkspace | undefined = saved[projectId];
    if (!next) {
      // Dự án chưa mở lần nào: một tập trống, canvas trống để chọn mẫu
      const epId = `ep_${projectId}_01`;
      next = {
        episodes: [
          {
            id: epId,
            projectId,
            episodeNumber: 1,
            title: "Tập 1",
            status: "draft",
            nodeCount: 0,
            updatedAt: new Date().toISOString(),
          },
        ],
        activeEpisodeId: epId,
        graphsByEpisode: { [epId]: { nodes: [], edges: [] } },
        nodes: [],
        edges: [],
      };
    }
    set({
      activeProjectId: projectId,
      projectWorkspaces: saved,
      episodes: next.episodes,
      activeEpisodeId: next.activeEpisodeId,
      graphsByEpisode: next.graphsByEpisode,
      nodes: next.nodes,
      edges: next.edges,
      selectedNodeId: null,
      undoStack: [],
      redoStack: [],
      saveState: "saved",
    } as any);
  },
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  setAspectRatio: (aspectRatio) =>
    set((state) => ({
      aspectRatio,
      saveState: "unsaved",
      nodes: state.nodes.map((n) =>
        n.data.params && "aspectRatio" in n.data.params
          ? {
              ...n,
              data: {
                ...n.data,
                params: { ...n.data.params, aspectRatio },
              },
            }
          : n
      ),
    })),
  setZoomLevel: (zoomLevel) => set({ zoomLevel }),
  setIsMockMode: (isMockMode) => set({ isMockMode }),
  setEpisodes: (episodes) => set({ episodes }),
  selectEpisode: (episodeId) =>
    set((state) => {
      const savedCurrent = {
        ...state.graphsByEpisode,
        [state.activeEpisodeId]: { nodes: state.nodes, edges: state.edges },
      };
      const nextGraph = savedCurrent[episodeId] || { nodes: [], edges: [] };
      return {
        activeEpisodeId: episodeId,
        graphsByEpisode: savedCurrent,
        nodes: nextGraph.nodes,
        edges: nextGraph.edges,
        selectedNodeId: nextGraph.nodes[0]?.id || null,
        undoStack: [],
        redoStack: [],
        saveState: "saved",
      };
    }),
  createEpisode: (title, opts) => {
    const state = get();
    const nextNum = state.episodes.length + 1;
    const newEp: Episode = {
      id: `ep_0${nextNum}_${Date.now().toString(36)}`,
      projectId: (state as any).activeProjectId || "soc-nho-tv",
      episodeNumber: nextNum,
      title: title.trim() || `Tập ${nextNum}: Câu chuyện mới`,
      status: "draft",
      nodeCount: opts?.blank ? 0 : 9,
      updatedAt: new Date().toISOString(),
    };
    const tpl = opts?.blank
      ? { nodes: [] as Node<StudioNodeData>[], edges: [] as Edge[] }
      : genericizeTemplate(buildSocNhoStoryTemplate(state.nodeCatalog), (state as any).activeProjectId || "soc-nho-tv");
    set({
      episodes: [...state.episodes, newEp],
      activeEpisodeId: newEp.id,
      graphsByEpisode: {
        ...state.graphsByEpisode,
        [state.activeEpisodeId]: { nodes: state.nodes, edges: state.edges },
        [newEp.id]: tpl,
      },
      nodes: tpl.nodes,
      edges: tpl.edges,
      selectedNodeId: tpl.nodes[0]?.id || null,
      undoStack: [],
      redoStack: [],
      saveState: "unsaved",
    });
    return newEp;
  },
  setNodeCatalog: (nodeCatalog, nodeCatalogFromCore) =>
    set({ nodeCatalog, nodeCatalogFromCore }),
  setNodesAndEdges: (nodes, edges, recordHistory = true) =>
    set((state) => {
      const nextUndo = recordHistory
        ? [...state.undoStack.slice(-24), { nodes: state.nodes, edges: state.edges }]
        : state.undoStack;
      return {
        nodes,
        edges,
        undoStack: nextUndo,
        redoStack: recordHistory ? [] : state.redoStack,
        saveState: "unsaved",
        graphsByEpisode: {
          ...state.graphsByEpisode,
          [state.activeEpisodeId]: { nodes, edges },
        },
        episodes: state.episodes.map((ep) =>
          ep.id === state.activeEpisodeId
            ? { ...ep, nodeCount: nodes.length, updatedAt: new Date().toISOString() }
            : ep
        ),
      };
    }),
  pushUndoSnapshot: () =>
    set((state) => ({
      undoStack: [
        ...state.undoStack.slice(-24),
        { nodes: state.nodes, edges: state.edges },
      ],
      redoStack: [],
    })),
  undoCanvas: () =>
    set((state) => {
      if (state.undoStack.length === 0) return state;
      const previous = state.undoStack[state.undoStack.length - 1];
      const nextUndo = state.undoStack.slice(0, -1);
      return {
        nodes: previous.nodes,
        edges: previous.edges,
        undoStack: nextUndo,
        redoStack: [
          ...state.redoStack,
          { nodes: state.nodes, edges: state.edges },
        ],
        saveState: "unsaved",
        graphsByEpisode: {
          ...state.graphsByEpisode,
          [state.activeEpisodeId]: previous,
        },
      };
    }),
  redoCanvas: () =>
    set((state) => {
      if (state.redoStack.length === 0) return state;
      const next = state.redoStack[state.redoStack.length - 1];
      const nextRedo = state.redoStack.slice(0, -1);
      return {
        nodes: next.nodes,
        edges: next.edges,
        undoStack: [
          ...state.undoStack,
          { nodes: state.nodes, edges: state.edges },
        ],
        redoStack: nextRedo,
        saveState: "unsaved",
        graphsByEpisode: {
          ...state.graphsByEpisode,
          [state.activeEpisodeId]: next,
        },
      };
    }),
  loadCanvasTemplate: (template) =>
    set((state) => {
      const nextGraph =
        template === "soc_nho_story"
          ? genericizeTemplate(buildSocNhoStoryTemplate(state.nodeCatalog), (state as any).activeProjectId)
          : {
              nodes: [
                {
                  id: "node_text_1",
                  type: "studioCard",
                  position: { x: 120, y: 140 },
                  data: {
                    nodeType: "text",
                    status: "idle" as NodeStatus,
                    params: {
                      content: "Nhập ý tưởng kịch bản cho tập mới...",
                    },
                    generations: [],
                    nextStepHint: "Bấm dấu + ở cổng ra để thêm bước tiếp theo",
                  },
                },
              ],
              edges: [],
            };
      return {
        nodes: nextGraph.nodes,
        edges: nextGraph.edges,
        selectedNodeId: nextGraph.nodes[0]?.id || null,
        undoStack: [
          ...state.undoStack.slice(-24),
          { nodes: state.nodes, edges: state.edges },
        ],
        redoStack: [],
        saveState: "unsaved",
        graphsByEpisode: {
          ...state.graphsByEpisode,
          [state.activeEpisodeId]: nextGraph,
        },
        episodes: state.episodes.map((ep) =>
          ep.id === state.activeEpisodeId
            ? { ...ep, nodeCount: nextGraph.nodes.length }
            : ep
        ),
      };
    }),
  updateNodeParams: (nodeId, patch) =>
    set((state) => {
      const downstreamIds = collectDownstreamIds(nodeId, state.edges);
      const nextNodes = state.nodes.map((n) => {
        if (n.id === nodeId) {
          return {
            ...n,
            data: {
              ...n.data,
              params: { ...n.data.params, ...patch },
            },
          };
        }
        if (downstreamIds.has(n.id) && n.data.status === "succeeded") {
          return {
            ...n,
            data: {
              ...n.data,
              isStale: true,
            },
          };
        }
        return n;
      });
      return {
        nodes: nextNodes,
        saveState: "unsaved",
        graphsByEpisode: {
          ...state.graphsByEpisode,
          [state.activeEpisodeId]: { nodes: nextNodes, edges: state.edges },
        },
      };
    }),
  updateNodeExecutionState: (nodeId, patch) =>
    set((state) => {
      const nextNodes = state.nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, ...patch } } : n
      );
      return {
        nodes: nextNodes,
        graphsByEpisode: {
          ...state.graphsByEpisode,
          [state.activeEpisodeId]: { nodes: nextNodes, edges: state.edges },
        },
      };
    }),
  pinNodeGeneration: (nodeId, generationId) =>
    set((state) => {
      const nextNodes = state.nodes.map((n) => {
        if (n.id !== nodeId) return n;
        const gen = n.data.generations.find((g) => g.id === generationId);
        return {
          ...n,
          data: {
            ...n.data,
            pinnedGenerationId: generationId,
            previewUrl: gen?.previewUrl || n.data.previewUrl,
            previewType: gen?.previewType || n.data.previewType,
            summaryText: gen?.summaryText || n.data.summaryText,
          },
        };
      });
      return { nodes: nextNodes, saveState: "unsaved" };
    }),
  markDownstreamStale: (sourceNodeId) =>
    set((state) => {
      const downstreamIds = collectDownstreamIds(sourceNodeId, state.edges);
      const nextNodes = state.nodes.map((n) =>
        downstreamIds.has(n.id)
          ? { ...n, data: { ...n.data, isStale: true } }
          : n
      );
      return { nodes: nextNodes };
    }),
  setSaveState: (saveState) => set({ saveState }),
  setIsRunningGraph: (isRunningGraph) => set({ isRunningGraph }),
  setValidationResult: (validationResult) => set({ validationResult }),
});
