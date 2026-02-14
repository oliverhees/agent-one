import api from "./api";

export interface TrustScore {
  agent_type: string;
  action_type: string;
  trust_level: number;
  successful_actions: number;
  total_actions: number;
}

export interface TrustOverview {
  scores: TrustScore[];
}

export interface ApprovalRequest {
  id: string;
  agent_type: string;
  action: string;
  action_details: Record<string, unknown>;
  status: string;
  timeout_seconds: number;
  expires_at: string | null;
  created_at: string;
}

export interface EmailConfig {
  id: string;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  imap_host: string;
  imap_port: number;
  imap_user: string;
  is_active: boolean;
}

export interface EmailConfigCreate {
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_password: string;
  imap_host: string;
  imap_port: number;
  imap_user: string;
  imap_password: string;
}

export interface AgentActivity {
  id: string;
  agent_type: string;
  action: string;
  status: string;
  details: Record<string, unknown> | null;
  result: string | null;
  duration_ms: number | null;
  error: string | null;
  created_at: string;
}

export const agentApi = {
  getTrustScores: async (): Promise<TrustOverview> => {
    const response = await api.get<TrustOverview>("/agents/trust");
    return response.data;
  },

  setTrustLevel: async (agent_type: string, trust_level: number) => {
    const response = await api.put("/agents/trust", { agent_type, trust_level });
    return response.data;
  },

  getPendingApprovals: async (): Promise<ApprovalRequest[]> => {
    const response = await api.get<ApprovalRequest[]>("/agents/approvals/pending");
    return response.data;
  },

  approve: async (approvalId: string, approved: boolean, reason?: string) => {
    const response = await api.post(`/agents/approve/${approvalId}`, { approved, reason });
    return response.data;
  },

  getEmailConfig: async (): Promise<EmailConfig | null> => {
    const response = await api.get<EmailConfig | null>("/agents/email/config");
    return response.data;
  },

  saveEmailConfig: async (config: EmailConfigCreate): Promise<EmailConfig> => {
    const response = await api.post<EmailConfig>("/agents/email/config", config);
    return response.data;
  },
};
