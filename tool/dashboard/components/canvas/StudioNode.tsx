"use client";

import { enterOnce } from "@/lib/motion";
import React, { memo, useEffect, useMemo, useRef, useState } from "react";
import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { useStudioStore } from "@/store";
import {
  PORT_TYPE_COLORS,
  type StudioNodeData,
} from "@/store/slices/canvasSlice";
import {
  FALLBACK_NODE_TYPES,
  estimateNodeCostUsd,
  isPortCompatible,
} from "@/lib/core-api";
import { useCanvasInteraction } from "@/components/canvas/CanvasContext";
import { NodeBody } from "./NodeBody";
import { Reveal } from "./Reveal";
import { applyPortOverride } from "@/lib/node-ports";
import { PortValueInput } from "./PortValueInput";
import { useHubScope } from "@/lib/hub";
import { CharacterCard } from "@/components/canvas/CharacterCard";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Plus,
  ChevronsDown,
  Sliders,
  ChevronDown,
  ChevronUp,
  Loader2,
  Circle,
  CircleDot,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  FileText,
  MessageSquare,
  Images,
  Users,
  Pencil,
  RefreshCw,
  Layers,
  Sparkles,
  Volume2,
  ShieldCheck,
  Film,
  Download,
} from "@/components/ui/icons";

export type StudioCardNodeType = Node<StudioNodeData, "studioCard">;
export type StudioNodeType = StudioCardNodeType;
export type DataType = string;
export type { StudioNodeData };

/** Card nguồn (không có đầu vào): có 2 chế độ xem / chỉnh sửa. Xem ai/rules/node-card-style.md */
const SOURCE_TYPES = new Set(["text", "image", "character"]);
/** Card xử lý có 2 chế độ: xem = kết quả; chỉnh sửa = tham số + cổng đầy đủ. */
const PROCESS_TYPES = new Set(["script", "image_gen", "video_gen", "voice_tts", "image_edit", "quality_check", "vision_analyze", "captions", "hyperframes_render", "export", "policy"]);

/** Icon thay cho chữ kiểu dữ liệu ở cổng. */
function portIconOf(portType: string): React.ComponentType<{ className?: string; strokeWidth?: number }> | null {
  if (portType === "text") return FileText;
  if (portType === "image" || portType === "image[]") return Images;
  if (portType === "character") return Users;
  if (portType === "audio") return Volume2;
  if (portType === "video") return Film;
  if (portType === "scenes") return Layers;
  if (portType === "policy") return ShieldCheck;
  if (portType === "dialogue") return MessageSquare;
  if (portType === "voice_clips") return Volume2;
  return null;
}

/** Card mở sẵn chế độ chi tiết khi hiển thị. */
const DETAIL_DEFAULT_TYPES = new Set(["character", "hyperframes_render", "export"]);

export const StudioNode = memo(function StudioNode({
  id,
  data,
  selected,
}: NodeProps<StudioCardNodeType>) {
  const t = useTranslations("canvas");
  const nodeCatalog = useStudioStore((s) => s.nodeCatalog);
  const isMockMode = useStudioStore((s) => s.isMockMode);
  const characters = useStudioStore((s) => s.characters);
  const isFlashing = useStudioStore((s) => s.flashingNodeId === id);
  const setSelectedNodeId = useStudioStore((s) => s.setSelectedNodeId);
  const flashNode = useStudioStore((s) => s.flashNode);
  // Nguồn của từng cổng vào: "Node nào · cổng nào" (rút thành chuỗi để chỉ render lại khi nguồn đổi)
  const incomingKey = useStudioStore((s: any) => {
    const rows: string[] = [];
    for (const e of s.edges) {
      if (e.target !== id) continue;
      const src = s.nodes.find((n: any) => n.id === e.source);
      if (!src) continue;
      const base = s.nodeCatalog.find((d: any) => d.typeName === src.data.nodeType);
      const custom = typeof src.data.params?._customName === "string" ? src.data.params._customName : "";
      rows.push([e.targetHandle, e.source, e.sourceHandle, custom || base?.displayName || src.data.nodeType].join("\u0001"));
    }
    return rows.join("\u0002");
  });
  const incoming = useMemo(() => {
    const m = new Map<string, { srcId: string; srcPort: string; srcName: string }[]>();
    if (!incomingKey) return m;
    for (const row of incomingKey.split("\u0002")) {
      const [port, srcId, srcPort, srcName] = row.split("\u0001");
      m.set(port, [...(m.get(port) || []), { srcId, srcPort, srcName }]);
    }
    return m;
  }, [incomingKey]);
  const {
    activeDragPort,
    connectedPorts,
    nodeIssues,
    onOpenQuickAdd,
    onRequestRun,
    onOpenNodeInspector,
    linkMode,
    startLink,
    finishLink,
    stepInfo,
  } = useCanvasInteraction();


  const baseDef =
    nodeCatalog.find((d) => d.typeName === data.nodeType) ||
    FALLBACK_NODE_TYPES.find((d) => d.typeName === data.nodeType) ||
    FALLBACK_NODE_TYPES[0];
  // Cổng/tên ghi đè riêng của node (tuỳ biến trong thanh bên phải)
  const def = useMemo(() => applyPortOverride(baseDef, data.params), [baseDef, data.params]);

  const categoryLabel = t(`categories.${def.category}` as any);

  // Compute state key: idle, ready, running, succeeded, failed, stale
  const hasAllRequiredInputs = def.inputPorts
    .filter((p) => p.required)
    .every(
      (p) =>
        connectedPorts.has(`${id}:in:${p.name}`) ||
        (data.params &&
          data.params[p.name] !== undefined &&
          data.params[p.name] !== "")
    );

  const stateKey = data.isStale
    ? "stale"
    : data.status === "idle" && hasAllRequiredInputs
    ? "ready"
    : data.status || "idle";

  const stateLabel = t(`status.${stateKey}` as any);
  const estCost = estimateNodeCostUsd(
    def.typeName,
    data.params || {},
    isMockMode
  );
  const issues = nodeIssues[id] || [];
  // isFlashing selected from store

  // Compact parameter summary
  const compactParams: string[] = [];
  const p = data.params || {};
  if (def.typeName === "character") {
    const ch = characters.find((c) => c.id === p.characterId);
    if (ch) {
      compactParams.push(`${ch.name} (${ch.heightCm} cm)`);
      compactParams.push(ch.voiceId);
    } else if (p.characterId) {
      compactParams.push(String(p.characterId));
    }
  } else {
    if (p.model) compactParams.push(String(p.model));
    if (p.aspectRatio) compactParams.push(String(p.aspectRatio));
    if (p.durationSec) compactParams.push(`${p.durationSec}s`);
    if (p.voiceId) compactParams.push(String(p.voiceId));
    if (p.tempo) compactParams.push(`${p.tempo}x`);
    if (p.targetSceneCount) compactParams.push(`${p.targetSceneCount} cảnh`);
    if (p.thresholdScore) compactParams.push(`>= ${p.thresholdScore}`);
    if (p.template) compactParams.push(String(p.template));
    if (p.outputFileName) compactParams.push(String(p.outputFileName));
  }

  const contentPreview =
    typeof p.content === "string" && p.content.trim() ? p.content.trim() : null;

  // Character reference preview if node is character
  const boundChar =
    def.typeName === "character"
      ? characters.find((c) => c.id === p.characterId)
      : undefined;

  const pinnedIdx = data.pinnedGenerationId
    ? data.generations.findIndex((g) => g.id === data.pinnedGenerationId) + 1
    : data.generations.length;


  const CategoryIcon =
    {
      Input: FileText,
      Identity: Users,
      Structure: Layers,
      Intelligence: Sparkles,
      Generation: Sparkles,
      Audio: Volume2,
      Quality: ShieldCheck,
      Composition: Film,
      Output: Download,
    }[def.category as string] || Layers;

  const StatusIcon =
    stateKey === "running"
      ? Loader2
      : stateKey === "succeeded" || stateKey === "completed"
      ? CheckCircle2
      : stateKey === "failed"
      ? AlertTriangle
      : stateKey === "stale"
      ? RotateCcw
      : stateKey === "ready"
      ? CircleDot
      : Circle;
  const statusColor =
    stateKey === "running"
      ? "text-brand"
      : stateKey === "failed"
      ? "text-semantic-danger"
      : stateKey === "succeeded" || stateKey === "completed"
      ? "text-semantic-success"
      : stateKey === "stale"
      ? "text-semantic-warning"
      : stateKey === "ready"
      ? "text-foreground"
      : "text-muted-foreground";


  // Bố cục 3 vùng: NHẬN (trên) · LÀM (giữa) · TRẢ (dưới). Cổng bám theo hàng của vùng tương ứng.
  const HEADER = 44;
  const LABEL = 22;
  const ROW = 22;
  const FOOTER = 30;
  const hasIn = def.inputPorts.length > 0;
  const hasOut = def.outputPorts.length > 0;
  const inTop = (i: number) => HEADER + 1 + LABEL + i * ROW + ROW / 2;
  // Chân card chỉ hiện khi có nội dung (chi phí > 0 hoặc có lịch sử tạo); không còn nút "chạy từ đây xuống"
  const hasFooter = !SOURCE_TYPES.has(def.typeName) && (estCost > 0 || data.generations.length > 0);
  const outBottom = (i: number) =>
    (hasFooter ? FOOTER : 8) + (def.outputPorts.length - 1 - i) * ROW + ROW / 2;

  const isSourceNode = SOURCE_TYPES.has(def.typeName);
  const isModeNode = isSourceNode || PROCESS_TYPES.has(def.typeName);
  const [collapsed, setCollapsed] = useState(false);
  const [charPicker, setCharPicker] = useState(false);
  const [renaming, setRenaming] = useState(false);
  // Tên hiển thị: tên tuỳ đặt > (node nhân vật) tên nhân vật > tên loại node
  const hasCustomName = typeof p._customName === "string" && p._customName.trim() !== "";
  const nodeTitle = hasCustomName
    ? def.displayName
    : def.typeName === "character" && boundChar
    ? boundChar.name
    : def.displayName;
  const updateNodeParams = useStudioStore((s) => s.updateNodeParams);
  useEffect(() => {
    if (!selected) setCharPicker(false);
  }, [selected]);
  // Card Text có 2 chế độ: xem (mặc định) / chỉnh sửa (mở rộng). Bấm tiêu đề để đổi.
  // Mỗi card tự quản lý trạng thái của mình (không ảnh hưởng card khác, không tự đóng khi bỏ chọn).
  // Cổng vào đang mở khung chọn nguồn (node khác / tải lên / dự án / nhân vật)
  const [activeInPort, setActiveInPort] = useState<string | null>(null);
  /** Vị trí dọc (px, tính từ đầu thẻ) của ô input đang mở để panel nguồn hiện ngay cạnh */
  const [activeInTop, setActiveInTop] = useState(0);
  const [expanded, setExpanded] = useState(() => DETAIL_DEFAULT_TYPES.has(def.typeName));

  // Kiểm tra đủ input: cổng bắt buộc phải được nối hoặc đã có giá trị
  const requiredPorts = def.inputPorts.filter((pt) => pt.required);
  const missingPorts = requiredPorts.filter(
    (pt) =>
      !connectedPorts.has(`${id}:in:${pt.name}`) &&
      (p[pt.name] === undefined || p[pt.name] === "")
  );
  const inputsOk = missingPorts.length === 0;

  // Thông báo lỗi THỐNG NHẤT cho mọi node — luôn hiện ngay dưới card.
  // Ưu tiên: lỗi chạy thật > lỗi kiểm tra đồ thị > thiếu đầu vào (tính trực tiếp từ dây đang nối).
  const missingMessage = inputsOk
    ? null
    : `Thiếu đầu vào bắt buộc: ${missingPorts
        .map((pt) => `${pt.name} (${t(`portTypes.${pt.portType}` as any)})`)
        .join(", ")}. Hãy nối node cấp dữ liệu vào.`;
  const staleRunError = data.errorMessage && data.status !== "failed" && inputsOk;
  const errorText =
    (staleRunError ? null : data.errorMessage) ||
    issues[0] ||
    missingMessage ||
    (data.status === "failed" ? "Node chạy thất bại nhưng không có chi tiết lỗi. Xem log chạy để biết thêm." : null);
  const hasError = Boolean(errorText);

  const [guide, setGuide] = useState<"in" | "out" | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!guide) return;
    const close = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as globalThis.Node)) setGuide(null);
    };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, [guide]);
  useEffect(() => {
    if (!selected) setGuide(null);
  }, [selected]);

  const typeLabel = (pt: string) => t(`portTypes.${pt}` as any);

  const linkTargetable =
    linkMode &&
    activeDragPort &&
    activeDragPort.nodeId !== id &&
    (activeDragPort.handleType === "source"
      ? def.inputPorts.some((pt) => isPortCompatible(activeDragPort.portType, pt.portType))
      : def.outputPorts.some((pt) => isPortCompatible(pt.portType, activeDragPort.portType)));

  const portHandle = (
    port: (typeof def.inputPorts)[number],
    index: number,
    side: "in" | "out"
  ) => {
    const isIn = side === "in";
    const portColor = PORT_TYPE_COLORS[port.portType] || "#737373";
    const drag = activeDragPort;
    const other = drag && drag.nodeId !== id && drag.handleType === (isIn ? "source" : "target");
    const compatible =
      other &&
      (isIn
        ? isPortCompatible(drag!.portType, port.portType)
        : isPortCompatible(port.portType, drag!.portType));
    const connected = connectedPorts.has(`${id}:${side}:${port.name}`);
    const missing = isIn && port.required && !connected;
    const pos = isIn
      ? isModeNode && !expanded
        ? { top: `${((index + 1) / (def.inputPorts.length + 1)) * 100}%`, transform: "translate(-50%, -50%)" }
        : { top: inTop(index), transform: "translate(-50%, -50%)" }
      : isModeNode && !expanded
      ? { top: `${((index + 1) / (def.outputPorts.length + 1)) * 100}%`, bottom: "auto", transform: "translate(50%, -50%)" }
      : { top: "auto", bottom: outBottom(index), transform: "translate(50%, 50%)" };
    return (
      <Handle
        key={`${side}:${port.name}`}
        id={port.name}
        type={isIn ? "target" : "source"}
        position={isIn ? Position.Left : Position.Right}
        onClick={(e) => {
          if (!linkMode) return;
          e.stopPropagation();
          if (compatible) finishLink(id, port.name, isIn ? "target" : "source");
        }}
        title={`${port.name} · ${typeLabel(port.portType)}${port.required ? " *" : ""}`}
        aria-label={`${port.name} (${typeLabel(port.portType)})`}
        style={{
          ...pos,
          [isIn ? "left" : "right"]: -1,
          width: portIconOf(port.portType) ? 20 : compatible ? 18 : 16,
          height: portIconOf(port.portType) ? 20 : compatible ? 18 : 16,
          borderRadius: portIconOf(port.portType) ? "50%" : isIn ? "50%" : 4,
          backgroundColor: portIconOf(port.portType) ? "hsl(var(--muted))" : portColor,
          color: portColor,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: portIconOf(port.portType) ? (compatible ? "1.5px solid hsl(var(--brand))" : missing ? "1.5px solid hsl(var(--danger))" : "1px solid hsl(var(--border) / 0.6)") : compatible
            ? "2px solid hsl(var(--brand))"
            : missing
            ? "2px solid hsl(var(--danger))"
            : "2px solid hsl(var(--card))",
          opacity: other && !compatible ? 0.3 : 1,
          boxShadow: compatible ? `0 0 0 4px ${portColor}55` : missing ? "0 0 0 2px hsl(var(--danger) / 0.25)" : undefined,
          cursor: linkMode && compatible ? "pointer" : undefined,
          transition: "all 150ms",
        }}
      >
        {(() => { const PI = portIconOf(port.portType); return PI ? <PI className="h-3 w-3 pointer-events-none opacity-70" strokeWidth={1.75} /> : null; })()}
      </Handle>
    );
  };

  const IconBtn = ({
    label,
    onClick,
    children,
    className,
  }: {
    label: string;
    onClick: () => void;
    children: React.ReactNode;
    className?: string;
  }) => (
    <button
      type="button"
      title={label}
      aria-label={label}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className={cn(
        "nodrag flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground active:scale-90",
        className
      )}
    >
      {children}
    </button>
  );

  const zoneLabel = (text: string, hint: string) => (
    <div className="flex items-baseline justify-between px-3" style={{ height: LABEL }}>
      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{text}</span>
      <span className="text-[10px] text-muted-foreground/70">{hint}</span>
    </div>
  );

  /** Nút + luôn ở giữa mép card: bấm để kéo dây (1 cổng) hoặc chọn cổng (nhiều cổng). Các node nối được sẽ sáng lên. */
  const plusBtn = (side: "in" | "out") => {
    const isIn = side === "in";
    const ports = isIn ? def.inputPorts : def.outputPorts;
    if (ports.length === 0) return null;
    const active = guide === side;
    const begin = (port: (typeof ports)[number]) => {
      setGuide(null);
      startLink({
        nodeId: id,
        portName: port.name,
        portType: port.portType,
        handleType: isIn ? "target" : "source",
      });
    };
    return (
      <>
        <button
          type="button"
          title={isIn ? "Nối đầu vào từ node khác" : "Nối đầu ra tới node khác"}
          aria-label={isIn ? "Nối đầu vào" : "Nối đầu ra"}
          aria-expanded={active}
          onClick={(e) => {
            e.stopPropagation();
            if (ports.length === 1) begin(ports[0]);
            else setGuide(active ? null : side);
          }}
          style={{ top: "50%", [isIn ? "left" : "right"]: -34, transform: "translateY(-50%)" }}
          className={cn(
            "nodrag absolute z-20 flex h-5 w-5 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-sm transition-all hover:scale-110 hover:border-foreground hover:text-foreground",
            active || selected
              ? "opacity-100"
              : "pointer-events-none opacity-0 group-hover/node:pointer-events-auto group-hover/node:opacity-100"
          )}
        >
          <Plus className={cn("h-3 w-3 transition-transform", active && "rotate-45")} />
        </button>
        <AnimatePresence>
          {active && (
            <motion.div
              initial={{ opacity: 0, x: isIn ? 6 : -6, scale: 0.97 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              style={{ top: "50%", translateY: "-50%", [isIn ? "right" : "left"]: "calc(100% + 40px)" }}
              className="nodrag nowheel absolute z-30 w-56 space-y-1 rounded-xl border border-border bg-card p-1.5 text-xs shadow-lg"
            >
              <p className="px-1.5 pb-0.5 pt-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {isIn ? "Chọn đầu vào để nối" : "Chọn đầu ra để nối"}
              </p>
              {ports.map((port) => {
                const connected = connectedPorts.has(`${id}:${side}:${port.name}`);
                return (
                  <div key={port.name} className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        begin(port);
                      }}
                      className="flex min-w-0 flex-1 items-center gap-1.5 rounded-lg px-1.5 py-1.5 text-left transition-colors hover:bg-accent"
                    >
                      <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: PORT_TYPE_COLORS[port.portType] || "#737373" }} />
                      <span className="truncate font-medium text-foreground">{port.name}</span>
                      <span className="truncate text-muted-foreground">{typeLabel(port.portType)}</span>
                      <span className={cn("ml-auto shrink-0 text-[10px]", connected ? "text-semantic-success" : isIn && port.required ? "text-semantic-danger" : "text-muted-foreground")}>
                        {connected ? "đã nối" : isIn && port.required ? "cần" : ""}
                      </span>
                    </button>
                    <button
                      type="button"
                      title="Thêm node mới và tự nối"
                      aria-label="Thêm node mới"
                      onClick={(e) => {
                        e.stopPropagation();
                        setGuide(null);
                        onOpenQuickAdd({ anchorNodeId: id, direction: isIn ? "before" : "after", portName: port.name, portType: port.portType });
                      }}
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                    >
                      <Plus className="h-3 w-3" />
                    </button>
                  </div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </>
    );
  };

  const outputsDone = data.status === "succeeded" || data.status === "completed";
  const isCharacter = def.typeName === "character";
  // Cổng text: chỉ hiện icon thay cho chữ "text" thừa
  const portType = (port: { name: string; portType: string }) =>
    (() => {
      const PI = portIconOf(port.portType);
      return PI ? <PI className="h-3 w-3 shrink-0" /> : typeLabel(port.portType);
    })();

  return (
    <motion.div
      ref={rootRef}
      tabIndex={0}
      role="group"
      aria-label={`${def.displayName} (${stateLabel})`}
      initial={enterOnce(`node:${id}`, { opacity: 0 })}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
      onFocusCapture={(e) => {
        if (isSourceNode && (e.target as HTMLElement).tagName === "TEXTAREA") setExpanded(true);
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" && (e.target as HTMLElement).tagName !== "TEXTAREA") {
          e.preventDefault();
          e.stopPropagation();
          onRequestRun("single_node", id);
        }
      }}
      data-node-card=""
      className={cn(
        "group/node relative w-[300px] rounded-[14px] border bg-card text-foreground select-none transition-[border-color,box-shadow,opacity]",
        stateKey === "stale" && "opacity-80",
        stateKey === "running" && "node-running",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        linkTargetable && "border-brand ring-4 ring-brand/20",
        linkMode && !linkTargetable && activeDragPort?.nodeId !== id && "opacity-50",
        isFlashing
          ? "border-brand bg-brand/5"
          : hasError
          ? "border-semantic-danger"
          : selected
          ? "border-foreground"
          : !linkTargetable && "border-border hover:border-foreground/40"
      )}
      style={{ boxShadow: "none" }}
    >
      {stateKey === "running" && (
        <div className="pointer-events-none absolute inset-x-2 bottom-0 h-0.5 overflow-hidden rounded-full bg-muted">
          {typeof data.progressPct === "number" ? (
            <motion.div
              className="h-full bg-brand"
              initial={false}
              animate={{ width: `${Math.max(4, Math.min(100, data.progressPct))}%` }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              style={{ willChange: "width" }}
            />
          ) : (
            <div className="h-full w-2/5 rounded-full bg-brand animate-node-indeterminate" />
          )}
        </div>
      )}
      {def.inputPorts.map((pt, i) => portHandle(pt, i, "in"))}
      {def.outputPorts.map((pt, i) => portHandle(pt, i, "out"))}
      {plusBtn("in")}
      {plusBtn("out")}

      {/* Đầu card */}
      <div className="flex items-center gap-2 px-3 py-1.5" style={{ minHeight: HEADER + 4 }}>
        {stepInfo[id] && (
          <span
            title={stepInfo[id].main ? `Bước ${stepInfo[id].step} · trục chính` : `Bước ${stepInfo[id].step} · hỗ trợ`}
            className={cn(
              "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold tnum",
              stepInfo[id].main ? "bg-foreground text-background" : "border border-border text-muted-foreground"
            )}
          >
            {stepInfo[id].step}
          </span>
        )}
        <span
          title={categoryLabel}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent text-foreground"
        >
          <CategoryIcon className="h-3.5 w-3.5" />
        </span>
        <span
          className="min-w-0 flex-1 cursor-pointer line-clamp-2 break-words text-[15px] font-semibold leading-tight"
          title={isModeNode ? `${def.displayName} · nhấn để ${expanded ? "thu gọn" : "chỉnh sửa"}` : `${def.displayName} · nhấn đúp để ${collapsed ? "mở rộng" : "thu gọn"}`}
          onClick={isModeNode ? () => setExpanded((v) => !v) : undefined}
          onDoubleClick={(e) => {
            if (isModeNode) return;
            e.stopPropagation();
            setCollapsed((v) => !v);
          }}
        >
          {renaming ? (
            <input
              autoFocus
              defaultValue={nodeTitle}
              onClick={(e) => e.stopPropagation()}
              onDoubleClick={(e) => e.stopPropagation()}
              onBlur={(e) => {
                updateNodeParams(id, { _customName: e.target.value.trim() });
                setRenaming(false);
              }}
              onKeyDown={(e) => {
                e.stopPropagation();
                if (e.key === "Enter") (e.target as HTMLInputElement).blur();
                if (e.key === "Escape") setRenaming(false);
              }}
              className="nodrag w-full rounded border border-border bg-card px-1 text-[15px] font-semibold outline-none focus:border-foreground"
            />
          ) : (
            nodeTitle
          )}
        </span>
        {stateKey !== "ready" && stateKey !== "idle" && (
        <span title={`${stateLabel}${stateKey === "running" && typeof data.progressPct === "number" ? ` ${Math.round(data.progressPct)}%` : ""}`} className={cn("flex h-6 w-6 items-center justify-center", statusColor)}>
          <StatusIcon className={cn("h-3.5 w-3.5", stateKey === "running" && "animate-spin")} />
        </span>
        )}
        <IconBtn label="Đổi tên node" onClick={() => setRenaming(true)}>
          <Pencil className="h-3 w-3" />
        </IconBtn>
        <IconBtn label={t("editInNodeTab")} onClick={() => { setSelectedNodeId(id); onOpenNodeInspector(id); }}>
          <Sliders className="h-3.5 w-3.5" />
        </IconBtn>
        <IconBtn label={t("runNode")} onClick={() => onRequestRun("single_node", id)}>
          <Play className="h-3 w-3" />
        </IconBtn>
      </div>

      {/* 1. NHẬN — chỉ hiện khi node có đầu vào */}
      {hasIn && (
        <div className="border-t border-border/70">
         <Reveal show={!isModeNode || expanded}>
          <div className="flex items-center justify-between px-3" style={{ height: LABEL }}>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Nhận</span>
            {requiredPorts.length > 0 ? (
              <span className={cn("flex items-center gap-1 text-[10px] font-medium", inputsOk ? "text-semantic-success" : "text-semantic-danger")}>
                {inputsOk ? <CheckCircle2 className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                {inputsOk ? "Đủ đầu vào" : `Thiếu ${missingPorts.length}/${requiredPorts.length}`}
              </span>
            ) : (
              <span className="text-[10px] text-muted-foreground/70">Tuỳ chọn</span>
            )}
          </div>
          {def.inputPorts.map((port) => {
            const connected = connectedPorts.has(`${id}:in:${port.name}`);
            const filled = connected || (p[port.name] !== undefined && p[port.name] !== "");
            return (
              <div
                key={port.name}
                role="button"
                tabIndex={-1}
                title="Chọn nguồn cho đầu vào này"
                onClick={(e) => {
                  e.stopPropagation();
                  const row = e.currentTarget as HTMLElement;
                  const card = row.closest("[data-node-card]") as HTMLElement | null;
                  if (card) setActiveInTop(row.getBoundingClientRect().top - card.getBoundingClientRect().top);
                  setActiveInPort((cur) => (cur === port.name ? null : port.name));
                }}
                className={cn(
                  "nodrag relative flex cursor-pointer items-center gap-1.5 px-3 text-xs transition-colors hover:bg-accent/60",
                  activeInPort === port.name && "z-40 bg-popover shadow-[inset_3px_0_0_hsl(var(--foreground))]"
                )}
                style={{ height: ROW }}
              >
                {activeInPort === port.name && (
                  <div
                    className="nodrag nowheel absolute left-full top-0 z-50 w-[320px] cursor-default space-y-1.5 rounded-xl rounded-tl-none border border-border bg-popover p-3 text-popover-foreground shadow-lg"
                    style={{ marginLeft: 12 }}
                    onClick={(e) => e.stopPropagation()}
                    onDoubleClick={(e) => e.stopPropagation()}
                  >
                    {/* Cầu nối: hàng input và panel liền một khối */}
                    <span aria-hidden className="absolute -left-3 top-0 h-[22px] w-3 border-y border-border bg-popover" />
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>
                        Nguồn cho <span className="font-mono text-foreground">{port.name}</span>
                      </span>
                      <button
                        type="button"
                        aria-label="Đóng"
                        title="Đóng"
                        onClick={() => setActiveInPort(null)}
                        className="flex h-5 w-5 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground"
                      >
                        ✕
                      </button>
                    </div>
                    <PortValueInput nodeId={id} port={port} />
                  </div>
                )}
                {!(portIconOf(port.portType) && port.name === port.portType) && (
                  <span className={cn("truncate", filled ? "text-foreground" : port.required ? "text-semantic-danger" : "text-muted-foreground")}>
                    {port.name}
                  </span>
                )}
                {!portIconOf(port.portType) && <span className="flex items-center text-muted-foreground/70">· {portType(port)}</span>}
                {(incoming.get(port.name) || []).map((src) => (
                  <button
                    key={`${src.srcId}:${src.srcPort}`}
                    type="button"
                    title={`Nguồn: ${src.srcName} · ${src.srcPort} — bấm để làm nổi node nguồn`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedNodeId(src.srcId);
                      flashNode(src.srcId);
                    }}
                    className="nodrag min-w-0 max-w-[110px] truncate rounded bg-accent/70 px-1 font-mono text-[10px] text-muted-foreground transition-colors hover:bg-brand/15 hover:text-foreground"
                  >
                    ← {src.srcName}.{src.srcPort}
                  </button>
                ))}
                <span className="ml-auto flex items-center gap-1 text-[10px]">
                  {data.inputSummary?.[port.name] && (
                    <span className="max-w-[90px] truncate font-medium text-foreground" title={`Dữ liệu nhận: ${data.inputSummary[port.name]}`}>
                      {data.inputSummary[port.name]}
                    </span>
                  )}
                  {filled ? <CheckCircle2 className="h-3 w-3 text-semantic-success" /> : port.required ? <span className="text-semantic-danger">thiếu</span> : <span className="text-muted-foreground/60">tuỳ chọn</span>}
                </span>
              </div>
            );
          })}
         </Reveal>
        </div>
      )}

      {/* 2. LÀM (node nguồn không có đầu vào thì gọi là "Cung cấp") */}
      <div className="border-t border-border/70">
        <Reveal show={!isModeNode || expanded}>
          <div className="flex items-center justify-between px-3" style={{ height: LABEL }}>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{hasIn ? "Làm" : "Cung cấp"}</span>
            {hasIn && <span className="text-[10px] text-muted-foreground/70">{categoryLabel}</span>}
          </div>
        </Reveal>
        <div className={cn("space-y-2 px-3 pb-3", isModeNode && "pt-2.5")}>
          {!collapsed && (
            <Reveal show={!isModeNode || expanded}>
              <p className="line-clamp-2 text-xs text-muted-foreground" title={def.description}>
                {def.description}
              </p>
            </Reveal>
          )}
          <NodeBody
            nodeType={def.typeName}
            nodeId={id}
            data={data}
            character={boundChar}
            compact={collapsed}
            expanded={expanded}
            onPickCharacter={() => setCharPicker((v) => !v)}
            connectedInputs={def.inputPorts.filter((pt) => connectedPorts.has(`${id}:in:${pt.name}`)).map((pt) => pt.name)}
          />
        </div>
      </div>

      {/* 3. TRẢ — chỉ hiện khi node có đầu ra */}
      {hasOut && (
        <div className="border-t border-border/70">
         <Reveal show={!isModeNode || expanded}>
          <div className={cn(!hasFooter && "pb-2")}>
          <div className="flex items-center justify-between px-3" style={{ height: LABEL }}>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Trả</span>
            {outputsDone && (
              <span className="flex items-center gap-1 text-[10px] font-medium text-semantic-success">
                <CheckCircle2 className="h-3 w-3" /> Đã có kết quả
              </span>
            )}
          </div>
          {def.outputPorts.map((port) => {
            const connected = connectedPorts.has(`${id}:out:${port.name}`);
            return (
              <div key={port.name} className="flex items-center justify-end gap-1.5 px-3 text-xs" style={{ height: ROW }}>
                {data.outputSummary?.[port.name] && (
                  <span className="max-w-[120px] truncate text-[10px] font-medium text-foreground" title={`Đã sinh ra: ${data.outputSummary[port.name]}`}>
                    {data.outputSummary[port.name]}
                  </span>
                )}
                {!portIconOf(port.portType) && <span className="flex items-center text-muted-foreground/70">{portType(port)}</span>}
                {port.name !== port.portType && (
                  <span className={cn("truncate", connected ? "text-foreground" : "text-muted-foreground")}>{port.name}</span>
                )}
              </div>
            );
          })}
          </div>
         </Reveal>
        </div>
      )}

      {data.summaryText && (
        <div className="px-2.5 pb-1">
          <p className="line-clamp-2 rounded border border-border/70 bg-muted/20 px-2 py-1 text-xs text-foreground">{data.summaryText}</p>
        </div>
      )}

      {/* Card Text không cần chân card (chi phí 0, không chạy tiếp từ đây) */}
      <Reveal show={hasFooter}>
      <div className="flex items-center justify-between px-3 text-xs text-muted-foreground tnum" style={{ height: FOOTER }}>
        <span className="truncate">
          {data.generations.length > 0 ? t("pinnedGen", { index: Math.max(1, pinnedIdx), total: data.generations.length }) : ""}
        </span>
        <span className="flex shrink-0 items-center gap-1">
          {estCost > 0 && <span title={t("estimatedCost", { cost: estCost.toFixed(2) })}>${estCost.toFixed(2)}</span>}
        </span>
      </div>
      </Reveal>

      {/* Bảng chọn nhân vật: tab card bên cạnh, dạng avatar + tạo mới */}
      {isCharacter && charPicker && (
        <div
          onClick={(e) => e.stopPropagation()}
          style={{ left: "calc(100% + 8px)", top: 0 }}
          className="nodrag nowheel absolute z-30 w-[min(380px,calc(100vw-32px))] rounded-xl border border-border bg-card p-2 shadow-lg"
        >
          <p className="px-1 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Đổi nhân vật</p>
          <div className="grid max-h-[460px] grid-cols-4 gap-2 overflow-y-auto scroll-quiet">
            {characters.map((c) => {
              const active = c.id === p.characterId;
              return (
                <button
                  key={c.id}
                  type="button"
                  title={`${c.name} · ${c.heightCm}cm`}
                  onClick={() => {
                    updateNodeParams(id, { characterId: c.id });
                    setCharPicker(false);
                  }}
                  className={cn(
                    "flex flex-col items-center gap-1 rounded-lg border p-1.5 text-center transition-colors hover:bg-accent",
                    active ? "border-foreground bg-accent" : "border-border"
                  )}
                >
                  {c.referenceImages?.[0] ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img decoding="async" loading="lazy" src={c.referenceImages[0]} alt="" className="h-16 w-16 rounded-full border border-border object-cover object-top" />
                  ) : (
                    <span className="flex h-16 w-16 items-center justify-center rounded-full bg-muted text-base font-semibold text-muted-foreground">
                      {c.name.charAt(0)}
                    </span>
                  )}
                  <span className="w-full truncate text-[10px] text-foreground">{c.name}</span>
                </button>
              );
            })}
            <button
              type="button"
              title="Tạo nhân vật mới"
              aria-label="Tạo nhân vật mới"
              onClick={() => {
                setCharPicker(false);
                useHubScope.getState().openTab("characters", "create-character");
              }}
              className="flex flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-border p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              <span className="flex h-16 w-16 items-center justify-center rounded-full border border-dashed border-border"><Plus className="h-5 w-5" /></span>
              <span className="text-[10px]">Tạo mới</span>
            </button>
          </div>
        </div>
      )}

      {/* Thông báo lỗi thống nhất: luôn nằm ngay dưới card, mọi loại node */}
      {errorText && (
        <div
          role="alert"
          data-node-error
          className="absolute inset-x-0 top-full z-10 mt-1.5 flex items-start gap-1.5 rounded-lg border border-semantic-danger/50 bg-card px-2.5 py-1.5 text-xs leading-snug text-semantic-danger shadow-sm"
        >
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span className="min-w-0 break-words">{errorText}</span>
        </div>
      )}
    </motion.div>
  );
});
