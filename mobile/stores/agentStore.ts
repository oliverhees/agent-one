import { create } from "zustand";
import { agentApi, ApprovalRequest } from "../services/agents";

interface AgentState {
  pendingApprovals: ApprovalRequest[];
  isLoading: boolean;
  fetchPendingApprovals: () => Promise<void>;
  approveAction: (id: string, approved: boolean, reason?: string) => Promise<void>;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  pendingApprovals: [],
  isLoading: false,
  fetchPendingApprovals: async () => {
    set({ isLoading: true });
    try {
      const data = await agentApi.getPendingApprovals();
      set({ pendingApprovals: data });
    } catch (e) {
      console.error("Failed to fetch approvals:", e);
    } finally {
      set({ isLoading: false });
    }
  },
  approveAction: async (id, approved, reason) => {
    await agentApi.approve(id, approved, reason);
    await get().fetchPendingApprovals();
  },
}));
