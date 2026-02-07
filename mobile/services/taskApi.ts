import api from "./api";
import {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskCompleteResponse,
  TaskListResponse,
  TaskTodayResponse,
  TaskListParams,
} from "../types/task";

export const taskApi = {
  create: async (data: TaskCreate): Promise<Task> => {
    const response = await api.post<Task>("/tasks", data);
    return response.data;
  },

  list: async (params?: TaskListParams): Promise<TaskListResponse> => {
    const response = await api.get<TaskListResponse>("/tasks", { params });
    return response.data;
  },

  get: async (id: string): Promise<Task> => {
    const response = await api.get<Task>(`/tasks/${id}`);
    return response.data;
  },

  update: async (id: string, data: TaskUpdate): Promise<Task> => {
    const response = await api.put<Task>(`/tasks/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/tasks/${id}`);
  },

  complete: async (id: string): Promise<TaskCompleteResponse> => {
    const response = await api.post<TaskCompleteResponse>(
      `/tasks/${id}/complete`
    );
    return response.data;
  },

  today: async (): Promise<TaskTodayResponse> => {
    const response = await api.get<TaskTodayResponse>("/tasks/today");
    return response.data;
  },
};
