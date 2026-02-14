import api from "./api";

export interface Webhook {
  id: string;
  user_id: string;
  name: string;
  url: string;
  direction: string;
  events: string[];
  is_active: boolean;
  created_at: string;
}

export interface WebhookCreate {
  name: string;
  url: string;
  direction: "incoming" | "outgoing";
  events?: string[];
}

export interface WebhookListResponse {
  webhooks: Webhook[];
  total: number;
}

export interface WebhookLog {
  id: string;
  webhook_id: string;
  direction: string;
  event_type: string;
  payload: Record<string, unknown>;
  status_code: number | null;
  attempt: number;
  success: boolean;
  created_at: string;
}

export interface WebhookLogListResponse {
  logs: WebhookLog[];
  total: number;
}

export const webhooksApi = {
  list: async (): Promise<WebhookListResponse> => {
    const response = await api.get<WebhookListResponse>("/webhooks");
    return response.data;
  },

  create: async (data: WebhookCreate): Promise<Webhook> => {
    const response = await api.post<Webhook>("/webhooks", data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/webhooks/${id}`);
  },

  getLogs: async (id: string, limit = 50): Promise<WebhookLogListResponse> => {
    const response = await api.get<WebhookLogListResponse>(
      `/webhooks/${id}/logs?limit=${limit}`
    );
    return response.data;
  },
};
