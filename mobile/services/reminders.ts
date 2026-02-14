import api from "./api";

export interface Reminder {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  remind_at: string;
  source: string;
  status: string;
  recurrence: string | null;
  recurrence_end: string | null;
  linked_task_id: string | null;
  linked_event_id: string | null;
  created_at: string;
}

export interface ReminderCreate {
  title: string;
  description?: string;
  remind_at: string;
  source?: string;
  recurrence?: string;
  recurrence_end?: string;
  linked_task_id?: string;
  linked_event_id?: string;
}

export interface ReminderListResponse {
  reminders: Reminder[];
  total: number;
}

export const remindersApi = {
  list: async (): Promise<ReminderListResponse> => {
    const response = await api.get<ReminderListResponse>("/reminders");
    return response.data;
  },

  listUpcoming: async (): Promise<ReminderListResponse> => {
    const response = await api.get<ReminderListResponse>("/reminders/upcoming");
    return response.data;
  },

  create: async (data: ReminderCreate): Promise<Reminder> => {
    const response = await api.post<Reminder>("/reminders", data);
    return response.data;
  },

  update: async (id: string, data: Partial<ReminderCreate>): Promise<Reminder> => {
    const response = await api.put<Reminder>(`/reminders/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/reminders/${id}`);
  },

  snooze: async (id: string, snoozeUntil: string): Promise<Reminder> => {
    const response = await api.post<Reminder>(`/reminders/${id}/snooze`, {
      snooze_until: snoozeUntil,
    });
    return response.data;
  },

  dismiss: async (id: string): Promise<Reminder> => {
    const response = await api.post<Reminder>(`/reminders/${id}/dismiss`);
    return response.data;
  },
};
