import { create } from "zustand";
import {
  AutomationRule,
  CalendarItem,
  CalendarResponse,
  CreativePerformance,
  HeatmapData,
  KPISummary,
  OutlierItem,
  PlatformType,
  Post,
  PostingWindow,
  PostStatus,
  QueueResponse,
  SocialAccount,
  SocialNotification,
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
  queueData: QueueResponse | null;
  queueBucket: "upcoming" | "overdue" | "published" | "failed";
  loading: boolean;
  error: string | null;

  // Analytics & Automation Data
  analyticsOverview: {
    kpis: KPISummary;
    views_by_day: Record<string, Record<string, number>>;
    outliers: { top_outliers: OutlierItem[]; underperforming: OutlierItem[] };
  } | null;
  heatmapData: HeatmapData | null;
  creativesData: CreativePerformance | null;
  learningsData: { learnings_md: string; recommendations: any } | null;
  automationRules: AutomationRule[];
  notifications: SocialNotification[];
  unreadNotifCount: number;

  // View state
  activeTab: "calendar" | "approvals" | "posts" | "accounts" | "analytics";
  calendarView: "month" | "week" | "agenda";
  selectedDate: string; // YYYY-MM-DD
  filters: SocialFilters;

  // Modals & Drawers state
  isComposerOpen: boolean;
  editingPost: Post | null;
  composerInitialDate: string | null;
  composerInitialAccount: string | null;
  isPublishCenterOpen: boolean;
  publishCenterTab: "plan" | "calendar";
  isAutomationModalOpen: boolean;
  isNotifDrawerOpen: boolean;
  isManualMetricsModalOpen: boolean;
  isImportCsvModalOpen: boolean;

  // History for Undo
  lastDragAction: { postId: string; targetId: string; previousTime: string | null } | null;

  // Actions
  setActiveTab: (tab: "calendar" | "approvals" | "posts" | "accounts" | "analytics") => void;
  setCalendarView: (view: "month" | "week" | "agenda") => void;
  setSelectedDate: (date: string) => void;
  setFilters: (filters: Partial<SocialFilters>) => void;
  setQueueBucket: (bucket: "upcoming" | "overdue" | "published" | "failed") => void;
  openComposer: (post?: Post | null, date?: string, accountId?: string) => void;
  closeComposer: () => void;
  openPublishCenter: (tab?: "plan" | "calendar") => void;
  closePublishCenter: () => void;
  setAutomationModalOpen: (open: boolean) => void;
  setNotifDrawerOpen: (open: boolean) => void;
  setManualMetricsModalOpen: (open: boolean) => void;
  setImportCsvModalOpen: (open: boolean) => void;

  // Async API Actions
  loadAccounts: (projectId: string) => Promise<void>;
  loadPosts: (projectId: string) => Promise<void>;
  loadQueue: (projectId: string, bucket?: "upcoming" | "overdue" | "published" | "failed") => Promise<void>;
  loadCalendar: (projectId: string, fromDate?: string, toDate?: string) => Promise<void>;
  loadAll: (projectId: string) => Promise<void>;

  // Analytics Actions
  loadAnalytics: (projectId: string, window?: string) => Promise<void>;
  loadHeatmap: (projectId: string) => Promise<void>;
  applyGoldenWindows: (projectId: string, accountId?: string) => Promise<void>;
  loadCreatives: (projectId: string) => Promise<void>;
  loadLearnings: (projectId: string) => Promise<void>;
  triggerAnalyticsCollect: (projectId: string) => Promise<void>;

  // Automation Actions
  loadAutomationRules: (projectId: string) => Promise<void>;
  toggleAutomationRule: (projectId: string, ruleId: string) => Promise<void>;
  runAutomation: (projectId: string, ruleId?: string) => Promise<void>;

  // Notification Actions
  loadNotifications: (projectId: string) => Promise<void>;
  markNotificationRead: (projectId: string, notifId: string) => Promise<void>;
  clearNotifications: (projectId: string) => Promise<void>;

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
  queueData: null,
  queueBucket: "upcoming",
  loading: false,
  error: null,

  analyticsOverview: null,
  heatmapData: null,
  creativesData: null,
  learningsData: null,
  automationRules: [],
  notifications: [],
  unreadNotifCount: 0,

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
  isPublishCenterOpen: false,
  publishCenterTab: "plan",
  isAutomationModalOpen: false,
  isNotifDrawerOpen: false,
  isManualMetricsModalOpen: false,
  isImportCsvModalOpen: false,
  lastDragAction: null,

  setActiveTab: (tab) => set({ activeTab: tab }),
  setCalendarView: (view) => set({ calendarView: view }),
  setSelectedDate: (date) => set({ selectedDate: date }),
  setFilters: (newFilters) =>
    set((state) => ({ filters: { ...state.filters, ...newFilters } })),
  setQueueBucket: (bucket) => set({ queueBucket: bucket }),

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

  openPublishCenter: (tab = "plan") =>
    set({ isPublishCenterOpen: true, publishCenterTab: tab }),

  closePublishCenter: () =>
    set({ isPublishCenterOpen: false }),

  setAutomationModalOpen: (open) => set({ isAutomationModalOpen: open }),
  setNotifDrawerOpen: (open) => set({ isNotifDrawerOpen: open }),
  setManualMetricsModalOpen: (open) => set({ isManualMetricsModalOpen: open }),
  setImportCsvModalOpen: (open) => set({ isImportCsvModalOpen: open }),

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

  loadQueue: async (projectId: string, bucket?: "upcoming" | "overdue" | "published" | "failed") => {
    try {
      const b = bucket || get().queueBucket || "upcoming";
      const queueData = await socialApi.getQueue(projectId, b);
      set({ queueData, queueBucket: b });
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
      const currentBucket = get().queueBucket || "upcoming";
      const [accounts, posts, calendarData, notifs, queueData] = await Promise.all([
        socialApi.listAccounts(projectId).catch(() => []),
        socialApi.listPosts(projectId).catch(() => []),
        socialApi.getCalendar(projectId, { view: get().calendarView }).catch(() => null),
        socialApi.listNotifications(projectId).catch(() => []),
        socialApi.getQueue(projectId, currentBucket).catch(() => null),
      ]);
      const unreadCount = notifs.filter((n) => !n.read).length;
      set({
        accounts,
        posts,
        calendarData,
        notifications: notifs,
        unreadNotifCount: unreadCount,
        queueData,
        loading: false,
      });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  loadAnalytics: async (projectId: string, window = "30d") => {
    try {
      const overview = await socialApi.getAnalyticsOverview(projectId, window);
      set({ analyticsOverview: overview });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  loadHeatmap: async (projectId: string) => {
    try {
      const heatmap = await socialApi.getAnalyticsHeatmap(projectId);
      set({ heatmapData: heatmap });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  applyGoldenWindows: async (projectId: string, accountId?: string) => {
    try {
      await socialApi.applyGoldenWindows(projectId, accountId);
      await get().loadAccounts(projectId);
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  loadCreatives: async (projectId: string) => {
    try {
      const creatives = await socialApi.getCreativePerformance(projectId);
      set({ creativesData: creatives });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  loadLearnings: async (projectId: string) => {
    try {
      const learnings = await socialApi.getAnalyticsLearnings(projectId);
      set({ learningsData: learnings });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  triggerAnalyticsCollect: async (projectId: string) => {
    try {
      await socialApi.triggerAnalyticsCollect(projectId);
      await Promise.all([
        get().loadAnalytics(projectId),
        get().loadPosts(projectId),
      ]);
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  loadAutomationRules: async (projectId: string) => {
    try {
      const rules = await socialApi.listAutomationRules(projectId);
      set({ automationRules: rules });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  toggleAutomationRule: async (projectId: string, ruleId: string) => {
    try {
      await socialApi.toggleAutomationRule(projectId, ruleId);
      await get().loadAutomationRules(projectId);
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  runAutomation: async (projectId: string, ruleId?: string) => {
    try {
      await socialApi.runAutomation(projectId, ruleId);
      await Promise.all([
        get().loadPosts(projectId),
        get().loadNotifications(projectId),
        get().loadAutomationRules(projectId),
      ]);
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  loadNotifications: async (projectId: string) => {
    try {
      const notifs = await socialApi.listNotifications(projectId);
      const unreadCount = notifs.filter((n) => !n.read).length;
      set({ notifications: notifs, unreadNotifCount: unreadCount });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  markNotificationRead: async (projectId: string, notifId: string) => {
    try {
      await socialApi.markNotificationRead(projectId, notifId);
      await get().loadNotifications(projectId);
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  clearNotifications: async (projectId: string) => {
    try {
      await socialApi.clearNotifications(projectId);
      set({ notifications: [], unreadNotifCount: 0 });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  moveTargetTime: async (projectId, postId, targetId, newTime) => {
    const { calendarData, posts } = get();
    let previousTime: string | null = null;

    if (calendarData) {
      const item = calendarData.items.find((i) => i.target_id === targetId);
      if (item) previousTime = item.scheduled_at || null;
    }

    if (calendarData) {
      const nextItems = calendarData.items.map((i) =>
        i.target_id === targetId ? { ...i, scheduled_at: newTime } : i
      );
      set({ calendarData: { ...calendarData, items: nextItems } });
    }

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
