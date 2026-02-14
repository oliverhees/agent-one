import { create } from "zustand";
import { modulesApi, ModuleInfo } from "../services/modules";

interface ModuleStore {
  activeModules: string[];
  availableModules: ModuleInfo[];
  isLoading: boolean;
  error: string | null;

  isModuleActive: (name: string) => boolean;
  fetchModules: () => Promise<void>;
  updateModules: (activeModules: string[]) => Promise<void>;
  updateModuleConfig: (
    moduleName: string,
    config: Record<string, unknown>
  ) => Promise<void>;
}

export const useModuleStore = create<ModuleStore>((set, get) => ({
  activeModules: ["core", "adhs"],
  availableModules: [],
  isLoading: false,
  error: null,

  isModuleActive: (name: string) => get().activeModules.includes(name),

  fetchModules: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await modulesApi.getModules();
      set({
        activeModules: data.active_modules,
        availableModules: data.available_modules,
        isLoading: false,
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  updateModules: async (activeModules: string[]) => {
    set({ isLoading: true, error: null });
    try {
      const data = await modulesApi.updateModules(activeModules);
      set({
        activeModules: data.active_modules,
        availableModules: data.available_modules,
        isLoading: false,
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  updateModuleConfig: async (
    moduleName: string,
    config: Record<string, unknown>
  ) => {
    try {
      const updated = await modulesApi.updateModuleConfig(moduleName, config);
      set((state) => ({
        availableModules: state.availableModules.map((m) =>
          m.name === moduleName ? updated : m
        ),
      }));
    } catch (err: any) {
      set({ error: err.message });
    }
  },
}));
