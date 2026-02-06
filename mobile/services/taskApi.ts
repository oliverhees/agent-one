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
    const response = await api.post<Task>("/api/v1/tasks", data);
    return response.data;
  },

  list: async (params?: TaskListParams): Promise<TaskListResponse> => {
    const response = await api.get<TaskListResponse>("/api/v1/tasks", { params });
    return response.data;
  },

  get: async (id: string): Promise<Task> => {
    const response = await api.get<Task>(`/api/v1/tasks/${id}`);
    return response.data;
  },

  update: async (id: string, data: TaskUpdate): Promise<Task> => {
    const response = await api.put<Task>(`/api/v1/tasks/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/tasks/${id}`);
  },

  complete: async (id: string): Promise<TaskCompleteResponse> => {
    const response = await api.post<TaskCompleteResponse>(
      `/api/v1/tasks/${id}/complete`
    );
    return response.data;
  },

  today: async (): Promise<TaskTodayResponse> => {
    const response = await api.get<TaskTodayResponse>("/api/v1/tasks/today");
    return response.data;
  },
};
