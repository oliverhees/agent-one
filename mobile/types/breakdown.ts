import { Task, TaskPriority } from "./task";

export interface SuggestedSubtask {
  title: string;
  description: string;
  estimated_minutes: number;
  order: number;
}

export interface BreakdownResponse {
  parent_task: {
    id: string;
    title: string;
    priority: TaskPriority;
    estimated_minutes: number | null;
  };
  suggested_subtasks: SuggestedSubtask[];
}

export interface BreakdownConfirmRequest {
  subtasks: {
    title: string;
    description?: string;
    estimated_minutes?: number;
  }[];
}

export interface BreakdownConfirmResponse {
  parent_task: {
    id: string;
    title: string;
    status: string;
  };
  created_subtasks: Task[];
}
