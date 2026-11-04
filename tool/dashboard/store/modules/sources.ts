import { create } from "zustand";

export interface SourcesState {}

export const useSourcesStore = create<SourcesState>()(() => ({}));
