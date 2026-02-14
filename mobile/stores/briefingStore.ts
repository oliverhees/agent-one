import { create } from "zustand";
import {
  briefingApi,
  BriefingData,
  BrainDumpResult,
} from "../services/briefing";

interface BriefingState {
  briefing: BriefingData | null;
  isLoading: boolean;
  error: string | null;
  fetchToday: () => Promise<void>;
  generateBriefing: () => Promise<void>;
  markAsRead: () => Promise<void>;
  submitBrainDump: (text: string) => Promise<BrainDumpResult | null>;
}

export const useBriefingStore = create<BriefingState>((set, get) => ({
  briefing: null,
  isLoading: false,
  error: null,

  fetchToday: async () => {
    set({ isLoading: true, error: null });
    try {
      const briefing = await briefingApi.getToday();
      set({ briefing, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  generateBriefing: async () => {
    set({ isLoading: true, error: null });
    try {
      const briefing = await briefingApi.generate();
      set({ briefing, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  markAsRead: async () => {
    const { briefing } = get();
    if (!briefing) return;
    try {
      await briefingApi.markAsRead(briefing.id);
      set({ briefing: { ...briefing, status: "read", read_at: new Date().toISOString() } });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  submitBrainDump: async (text: string) => {
    try {
      const result = await briefingApi.brainDump(text);
      return result;
    } catch (e: any) {
      set({ error: e.message });
      return null;
    }
  },
}));
