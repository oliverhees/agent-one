export type TaskPriority = "low" | "medium" | "high" | "urgent";
export type TaskStatus = "open" | "in_progress" | "done" | "cancelled";
export type TaskSource = "manual" | "chat_extract" | "breakdown" | "recurring";

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  due_date: string | null;
  completed_at: string | null;
  xp_earned: number;
  parent_id: string | null;
  is_recurring: boolean;
  recurrence_rule: string | null;
  tags: string[];
  source: TaskSource;
  source_message_id: string | null;
  estimated_minutes: number | null;
  sub_tasks: Task[];
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  priority?: TaskPriority;
  due_date?: string;
  tags?: string[];
  parent_id?: string;
  estimated_minutes?: number;
}

export interface TaskUpdate {
  title?: string;
  description?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_date?: string | null;
  tags?: string[];
  estimated_minutes?: number | null;
}

export interface TaskCompleteResponse {
  task: Task;
  xp_earned: number;
  xp_breakdown: {
    base: number;
    on_time_bonus: number;
    streak_bonus: number;
  };
  total_xp: number;
  level: number;
  level_up: boolean;
}

export interface TaskListResponse {
  items: Task[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number;
}

export interface TaskTodayResponse {
  items: Task[];
  total_count: number;
  total_estimated_minutes: number;
}

export interface TaskListParams {
  cursor?: string;
  limit?: number;
  status?: TaskStatus;
  priority?: TaskPriority;
  tags?: string;
  has_due_date?: boolean;
  parent_id?: string;
}
