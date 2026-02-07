import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { settingsApi } from "../services/settingsApi";
import { ADHSSettings, ADHSSettingsUpdate } from "../types/settings";

const SETTINGS_KEYS = {
  all: ["settings"] as const,
  adhs: () => [...SETTINGS_KEYS.all, "adhs"] as const,
};

export function useADHSSettings() {
  return useQuery<ADHSSettings, AxiosError>({
    queryKey: SETTINGS_KEYS.adhs(),
    queryFn: () => settingsApi.getADHSSettings(),
  });
}

export function useUpdateADHSSettings() {
  const queryClient = useQueryClient();
  return useMutation<ADHSSettings, AxiosError, ADHSSettingsUpdate>({
    mutationFn: (data) => settingsApi.updateADHSSettings(data),
    onMutate: async (newSettings) => {
      await queryClient.cancelQueries({ queryKey: SETTINGS_KEYS.adhs() });
      const previous = queryClient.getQueryData<ADHSSettings>(
        SETTINGS_KEYS.adhs()
      );
      if (previous) {
        queryClient.setQueryData<ADHSSettings>(SETTINGS_KEYS.adhs(), {
          ...previous,
          ...newSettings,
        });
      }
      return { previous };
    },
    onError: (_err, _newSettings, context: any) => {
      if (context?.previous) {
        queryClient.setQueryData(SETTINGS_KEYS.adhs(), context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: SETTINGS_KEYS.adhs() });
    },
  });
}

export { SETTINGS_KEYS };
