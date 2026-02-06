import { create } from "zustand";

// Placeholder für Phase 2
interface Notification {
  id: string;
  title: string;
  message: string;
  read: boolean;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
}));
