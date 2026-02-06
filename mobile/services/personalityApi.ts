import api from "./api";
import {
  PersonalityProfile,
  PersonalityProfileCreate,
  PersonalityProfileUpdate,
  PersonalityProfileListResponse,
  PersonalityTemplateListResponse,
} from "../types/personality";

export const personalityApi = {
  createProfile: async (
    data: PersonalityProfileCreate
  ): Promise<PersonalityProfile> => {
    const response = await api.post<PersonalityProfile>(
      "/api/v1/personality/profiles",
      data
    );
    return response.data;
  },

  listProfiles: async (): Promise<PersonalityProfileListResponse> => {
    const response = await api.get<PersonalityProfileListResponse>(
      "/api/v1/personality/profiles"
    );
    return response.data;
  },

  updateProfile: async (
    id: string,
    data: PersonalityProfileUpdate
  ): Promise<PersonalityProfile> => {
    const response = await api.put<PersonalityProfile>(
      `/api/v1/personality/profiles/${id}`,
      data
    );
    return response.data;
  },

  deleteProfile: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/personality/profiles/${id}`);
  },

  activateProfile: async (id: string): Promise<PersonalityProfile> => {
    const response = await api.post<PersonalityProfile>(
      `/api/v1/personality/profiles/${id}/activate`
    );
    return response.data;
  },

  listTemplates: async (): Promise<PersonalityTemplateListResponse> => {
    const response = await api.get<PersonalityTemplateListResponse>(
      "/api/v1/personality/templates"
    );
    return response.data;
  },
};
