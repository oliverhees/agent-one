import api from "./api";

export interface WellbeingScore {
  score: number;
  zone: "red" | "yellow" | "green";
  components: Record<string, number>;
  calculated_at: string;
}

export interface WellbeingHistory {
  scores: WellbeingScore[];
  trend: "rising" | "declining" | "stable";
  average_score: number;
  days: number;
}

export interface InterventionItem {
  id: string;
  type: string;
  trigger_pattern: string;
  message: string;
  status: string;
  created_at: string;
}

export const wellbeingApi = {
  getScore: async (): Promise<WellbeingScore> => {
    const response = await api.get<WellbeingScore>("/wellbeing/score");
    return response.data;
  },

  getHistory: async (days = 7): Promise<WellbeingHistory> => {
    const response = await api.get<WellbeingHistory>(
      `/wellbeing/history?days=${days}`
    );
    return response.data;
  },

  getInterventions: async (): Promise<InterventionItem[]> => {
    const response = await api.get<InterventionItem[]>(
      "/wellbeing/interventions"
    );
    return response.data;
  },

  dismissIntervention: async (id: string): Promise<void> => {
    await api.put(`/wellbeing/interventions/${id}`, { action: "dismiss" });
  },

  actOnIntervention: async (id: string): Promise<void> => {
    await api.put(`/wellbeing/interventions/${id}`, { action: "act" });
  },
};
