import { create } from "zustand";

export interface SocialState {}

export const useSocialStore = create<SocialState>()(() => ({}));
