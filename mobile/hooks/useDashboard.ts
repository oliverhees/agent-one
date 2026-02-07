import { useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { dashboardApi } from "../services/dashboardApi";
import { DashboardSummary } from "../types/dashboard";

const DASHBOARD_KEYS = {
  all: ["dashboard"] as const,
  summary: () => [...DASHBOARD_KEYS.all, "summary"] as const,
};

export function useDashboardSummary() {
  return useQuery<DashboardSummary, AxiosError>({
    queryKey: DASHBOARD_KEYS.summary(),
    queryFn: () => dashboardApi.getSummary(),
    refetchInterval: 60000,
  });
}

export { DASHBOARD_KEYS };
