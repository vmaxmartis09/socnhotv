import { create } from "zustand";
import type { SourceItem } from "@/lib/api/sources";

export interface SourcesState {
  sources: SourceItem[];
  activeSource: SourceItem | null;
  loading: boolean;
  filterPlatform: string;
  filterRights: string;
  searchQuery: string;

  setSources: (sources: SourceItem[]) => void;
  setActiveSource: (source: SourceItem | null) => void;
  setLoading: (loading: boolean) => void;
  setFilterPlatform: (platform: string) => void;
  setFilterRights: (rights: string) => void;
  setSearchQuery: (query: string) => void;
  removeSource: (sourceId: string) => void;
}

export const useSourcesStore = create<SourcesState>((set) => ({
  sources: [],
  activeSource: null,
  loading: false,
  filterPlatform: "",
  filterRights: "",
  searchQuery: "",

  setSources: (sources) => set({ sources }),
  setActiveSource: (activeSource) => set({ activeSource }),
  setLoading: (loading) => set({ loading }),
  setFilterPlatform: (filterPlatform) => set({ filterPlatform }),
  setFilterRights: (filterRights) => set({ filterRights }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  removeSource: (sourceId) =>
    set((state) => ({
      sources: state.sources.filter((s) => s.id !== sourceId),
      activeSource: state.activeSource?.id === sourceId ? null : state.activeSource,
    })),
}));
