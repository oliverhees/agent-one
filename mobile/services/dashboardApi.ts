import api from "./api";
import { DashboardSummary } from "../types/dashboard";

export const dashboardApi = {
  getSummary: async (): Promise<DashboardSummary> => {
    const response = await api.get<DashboardSummary>(
      "/dashboard/summary"
    );
    return response.data;
  },
};
