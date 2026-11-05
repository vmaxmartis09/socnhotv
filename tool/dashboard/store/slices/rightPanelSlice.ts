import type { StateCreator } from "zustand";

export type RightPanelTab = "chat" | "node" | "project" | "publish" | "jobs" | "shortcuts" | "templates" | "toolbox" | "policy";
export type CharacterProfileSection =
  | "profile"
  | "images"
  | "videos"
  | "voice"
  | "usage";

export interface RightPanelSlice {
  activeRightTab: RightPanelTab;
  rightPanelWidth: number;
  rightPanelCollapsed: boolean;
  mobileSheetOpen: boolean;
  selectedCharacterId: string | null;
  activeCharacterSection: CharacterProfileSection;
  flashingNodeId: string | null;
  setActiveRightTab: (tab: RightPanelTab) => void;
  setRightPanelWidth: (width: number) => void;
  setRightPanelCollapsed: (collapsed: boolean) => void;
  toggleRightPanel: () => void;
  setMobileSheetOpen: (open: boolean) => void;
  setSelectedCharacterId: (id: string | null) => void;
  setActiveCharacterSection: (section: CharacterProfileSection) => void;
  flashNode: (nodeId: string) => void;
}

export const createRightPanelSlice: StateCreator<
  RightPanelSlice,
  [],
  [],
  RightPanelSlice
> = (set) => ({
  activeRightTab: "chat",
  rightPanelWidth: 380,
  rightPanelCollapsed: true,
  mobileSheetOpen: false,
  selectedCharacterId: null,
  activeCharacterSection: "profile",
  flashingNodeId: null,
  setActiveRightTab: (activeRightTab) =>
    set({ activeRightTab, rightPanelCollapsed: false, mobileSheetOpen: true }),
  setRightPanelWidth: (w) =>
    set({ rightPanelWidth: Math.min(560, Math.max(320, Math.round(w))) }),
  setRightPanelCollapsed: (rightPanelCollapsed) => set({ rightPanelCollapsed }),
  toggleRightPanel: () =>
    set((s) => ({ rightPanelCollapsed: !s.rightPanelCollapsed })),
  setMobileSheetOpen: (mobileSheetOpen) => set({ mobileSheetOpen }),
  setSelectedCharacterId: (selectedCharacterId) => set({ selectedCharacterId }),
  setActiveCharacterSection: (activeCharacterSection) =>
    set({ activeCharacterSection }),
  flashNode: (nodeId) => {
    set({ flashingNodeId: nodeId });
    if (typeof window !== "undefined") {
      window.setTimeout(() => {
        set((s) => (s.flashingNodeId === nodeId ? { flashingNodeId: null } : s));
      }, 1400);
    }
  },
});
