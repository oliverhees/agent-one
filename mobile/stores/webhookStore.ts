import { create } from "zustand";
import { webhooksApi, Webhook, WebhookCreate } from "../services/webhooks";

interface WebhookState {
  webhooks: Webhook[];
  isLoading: boolean;
  error: string | null;
  fetchWebhooks: () => Promise<void>;
  createWebhook: (data: WebhookCreate) => Promise<void>;
  deleteWebhook: (id: string) => Promise<void>;
}

export const useWebhookStore = create<WebhookState>((set, get) => ({
  webhooks: [],
  isLoading: false,
  error: null,

  fetchWebhooks: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await webhooksApi.list();
      set({ webhooks: res.webhooks, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  createWebhook: async (data) => {
    try {
      const webhook = await webhooksApi.create(data);
      const { webhooks } = get();
      set({ webhooks: [...webhooks, webhook] });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  deleteWebhook: async (id) => {
    try {
      await webhooksApi.delete(id);
      const { webhooks } = get();
      set({ webhooks: webhooks.filter((w) => w.id !== id) });
    } catch (e: any) {
      set({ error: e.message });
    }
  },
}));
