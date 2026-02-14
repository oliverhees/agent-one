import api from "./api";

export interface ModuleInfo {
  name: string;
  label: string;
  icon: string;
  description: string;
  active: boolean;
  config: Record<string, unknown>;
}

export interface ModulesResponse {
  active_modules: string[];
  available_modules: ModuleInfo[];
}

export const modulesApi = {
  getModules: async (): Promise<ModulesResponse> => {
    const response = await api.get<ModulesResponse>("/settings/modules");
    return response.data;
  },

  updateModules: async (activeModules: string[]): Promise<ModulesResponse> => {
    const response = await api.put<ModulesResponse>("/settings/modules", {
      active_modules: activeModules,
    });
    return response.data;
  },

  updateModuleConfig: async (
    moduleName: string,
    config: Record<string, unknown>
  ): Promise<ModuleInfo> => {
    const response = await api.put<ModuleInfo>(
      `/settings/modules/${moduleName}/config`,
      { config }
    );
    return response.data;
  },
};
