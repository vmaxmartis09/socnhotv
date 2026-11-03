import { create } from "zustand";
import { persist } from "zustand/middleware";
import { createUISlice, type UISlice } from "./slices/uiSlice";
import {
  createWorkspaceSlice,
  type WorkspaceSlice,
} from "./slices/workspaceSlice";
import { createCanvasSlice, type CanvasSlice } from "./slices/canvasSlice";
import { createJobsSlice, type JobsSlice } from "./slices/jobsSlice";

export type StudioStore = UISlice & WorkspaceSlice & CanvasSlice & JobsSlice;

export const useStudioStore = create<StudioStore>()(
  persist(
    (...a) => ({
      ...createUISlice(...a),
      ...createWorkspaceSlice(...a),
      ...createCanvasSlice(...a),
      ...createJobsSlice(...a),
    }),
    {
      name: "ai_video_studio_settings_v1",
      partialize: (state) => ({
        theme: state.theme,
        locale: state.locale,
        isMockMode: state.isMockMode,
        spendingLimitUsd: state.spendingLimitUsd,
      }),
    }
  )
);
