import { create } from "zustand";
import {
  CalendarItem,
  CalendarResponse,
  PlatformType,
  Post,
  PostStatus,
  SocialAccount,
  socialApi,
} from "@/lib/api/social";

export interface SocialFilters {
  platform: PlatformType | "all";
  status: PostStatus | "all";
  accountId: string | "all";
  search: string;
}

export interface SocialState {
  // Data
  accounts: SocialAccount[];
  posts: Post[];
  calendarData: CalendarResponse | null;
  loading: boolean;
  error: string | null;

  // View state
  activeTab: "calendar" | "approvals" | "posts" | "accounts" | "analytics";
  calendarView: "month" | "week" | "agenda";
  selectedDate: string; // YYYY-MM-DD
  filters: SocialFilters;

  // Composer Drawer state
  isComposerOpen: boolean;
  editingPost: Post | null;
  composerInitialDate: string | null;
  composerInitialAccount: string | null;

  // History for Undo
  lastDragAction: { postId: string; targetId: string; previousTime: string | null } | null;

  // Actions
  setActiveTab: (tab: "calendar" | "approvals" | "posts" | "accounts" | "analytics") => void;
  setCalendarView: (view: "month" | "week" | "agenda") => void;
  setSelectedDate: (date: string) => void;
  setFilters: (filters: Partial<SocialFilters>) => void;
  openComposer: (post?: Post | null, date?: string, accountId?: string) => void;
  closeComposer: () => void;

  // Async API Actions
  loadAccounts: (projectId: string) => Promise<void>;
  loadPosts: (projectId: string) => Promise<void>;
  loadCalendar: (projectId: string, fromDate?: string, toDate?: string) => Promise<void>;
  loadAll: (projectId: string) => Promise<void>;

  // Optimistic Target Time & Undo
  moveTargetTime: (
    projectId: string,
    postId: string,
    targetId: string,
    newTime: string
  ) => Promise<void>;
  undoLastDrag: (projectId: string) => Promise<void>;
}

export const useSocialStore = create<SocialState>((set, get) => ({
  accounts: [],
  posts: [],
  calendarData: null,
  loading: false,
  error: null,

  activeTab: "calendar",
  calendarView: "month",
  selectedDate: new Date().toISOString().slice(0, 10),
  filters: {
    platform: "all",
    status: "all",
    accountId: "all",
    search: "",
  },

  isComposerOpen: false,
  editingPost: null,
  composerInitialDate: null,
  composerInitialAccount: null,
  lastDragAction: null,

  setActiveTab: (tab) => set({ activeTab: tab }),
  setCalendarView: (view) => set({ calendarView: view }),
  setSelectedDate: (date) => set({ selectedDate: date }),
  setFilters: (newFilters) =>
    set((state) => ({ filters: { ...state.filters, ...newFilters } })),

  openComposer: (post = null, date, accountId) =>
    set({
      isComposerOpen: true,
      editingPost: post,
      composerInitialDate: date || null,
      composerInitialAccount: accountId || null,
    }),

  closeComposer: () =>
    set({
      isComposerOpen: false,
      editingPost: null,
      composerInitialDate: null,
      composerInitialAccount: null,
    }),

  loadAccounts: async (projectId: string) => {
    try {
      const accounts = await socialApi.listAccounts(projectId);
      set({ accounts });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  loadPosts: async (projectId: string) => {
    try {
      const posts = await socialApi.listPosts(projectId);
      set({ posts });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  loadCalendar: async (projectId: string, fromDate, toDate) => {
    try {
      const { calendarView } = get();
      const calendarData = await socialApi.getCalendar(projectId, {
        from: fromDate,
        to: toDate,
        view: calendarView,
      });
      set({ calendarData });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  loadAll: async (projectId: string) => {
    set({ loading: true, error: null });
    try {
      const [accounts, posts, calendarData] = await Promise.all([
        socialApi.listAccounts(projectId).catch(() => []),
        socialApi.listPosts(projectId).catch(() => []),
        socialApi.getCalendar(projectId, { view: get().calendarView }).catch(() => null),
      ]);
      set({ accounts, posts, calendarData, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  moveTargetTime: async (projectId, postId, targetId, newTime) => {
    const { calendarData, posts } = get();
    let previousTime: string | null = null;

    // Find previous time for undo
    if (calendarData) {
      const item = calendarData.items.find((i) => i.target_id === targetId);
      if (item) previousTime = item.scheduled_at || null;
    }

    // Optimistically update calendarData
    if (calendarData) {
      const nextItems = calendarData.items.map((i) =>
        i.target_id === targetId ? { ...i, scheduled_at: newTime } : i
      );
      set({ calendarData: { ...calendarData, items: nextItems } });
    }

    // Optimistically update posts
    const nextPosts = posts.map((p) => {
      if (p.id !== postId) return p;
      return {
        ...p,
        targets: p.targets.map((t) =>
          t.id === targetId ? { ...t, scheduled_at: newTime } : t
        ),
      };
    });
    set({
      posts: nextPosts,
      lastDragAction: { postId, targetId, previousTime },
    });

    try {
      await socialApi.updateTargetTime(projectId, postId, targetId, newTime);
    } catch (e: any) {
      // Revert on error
      if (previousTime) {
        get().undoLastDrag(projectId);
      }
      throw e;
    }
  },

  undoLastDrag: async (projectId) => {
    const { lastDragAction } = get();
    if (!lastDragAction || !lastDragAction.previousTime) return;
    const { postId, targetId, previousTime } = lastDragAction;
    set({ lastDragAction: null });
    await socialApi.updateTargetTime(projectId, postId, targetId, previousTime);
    await get().loadCalendar(projectId);
  },
}));
