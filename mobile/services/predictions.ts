import api from "./api";

export interface Prediction {
  id: string;
  user_id: string;
  pattern_type: string;
  confidence: number;
  predicted_for: string;
  time_horizon: string;
  trigger_factors: Record<string, unknown>;
  graphiti_context: Record<string, unknown>;
  status: string;
  resolved_at: string | null;
  created_at: string;
}

export interface PredictionListResponse {
  predictions: Prediction[];
  total: number;
}

export interface RunManuallyResponse {
  predictions: Prediction[];
  expired_count: number;
}

export const predictionsApi = {
  getActive: async (): Promise<PredictionListResponse> => {
    const response = await api.get<PredictionListResponse>("/predictions/active");
    return response.data;
  },

  getHistory: async (limit = 20, offset = 0): Promise<PredictionListResponse> => {
    const response = await api.get<PredictionListResponse>(
      `/predictions/history?limit=${limit}&offset=${offset}`
    );
    return response.data;
  },

  resolve: async (id: string, status: "confirmed" | "avoided"): Promise<Prediction> => {
    const response = await api.post<Prediction>(`/predictions/${id}/resolve`, { status });
    return response.data;
  },

  runManually: async (): Promise<RunManuallyResponse> => {
    const response = await api.post<RunManuallyResponse>("/predictions/run");
    return response.data;
  },
};
