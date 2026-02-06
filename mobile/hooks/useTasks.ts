import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { AxiosError } from "axios";
import { taskApi } from "../services/taskApi";
import {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskCompleteResponse,
  TaskListResponse,
  TaskTodayResponse,
  TaskListParams,
} from "../types/task";

const TASK_KEYS = {
  all: ["tasks"] as const,
  lists: () => [...TASK_KEYS.all, "list"] as const,
  list: (params?: TaskListParams) => [...TASK_KEYS.lists(), params] as const,
  details: () => [...TASK_KEYS.all, "detail"] as const,
  detail: (id: string) => [...TASK_KEYS.details(), id] as const,
  today: () => [...TASK_KEYS.all, "today"] as const,
};

export function useTaskList(params?: TaskListParams) {
  return useInfiniteQuery<TaskListResponse, AxiosError>({
    queryKey: TASK_KEYS.list(params),
    queryFn: ({ pageParam }) =>
      taskApi.list({ ...params, cursor: pageParam as string | undefined }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.next_cursor ?? undefined : undefined,
  });
}

export function useTask(id: string) {
  return useQuery<Task, AxiosError>({
    queryKey: TASK_KEYS.detail(id),
    queryFn: () => taskApi.get(id),
    enabled: !!id,
  });
}

export function useTodayTasks() {
  return useQuery<TaskTodayResponse, AxiosError>({
    queryKey: TASK_KEYS.today(),
    queryFn: () => taskApi.today(),
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation<Task, AxiosError, TaskCreate>({
    mutationFn: (data) => taskApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.lists() });
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.today() });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  return useMutation<Task, AxiosError, { id: string; data: TaskUpdate }>({
    mutationFn: ({ id, data }) => taskApi.update(id, data),
    onSuccess: (updatedTask) => {
      queryClient.setQueryData(TASK_KEYS.detail(updatedTask.id), updatedTask);
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.lists() });
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.today() });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  return useMutation<void, AxiosError, string>({
    mutationFn: (id) => taskApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.lists() });
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.today() });
    },
  });
}

export function useCompleteTask() {
  const queryClient = useQueryClient();
  return useMutation<TaskCompleteResponse, AxiosError, string>({
    mutationFn: (id) => taskApi.complete(id),
    onSuccess: (response) => {
      queryClient.setQueryData(
        TASK_KEYS.detail(response.task.id),
        response.task
      );
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.lists() });
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.today() });
    },
  });
}
