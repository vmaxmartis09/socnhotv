import { create } from "zustand";
import { persist } from "zustand/middleware";
import { createUISlice, type UISlice } from "./slices/uiSlice";
import {
  createWorkspaceSlice,
  type WorkspaceSlice,
} from "./slices/workspaceSlice";
import { createCanvasSlice, type CanvasSlice } from "./slices/canvasSlice";
import { createJobsSlice, type JobsSlice } from "./slices/jobsSlice";
import {
  createRightPanelSlice,
  type RightPanelSlice,
} from "./slices/rightPanelSlice";
import { createChatSlice, type ChatSlice } from "./slices/chatSlice";
import {
  createUserSettingsSlice,
  type UserSettingsSlice,
} from "./slices/userSettingsSlice";

export type StudioStore = UISlice &
  WorkspaceSlice &
  CanvasSlice &
  JobsSlice &
  RightPanelSlice &
  ChatSlice &
  UserSettingsSlice;

export const useStudioStore = create<StudioStore>()(
  persist(
    (...a) => ({
      ...createUISlice(...a),
      ...createWorkspaceSlice(...a),
      ...createCanvasSlice(...a),
      ...createJobsSlice(...a),
      ...createRightPanelSlice(...a),
      ...createChatSlice(...a),
      ...createUserSettingsSlice(...a),
    }),
    {
      name: "ai_video_studio_settings_v2",
      partialize: (state) => ({
        theme: state.theme,
        locale: state.locale,
        isMockMode: state.isMockMode,
        runPolicy: state.runPolicy,
        spendingLimitUsd: state.spendingLimitUsd,
        perRunSpendingLimitUsd: state.perRunSpendingLimitUsd,
        dailySpendingLimitUsd: state.dailySpendingLimitUsd,
        userProfile: state.userProfile,
        storageBackend: state.storageBackend,
        apiKeyStatus: state.apiKeyStatus,
        activeRightTab: state.activeRightTab,
        rightPanelWidth: state.rightPanelWidth,
      }),
      // Panel nổi luôn khởi động ở trạng thái đóng, kể cả khi bản lưu cũ đang mở
      merge: (persisted, current) => ({
        ...current,
        ...(persisted as object),
        rightPanelCollapsed: true,
      }),
    }
  )
);
