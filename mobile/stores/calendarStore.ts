import { create } from "zustand";
import { calendarApi, CalendarEvent, CalendarStatus } from "../services/calendar";

interface CalendarState {
  status: CalendarStatus | null;
  todayEvents: CalendarEvent[];
  isLoading: boolean;
  error: string | null;
  fetchStatus: () => Promise<void>;
  fetchTodayEvents: () => Promise<void>;
  sync: () => Promise<void>;
  disconnect: () => Promise<void>;
}

export const useCalendarStore = create<CalendarState>((set) => ({
  status: null,
  todayEvents: [],
  isLoading: false,
  error: null,

  fetchStatus: async () => {
    try {
      const status = await calendarApi.getStatus();
      set({ status });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  fetchTodayEvents: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await calendarApi.getTodayEvents();
      set({ todayEvents: res.events, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  sync: async () => {
    set({ isLoading: true, error: null });
    try {
      await calendarApi.sync();
      const res = await calendarApi.getTodayEvents();
      set({ todayEvents: res.events, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  disconnect: async () => {
    try {
      await calendarApi.disconnect();
      set({ status: { connected: false, provider: null, last_synced: null }, todayEvents: [] });
    } catch (e: any) {
      set({ error: e.message });
    }
  },
}));
