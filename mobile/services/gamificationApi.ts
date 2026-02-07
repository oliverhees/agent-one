import api from "./api";
import {
  GamificationStats,
  XPHistoryResponse,
  AchievementListResponse,
} from "../types/gamification";

export const gamificationApi = {
  getStats: async (): Promise<GamificationStats> => {
    const response = await api.get<GamificationStats>(
      "/gamification/stats"
    );
    return response.data;
  },

  getHistory: async (days: number = 30): Promise<XPHistoryResponse> => {
    const response = await api.get<XPHistoryResponse>(
      "/gamification/history",
      { params: { days } }
    );
    return response.data;
  },

  getAchievements: async (): Promise<AchievementListResponse> => {
    const response = await api.get<AchievementListResponse>(
      "/gamification/achievements"
    );
    return response.data;
  },
};
