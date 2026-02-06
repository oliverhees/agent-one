import { useQuery, useMutation, UseQueryOptions } from "@tanstack/react-query";
import api from "../services/api";
import { AxiosError } from "axios";

/**
 * Generic API Hook mit TanStack Query
 * Kann für beliebige GET Requests verwendet werden
 */
export const useApiQuery = <T>(
  key: string[],
  url: string,
  options?: UseQueryOptions<T, AxiosError>
) => {
  return useQuery<T, AxiosError>({
    queryKey: key,
    queryFn: async () => {
      const response = await api.get<T>(url);
      return response.data;
    },
    ...options,
  });
};

/**
 * Generic Mutation Hook
 * Kann für POST/PUT/DELETE Requests verwendet werden
 */
export const useApiMutation = <TData, TVariables>(
  url: string,
  method: "post" | "put" | "delete" = "post"
) => {
  return useMutation<TData, AxiosError, TVariables>({
    mutationFn: async (data: TVariables) => {
      const response = await api[method]<TData>(url, data);
      return response.data;
    },
  });
};
