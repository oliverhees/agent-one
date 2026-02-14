import api from "./api";

export interface N8nWorkflow {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  webhook_url: string;
  input_schema: Record<string, unknown>;
  is_active: boolean;
  execution_count: number;
  last_executed_at: string | null;
  created_at: string;
}

export interface N8nWorkflowCreate {
  name: string;
  webhook_url: string;
  description?: string;
  input_schema?: Record<string, unknown>;
}

export interface N8nWorkflowListResponse {
  workflows: N8nWorkflow[];
  total: number;
}

export interface N8nExecuteResponse {
  workflow_id: string;
  success: boolean;
  response_data: Record<string, unknown>;
  execution_count: number;
}

export const n8nApi = {
  listWorkflows: async (): Promise<N8nWorkflowListResponse> => {
    const response = await api.get<N8nWorkflowListResponse>("/n8n/workflows");
    return response.data;
  },

  createWorkflow: async (data: N8nWorkflowCreate): Promise<N8nWorkflow> => {
    const response = await api.post<N8nWorkflow>("/n8n/workflows", data);
    return response.data;
  },

  deleteWorkflow: async (id: string): Promise<void> => {
    await api.delete(`/n8n/workflows/${id}`);
  },

  executeWorkflow: async (
    id: string,
    inputData: Record<string, unknown> = {}
  ): Promise<N8nExecuteResponse> => {
    const response = await api.post<N8nExecuteResponse>(
      `/n8n/workflows/${id}/execute`,
      { input_data: inputData }
    );
    return response.data;
  },
};
