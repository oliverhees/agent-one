import { useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { gamificationApi } from "../services/gamificationApi";
import {
  GamificationStats,
  XPHistoryResponse,
  AchievementListResponse,
} from "../types/gamification";

const GAMIFICATION_KEYS = {
  all: ["gamification"] as const,
  stats: () => [...GAMIFICATION_KEYS.all, "stats"] as const,
  history: (days?: number) =>
    [...GAMIFICATION_KEYS.all, "history", days] as const,
  achievements: () => [...GAMIFICATION_KEYS.all, "achievements"] as const,
};

export function useGamificationStats() {
  return useQuery<GamificationStats, AxiosError>({
    queryKey: GAMIFICATION_KEYS.stats(),
    queryFn: () => gamificationApi.getStats(),
  });
}

export function useXPHistory(days: number = 30) {
  return useQuery<XPHistoryResponse, AxiosError>({
    queryKey: GAMIFICATION_KEYS.history(days),
    queryFn: () => gamificationApi.getHistory(days),
  });
}

export function useAchievements() {
  return useQuery<AchievementListResponse, AxiosError>({
    queryKey: GAMIFICATION_KEYS.achievements(),
    queryFn: () => gamificationApi.getAchievements(),
  });
}

export { GAMIFICATION_KEYS };
