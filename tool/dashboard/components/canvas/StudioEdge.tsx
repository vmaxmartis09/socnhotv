"use client";

import React from "react";
import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from "@xyflow/react";
import { useStudioStore } from "@/store";
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
}: EdgeProps) {
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
        style={selected ? { ...style, strokeWidth: 2.5 } : style}
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
