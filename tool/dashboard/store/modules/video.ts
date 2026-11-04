import { create } from "zustand";
import type { PlatformPreset, RenderJob, TemplateMeta } from "@/lib/api/video";

export interface VideoState {
  templates: TemplateMeta[];
  activeTemplate: TemplateMeta | null;
  platforms: PlatformPreset[];
  renderJobs: RenderJob[];
  activeJob: RenderJob | null;
  loading: boolean;
  selectedCategory: string;
  selectedPlatform: string;
  searchQuery: string;

  setTemplates: (templates: TemplateMeta[]) => void;
  setActiveTemplate: (template: TemplateMeta | null) => void;
  setPlatforms: (platforms: PlatformPreset[]) => void;
  setRenderJobs: (jobs: RenderJob[]) => void;
  updateRenderJob: (job: RenderJob) => void;
  setActiveJob: (job: RenderJob | null) => void;
  setLoading: (loading: boolean) => void;
  setSelectedCategory: (category: string) => void;
  setSelectedPlatform: (platform: string) => void;
  setSearchQuery: (query: string) => void;
}

export const useVideoStore = create<VideoState>((set) => ({
  templates: [],
  activeTemplate: null,
  platforms: [],
  renderJobs: [],
  activeJob: null,
  loading: false,
  selectedCategory: "all",
  selectedPlatform: "all",
  searchQuery: "",

  setTemplates: (templates) => set({ templates }),
  setActiveTemplate: (activeTemplate) => set({ activeTemplate }),
  setPlatforms: (platforms) => set({ platforms }),
  setRenderJobs: (renderJobs) => set({ renderJobs }),
  updateRenderJob: (job) =>
    set((state) => ({
      renderJobs: state.renderJobs.some((j) => j.job_id === job.job_id)
        ? state.renderJobs.map((j) => (j.job_id === job.job_id ? job : j))
        : [job, ...state.renderJobs],
      activeJob: state.activeJob?.job_id === job.job_id ? job : state.activeJob,
    })),
  setActiveJob: (activeJob) => set({ activeJob }),
  setLoading: (loading) => set({ loading }),
  setSelectedCategory: (selectedCategory) => set({ selectedCategory }),
  setSelectedPlatform: (selectedPlatform) => set({ selectedPlatform }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
}));
