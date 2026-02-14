import { create } from "zustand";
import { predictionsApi, Prediction } from "../services/predictions";

interface PredictionState {
  activePredictions: Prediction[];
  history: Prediction[];
  historyTotal: number;
  isLoading: boolean;
  error: string | null;
  fetchActive: () => Promise<void>;
  fetchHistory: (limit?: number, offset?: number) => Promise<void>;
  resolve: (id: string, status: "confirmed" | "avoided") => Promise<void>;
  runManually: () => Promise<void>;
}

export const usePredictionStore = create<PredictionState>((set, get) => ({
  activePredictions: [],
  history: [],
  historyTotal: 0,
  isLoading: false,
  error: null,

  fetchActive: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await predictionsApi.getActive();
      set({ activePredictions: res.predictions, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  fetchHistory: async (limit = 20, offset = 0) => {
    set({ isLoading: true, error: null });
    try {
      const res = await predictionsApi.getHistory(limit, offset);
      set({
        history: res.predictions,
        historyTotal: res.total,
        isLoading: false,
      });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  resolve: async (id, status) => {
    try {
      await predictionsApi.resolve(id, status);
      const { activePredictions } = get();
      set({
        activePredictions: activePredictions.filter((p) => p.id !== id),
      });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  runManually: async () => {
    set({ isLoading: true, error: null });
    try {
      await predictionsApi.runManually();
      await get().fetchActive();
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },
}));
