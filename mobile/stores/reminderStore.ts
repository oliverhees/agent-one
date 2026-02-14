import { create } from "zustand";
import { remindersApi, Reminder, ReminderCreate } from "../services/reminders";

interface ReminderState {
  reminders: Reminder[];
  total: number;
  isLoading: boolean;
  error: string | null;
  fetchReminders: () => Promise<void>;
  createReminder: (data: ReminderCreate) => Promise<void>;
  deleteReminder: (id: string) => Promise<void>;
  snoozeReminder: (id: string, until: string) => Promise<void>;
  dismissReminder: (id: string) => Promise<void>;
}

export const useReminderStore = create<ReminderState>((set, get) => ({
  reminders: [],
  total: 0,
  isLoading: false,
  error: null,

  fetchReminders: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await remindersApi.list();
      set({ reminders: res.reminders, total: res.total, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  createReminder: async (data) => {
    try {
      const reminder = await remindersApi.create(data);
      const { reminders, total } = get();
      set({ reminders: [...reminders, reminder], total: total + 1 });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  deleteReminder: async (id) => {
    try {
      await remindersApi.delete(id);
      const { reminders, total } = get();
      set({ reminders: reminders.filter((r) => r.id !== id), total: total - 1 });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  snoozeReminder: async (id, until) => {
    try {
      const updated = await remindersApi.snooze(id, until);
      const { reminders } = get();
      set({ reminders: reminders.map((r) => (r.id === id ? updated : r)) });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  dismissReminder: async (id) => {
    try {
      const updated = await remindersApi.dismiss(id);
      const { reminders } = get();
      set({ reminders: reminders.map((r) => (r.id === id ? updated : r)) });
    } catch (e: any) {
      set({ error: e.message });
    }
  },
}));
