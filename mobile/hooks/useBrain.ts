import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { AxiosError } from "axios";
import { brainApi } from "../services/brainApi";
import {
  BrainEntry,
  BrainEntryCreate,
  BrainEntryUpdate,
  BrainEntryListResponse,
  BrainSearchResponse,
  BrainEntryListParams,
  BrainSearchParams,
} from "../types/brain";

const BRAIN_KEYS = {
  all: ["brain"] as const,
  lists: () => [...BRAIN_KEYS.all, "list"] as const,
  list: (params?: BrainEntryListParams) =>
    [...BRAIN_KEYS.lists(), params] as const,
  details: () => [...BRAIN_KEYS.all, "detail"] as const,
  detail: (id: string) => [...BRAIN_KEYS.details(), id] as const,
  search: (params: BrainSearchParams) =>
    [...BRAIN_KEYS.all, "search", params] as const,
};

export function useBrainEntryList(params?: BrainEntryListParams) {
  return useInfiniteQuery<BrainEntryListResponse, AxiosError>({
    queryKey: BRAIN_KEYS.list(params),
    queryFn: ({ pageParam }) =>
      brainApi.list({ ...params, cursor: pageParam as string | undefined }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.next_cursor ?? undefined : undefined,
  });
}

export function useBrainEntry(id: string) {
  return useQuery<BrainEntry, AxiosError>({
    queryKey: BRAIN_KEYS.detail(id),
    queryFn: () => brainApi.get(id),
    enabled: !!id,
  });
}

export function useBrainSearch(params: BrainSearchParams) {
  return useQuery<BrainSearchResponse, AxiosError>({
    queryKey: BRAIN_KEYS.search(params),
    queryFn: () => brainApi.search(params),
    enabled: params.q.length > 0,
  });
}

export function useCreateBrainEntry() {
  const queryClient = useQueryClient();
  return useMutation<BrainEntry, AxiosError, BrainEntryCreate>({
    mutationFn: (data) => brainApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BRAIN_KEYS.lists() });
    },
  });
}

export function useUpdateBrainEntry() {
  const queryClient = useQueryClient();
  return useMutation<
    BrainEntry,
    AxiosError,
    { id: string; data: BrainEntryUpdate }
  >({
    mutationFn: ({ id, data }) => brainApi.update(id, data),
    onSuccess: (updatedEntry) => {
      queryClient.setQueryData(
        BRAIN_KEYS.detail(updatedEntry.id),
        updatedEntry
      );
      queryClient.invalidateQueries({ queryKey: BRAIN_KEYS.lists() });
    },
  });
}

export function useDeleteBrainEntry() {
  const queryClient = useQueryClient();
  return useMutation<void, AxiosError, string>({
    mutationFn: (id) => brainApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BRAIN_KEYS.lists() });
    },
  });
}
