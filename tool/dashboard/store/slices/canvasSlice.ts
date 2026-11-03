import type { StateCreator } from "zustand";

export interface CanvasSlice {
  selectedNodeId: string | null;
  aspectRatio: "9:16" | "16:9" | "1:1" | "4:5";
  zoomLevel: number;
  isMockMode: boolean;
  setSelectedNodeId: (id: string | null) => void;
  setAspectRatio: (ratio: "9:16" | "16:9" | "1:1" | "4:5") => void;
  setZoomLevel: (zoom: number) => void;
  setIsMockMode: (mock: boolean) => void;
}

export const createCanvasSlice: StateCreator<
  CanvasSlice,
  [],
  [],
  CanvasSlice
> = (set) => ({
  selectedNodeId: null,
  aspectRatio: "9:16",
  zoomLevel: 1.0,
  isMockMode: true,
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  setAspectRatio: (aspectRatio) => set({ aspectRatio }),
  setZoomLevel: (zoomLevel) => set({ zoomLevel }),
  setIsMockMode: (isMockMode) => set({ isMockMode }),
});
