import api from "./api";
import { ADHSSettings, ADHSSettingsUpdate } from "../types/settings";

export const settingsApi = {
  getADHSSettings: async (): Promise<ADHSSettings> => {
    const response = await api.get<ADHSSettings>("/settings/adhs");
    return response.data;
  },

  updateADHSSettings: async (
    data: ADHSSettingsUpdate
  ): Promise<ADHSSettings> => {
    const response = await api.put<ADHSSettings>(
      "/settings/adhs",
      data
    );
    return response.data;
  },
};
