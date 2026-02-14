import { create } from "zustand";
import { agentApi, TrustScore } from "../services/agents";

interface TrustState {
  scores: TrustScore[];
  fetchScores: () => Promise<void>;
  setLevel: (agentType: string, level: number) => Promise<void>;
}

export const useTrustStore = create<TrustState>((set) => ({
  scores: [],
  fetchScores: async () => {
    try {
      const data = await agentApi.getTrustScores();
      set({ scores: data.scores });
    } catch (e) {
      console.error("Failed to fetch trust scores:", e);
    }
  },
  setLevel: async (agentType, level) => {
    await agentApi.setTrustLevel(agentType, level);
    const data = await agentApi.getTrustScores();
    set({ scores: data.scores });
  },
}));
