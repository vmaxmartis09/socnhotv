import type { StateCreator } from "zustand";
import type { Project, Channel } from "@/lib/repositories/types";

export interface WorkspaceSlice {
  activeProjectId: string;
  projects: Project[];
  channels: Channel[];
  isLoading: boolean;
  setActiveProjectId: (id: string) => void;
  setProjects: (projects: Project[]) => void;
  setChannels: (channels: Channel[]) => void;
  setIsLoading: (loading: boolean) => void;
}

export const createWorkspaceSlice: StateCreator<
  WorkspaceSlice,
  [],
  [],
  WorkspaceSlice
> = (set) => ({
  activeProjectId: "soc-nho-tv",
  projects: [],
  channels: [],
  isLoading: false,
  setActiveProjectId: (id) => set({ activeProjectId: id }),
  setProjects: (projects) => set({ projects }),
  setChannels: (channels) => set({ channels }),
  setIsLoading: (loading) => set({ isLoading: loading }),
});
