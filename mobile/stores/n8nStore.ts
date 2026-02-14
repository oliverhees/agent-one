import { create } from "zustand";
import { n8nApi, N8nWorkflow, N8nWorkflowCreate } from "../services/n8n";

interface N8nState {
  workflows: N8nWorkflow[];
  isLoading: boolean;
  error: string | null;
  fetchWorkflows: () => Promise<void>;
  createWorkflow: (data: N8nWorkflowCreate) => Promise<void>;
  deleteWorkflow: (id: string) => Promise<void>;
  executeWorkflow: (id: string, inputData?: Record<string, unknown>) => Promise<void>;
}

export const useN8nStore = create<N8nState>((set, get) => ({
  workflows: [],
  isLoading: false,
  error: null,

  fetchWorkflows: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await n8nApi.listWorkflows();
      set({ workflows: res.workflows, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  createWorkflow: async (data) => {
    try {
      const workflow = await n8nApi.createWorkflow(data);
      const { workflows } = get();
      set({ workflows: [...workflows, workflow] });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  deleteWorkflow: async (id) => {
    try {
      await n8nApi.deleteWorkflow(id);
      const { workflows } = get();
      set({ workflows: workflows.filter((w) => w.id !== id) });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  executeWorkflow: async (id, inputData) => {
    set({ isLoading: true, error: null });
    try {
      await n8nApi.executeWorkflow(id, inputData);
      set({ isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },
}));
