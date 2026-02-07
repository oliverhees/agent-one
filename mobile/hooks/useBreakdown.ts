import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { breakdownApi } from "../services/breakdownApi";
import {
  BreakdownResponse,
  BreakdownConfirmRequest,
  BreakdownConfirmResponse,
} from "../types/breakdown";

const TASK_KEYS = {
  all: ["tasks"] as const,
  lists: () => [...TASK_KEYS.all, "list"] as const,
  details: () => [...TASK_KEYS.all, "detail"] as const,
  detail: (id: string) => [...TASK_KEYS.details(), id] as const,
};

export function useTaskBreakdown() {
  return useMutation<BreakdownResponse, AxiosError, string>({
    mutationFn: (taskId) => breakdownApi.suggest(taskId),
  });
}

export function useConfirmBreakdown() {
  const queryClient = useQueryClient();
  return useMutation<
    BreakdownConfirmResponse,
    AxiosError,
    { taskId: string; data: BreakdownConfirmRequest }
  >({
    mutationFn: ({ taskId, data }) => breakdownApi.confirm(taskId, data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({
        queryKey: TASK_KEYS.detail(response.parent_task.id),
      });
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.lists() });
    },
  });
}
