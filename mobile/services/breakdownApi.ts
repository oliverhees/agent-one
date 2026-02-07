import api from "./api";
import {
  BreakdownResponse,
  BreakdownConfirmRequest,
  BreakdownConfirmResponse,
} from "../types/breakdown";

export const breakdownApi = {
  suggest: async (taskId: string): Promise<BreakdownResponse> => {
    const response = await api.post<BreakdownResponse>(
      `/tasks/${taskId}/breakdown`
    );
    return response.data;
  },

  confirm: async (
    taskId: string,
    data: BreakdownConfirmRequest
  ): Promise<BreakdownConfirmResponse> => {
    const response = await api.post<BreakdownConfirmResponse>(
      `/tasks/${taskId}/breakdown/confirm`,
      data
    );
    return response.data;
  },
};
