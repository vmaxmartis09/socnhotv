import type { StateCreator } from "zustand";

export type ProviderKeyId = "gemini" | "fal" | "openai" | "replicate";

export interface UserProfile {
  name: string;
  email: string;
  avatarDataUrl?: string;
}

export interface CoreHealthState {
  online: boolean;
  version: string;
  repoRoot?: string;
  checkedAt?: string;
}

export interface UserSettingsSlice {
  userProfile: UserProfile;
  perRunSpendingLimitUsd: number;
  dailySpendingLimitUsd: number;
  storageBackend: "local" | "supabase";
  storageUsedBytes: number;
  apiKeyStatus: Record<
    ProviderKeyId,
    { configured: boolean; updatedAt?: string | null }
  >;
  coreHealth: CoreHealthState;
  setUserProfile: (updates: Partial<UserProfile>) => void;
  setPerRunSpendingLimitUsd: (limit: number) => void;
  setDailySpendingLimitUsd: (limit: number) => void;
  setStorageBackend: (backend: "local" | "supabase") => void;
  setStorageUsedBytes: (bytes: number) => void;
  setProviderKeyConfigured: (
    provider: ProviderKeyId,
    configured: boolean,
    updatedAt?: string | null
  ) => void;
  setCoreHealth: (health: CoreHealthState) => void;
}

export const createUserSettingsSlice: StateCreator<
  UserSettingsSlice,
  [],
  [],
  UserSettingsSlice
> = (set) => ({
  userProfile: {
    name: "Đạo diễn Sóc Nhỏ",
    email: "director@socnhotv.vn",
    avatarDataUrl: "/demo/characters/soc_nho_01.png",
  },
  perRunSpendingLimitUsd: 2.5,
  dailySpendingLimitUsd: 15.0,
  storageBackend: "local",
  storageUsedBytes: 142080,
  apiKeyStatus: {
    gemini: { configured: false, updatedAt: null },
    fal: { configured: false, updatedAt: null },
    openai: { configured: false, updatedAt: null },
    replicate: { configured: false, updatedAt: null },
  },
  coreHealth: {
    online: true,
    version: "0.1.0",
  },
  setUserProfile: (updates) =>
    set((s) => ({ userProfile: { ...s.userProfile, ...updates } })),
  setPerRunSpendingLimitUsd: (perRunSpendingLimitUsd) =>
    set({ perRunSpendingLimitUsd: Math.max(0.1, perRunSpendingLimitUsd) }),
  setDailySpendingLimitUsd: (dailySpendingLimitUsd) =>
    set({ dailySpendingLimitUsd: Math.max(0.5, dailySpendingLimitUsd) }),
  setStorageBackend: (storageBackend) => set({ storageBackend }),
  setStorageUsedBytes: (storageUsedBytes) => set({ storageUsedBytes }),
  setProviderKeyConfigured: (provider, configured, updatedAt = null) =>
    set((s) => ({
      apiKeyStatus: {
        ...s.apiKeyStatus,
        [provider]: {
          configured,
          updatedAt: updatedAt || new Date().toISOString(),
        },
      },
    })),
  setCoreHealth: (coreHealth) => set({ coreHealth }),
});
