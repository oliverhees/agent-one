import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { personalityApi } from "../services/personalityApi";
import {
  PersonalityProfile,
  PersonalityProfileCreate,
  PersonalityProfileUpdate,
  PersonalityProfileListResponse,
  PersonalityTemplateListResponse,
} from "../types/personality";

const PERSONALITY_KEYS = {
  all: ["personality"] as const,
  profiles: () => [...PERSONALITY_KEYS.all, "profiles"] as const,
  templates: () => [...PERSONALITY_KEYS.all, "templates"] as const,
};

export function usePersonalityProfiles() {
  return useQuery<PersonalityProfileListResponse, AxiosError>({
    queryKey: PERSONALITY_KEYS.profiles(),
    queryFn: () => personalityApi.listProfiles(),
  });
}

export function usePersonalityTemplates() {
  return useQuery<PersonalityTemplateListResponse, AxiosError>({
    queryKey: PERSONALITY_KEYS.templates(),
    queryFn: () => personalityApi.listTemplates(),
  });
}

export function useCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation<PersonalityProfile, AxiosError, PersonalityProfileCreate>({
    mutationFn: (data) => personalityApi.createProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.profiles() });
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation<
    PersonalityProfile,
    AxiosError,
    { id: string; data: PersonalityProfileUpdate }
  >({
    mutationFn: ({ id, data }) => personalityApi.updateProfile(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.profiles() });
    },
  });
}

export function useDeleteProfile() {
  const queryClient = useQueryClient();
  return useMutation<void, AxiosError, string>({
    mutationFn: (id) => personalityApi.deleteProfile(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.profiles() });
    },
  });
}

export function useActivateProfile() {
  const queryClient = useQueryClient();
  return useMutation<PersonalityProfile, AxiosError, string>({
    mutationFn: (id) => personalityApi.activateProfile(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.profiles() });
    },
  });
}
