"use client";

import { useShallow } from "zustand/react/shallow";
import React, {
  useState,
  useCallback,
  useMemo,
  useRef,
  useEffect,
} from "react";
import { useTranslations } from "next-intl";
import {
  ReactFlow,
  Controls,
  MiniMap,
  applyNodeChanges,
  applyEdgeChanges,
  ReactFlowProvider,
  Panel,
  ConnectionLineType,
  useReactFlow,
  type Connection,
  type OnNodesChange,
  type OnEdgesChange,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { autoLayout, analyzeGraph } from "@/lib/graph-layout";
import { applyPortOverride } from "@/lib/node-ports";
import { StudioEdge } from "./StudioEdge";
import { useStudioStore, type StudioStore } from "@/store";
import {
  PORT_TYPE_COLORS,
  type StudioNodeData,
  type NodeGenerationRecord,
} from "@/store/slices/canvasSlice";
import { StudioNode, type StudioCardNodeType } from "@/components/canvas/StudioNode";
import { StudioStickToolbar, type CanvasMode } from "@/components/canvas/StudioStickToolbar";
import {
  CanvasInteractionContext,
  type ActiveDragPort,
  type QuickAddRequest,
} from "@/components/canvas/CanvasContext";
import {
  isPortCompatible,
  estimateNodeCostUsd,
  validateGraphWithCore,
  saveGraphToCore,
  runGraphOnCore,
  cancelRunOnCore,
  fetchActiveRun,
} from "@/lib/core-api";
import { RunStatusBar, type RunStateInfo } from "@/components/canvas/RunStatusBar";
import { CORE_URL } from "@/lib/repositories/core";
import { uploadNodeFile } from "@/lib/api/nodes";
import type {
  Graph,
  NodeDefinition,
  PortType,
  RunMode,
} from "@/lib/core-contracts";
import { Button } from "@/components/ui/Button";
import {
  Play,
  Square,
  Plus,
  Undo2,
  Redo2,
  Copy,
  Trash2,
  Check,
  Search,
  X,
  Layers,
  Sparkles,
  DollarSign,
} from "@/components/ui/icons";
import { cn } from "@/lib/utils";
import dynamic from "next/dynamic";
import { TemplateGroupNode } from "@/components/canvas/TemplateGroupNode";

const CreateVideoModal = dynamic(
  () => import("@/components/studio/CreateVideoModal").then((m) => m.CreateVideoModal),
  { ssr: false }
);

const nodeTypes = {
  studioCard: StudioNode,
  templateGroup: TemplateGroupNode,
};

const edgeTypes = {
  default: StudioEdge,
};

const DATA_LEGEND = [
  { type: "text", color: "bg-[#737373]" },
  { type: "image", color: "bg-[#1b6c80]" },
  { type: "video", color: "bg-[#b4531a]" },
  { type: "audio", color: "bg-[#a86f0c]" },
] as const;

const uid = (prefix: string) =>
  `${prefix}_${Date.now().toString(36)}_${Math.random()
    .toString(36)
    .slice(2, 5)}`;

export function toCoreGraph(
  projectId: string,
  nodes: Node<StudioNodeData>[],
  edges: Edge[]
): Graph {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const real = nodes.filter((n) => n.type !== "templateGroup");
  return {
    id: `graph_${projectId}`,
    projectId,
    name: `Graph ${projectId}`,
    nodes: real.map((n) => ({
      id: n.id,
      type: n.data.nodeType,
      position: n.parentId && byId.get(n.parentId)
        ? { x: n.position.x + byId.get(n.parentId)!.position.x, y: n.position.y + byId.get(n.parentId)!.position.y }
        : n.position,
      params: n.data.params || {},
      inputs: (n.data.inputs as any) || {},
      state: (n.data.status || "idle") as any,
      isStale: Boolean(n.data.isStale),
      pinnedGenerationId: n.data.pinnedGenerationId ?? null,
      generations: (n.data.generations as any) || [],
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
}

function wouldCreateCycle(
  edges: Edge[],
  sourceId: string,
  targetId: string
): boolean {
  if (sourceId === targetId) return true;
  const visited = new Set<string>();
  const stack = [targetId];
  while (stack.length > 0) {
    const curr = stack.pop()!;
    if (curr === sourceId) return true;
    if (visited.has(curr)) continue;
    visited.add(curr);
    for (const e of edges) {
      if (e.source === curr) {
        stack.push(e.target);
      }
    }
  }
  return false;
}

export function StudioCanvas() {
  return (
    <ReactFlowProvider>
      <StudioCanvasInner />
    </ReactFlowProvider>
  );
}

/** Sợi dây tạm đi theo con trỏ khi bấm nút + trên card; Esc để huỷ. */
function LinkGhost({ from, onCancel }: { from: ActiveDragPort; onCancel: () => void }) {
  const [mouse, setMouse] = useState<{ x: number; y: number } | null>(null);
  const [origin, setOrigin] = useState<{ x: number; y: number } | null>(null);
  useEffect(() => {
    const el = document.querySelector(
      `.react-flow__node[data-id="${from.nodeId}"] .react-flow__handle[data-handleid="${from.portName}"]`
    ) as HTMLElement | null;
    if (el) {
      const r = el.getBoundingClientRect();
      setOrigin({ x: r.left + r.width / 2, y: r.top + r.height / 2 });
    }
    const move = (e: MouseEvent) => setMouse({ x: e.clientX, y: e.clientY });
    const key = (e: KeyboardEvent) => e.key === "Escape" && onCancel();
    window.addEventListener("mousemove", move);
    window.addEventListener("keydown", key);
    return () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("keydown", key);
    };
  }, [from, onCancel]);
  if (!origin || !mouse) return null;
  const dir = from.handleType === "source" ? 1 : -1;
  const dx = Math.max(60, Math.abs(mouse.x - origin.x) / 2) * dir;
  const color = PORT_TYPE_COLORS[from.portType] || "#737373";
  return (
    <svg className="pointer-events-none fixed inset-0 z-[60] h-full w-full" aria-hidden="true">
      <path
        d={`M ${origin.x} ${origin.y} C ${origin.x + dx} ${origin.y}, ${mouse.x - dx} ${mouse.y}, ${mouse.x} ${mouse.y}`}
        fill="none"
        stroke={color}
        strokeWidth={1.25}
        strokeDasharray="6 5"
      />
      <circle cx={mouse.x} cy={mouse.y} r={4} fill={color} />
    </svg>
  );
}

function StudioCanvasInner() {
  const t = useTranslations("canvas");
  const c = useTranslations("common");
  const { screenToFlowPosition, fitView } = useReactFlow();

  const {
    activeProjectId,
    nodeCatalog,
    nodes,
    edges,
    selectedNodeId,
    setSelectedNodeId,
    setNodesAndEdges,
    pushUndoSnapshot,
    undoCanvas,
    redoCanvas,
    undoStack,
    redoStack,
    loadCanvasTemplate,
    updateNodeExecutionState,
    updateNodeParams,
    isMockMode,
    setIsMockMode,
    isRunningGraph,
    setIsRunningGraph,
    setSaveState,
    validationResult,
    setValidationResult,
    coreHealth,
    perRunSpendingLimitUsd,
    addJob,
    updateJob,
    setActiveRightTab,
    setMobileSheetOpen,
  } = useStudioStore(
    useShallow((s: StudioStore) => ({
      activeProjectId: s.activeProjectId,
      nodeCatalog: s.nodeCatalog,
      nodes: s.nodes,
      edges: s.edges,
      selectedNodeId: s.selectedNodeId,
      setSelectedNodeId: s.setSelectedNodeId,
      setNodesAndEdges: s.setNodesAndEdges,
      pushUndoSnapshot: s.pushUndoSnapshot,
      undoCanvas: s.undoCanvas,
      redoCanvas: s.redoCanvas,
      undoStack: s.undoStack,
      redoStack: s.redoStack,
      loadCanvasTemplate: s.loadCanvasTemplate,
      updateNodeExecutionState: s.updateNodeExecutionState,
      updateNodeParams: s.updateNodeParams,
      isMockMode: s.isMockMode,
      setIsMockMode: s.setIsMockMode,
      isRunningGraph: s.isRunningGraph,
      setIsRunningGraph: s.setIsRunningGraph,
      setSaveState: s.setSaveState,
      validationResult: s.validationResult,
      setValidationResult: s.setValidationResult,
      coreHealth: s.coreHealth,
      perRunSpendingLimitUsd: s.perRunSpendingLimitUsd,
      addJob: s.addJob,
      updateJob: s.updateJob,
      setActiveRightTab: s.setActiveRightTab,
      setMobileSheetOpen: s.setMobileSheetOpen,
    }))
  );

  const [snapToGrid, setSnapToGrid] = useState(true);
  const [addMenuOpen, setAddMenuOpen] = useState(false);
  const [canvasMode, setCanvasMode] = useState<CanvasMode>("select");
  // Phím tắt công cụ (V/H/N/[/]/G/S): bảng hành động được gán lại mỗi lần render, bên dưới
  const toolKeyRef = useRef<Record<string, () => void>>({});
  const [addSearch, setAddSearch] = useState("");
  const [quickAddReq, setQuickAddReq] = useState<QuickAddRequest | null>(null);
  const [activeDragPort, setActiveDragPort] = useState<ActiveDragPort | null>(
    null
  );
  const [linkMode, setLinkMode] = useState(false);
  const [bannerMsg, setBannerMsg] = useState<{
    tone: "error" | "info" | "success";
    text: string;
  } | null>(null);
  const [createVideoModalOpen, setCreateVideoModalOpen] = useState(false);
  const [pendingRunConfirm, setPendingRunConfirm] = useState<{
    mode: RunMode;
    targetNodeId?: string;
    estimatedCost: number;
    nodeCount: number;
  } | null>(null);
  const [activeRunState, setActiveRunState] = useState<RunStateInfo | null>(null);

  // Khôi phục active run khi tải lại trang (Mục 2B-B)
  useEffect(() => {
    let isMounted = true;
    const checkActiveRun = async () => {
      try {
        const active = await fetchActiveRun(activeProjectId);
        if (!isMounted) return;
        if (active && active.status === "running") {
          setIsRunningGraph(true);
          setActiveRunState({ ...active, startedAt: Date.now() - (active.elapsedSec || 0) * 1000 });
          if (active.nodes) {
            for (const n of active.nodes) {
              updateNodeExecutionState(n.id, {
                status: n.state,
                progressPct: n.progressPct,
                errorMessage: n.error,
              });
            }
          }
        }
      } catch {
        // ignore
      }
    };
    checkActiveRun();
    return () => {
      isMounted = false;
    };
  }, [activeProjectId, setIsRunningGraph, updateNodeExecutionState]);

  // Canvas timer isolated to RunStatusBar (P-04)

  const canvasWrapperRef = useRef<HTMLDivElement>(null);
  const clipboardRef = useRef<{
    nodes: Node<StudioNodeData>[];
    edges: Edge[];
  } | null>(null);

  const baseDefMap = useMemo(
    () => new Map(nodeCatalog.map((d) => [d.typeName, d])),
    [nodeCatalog]
  );
  // Tra định nghĩa hiệu lực theo node (có tính cổng ghi đè riêng); gọi: defMap.get(node)
  const defMap = useMemo(
    () => ({
      get: (key: string | { data: { nodeType: string; params?: Record<string, any> } }) => {
        if (typeof key === "string") return baseDefMap.get(key);
        const d = baseDefMap.get(key.data.nodeType);
        return d ? applyPortOverride(d, key.data.params) : undefined;
      },
    }),
    [baseDefMap]
  );

  const connectedPorts = useMemo(() => {
    const s = new Set<string>();
    for (const e of edges) {
      if (e.source && e.sourceHandle) {
        s.add(`${e.source}:out:${e.sourceHandle}`);
      }
      if (e.target && e.targetHandle) {
        s.add(`${e.target}:in:${e.targetHandle}`);
      }
    }
    return s;
  }, [edges]);

  const nodeIdsKey = useMemo(() => nodes.map((n) => n.id).join(","), [nodes]);

  const nodeIssues = useMemo(() => {
    const map: Record<string, string[]> = {};
    if (!validationResult) return map;
    for (const msg of [
      ...validationResult.errors,
      ...validationResult.warnings,
    ]) {
      for (const n of nodes) {
        if (msg.includes(`'${n.id}'`)) {
          map[n.id] = [...(map[n.id] || []), msg];
        }
      }
    }
    return map;
  }, [validationResult, nodeIdsKey]);

  const totalEstimatedCost = useMemo(() => {
    return nodes.reduce(
      (acc, n) =>
        acc +
        estimateNodeCostUsd(
          n.data.nodeType,
          n.data.params || {},
          isMockMode
        ),
      0
    );
  }, [nodes, isMockMode]);

  const normalizedEdges = useMemo(
    () => edges.map((e) => (e.type === "smoothstep" || e.type === "step" ? { ...e, type: "default" } : e)),
    [edges]
  );

  // Nạp đồ thị đã lưu của dự án từ Core mỗi khi vào/đổi dự án
  const loadProjectGraph = useStudioStore((st) => st.loadProjectGraph);
  const graphLoaded = useStudioStore((st) => Boolean(st.loadedGraphs[activeProjectId]));
  useEffect(() => {
    loadProjectGraph(activeProjectId);
  }, [activeProjectId, loadProjectGraph]);

  // Debounced auto-save to Core (chỉ sau khi đã nạp đồ thị của dự án này)
  useEffect(() => {
    if (!graphLoaded) return;
    const timer = window.setTimeout(async () => {
      setSaveState("saving");
      const g = toCoreGraph(activeProjectId, nodes, edges);
      await saveGraphToCore(activeProjectId, g);
      setSaveState("saved");
    }, 650);
    return () => window.clearTimeout(timer);
  }, [activeProjectId, graphLoaded, nodes, edges, setSaveState]);

  const showBanner = useCallback(
    (tone: "error" | "info" | "success", text: string) => {
      setBannerMsg({ tone, text });
    },
    []
  );

  const onNodesChange: OnNodesChange<Node<StudioNodeData>> = useCallback(
    (changes) => {
      const updated = applyNodeChanges(changes, nodes) as Node<StudioNodeData>[];
      const sel = updated.find((n) => n.selected);
      if (sel && sel.id !== selectedNodeId) {
        setSelectedNodeId(sel.id);
      }
      setNodesAndEdges(updated, edges, false);
    },
    [nodes, edges, selectedNodeId, setSelectedNodeId, setNodesAndEdges]
  );

  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => {
      const updated = applyEdgeChanges(changes, edges);
      setNodesAndEdges(nodes, updated, false);
    },
    [nodes, edges, setNodesAndEdges]
  );

  // Đầu kéo dây bắt đầu từ cổng ra (source) hay cổng vào (target)
  const dragFromRef = useRef<"source" | "target" | null>(null);

  const handleConnectStart = useCallback(
    (
      _: any,
      params: {
        nodeId: string | null;
        handleId: string | null;
        handleType: "source" | "target" | null;
      }
    ) => {
      dragFromRef.current = params.handleType;
      if (!params.nodeId || !params.handleId || !params.handleType) return;
      const n = nodes.find((x) => x.id === params.nodeId);
      if (!n) return;
      const def = defMap.get(n);
      if (!def) return;
      const port =
        params.handleType === "source"
          ? def.outputPorts.find((p) => p.name === params.handleId)
          : def.inputPorts.find((p) => p.name === params.handleId);
      if (!port) return;
      setActiveDragPort({
        nodeId: params.nodeId,
        portName: port.name,
        portType: port.portType,
        handleType: params.handleType,
      });
    },
    [nodes, defMap]
  );

  const handleConnectEnd = useCallback(() => {
    setActiveDragPort(null);
    setLinkMode(false);
  }, []);

  const startLink = useCallback((port: ActiveDragPort) => {
    setActiveDragPort(port);
    setLinkMode(true);
  }, []);

  const cancelLink = useCallback(() => {
    setActiveDragPort(null);
    setLinkMode(false);
  }, []);

  const onConnect = useCallback(
    (conn: Connection) => {
      setActiveDragPort(null);
      // Không cho nối ngược: phải kéo từ cổng ra sang cổng vào
      if (dragFromRef.current === "target") {
        dragFromRef.current = null;
        showBanner("error", "Chỉ nối từ đầu ra sang đầu vào.");
        return;
      }
      dragFromRef.current = null;
      if (
        !conn.source ||
        !conn.target ||
        !conn.sourceHandle ||
        !conn.targetHandle
      )
        return;

      const srcNode = nodes.find((n) => n.id === conn.source);
      const tgtNode = nodes.find((n) => n.id === conn.target);
      if (!srcNode || !tgtNode) return;

      const srcDef = defMap.get(srcNode);
      const tgtDef = defMap.get(tgtNode);
      const srcPort = srcDef?.outputPorts.find(
        (p) => p.name === conn.sourceHandle
      );
      const tgtPort = tgtDef?.inputPorts.find(
        (p) => p.name === conn.targetHandle
      );

      if (!srcPort || !tgtPort) return;

      if (!isPortCompatible(srcPort.portType, tgtPort.portType)) {
        showBanner(
          "error",
          t("rejectIncompatible", {
            expected: t(`portTypes.${tgtPort.portType}` as any),
            actual: t(`portTypes.${srcPort.portType}` as any),
          })
        );
        return;
      }

      if (wouldCreateCycle(edges, conn.source, conn.target)) {
        showBanner("error", t("rejectCycle"));
        return;
      }

      const color = PORT_TYPE_COLORS[srcPort.portType] || "#737373";
      const newEdge: Edge = {
        id: uid("edge"),
        source: conn.source,
        sourceHandle: conn.sourceHandle,
        target: conn.target,
        targetHandle: conn.targetHandle,
        type: "default",
        style: { stroke: color, strokeWidth: 1.75 },
        data: { portType: srcPort.portType },
      };

      const filtered = edges.filter(
        (e) =>
          !(e.target === conn.target && e.targetHandle === conn.targetHandle)
      );
      setNodesAndEdges(nodes, [...filtered, newEdge], true);
      setBannerMsg(null);
    },
    [nodes, edges, defMap, setNodesAndEdges, showBanner, t]
  );

  const finishLink = useCallback(
    (nodeId: string, portName: string, handleType: "source" | "target") => {
      const from = activeDragPort;
      if (!from || from.nodeId === nodeId || from.handleType === handleType) return;
      const conn: Connection =
        from.handleType === "source"
          ? { source: from.nodeId, sourceHandle: from.portName, target: nodeId, targetHandle: portName }
          : { source: nodeId, sourceHandle: portName, target: from.nodeId, targetHandle: from.portName };
      onConnect(conn);
      setActiveDragPort(null);
      setLinkMode(false);
    },
    [activeDragPort, onConnect]
  );

  // Add node at center or specific coordinates
  const createNodeOfType = useCallback(
    (
      typeName: string,
      pos?: { x: number; y: number },
      extraParams?: Record<string, any>
    ): Node<StudioNodeData> => {
      const def = defMap.get(typeName) || nodeCatalog[0];
      // Loại node tuỳ biến: tạo node thuộc loại gốc, kèm cổng + tên riêng
      const base = def.baseType ? baseDefMap.get(def.baseType) : undefined;
      const defaultPos = pos || {
        x: 240 + (nodes.length % 4) * 80,
        y: 120 + (nodes.length % 3) * 60,
      };
      return {
        id: uid(`node_${typeName}`),
        type: "studioCard",
        position: defaultPos,
        selected: true,
        data: {
          nodeType: base ? base.typeName : def.typeName,
          status: "idle",
          params: {
            ...(base?.defaultParams || {}),
            ...(def.defaultParams || {}),
            ...(base
              ? {
                  _ports: { inputs: def.inputPorts, outputs: def.outputPorts },
                  _customName: def.displayName,
                  _customType: def.typeName,
                }
              : {}),
            ...(extraParams || {}),
          },
          generations: [],
        },
      };
    },
    [defMap, baseDefMap, nodeCatalog, nodes.length]
  );

  const handlePlaceNewNode = useCallback(
    (typeName: string, pos?: { x: number; y: number }, params?: Record<string, any>) => {
      const newNode = createNodeOfType(typeName, pos, params);
      const nextNodes = [
        ...nodes.map((n) => ({ ...n, selected: false })),
        newNode,
      ];
      setNodesAndEdges(nextNodes, edges, true);
      setSelectedNodeId(newNode.id);
      setAddMenuOpen(false);
    },
    [createNodeOfType, nodes, edges, setNodesAndEdges, setSelectedNodeId]
  );

  // Quick-add before or after a specific node & port, auto-wiring
  const handleSelectQuickAddNode = useCallback(
    (def: NodeDefinition) => {
      if (!quickAddReq) return;
      const anchor = nodes.find((n) => n.id === quickAddReq.anchorNodeId);
      if (!anchor) {
        setQuickAddReq(null);
        return;
      }

      const pos =
        quickAddReq.direction === "after"
          ? { x: anchor.position.x + 340, y: anchor.position.y }
          : { x: Math.max(20, anchor.position.x - 340), y: anchor.position.y };

      const newNode = createNodeOfType(def.typeName, pos);
      let newEdge: Edge | null = null;

      if (quickAddReq.direction === "after") {
        const targetPort = def.inputPorts.find((p) =>
          isPortCompatible(quickAddReq.portType, p.portType)
        );
        if (targetPort) {
          newEdge = {
            id: uid("edge"),
            source: anchor.id,
            sourceHandle: quickAddReq.portName,
            target: newNode.id,
            targetHandle: targetPort.name,
            type: "default",
            style: {
              stroke: PORT_TYPE_COLORS[quickAddReq.portType] || "#737373",
              strokeWidth: 1.75,
            },
          };
        }
      } else {
        const sourcePort = def.outputPorts.find((p) =>
          isPortCompatible(p.portType, quickAddReq.portType)
        );
        if (sourcePort) {
          newEdge = {
            id: uid("edge"),
            source: newNode.id,
            sourceHandle: sourcePort.name,
            target: anchor.id,
            targetHandle: quickAddReq.portName,
            type: "default",
            style: {
              stroke: PORT_TYPE_COLORS[sourcePort.portType] || "#737373",
              strokeWidth: 1.75,
            },
          };
        }
      }

      const nextNodes = [
        ...nodes.map((n) => ({ ...n, selected: false })),
        newNode,
      ];
      const nextEdges = newEdge ? [...edges, newEdge] : edges;
      setNodesAndEdges(nextNodes, nextEdges, true);
      setSelectedNodeId(newNode.id);
      setQuickAddReq(null);
    },
    [
      quickAddReq,
      nodes,
      edges,
      createNodeOfType,
      setNodesAndEdges,
      setSelectedNodeId,
    ]
  );

  // Selected node "+ Bước trước" / "+ Bước sau" toolbar triggers
  const triggerStepRelativeToSelected = useCallback(
    (direction: "before" | "after") => {
      const sel =
        nodes.find((n) => n.id === selectedNodeId) ||
        nodes.find((n) => n.selected);
      if (!sel) return;
      const def = defMap.get(sel);
      if (!def) return;
      if (direction === "before" && def.inputPorts.length > 0) {
        const p = def.inputPorts[0];
        setQuickAddReq({
          anchorNodeId: sel.id,
          direction: "before",
          portName: p.name,
          portType: p.portType,
        });
      } else if (direction === "after" && def.outputPorts.length > 0) {
        const p = def.outputPorts[0];
        setQuickAddReq({
          anchorNodeId: sel.id,
          direction: "after",
          portName: p.name,
          portType: p.portType,
        });
      }
    },
    [nodes, selectedNodeId, defMap]
  );

  // Copy, Paste, Duplicate, Delete, Group
  const handleDuplicateSelected = useCallback(() => {
    const selected = nodes.filter(
      (n) => n.selected || n.id === selectedNodeId
    );
    if (selected.length === 0) return;
    const copies = selected.map((n) => ({
      ...n,
      id: uid(`node_${n.data.nodeType}`),
      position: { x: n.position.x + 36, y: n.position.y + 36 },
      selected: true,
    }));
    setNodesAndEdges(
      [...nodes.map((n) => ({ ...n, selected: false })), ...copies],
      edges,
      true
    );
    setSelectedNodeId(copies[0].id);
  }, [nodes, edges, selectedNodeId, setNodesAndEdges, setSelectedNodeId]);

  const handleDeleteSelected = useCallback(() => {
    const selectedIds = new Set(
      nodes
        .filter((n) => n.selected || n.id === selectedNodeId)
        .map((n) => n.id)
    );
    const hasSelectedEdges = edges.some((e) => e.selected);
    if (selectedIds.size === 0 && !hasSelectedEdges) return;
    nodes.forEach((n) => {
      if (n.parentId && selectedIds.has(n.parentId)) selectedIds.add(n.id);
    });
    const nextNodes = nodes.filter((n) => !selectedIds.has(n.id));
    const nextEdges = edges.filter(
      (e) =>
        !e.selected &&
        !selectedIds.has(e.source) &&
        !selectedIds.has(e.target)
    );
    setNodesAndEdges(nextNodes, nextEdges, true);
    setSelectedNodeId(nextNodes[0]?.id || null);
  }, [nodes, edges, selectedNodeId, setNodesAndEdges, setSelectedNodeId]);

  const handleCopy = useCallback(() => {
    const sel = nodes.filter((n) => n.selected || n.id === selectedNodeId);
    if (sel.length === 0) return;
    const ids = new Set(sel.map((n) => n.id));
    clipboardRef.current = {
      nodes: sel,
      edges: edges.filter((e) => ids.has(e.source) && ids.has(e.target)),
    };
  }, [nodes, edges, selectedNodeId]);

  const handlePaste = useCallback(() => {
    const clip = clipboardRef.current;
    if (!clip) return;
    const idMap = new Map(
      clip.nodes.map((n) => [n.id, uid(`node_${n.data.nodeType}`)])
    );
    const newNodes = clip.nodes.map((n) => ({
      ...n,
      id: idMap.get(n.id)!,
      position: { x: n.position.x + 48, y: n.position.y + 48 },
      selected: true,
    }));
    const newEdges = clip.edges.map((e) => ({
      ...e,
      id: uid("edge"),
      source: idMap.get(e.source)!,
      target: idMap.get(e.target)!,
    }));
    setNodesAndEdges(
      [...nodes.map((n) => ({ ...n, selected: false })), ...newNodes],
      [...edges, ...newEdges],
      true
    );
  }, [nodes, edges, setNodesAndEdges]);

  const handleAlignGroup = useCallback(() => {
    // Sắp xếp tự động: cột trái → phải theo thứ tự chạy, trục chính ở giữa
    const nextNodes = autoLayout(nodes, edges);
    setNodesAndEdges(nextNodes, edges, true);
    setTimeout(() => fitView({ padding: 0.12, duration: 300 }), 60);
  }, [nodes, edges, setNodesAndEdges, fitView]);

  // Keyboard shortcuts: Delete, Ctrl+Z, Ctrl+Shift+Z, Ctrl+D, Ctrl+C, Ctrl+V
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      if (
        el &&
        (el.tagName === "INPUT" ||
          el.tagName === "TEXTAREA" ||
          el.tagName === "SELECT" ||
          el.isContentEditable)
      ) {
        return;
      }
      if (e.key === "Delete" || e.key === "Backspace") {
        e.preventDefault();
        handleDeleteSelected();
        return;
      }
      if (!(e.metaKey || e.ctrlKey) && !e.altKey) {
        const act = toolKeyRef.current[e.key.toLowerCase()];
        if (act) {
          e.preventDefault();
          act();
          return;
        }
      }
      if (!(e.metaKey || e.ctrlKey)) return;
      const k = e.key.toLowerCase();
      if (k === "z") {
        e.preventDefault();
        if (e.shiftKey) redoCanvas();
        else undoCanvas();
      } else if (k === "d") {
        e.preventDefault();
        handleDuplicateSelected();
      } else if (k === "c") {
        e.preventDefault();
        handleCopy();
      } else if (k === "v") {
        e.preventDefault();
        handlePaste();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    handleDeleteSelected,
    undoCanvas,
    redoCanvas,
    handleDuplicateSelected,
    handleCopy,
    handlePaste,
  ]);

  toolKeyRef.current = {
    v: () => setCanvasMode("select"),
    h: () => setCanvasMode("pan"),
    n: () => setAddMenuOpen((v) => !v),
    "[": () => triggerStepRelativeToSelected("before"),
    "]": () => triggerStepRelativeToSelected("after"),
    g: () => handleAlignGroup(),
    s: () => setSnapToGrid((v) => !v),
  };

  // Validate graph via Core
  const handleValidateGraph = useCallback(async () => {
    const g = toCoreGraph(activeProjectId, nodes, edges);
    const res = await validateGraphWithCore(activeProjectId, g, nodeCatalog);
    setValidationResult(res);
    if (res.isValid && res.warnings.length === 0) {
      showBanner("success", t("validateOk", { count: nodes.length }));
    } else {
      showBanner(
        "error",
        res.errors[0] || res.warnings[0] || "Graph validation warning"
      );
    }
  }, [
    activeProjectId,
    nodes,
    edges,
    nodeCatalog,
    setValidationResult,
    showBanner,
    t,
  ]);

  // Request run: check upstream if single node, then open cost confirmation modal
  const handleRequestRun = useCallback(
    (mode: RunMode, targetNodeId?: string) => {
      if (mode === "single_node" && targetNodeId) {
        const target = nodes.find((n) => n.id === targetNodeId);
        const def = target ? defMap.get(target) : undefined;
        if (target && def) {
          for (const port of def.inputPorts) {
            if (!port.required) continue;
            const incomingEdge = edges.find(
              (e) => e.target === target.id && e.targetHandle === port.name
            );
            const hasParam =
              target.data.params &&
              target.data.params[port.name] !== undefined &&
              target.data.params[port.name] !== "";
            if (!incomingEdge && !hasParam) {
              const portLabel = t(`portTypes.${port.portType}` as any);
              updateNodeExecutionState(target.id, {
                errorMessage: t("upstreamMissing", { port: portLabel }),
              });
              showBanner("error", t("upstreamMissing", { port: portLabel }));
              return;
            }
            if (incomingEdge) {
              const upstreamNode = nodes.find(
                (n) => n.id === incomingEdge.source
              );
              if (
                upstreamNode &&
                upstreamNode.data.status !== "succeeded" &&
                upstreamNode.data.nodeType !== "text" &&
                upstreamNode.data.nodeType !== "character"
              ) {
                const portLabel = t(`portTypes.${port.portType}` as any);
                updateNodeExecutionState(target.id, {
                  errorMessage: t("upstreamMissing", { port: portLabel }),
                });
                showBanner("error", t("upstreamMissing", { port: portLabel }));
                return;
              }
            }
          }
        }
      }

      const est =
        mode === "single_node" && targetNodeId
          ? estimateNodeCostUsd(
              nodes.find((n) => n.id === targetNodeId)?.data.nodeType || "text",
              nodes.find((n) => n.id === targetNodeId)?.data.params || {},
              isMockMode
            )
          : totalEstimatedCost;

      setPendingRunConfirm({
        mode,
        targetNodeId,
        estimatedCost: est,
        nodeCount: mode === "single_node" ? 1 : nodes.length,
      });
    },
    [
      nodes,
      edges,
      defMap,
      isMockMode,
      totalEstimatedCost,
      updateNodeExecutionState,
      showBanner,
      t,
    ]
  );

  // Execute confirmed run via Core + SSE (with local deterministic fallback)
  const executeConfirmedRun = useCallback(async () => {
    if (!pendingRunConfirm) return;
    const { mode, targetNodeId, estimatedCost } = pendingRunConfirm;
    setPendingRunConfirm(null);
    setIsRunningGraph(true);
    setBannerMsg(null);

    const jobId = uid("job");
    addJob({
      id: jobId,
      projectId: activeProjectId,
      type: "render",
      status: "running",
      progress: 10,
      estimatedCostUsd: estimatedCost,
      actualCostUsd: 0,
      createdAt: new Date().toISOString(),
    });

    // Helper to produce realistic preview per node type
    const buildNodeOutputPreview = (
      nodeType: string
    ): Partial<StudioNodeData> => {
      if (
        nodeType === "image_gen" ||
        nodeType === "image_edit" ||
        nodeType === "image"
      ) {
        return {
          previewType: "image",
          previewUrl: "/demo/characters/soc_nho_01.png",
          summaryText: "Ảnh 3D Pixar Sóc Nhỏ (100cm) khung hình 9:16",
        };
      }
      if (nodeType === "quality_check") {
        return {
          previewType: "image",
          previewUrl: "/demo/characters/soc_nho_02.png",
          summaryText: "PASS (score=0.94 >= 0.85) · Đạt chuẩn nhận diện DNA",
        };
      }
      if (nodeType === "video_gen" || nodeType === "hyperframes_render") {
        return {
          previewType: "video",
          previewUrl: "/demo/scenes/canh_01.mp4",
          summaryText:
            nodeType === "hyperframes_render"
              ? "Thành phẩm HyperFrames 9:16 · Safe Zone 180/320px"
              : "Video Veo 2 · 8.0s · 24fps",
        };
      }
      if (nodeType === "voice_tts") {
        return {
          previewType: "audio",
          previewUrl: "/demo/audio/canh_01.mp3",
          summaryText: "Giọng soc-nho OmniVoice · -14 LUFS · 44.1kHz",
        };
      }
      if (nodeType === "script") {
        return {
          previewType: "text",
          summaryText:
            "Đã tách 6 phân cảnh (45 giây): Cảnh 1 kẹo hạt dẻ -> Cảnh 6 cười tươi",
        };
      }
      if (nodeType === "export") {
        return {
          previewType: "text",
          summaryText:
            "Đã đóng gói output/soc_nho_tap_01.mp4 & manifest xuất bản",
        };
      }
      return {
        previewType: "text",
        summaryText: "Hoàn tất xử lý",
      };
    };

    const targetNodes =
      mode === "single_node" && targetNodeId
        ? nodes.filter((n) => n.id === targetNodeId)
        : nodes;

    const catalogNow = useStudioStore.getState().nodeCatalog;
    const initialRunNodes = targetNodes.map((n) => {
      const base = catalogNow.find((d) => d.typeName === n.data.nodeType);
      const custom = typeof n.data.params?._customName === "string" ? n.data.params._customName : "";
      return {
        id: n.id,
        type: n.data.nodeType,
        name: custom || base?.displayName || n.data.nodeType,
        // Chế độ "chạy cả chuỗi" bỏ qua node đã có kết quả và chưa lỗi thời -> hiện là dùng lại kết quả trước
        state:
          mode === "all" && n.data.status === "succeeded" && !n.data.isStale ? "skipped" : "pending",
        progressPct: 0,
        detail:
          mode === "all" && n.data.status === "succeeded" && !n.data.isStale
            ? "Dùng lại kết quả lần chạy trước (đầu vào không đổi, không tốn phí)"
            : undefined,
      };
    });

    setActiveRunState({
      status: "running",
      stage: "Bắt đầu khởi chạy...",
      progress: 0.05,
      progressPct: 5,
      elapsedSec: 0,
      startedAt: Date.now(),
      nodes: initialRunNodes,
    });

    // Subscribe to Core SSE if online
    let es: EventSource | null = null;
    try {
      es = new EventSource(`${CORE_URL}/projects/${activeProjectId}/events`);
      es.onmessage = (ev) => {
        try {
          const payload = JSON.parse(ev.data);
          const nodeId = payload.nodeId;
          const status = payload.status || payload.state;
          const progressPct = payload.progressPct ?? (payload.progress ? Math.round(payload.progress * 100) : undefined);
          const message = payload.message;

          if (nodeId && status) {
            updateNodeExecutionState(nodeId, {
              status,
              progressPct,
              lastLog: message,
              errorMessage:
                status === "failed"
                  ? String(message || "Node chạy thất bại").replace(/^Node dừng lại:\s*/, "")
                  : undefined,
            });

            setActiveRunState((prev) => {
              if (!prev) return prev;
              const updatedNodes = (prev.nodes || []).map((n) => {
                if (n.id !== nodeId) return n;
                const logs = [...(n.logs || [])];
                if (message && logs[logs.length - 1] !== message) logs.push(String(message));
                return {
                  ...n,
                  state: status,
                  progressPct: progressPct ?? n.progressPct,
                  model: payload.model ?? n.model,
                  provider: payload.provider ?? n.provider,
                  detail: payload.detail ?? n.detail,
                  estimatedCostUsd: payload.estimatedCostUsd ?? n.estimatedCostUsd,
                  costUsd: payload.costUsd ?? n.costUsd,
                  durationSec: payload.durationSec ?? n.durationSec,
                  startedAt: n.startedAt ?? (status === "running" ? Date.now() : undefined),
                  logs: logs.slice(-40),
                };
              });
              return {
                ...prev,
                nodes: updatedNodes,
                currentNodeId: nodeId,
                stage: message || prev.stage,
                progressPct: progressPct !== undefined ? Math.max(prev.progressPct || 0, progressPct) : prev.progressPct,
              };
            });
          }
        } catch {
          // ignore
        }
      };
    } catch {
      // ignore if offline
    }

    // Chờ kênh SSE mở xong rồi mới gửi lệnh chạy, để không mất các sự kiện đầu tiên
    if (es) {
      const source = es;
      await new Promise<void>((resolve) => {
        const t = setTimeout(resolve, 1500);
        source.addEventListener("open", () => {
          clearTimeout(t);
          resolve();
        }, { once: true });
        if (source.readyState === 1) {
          clearTimeout(t);
          resolve();
        }
      });
    }

    try {
      // Đánh dấu queued cho các node sẽ chạy (không fake running/25%!)
      for (const n of targetNodes) {
        updateNodeExecutionState(n.id, {
          status: "queued",
          progressPct: 0,
          errorMessage: undefined,
        });
      }

      const g = toCoreGraph(activeProjectId, nodes, edges);
      let runError = "";
      const summary = await runGraphOnCore(activeProjectId, {
        graph: g,
        mode,
        targetNodeId,
        spendingLimitUsd: perRunSpendingLimitUsd,
        mockMode: isMockMode,
      }).catch((err) => {
        runError = String(err?.message || err);
        setBannerMsg({ tone: "error", text: `Lỗi chạy đồ thị: ${runError}` });
        return null;
      });

      // Cập nhật kết quả thực tế cho từng node
      for (const n of targetNodes) {
        const isExecuted = summary?.executedNodes?.includes(n.id);
        const isFailed = summary?.failedNodes?.includes(n.id);
        const nodeError = summary?.errors?.[n.id];

        if (!summary) {
          // Không nhận được kết quả (mất kết nối Core, lỗi mạng...) → báo rõ dưới từng node
          updateNodeExecutionState(n.id, {
            status: "failed",
            errorMessage: `Không chạy được: ${runError || "không nhận được phản hồi từ Core"}`,
          });
        } else if (isFailed) {
          updateNodeExecutionState(n.id, {
            status: "failed",
            errorMessage: nodeError || "Lỗi xử lý",
          });
        } else if (isExecuted || summary?.isSuccess) {
          // Chế độ thật: không gắn ảnh/video/audio demo giả; chỉ mock mới có preview mẫu
          const preview: Partial<StudioNodeData> = isMockMode
            ? buildNodeOutputPreview(n.data.nodeType)
            : { previewType: "text", summaryText: "Đã chạy xong — xem kết quả trong thư mục output của project" };
          const genId = uid("gen");
          const newGen: NodeGenerationRecord = {
            id: genId,
            createdAt: new Date().toISOString(),
            previewUrl: preview.previewUrl,
            previewType: preview.previewType,
            summaryText: preview.summaryText,
            costUsd: estimateNodeCostUsd(
              n.data.nodeType,
              n.data.params || {},
              isMockMode
            ),
            model: n.data.params?.model,
          };
          const existingGens = n.data.generations || [];
          updateNodeExecutionState(n.id, {
            status: "succeeded",
            isStale: false,
            progressPct: 100,
            ...preview,
            generations: [newGen, ...existingGens],
            pinnedGenerationId: genId,
            errorMessage: undefined,
          });
        }
      }

      const isAllOk = summary ? summary.isSuccess : false;
      setActiveRunState((prev) =>
        prev && prev.status === "cancelled"
          ? prev
          : prev
          ? {
              ...prev,
              status: isAllOk ? "completed" : "failed",
              progressPct: isAllOk ? 100 : prev.progressPct,
              stage: isAllOk ? "Hoàn tất xuất sắc!" : "Gặp lỗi trong quá trình thực thi",
            }
          : null
      );

      // Core báo node con lỗi thời theo từng cổng ra (chỉ con nối cổng có dữ liệu đổi) -> đồng bộ lên thẻ
      const executedSet = new Set(summary?.executedNodes || []);
      for (const sid of summary?.staleNodes || []) {
        if (!executedSet.has(sid)) {
          updateNodeExecutionState(sid, { isStale: true });
        }
      }

      if (useStudioStore.getState().jobs.find((j) => j.id === jobId)?.status === "cancelled") return;
      updateJob(jobId, {
        status: isAllOk ? "completed" : "failed",
        progress: isAllOk ? 100 : 50,
        actualCostUsd: isMockMode ? 0 : estimatedCost,
        completedAt: new Date().toISOString(),
      });
    } finally {
      es?.close();
      setIsRunningGraph(false);
    }
  }, [
    pendingRunConfirm,
    activeProjectId,
    nodes,
    edges,
    isMockMode,
    perRunSpendingLimitUsd,
    addJob,
    updateJob,
    updateNodeExecutionState,
    setIsRunningGraph,
  ]);

  const handleStopRun = useCallback(async () => {
    await cancelRunOnCore(activeProjectId);
    setIsRunningGraph(false);
    setActiveRunState((prev) =>
      prev ? { ...prev, status: "cancelled", stage: "Đã huỷ theo yêu cầu người dùng" } : null
    );
    for (const j of useStudioStore.getState().jobs) {
      if (j.projectId === activeProjectId && (j.status === "running" || j.status === "queued")) {
        updateJob(j.id, { status: "cancelled", completedAt: new Date().toISOString() });
      }
    }
    for (const n of nodes) {
      if (n.data.status === "running" || n.data.status === "queued") {
        updateNodeExecutionState(n.id, { status: "idle", progressPct: 0 });
      }
    }
  }, [activeProjectId, nodes, setIsRunningGraph, updateNodeExecutionState, updateJob]);

  // Drag & Drop Character, Node, hoặc Files trực tiếp từ máy tính lên Canvas
  const handleDragOverCanvas = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
  }, []);

  const handleDropOnCanvas = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      const pos = screenToFlowPosition({ x: e.clientX, y: e.clientY });

      // 1. Kiểm tra nếu kéo thả File từ máy tính
      const files = e.dataTransfer.files ? Array.from(e.dataTransfer.files) : [];
      if (files.length > 0) {
        // Kiểm tra xem thả trúng node nào đang có trên canvas không
        const targetEl = (e.target as HTMLElement).closest("[data-id]");
        const targetNodeId = targetEl?.getAttribute("data-id");
        const existingNode = targetNodeId ? nodes.find((n) => n.id === targetNodeId) : null;

        if (existingNode) {
          const f = files[0];
          if (["image", "character_image", "scene"].includes(existingNode.data.nodeType) && f.type.startsWith("image/")) {
            try {
              const res = await uploadNodeFile(activeProjectId, f);
              updateNodeParams(existingNode.id, { uri: res.uri, name: res.name || f.name });
            } catch {
              // ignore
            }
            return;
          }
          if (existingNode.data.nodeType === "script" && (f.name.endsWith(".txt") || f.name.endsWith(".md"))) {
            const text = await f.text();
            updateNodeParams(existingNode.id, { mode: "paste", rawScript: text });
            return;
          }
        }

        // Thả tự do lên canvas
        const imageFiles = files.filter((f) => f.type.startsWith("image/"));
        const textFiles = files.filter((f) => f.name.endsWith(".txt") || f.name.endsWith(".md") || f.type.startsWith("text/"));
        const videoFiles = files.filter((f) => f.type.startsWith("video/"));

        // Thả nhiều ảnh -> tạo nhiều node image xếp lưới gọn (3 cột)
        if (imageFiles.length > 0) {
          imageFiles.forEach(async (file, idx) => {
            const col = idx % 3;
            const row = Math.floor(idx / 3);
            const nodePos = {
              x: pos.x + col * 320,
              y: pos.y + row * 340,
            };
            try {
              const res = await uploadNodeFile(activeProjectId, file);
              handlePlaceNewNode("image", nodePos, {
                uri: res.uri,
                name: res.name || file.name,
              });
            } catch {
              handlePlaceNewNode("image", nodePos, { name: file.name });
            }
          });
        }

        // Thả file văn bản / kịch bản
        if (textFiles.length > 0) {
          textFiles.forEach(async (file, idx) => {
            const text = await file.text();
            const nodePos = { x: pos.x + idx * 320, y: pos.y };
            const isScriptLike = /^(?:[#*>\s]*)(?:Cảnh|Scene|Phân cảnh|\bBi:|\bKoala:|\bSóc Nhỏ:)|[-=_*~]{3,}/im.test(text);
            if (isScriptLike) {
              handlePlaceNewNode("script", nodePos, {
                mode: "paste",
                rawScript: text,
              });
            } else {
              handlePlaceNewNode("text", nodePos, {
                content: text,
              });
            }
          });
        }

        if (videoFiles.length > 0) {
          videoFiles.forEach((file, idx) => {
            const nodePos = { x: pos.x + idx * 320, y: pos.y };
            handlePlaceNewNode("video_gen", nodePos, { prompt: file.name });
          });
        }
        return;
      }

      // 2. Kéo thả nhân vật từ panel
      const charId = e.dataTransfer.getData("application/x-studio-character");
      if (charId) {
        handlePlaceNewNode("character", pos, { characterId: charId });
        return;
      }

      // 3. Kéo thả loại node từ menu
      const nodeType = e.dataTransfer.getData("application/x-studio-nodetype");
      if (nodeType) {
        handlePlaceNewNode(nodeType, pos);
      }
    },
    [screenToFlowPosition, handlePlaceNewNode, nodes, activeProjectId, updateNodeParams]
  );

  // Lắng nghe dán Clipboard (Ctrl+V) khi focus canvas
  useEffect(() => {
    const handleCanvasPaste = async (e: ClipboardEvent) => {
      const activeEl = document.activeElement as HTMLElement;
      if (
        activeEl &&
        (activeEl.tagName === "INPUT" ||
          activeEl.tagName === "TEXTAREA" ||
          activeEl.isContentEditable)
      ) {
        return;
      }

      if (!canvasWrapperRef.current) return;
      const rect = canvasWrapperRef.current.getBoundingClientRect();
      const centerScreen = {
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      };
      const pos = screenToFlowPosition(centerScreen);

      // Dán ảnh từ clipboard
      if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
        const f = e.clipboardData.files[0];
        if (f.type.startsWith("image/")) {
          e.preventDefault();
          try {
            const res = await uploadNodeFile(activeProjectId, f);
            handlePlaceNewNode("image", pos, {
              uri: res.uri,
              name: res.name || "clipboard_image.png",
            });
          } catch {
            handlePlaceNewNode("image", pos, { name: "clipboard_image.png" });
          }
          return;
        }
      }

      // Dán văn bản từ clipboard
      const text = e.clipboardData?.getData("text/plain");
      if (text && text.trim()) {
        e.preventDefault();
        const isScriptLike = /^(?:[#*>\s]*)(?:Cảnh|Scene|Phân cảnh|\bBi:|\bKoala:|\bSóc Nhỏ:)|[-=_*~]{3,}/im.test(text);
        if (isScriptLike) {
          handlePlaceNewNode("script", pos, { mode: "paste", rawScript: text });
        } else {
          handlePlaceNewNode("text", pos, { content: text });
        }
      }
    };

    window.addEventListener("paste", handleCanvasPaste);
    return () => window.removeEventListener("paste", handleCanvasPaste);
  }, [activeProjectId, screenToFlowPosition, handlePlaceNewNode]);

  // Danh sách node phụ ẩn khỏi bảng thêm node (giữ backend, chỉ ẩn UI)
  const HIDDEN_NODE_TYPES = useMemo(
    () =>
      new Set([
        "source_video",
        "localize",
        "blueprint_analyze",
        "script_from_blueprint",
        "channel_insight",
      ]),
    []
  );

  // Filtered node definitions for Add Node popover
  const filteredAddDefs = useMemo(() => {
    const visibleCatalog = nodeCatalog.filter(
      (d) => !HIDDEN_NODE_TYPES.has(d.typeName)
    );
    const q = addSearch.trim().toLowerCase();
    if (!q) return visibleCatalog;
    return visibleCatalog.filter(
      (d) =>
        d.displayName.toLowerCase().includes(q) ||
        d.typeName.toLowerCase().includes(q) ||
        d.category.toLowerCase().includes(q) ||
        d.description.toLowerCase().includes(q)
    );
  }, [nodeCatalog, addSearch, HIDDEN_NODE_TYPES]);

  // Filtered node definitions for Quick-Add (+) port menu: ONLY compatible types!
  const compatibleQuickAddDefs = useMemo(() => {
    if (!quickAddReq) return [];
    return nodeCatalog
      .filter((d) => !HIDDEN_NODE_TYPES.has(d.typeName))
      .filter((d) => {
        if (quickAddReq.direction === "after") {
          return d.inputPorts.some((p) =>
            isPortCompatible(quickAddReq.portType, p.portType)
          );
        } else {
          return d.outputPorts.some((p) =>
            isPortCompatible(p.portType, quickAddReq.portType)
          );
        }
      });
  }, [nodeCatalog, quickAddReq, HIDDEN_NODE_TYPES]);

  const stepInfo = useMemo(() => analyzeGraph(nodes, edges), [nodeIdsKey, edges]);

  const onOpenQuickAdd = useCallback((req: QuickAddRequest) => setQuickAddReq(req), []);
  const onOpenNodeInspector = useCallback(
    (nodeId: string) => {
      setSelectedNodeId(nodeId);
      setActiveRightTab("node");
    },
    [setSelectedNodeId, setActiveRightTab]
  );

  const contextValue = useMemo(
    () => ({
      activeDragPort,
      connectedPorts,
      nodeIssues,
      onOpenQuickAdd,
      onRequestRun: handleRequestRun,
      onOpenNodeInspector,
      linkMode,
      startLink,
      finishLink,
      cancelLink,
      stepInfo,
    }),
    [
      stepInfo,
      linkMode,
      startLink,
      finishLink,
      cancelLink,
      activeDragPort,
      connectedPorts,
      nodeIssues,
      handleRequestRun,
      setSelectedNodeId,
      setActiveRightTab,
    ]
  );

  return (
    <CanvasInteractionContext.Provider value={contextValue}>
      {linkMode && activeDragPort && <LinkGhost from={activeDragPort} onCancel={cancelLink} />}
      <div className="relative flex h-full min-w-0 flex-1 flex-col bg-card">
        {/* Core Offline or Outdated Status Banner (still allows mock graph building & testing) */}
        {!coreHealth.online ? (
          <div
            role="status"
            className="flex items-center justify-between gap-2 border-b border-border bg-accent/60 px-3 py-1.5 text-xs text-foreground"
          >
            <span>{t("coreOfflineBanner")}</span>
          </div>
        ) : coreHealth.outdated ? (
          <div
            role="status"
            className="flex items-center justify-between gap-2 border-b border-border bg-amber-500/10 text-amber-600 dark:text-amber-400 px-3 py-1.5 text-xs"
          >
            <span>{t("coreOutdatedBanner")}</span>
          </div>
        ) : null}

        {/* Validation / Connection Rejection Banner */}
        {bannerMsg && (
          <div
            role="alert"
            className={cn(
              "flex items-center justify-between gap-2 border-b border-border px-3 py-1.5 text-xs",
              bannerMsg.tone === "error"
                ? "bg-semantic-danger/10 text-semantic-danger"
                : bannerMsg.tone === "success"
                ? "bg-semantic-success/10 text-semantic-success"
                : "bg-accent text-foreground"
            )}
          >
            <span>{bannerMsg.text}</span>
            <button
              type="button"
              onClick={() => setBannerMsg(null)}
              aria-label={c("close")}
              className="rounded p-0.5 hover:bg-accent"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* Top Canvas Toolbar */}
        <div className="absolute right-[72px] top-3 z-20 hidden items-center gap-1 rounded-full border border-border bg-card/90 p-1 backdrop-blur select-none md:flex">
          {/* Kiểm tra đồ thị: chấm trạng thái hợp lệ / có lỗi */}
          <button
            type="button"
            onClick={handleValidateGraph}
            title={validationResult ? (validationResult.isValid ? "Đồ thị hợp lệ — kiểm tra lại" : `${validationResult.errors.length} lỗi — kiểm tra lại`) : t("validateBtn")}
            aria-label={t("validateBtn")}
            className="relative flex h-8 w-8 items-center justify-center rounded-full text-foreground transition-colors hover:bg-accent active:scale-90"
          >
            <Check className="h-4 w-4" />
            {validationResult && (
              <span className={cn("absolute right-1 top-1 h-2 w-2 rounded-full ring-2 ring-card", validationResult.isValid ? "bg-semantic-success" : "bg-semantic-danger")} />
            )}
          </button>

          {/* Thông tin: số bước (xong/tổng), chế độ, chi phí ước tính */}
          <span title="Số bước đã xong / tổng" className="flex h-8 items-center gap-1 rounded-full bg-muted/50 px-2.5 text-xs tnum text-foreground">
            <Layers className="h-3.5 w-3.5 text-muted-foreground" />
            {nodes.filter((n) => n.data.status === "succeeded").length}/{nodes.length}
          </span>

          <button
            type="button"
            onClick={() => setIsMockMode(!isMockMode)}
            title={isMockMode ? `${t("mockMode")} — bấm để chuyển sang API thật` : `${t("liveMode")} — bấm để chuyển sang chạy thử`}
            aria-label={isMockMode ? t("mockMode") : t("liveMode")}
            aria-pressed={!isMockMode}
            className={cn(
              "flex h-8 items-center gap-1.5 rounded-full px-2.5 text-xs transition-colors active:scale-95",
              isMockMode ? "bg-muted/50 text-foreground" : "bg-brand/10 text-brand"
            )}
          >
            <span className={cn("h-1.5 w-1.5 rounded-full", isMockMode ? "bg-muted-foreground" : "bg-brand")} />
            <span className="font-medium">{isMockMode ? "Mock" : "Live"}</span>
          </button>

          <span title={`Chi phí ước tính cả chuỗi: $${totalEstimatedCost.toFixed(2)}${isMockMode ? " (chạy thử: thực tế $0)" : ""}`} className="flex h-8 items-center gap-1 rounded-full bg-muted/50 px-2.5 text-xs tnum text-foreground">
            <DollarSign className="h-3.5 w-3.5 text-muted-foreground" />
            {isMockMode ? "0.00" : totalEstimatedCost.toFixed(2)}
          </span>

          {isRunningGraph ? (
            <button
              type="button"
              onClick={handleStopRun}
              title={t("stop")}
              aria-label={t("stop")}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-semantic-danger text-semantic-danger transition-transform active:scale-90"
            >
              <Square className="h-3 w-3" />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => handleRequestRun("all")}
              title={t("runAll")}
              aria-label={t("runAll")}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform hover:bg-primary-hover active:scale-90"
            >
              <Play className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Quick-Add Filtered Node Menu (when user clicks + on an input/output port or + Bước trước/sau) */}
        {quickAddReq && (
          <div className="absolute left-4 top-14 z-40 w-80 rounded-lg border border-border bg-popover p-3 text-popover-foreground">
            <div className="mb-2 flex items-center justify-between border-b border-border pb-1.5">
              <span className="text-xs font-semibold">
                {quickAddReq.direction === "after"
                  ? t("addDownstreamPort")
                  : t("addUpstreamPort")}{" "}
                ({t(`portTypes.${quickAddReq.portType}` as any)})
              </span>
              <button
                type="button"
                onClick={() => setQuickAddReq(null)}
                aria-label={c("close")}
                className="rounded p-0.5 text-muted-foreground hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            <ul className="max-h-60 space-y-1 overflow-y-auto scroll-quiet">
              {compatibleQuickAddDefs.map((def) => (
                <li key={def.typeName}>
                  <button
                    type="button"
                    onClick={() => handleSelectQuickAddNode(def)}
                    className="flex w-full flex-col rounded border border-transparent px-2 py-1.5 text-left hover:border-border hover:bg-accent"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-foreground">
                        {def.displayName}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {t(`categories.${def.category}` as any)}
                      </span>
                    </div>
                    <span className="text-[13px] text-muted-foreground line-clamp-1">
                      {def.description}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Cost Confirmation Dialog before Running */}
        {pendingRunConfirm && (
          <div
            role="dialog"
            aria-modal="true"
            aria-label={t("costConfirmTitle")}
            className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 p-4"
          >
            <div className="w-full max-w-md rounded-lg border border-border bg-popover p-4 text-popover-foreground space-y-3">
              <h2 className="text-sm font-semibold">{t("costConfirmTitle")}</h2>
              <p className="text-xs text-muted-foreground leading-relaxed tnum">
                {t("costConfirmDesc", {
                  mode:
                    pendingRunConfirm.mode === "single_node"
                      ? t("runNode")
                      : pendingRunConfirm.mode === "downstream"
                      ? t("runFromHere")
                      : t("runAll"),
                  nodeCount: pendingRunConfirm.nodeCount,
                  cost: pendingRunConfirm.estimatedCost.toFixed(2),
                  limit: perRunSpendingLimitUsd.toFixed(2),
                })}
              </p>
              {isMockMode && (
                <p className="rounded border border-border bg-accent/60 px-2.5 py-1.5 text-xs text-foreground">
                  {t("costConfirmMockNote")}
                </p>
              )}
              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setPendingRunConfirm(null)}
                  className="h-8 rounded-md border border-border bg-card px-3 text-xs text-foreground hover:bg-accent"
                >
                  {c("cancel")}
                </button>
                <button
                  type="button"
                  onClick={executeConfirmedRun}
                  className="h-8 rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground"
                >
                  {t("costConfirmProceed")}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Desktop Interactive Canvas (>= 768px) */}
        <div
          ref={canvasWrapperRef}
          onDragOver={handleDragOverCanvas}
          onDrop={handleDropOnCanvas}
          className="hidden md:block relative flex-1 min-h-0 w-full"
        >
          <RunStatusBar
            isRunning={isRunningGraph}
            activeRun={activeRunState}
            onCancel={handleStopRun}
            onOpenJobsTab={() => setActiveRightTab("jobs")}
            onDismiss={() => setActiveRunState(null)}
          />
          {/* Never-Empty Canvas Template Picker when nodes.length === 0 */}
          {nodes.length === 0 ? (
            <div className="flex h-full w-full items-center justify-center p-6">
              <div className="max-w-xl w-full rounded-xl border border-border bg-card p-6 space-y-4">
                <div>
                  <h2 className="text-base font-semibold text-foreground">
                    {t("emptyTitle")}
                  </h2>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {t("emptySubtitle")}
                  </p>
                </div>

                {/* Primary Automated Creation Banner */}
                <div className="rounded-xl border border-primary/40 bg-primary/5 p-4 flex items-center justify-between">
                  <div className="space-y-1">
                    <h3 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <Sparkles className="h-4 w-4 text-primary" />
                      Tạo video tự động từ 8 mẫu dựng sẵn
                    </h3>
                    <p className="text-[12px] text-muted-foreground">
                      Tự sinh kịch bản, nối sẵn đồ thị node chuẩn, tự áp thông số nền tảng không cần chỉnh tay.
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => setCreateVideoModalOpen(true)}
                    className="shrink-0 ml-3"
                  >
                    Tạo video ngay
                  </Button>
                </div>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div className="flex flex-col justify-between rounded-lg border border-border bg-muted/20 p-4 space-y-3">
                    <div>
                      <h3 className="text-xs font-semibold text-foreground">
                        {t("tplSocNhoTitle")}
                      </h3>
                      <p className="mt-1 text-[13px] text-muted-foreground leading-relaxed">
                        {t("tplSocNhoDesc")}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => loadCanvasTemplate("soc_nho_story")}
                    >
                      {t("tplSocNhoAction")}
                    </Button>
                  </div>

                  <div className="flex flex-col justify-between rounded-lg border border-border bg-muted/20 p-4 space-y-3">
                    <div>
                      <h3 className="text-xs font-semibold text-foreground">
                        {t("tplBlankTitle")}
                      </h3>
                      <p className="mt-1 text-[13px] text-muted-foreground leading-relaxed">
                        {t("tplBlankDesc")}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => loadCanvasTemplate("blank")}
                    >
                      {t("tplBlankAction")}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={normalizedEdges}
              defaultEdgeOptions={{ type: "default" }}
              connectionLineType={ConnectionLineType.Bezier}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onConnectStart={handleConnectStart}
              onConnectEnd={handleConnectEnd}
              onNodeDragStart={() => pushUndoSnapshot()}
              onNodeClick={(_, n) => setSelectedNodeId(n.id)}
              onPaneClick={() => linkMode && cancelLink()}
              snapToGrid={snapToGrid}
              panOnDrag={canvasMode === "pan" ? true : [1, 2]}
              selectionOnDrag={canvasMode === "select"}
              nodesDraggable={canvasMode === "select"}
              snapGrid={[24, 24]}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              defaultViewport={{ x: 72, y: 72, zoom: 1 }}
              minZoom={0.4}
              maxZoom={1.4}
              proOptions={{ hideAttribution: true }}
              className="bg-card"
            >
              <Panel position="top-left" style={{ top: "calc(50% - 44px)", transform: "translateY(-50%)", margin: 12 }}>
                <StudioStickToolbar
                  mode={canvasMode}
                  onMode={setCanvasMode}
                  addOpen={addMenuOpen}
                  onToggleAdd={() => setAddMenuOpen((v) => !v)}
                  addMenu={
                <div className="z-40 w-[min(340px,calc(100vw-32px))] rounded-lg border border-border bg-popover p-2.5 text-popover-foreground">
                    <div className="relative mb-2">
                      <Search className="pointer-events-none absolute left-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
                      <input
                        type="search"
                        value={addSearch}
                        onChange={(e) => setAddSearch(e.target.value)}
                        placeholder={t("addNodePlaceholder")}
                        autoFocus
                        className="h-7 w-full rounded border border-border bg-background pl-7 pr-2 text-xs text-foreground"
                      />
                    </div>
                    <ul className="max-h-72 space-y-1 overflow-y-auto scroll-quiet">
                      {filteredAddDefs.map((def) => (
                        <li key={def.typeName}>
                          <button
                            type="button"
                            draggable
                            onDragStart={(e) =>
                              e.dataTransfer.setData(
                                "application/x-studio-nodetype",
                                def.typeName
                              )
                            }
                            onClick={() => handlePlaceNewNode(def.typeName)}
                            className="flex w-full flex-col gap-0.5 rounded-md border border-transparent px-2 py-1.5 text-left hover:border-border hover:bg-accent"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-semibold text-foreground">
                                {def.displayName}
                              </span>
                              <span className="rounded border border-border bg-card px-1.5 py-0.5 text-xs text-muted-foreground">
                                {t(`categories.${def.category}` as any)}
                              </span>
                            </div>
                            <p className="text-[13px] text-muted-foreground line-clamp-1">
                              {def.description}
                            </p>
                            <p className="font-mono text-xs text-muted-foreground">
                              In:{" "}
                              {def.inputPorts.map((p) => p.name).join(", ") ||
                                "—"}{" "}
                              → Out:{" "}
                              {def.outputPorts.map((p) => p.name).join(", ") ||
                                "—"}
                            </p>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
  
                  }
                  hasSelection={Boolean(selectedNodeId)}
                  onStepBefore={() => triggerStepRelativeToSelected("before")}
                  onStepAfter={() => triggerStepRelativeToSelected("after")}
                  onDuplicate={handleDuplicateSelected}
                  onDelete={handleDeleteSelected}
                  onGroup={handleAlignGroup}
                  onUndo={undoCanvas}
                  onRedo={redoCanvas}
                  canUndo={undoStack.length > 0}
                  canRedo={redoStack.length > 0}
                  snap={snapToGrid}
                  onToggleSnap={() => setSnapToGrid((v) => !v)}
                  onCreateVideo={() => setCreateVideoModalOpen(true)}
                />
              </Panel>
              <Controls
                showInteractive={false}
                position="bottom-right"
                className="!mb-3 !ml-3 !mr-3 xl:!mr-[14rem] !mt-3 !border !border-border !bg-card !shadow-none !rounded-md"
              />
              <MiniMap
                zoomable
                pannable
                className="!hidden xl:!block !m-3 !border !border-border !bg-card !shadow-none !rounded-md"
                nodeColor={() => "hsl(var(--accent))"}
                maskColor="rgba(0, 0, 0, 0.06)"
              />
            </ReactFlow>
          )}

          {/* Port & Wire Data Type Legend (Bottom-Left of Canvas) */}
          <aside
            aria-label="Port data type legend"
            className="pointer-events-none absolute bottom-3 right-16 xl:right-[17rem] z-10 flex items-center gap-3 rounded-md border border-border bg-card px-3 py-1.5 text-[13px] text-muted-foreground select-none"
          >
            {DATA_LEGEND.map((item) => (
              <span key={item.type} title={t(`legend.${item.type}`)} className="flex items-center gap-1.5">
                <span
                  className={cn("h-2 w-2 rounded-full", item.color)}
                  aria-hidden="true"
                />
              </span>
            ))}
          </aside>
        </div>

        {/* Mobile Read-Only Vertical Node List (< 768px) */}
        <div className="md:hidden flex-1 overflow-y-auto px-4 py-4 space-y-3 scroll-quiet">
          <div className="flex items-center justify-between border-b border-border pb-2.5">
            <div>
              <h2 className="text-sm font-semibold text-foreground">
                {t("mobileListTitle")}
              </h2>
              <p className="text-[13px] text-muted-foreground tnum">
                {t("estimatedCost", { cost: totalEstimatedCost.toFixed(2) })}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setMobileSheetOpen(true)}
              className="h-8 rounded-md border border-border bg-card px-3 text-[13px] font-medium text-foreground"
            >
              {t("openSheetBtn")}
            </button>
          </div>

          <ol className="space-y-2.5">
            {nodes.map((node, index) => {
              const def = defMap.get(node);
              return (
                <li
                  key={node.id}
                  onClick={() => {
                    setSelectedNodeId(node.id);
                    setActiveRightTab("node");
                    setMobileSheetOpen(true);
                  }}
                  className="rounded-lg border border-border bg-card p-3.5 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-foreground tnum">
                      {index + 1}. {def?.displayName || node.data.nodeType}
                    </span>
                    <span className="text-[13px] text-muted-foreground">
                      {t(`status.${node.data.status || "idle"}` as any)}
                    </span>
                  </div>
                  <p className="text-[13px] text-muted-foreground leading-snug">
                    {def?.description}
                  </p>
                </li>
              );
            })}
          </ol>
        </div>

        {/* Create Video 3-Step Modal */}
        <CreateVideoModal
          isOpen={createVideoModalOpen}
          onClose={() => setCreateVideoModalOpen(false)}
        />
      </div>
    </CanvasInteractionContext.Provider>
  );
}
