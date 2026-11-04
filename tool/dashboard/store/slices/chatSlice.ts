import type { StateCreator } from "zustand";

export interface ChatActionCard {
  id: string;
  summaryVi: string;
  summaryEn: string;
  targetNodeId?: string;
  undone?: boolean;
  snapshotBefore?: {
    nodes: any[];
    edges: any[];
    aspectRatio?: "9:16" | "16:9" | "1:1" | "4:5";
  };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: string;
  mode?: "rule_based_mock" | "provider";
  actionCard?: ChatActionCard;
}

export interface PendingChatConfirmation {
  id: string;
  kind: "run" | "publish";
  titleVi: string;
  titleEn: string;
  detailVi: string;
  detailEn: string;
  estimatedCostUsd?: number;
  platform?: string;
  time?: string;
  episodeTitle?: string;
  mode?: string;
  prompt: string;
}

export type ChatModel = "auto" | "gemini-3.8-flash" | "gemini-2.5-pro" | "gemini-2.5-flash" | "rules";
export type ChatFlowMode = "current" | "new" | "blank";
export type ChatCharMode = "update" | "create";

export type ChatFocus = "project" | "character" | "flow";

export interface ChatContext {
  focus: ChatFocus;
  model: ChatModel;
  flowMode: ChatFlowMode;
  characterId: string | null;
  characterMode: ChatCharMode;
}

export interface ChatSlice {
  chatContext: ChatContext;
  setChatContext: (patch: Partial<ChatContext>) => void;
  chatByProject: Record<string, ChatMessage[]>;
  pendingConfirmation: PendingChatConfirmation | null;
  addChatMessage: (projectId: string, msg: ChatMessage) => void;
  markChatActionUndone: (projectId: string, messageId: string) => void;
  setPendingConfirmation: (conf: PendingChatConfirmation | null) => void;
  clearProjectChat: (projectId: string) => void;
}

const DEFAULT_WELCOME_MESSAGES: Record<string, ChatMessage[]> = {
  "soc-nho-tv": [
    {
      id: "msg_welcome_1",
      role: "assistant",
      text: "[Chế độ chạy thử — Trợ lý quy tắc] Xin chào! Tôi là trợ lý điều khiển Studio Sóc Nhỏ TV. Bạn có thể gõ lệnh tự nhiên như: 'thêm bước kiểm tra nhân vật trước khi tạo video', 'đổi tỉ lệ sang 16:9', 'chạy từ cảnh 3', 'lên lịch đăng tập 1 lúc 19:00 lên YouTube', hoặc 'cho tôi xem nhân vật Koala'.",
      timestamp: "2026-11-03T15:30:00.000Z",
      mode: "rule_based_mock",
    },
  ],
};

export const createChatSlice: StateCreator<ChatSlice, [], [], ChatSlice> = (
  set
) => ({
  chatByProject: DEFAULT_WELCOME_MESSAGES,
  chatContext: { focus: "character", model: "auto", flowMode: "current", characterId: null, characterMode: "update" },
  setChatContext: (patch) => set((s) => ({ chatContext: { ...s.chatContext, ...patch } })),
  pendingConfirmation: null,
  addChatMessage: (projectId, msg) =>
    set((state) => ({
      chatByProject: {
        ...state.chatByProject,
        [projectId]: [...(state.chatByProject[projectId] || []), msg],
      },
    })),
  markChatActionUndone: (projectId, messageId) =>
    set((state) => ({
      chatByProject: {
        ...state.chatByProject,
        [projectId]: (state.chatByProject[projectId] || []).map((m) =>
          m.id === messageId && m.actionCard
            ? { ...m, actionCard: { ...m.actionCard, undone: true } }
            : m
        ),
      },
    })),
  setPendingConfirmation: (pendingConfirmation) => set({ pendingConfirmation }),
  clearProjectChat: (projectId) =>
    set((state) => ({
      chatByProject: {
        ...state.chatByProject,
        [projectId]: DEFAULT_WELCOME_MESSAGES[projectId] || [],
      },
    })),
});
