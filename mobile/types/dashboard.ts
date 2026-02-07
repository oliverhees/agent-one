import { TaskPriority, TaskStatus } from "./task";

export interface DashboardTask {
  id: string;
  title: string;
  priority: TaskPriority;
  status: TaskStatus;
  due_date: string | null;
  estimated_minutes: number | null;
}

export interface DashboardGamification {
  total_xp: number;
  level: number;
  streak: number;
  progress_percent: number;
}

export interface DashboardDeadline {
  task_title: string;
  due_date: string;
}

export interface DashboardSummary {
  today_tasks: DashboardTask[];
  gamification: DashboardGamification;
  next_deadline: DashboardDeadline | null;
  active_nudges_count: number;
  motivational_quote: string;
}
