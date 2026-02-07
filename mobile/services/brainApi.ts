import api from "./api";
import {
  BrainEntry,
  BrainEntryCreate,
  BrainEntryUpdate,
  BrainEntryListResponse,
  BrainSearchResponse,
  BrainEntryListParams,
  BrainSearchParams,
} from "../types/brain";

export const brainApi = {
  create: async (data: BrainEntryCreate): Promise<BrainEntry> => {
    const response = await api.post<BrainEntry>("/brain/entries", data);
    return response.data;
  },

  list: async (params?: BrainEntryListParams): Promise<BrainEntryListResponse> => {
    const response = await api.get<BrainEntryListResponse>("/brain/entries", {
      params,
    });
    return response.data;
  },

  get: async (id: string): Promise<BrainEntry> => {
    const response = await api.get<BrainEntry>(`/brain/entries/${id}`);
    return response.data;
  },

  update: async (id: string, data: BrainEntryUpdate): Promise<BrainEntry> => {
    const response = await api.put<BrainEntry>(
      `/brain/entries/${id}`,
      data
    );
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/brain/entries/${id}`);
  },

  search: async (params: BrainSearchParams): Promise<BrainSearchResponse> => {
    const response = await api.get<BrainSearchResponse>("/brain/search", {
      params,
    });
    return response.data;
  },
};
