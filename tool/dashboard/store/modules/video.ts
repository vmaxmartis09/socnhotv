import { create } from "zustand";

export interface VideoState {}

export const useVideoStore = create<VideoState>()(() => ({}));
