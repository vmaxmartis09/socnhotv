"use client";

import React from "react";
import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from "@xyflow/react";
import { useStudioStore } from "@/store";
import { PORT_TYPE_COLORS } from "@/store/slices/canvasSlice";
import { FALLBACK_NODE_TYPES } from "@/lib/core-api";
import { applyPortOverride } from "@/lib/node-ports";
import { Trash2 } from "@/components/ui/icons";

/** Dây nối: bấm vào dây thì hiện nút xoá ở giữa dây. */
export function StudioEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  selected,
  style,
  markerEnd,
  source,
  sourceHandleId,
  data,
}: EdgeProps) {
  // Màu dây luôn theo kiểu dữ liệu của cổng ra (tính từ node nguồn, kể cả khi dây được nạp từ file)
  const portType = useStudioStore((st: any) => {
    const n = st.nodes.find((x: any) => x.id === source);
    if (!n) return (data as any)?.portType as string | undefined;
    const base =
      st.nodeCatalog.find((d: any) => d.typeName === n.data.nodeType) ||
      FALLBACK_NODE_TYPES.find((d) => d.typeName === n.data.nodeType);
    const def = base ? applyPortOverride(base, n.data.params) : undefined;
    return def?.outputPorts.find((p) => p.name === sourceHandleId)?.portType || ((data as any)?.portType as string | undefined);
  });
  const color = (portType && PORT_TYPE_COLORS[portType as keyof typeof PORT_TYPE_COLORS]) || (style as any)?.stroke || "#737373";
  const [path, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });

  const remove = () => {
    const s = useStudioStore.getState() as any;
    s.setNodesAndEdges(
      s.nodes,
      s.edges.filter((e: any) => e.id !== id),
      true
    );
  };

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        markerEnd={markerEnd}
        interactionWidth={22}
        style={{ ...style, stroke: color, strokeWidth: selected ? 2.5 : 1.75 }}
      />
      {selected && (
        <EdgeLabelRenderer>
          <button
            type="button"
            title="Xoá dây nối"
            aria-label="Xoá dây nối"
            onClick={remove}
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all",
            }}
            className="nodrag nopan flex h-6 w-6 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-sm transition-colors hover:border-destructive hover:text-destructive"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
