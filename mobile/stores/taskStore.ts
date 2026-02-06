import { create } from "zustand";

// Placeholder für Phase 2
interface Task {
  id: string;
  title: string;
  completed: boolean;
}

interface TaskState {
  tasks: Task[];
  isLoading: boolean;
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  isLoading: false,
}));
