import { create } from "zustand";
import {
  wellbeingApi,
  WellbeingScore,
  WellbeingHistory,
  InterventionItem,
} from "../services/wellbeing";

interface WellbeingState {
  score: WellbeingScore | null;
  history: WellbeingHistory | null;
  interventions: InterventionItem[];
  isLoading: boolean;
  error: string | null;
  fetchScore: () => Promise<void>;
  fetchHistory: (days?: number) => Promise<void>;
  fetchInterventions: () => Promise<void>;
  dismissIntervention: (id: string) => Promise<void>;
  actOnIntervention: (id: string) => Promise<void>;
}

export const useWellbeingStore = create<WellbeingState>((set, get) => ({
  score: null,
  history: null,
  interventions: [],
  isLoading: false,
  error: null,

  fetchScore: async () => {
    set({ isLoading: true, error: null });
    try {
      const score = await wellbeingApi.getScore();
      set({ score, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  fetchHistory: async (days = 7) => {
    try {
      const history = await wellbeingApi.getHistory(days);
      set({ history });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  fetchInterventions: async () => {
    try {
      const interventions = await wellbeingApi.getInterventions();
      set({ interventions });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  dismissIntervention: async (id: string) => {
    await wellbeingApi.dismissIntervention(id);
    set((state) => ({
      interventions: state.interventions.filter((i) => i.id !== id),
    }));
  },

  actOnIntervention: async (id: string) => {
    await wellbeingApi.actOnIntervention(id);
    set((state) => ({
      interventions: state.interventions.filter((i) => i.id !== id),
    }));
  },
}));
