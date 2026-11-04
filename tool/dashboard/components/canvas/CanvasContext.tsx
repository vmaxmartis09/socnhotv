"use client";

import React, { createContext, useContext } from "react";
import type { PortType, RunMode } from "@/lib/core-contracts";

export interface ActiveDragPort {
  nodeId: string;
  portName: string;
  portType: PortType;
  handleType: "source" | "target";
}

export interface QuickAddRequest {
  anchorNodeId: string;
  direction: "before" | "after";
  portName: string;
  portType: PortType;
}

export interface CanvasInteractionContextValue {
  activeDragPort: ActiveDragPort | null;
  connectedPorts: Set<string>;
  nodeIssues: Record<string, string[]>;
  onOpenQuickAdd: (req: QuickAddRequest) => void;
  onRequestRun: (mode: RunMode, targetNodeId?: string) => void;
  onOpenNodeInspector: (nodeId: string) => void;
  /** Đang ở chế độ "kéo dây bằng nút +": chọn xong cổng đích bằng một cú bấm */
  linkMode: boolean;
  startLink: (port: ActiveDragPort) => void;
  finishLink: (nodeId: string, portName: string, handleType: "source" | "target") => void;
  cancelLink: () => void;
}

export const CanvasInteractionContext =
  createContext<CanvasInteractionContextValue>({
    activeDragPort: null,
    connectedPorts: new Set(),
    nodeIssues: {},
    onOpenQuickAdd: () => {},
    onRequestRun: () => {},
    onOpenNodeInspector: () => {},
    linkMode: false,
    startLink: () => {},
    finishLink: () => {},
    cancelLink: () => {},
  });

export function useCanvasInteraction() {
  return useContext(CanvasInteractionContext);
}
