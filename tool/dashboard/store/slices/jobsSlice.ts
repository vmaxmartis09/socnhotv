import type { StateCreator } from "zustand";
import type { Job } from "@/lib/repositories/types";

export interface JobsSlice {
  jobs: Job[];
  totalSpentUsd: number;
  spendingLimitUsd: number;
  addJob: (job: Job) => void;
  updateJob: (id: string, updates: Partial<Job>) => void;
  removeJob: (id: string) => void;
  clearFinishedJobs: () => void;
  setJobs: (jobs: Job[]) => void;
  setSpendingLimitUsd: (limit: number) => void;
}

export const createJobsSlice: StateCreator<
  JobsSlice,
  [],
  [],
  JobsSlice
> = (set) => ({
  jobs: [],
  totalSpentUsd: 0.0,
  spendingLimitUsd: 15.0,
  addJob: (job) =>
    set((state) => ({
      jobs: [job, ...state.jobs],
      totalSpentUsd: state.totalSpentUsd + (job.actualCostUsd || 0),
    })),
  updateJob: (id, updates) =>
    set((state) => ({
      jobs: state.jobs.map((j) => (j.id === id ? { ...j, ...updates } : j)),
    })),
  removeJob: (id) => set((state) => ({ jobs: state.jobs.filter((j) => j.id !== id) })),
  clearFinishedJobs: () =>
    set((state) => ({
      jobs: state.jobs.filter((j) => j.status === "running" || j.status === "queued" || j.status === "pending"),
    })),
  setJobs: (jobs) => set({ jobs }),
  setSpendingLimitUsd: (spendingLimitUsd) => set({ spendingLimitUsd }),
});
