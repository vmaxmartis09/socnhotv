import { create } from "zustand";

interface CreateState {
  isOpen: boolean;
  openCreate: () => void;
  closeCreate: () => void;
  toggleCreate: () => void;
}

export const useCreateStore = create<CreateState>((set) => ({
  isOpen: false,
  openCreate: () => set({ isOpen: true }),
  closeCreate: () => set({ isOpen: false }),
  toggleCreate: () => set((s) => ({ isOpen: !s.isOpen })),
}));
