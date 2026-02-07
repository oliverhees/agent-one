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
      "/personality/profiles",
      data
    );
    return response.data;
  },

  listProfiles: async (): Promise<PersonalityProfileListResponse> => {
    const response = await api.get<PersonalityProfileListResponse>(
      "/personality/profiles"
    );
    return response.data;
  },

  updateProfile: async (
    id: string,
    data: PersonalityProfileUpdate
  ): Promise<PersonalityProfile> => {
    const response = await api.put<PersonalityProfile>(
      `/personality/profiles/${id}`,
      data
    );
    return response.data;
  },

  deleteProfile: async (id: string): Promise<void> => {
    await api.delete(`/personality/profiles/${id}`);
  },

  activateProfile: async (id: string): Promise<PersonalityProfile> => {
    const response = await api.post<PersonalityProfile>(
      `/personality/profiles/${id}/activate`
    );
    return response.data;
  },

  listTemplates: async (): Promise<PersonalityTemplateListResponse> => {
    const response = await api.get<PersonalityTemplateListResponse>(
      "/personality/templates"
    );
    return response.data;
  },
};
