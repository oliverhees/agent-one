import api from "./api";
import {
  NudgeListResponse,
  NudgeHistoryResponse,
  NudgeAcknowledgeResponse,
} from "../types/nudge";

export const nudgeApi = {
  getActive: async (): Promise<NudgeListResponse> => {
    const response = await api.get<NudgeListResponse>("/nudges");
    return response.data;
  },

  acknowledge: async (id: string): Promise<NudgeAcknowledgeResponse> => {
    const response = await api.post<NudgeAcknowledgeResponse>(
      `/nudges/${id}/acknowledge`
    );
    return response.data;
  },

  getHistory: async (params?: {
    cursor?: string;
    limit?: number;
  }): Promise<NudgeHistoryResponse> => {
    const response = await api.get<NudgeHistoryResponse>(
      "/nudges/history",
      { params }
    );
    return response.data;
  },
};
