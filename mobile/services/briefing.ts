import api from "./api";

export interface BriefingTaskItem {
  task_id: string;
  title: string;
  priority: string;
  reason: string | null;
}

export interface BriefingData {
  id: string;
  briefing_date: string;
  content: string;
  tasks_suggested: BriefingTaskItem[];
  wellbeing_snapshot: Record<string, number | string>;
  status: string;
  read_at: string | null;
  created_at: string;
}

export interface BrainDumpResult {
  tasks_created: number;
  tasks: Array<{ title: string; priority: string }>;
  message: string;
}

export interface BriefingHistoryResponse {
  briefings: BriefingData[];
  days: number;
}

export const briefingApi = {
  getToday: async (): Promise<BriefingData | null> => {
    const response = await api.get<BriefingData | null>("/briefing/today");
    return response.data;
  },

  generate: async (): Promise<BriefingData> => {
    const response = await api.post<BriefingData>("/briefing/generate");
    return response.data;
  },

  getHistory: async (days = 7): Promise<BriefingHistoryResponse> => {
    const response = await api.get<BriefingHistoryResponse>(
      `/briefing/history?days=${days}`
    );
    return response.data;
  },

  markAsRead: async (id: string): Promise<void> => {
    await api.put(`/briefing/${id}/read`);
  },

  brainDump: async (text: string): Promise<BrainDumpResult> => {
    const response = await api.post<BrainDumpResult>("/briefing/brain-dump", {
      text,
    });
    return response.data;
  },
};
