import {
  useQuery,
  useMutation,
  useQueryClient,
  useInfiniteQuery,
} from "@tanstack/react-query";
import { AxiosError } from "axios";
import { nudgeApi } from "../services/nudgeApi";
import {
  NudgeListResponse,
  NudgeHistoryResponse,
  NudgeAcknowledgeResponse,
} from "../types/nudge";

const NUDGE_KEYS = {
  all: ["nudges"] as const,
  active: () => [...NUDGE_KEYS.all, "active"] as const,
  history: () => [...NUDGE_KEYS.all, "history"] as const,
};

export function useActiveNudges() {
  return useQuery<NudgeListResponse, AxiosError>({
    queryKey: NUDGE_KEYS.active(),
    queryFn: () => nudgeApi.getActive(),
  });
}

export function useAcknowledgeNudge() {
  const queryClient = useQueryClient();
  return useMutation<NudgeAcknowledgeResponse, AxiosError, string>({
    mutationFn: (id) => nudgeApi.acknowledge(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NUDGE_KEYS.active() });
      queryClient.invalidateQueries({ queryKey: NUDGE_KEYS.history() });
    },
  });
}

export function useNudgeHistory() {
  return useInfiniteQuery<NudgeHistoryResponse, AxiosError>({
    queryKey: NUDGE_KEYS.history(),
    queryFn: ({ pageParam }) =>
      nudgeApi.getHistory({ cursor: pageParam as string | undefined }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.next_cursor ?? undefined : undefined,
  });
}

export { NUDGE_KEYS };
