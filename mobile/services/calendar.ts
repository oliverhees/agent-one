import api from "./api";

export interface CalendarEvent {
  id: string;
  title: string;
  description: string | null;
  start_time: string;
  end_time: string;
  location: string | null;
  is_all_day: boolean;
  calendar_provider: string;
  raw_data: Record<string, unknown>;
  created_at: string;
}

export interface CalendarEventListResponse {
  events: CalendarEvent[];
  total: number;
}

export interface CalendarStatus {
  connected: boolean;
  provider: string | null;
  last_synced: string | null;
}

export const calendarApi = {
  getStatus: async (): Promise<CalendarStatus> => {
    const response = await api.get<CalendarStatus>("/calendar/status");
    return response.data;
  },

  getTodayEvents: async (): Promise<CalendarEventListResponse> => {
    const response = await api.get<CalendarEventListResponse>("/calendar/events");
    return response.data;
  },

  getUpcomingEvents: async (hours = 24): Promise<CalendarEventListResponse> => {
    const response = await api.get<CalendarEventListResponse>(
      `/calendar/events/upcoming?hours=${hours}`
    );
    return response.data;
  },

  sync: async (): Promise<{ synced_count: number }> => {
    const response = await api.post<{ synced_count: number }>("/calendar/sync");
    return response.data;
  },

  getAuthUrl: async (): Promise<{ auth_url: string }> => {
    const response = await api.get<{ auth_url: string }>("/calendar/auth/google");
    return response.data;
  },

  disconnect: async (): Promise<void> => {
    await api.delete("/calendar/disconnect");
  },
};
