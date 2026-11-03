import type { StateCreator } from "zustand";

export interface UISlice {
  theme: "light" | "dark" | "system";
  locale: "vi" | "en";
  mobileMenuOpen: boolean;
  activeDrawer: string | null;
  setTheme: (theme: "light" | "dark" | "system") => void;
  setLocale: (locale: "vi" | "en") => void;
  setMobileMenuOpen: (open: boolean) => void;
  setActiveDrawer: (drawer: string | null) => void;
}

export const createUISlice: StateCreator<UISlice, [], [], UISlice> = (set) => ({
  theme: "system",
  locale: "vi",
  mobileMenuOpen: false,
  activeDrawer: null,
  setTheme: (theme) => set({ theme }),
  setLocale: (locale) => set({ locale }),
  setMobileMenuOpen: (open) => set({ mobileMenuOpen: open }),
  setActiveDrawer: (drawer) => set({ activeDrawer: drawer }),
});
