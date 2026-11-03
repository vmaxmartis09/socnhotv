import type { StateCreator } from "zustand";
import type {
  Project,
  Channel,
  Character,
  ScheduledPost,
} from "@/lib/repositories/types";

export interface WorkspaceSlice {
  activeProjectId: string;
  projects: Project[];
  characters: Character[];
  channels: Channel[];
  scheduledPosts: ScheduledPost[];
  isLoading: boolean;
  setActiveProjectId: (id: string) => void;
  setProjects: (projects: Project[]) => void;
  setCharacters: (characters: Character[]) => void;
  upsertCharacterInStore: (character: Character) => void;
  removeCharacterFromStore: (id: string) => void;
  setChannels: (channels: Channel[]) => void;
  setScheduledPosts: (posts: ScheduledPost[]) => void;
  addScheduledPost: (post: ScheduledPost) => void;
  updateScheduledPost: (id: string, updates: Partial<ScheduledPost>) => void;
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
  characters: [],
  channels: [],
  scheduledPosts: [],
  isLoading: false,
  setActiveProjectId: (id) => set({ activeProjectId: id }),
  setProjects: (projects) => set({ projects }),
  setCharacters: (characters) => set({ characters }),
  upsertCharacterInStore: (character) =>
    set((state) => {
      const exists = state.characters.some((c) => c.id === character.id);
      return {
        characters: exists
          ? state.characters.map((c) => (c.id === character.id ? character : c))
          : [...state.characters, character],
      };
    }),
  removeCharacterFromStore: (id) =>
    set((state) => ({
      characters: state.characters.filter((c) => c.id !== id),
    })),
  setChannels: (channels) => set({ channels }),
  setScheduledPosts: (scheduledPosts) => set({ scheduledPosts }),
  addScheduledPost: (post) =>
    set((state) => ({
      scheduledPosts: [post, ...state.scheduledPosts],
    })),
  updateScheduledPost: (id, updates) =>
    set((state) => ({
      scheduledPosts: state.scheduledPosts.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
    })),
  setIsLoading: (loading) => set({ isLoading: loading }),
});
