import { create } from "zustand";
import AsyncStorage from "@react-native-async-storage/async-storage";

interface WakeWordState {
  enabled: boolean;
  sensitivity: number;
  continuousMode: boolean;
  isListening: boolean;
  modelLoaded: boolean;
  setEnabled: (enabled: boolean) => void;
  setSensitivity: (sensitivity: number) => void;
  setContinuousMode: (continuousMode: boolean) => void;
  setIsListening: (isListening: boolean) => void;
  setModelLoaded: (loaded: boolean) => void;
  loadSettings: () => Promise<void>;
}

const STORAGE_KEY = "alice_wake_word_settings";

export const useWakeWordStore = create<WakeWordState>((set, get) => ({
  enabled: false,
  sensitivity: 0.5,
  continuousMode: true,
  isListening: false,
  modelLoaded: false,

  setEnabled: (enabled) => {
    set({ enabled });
    persistSettings(get());
  },
  setSensitivity: (sensitivity) => {
    set({ sensitivity });
    persistSettings(get());
  },
  setContinuousMode: (continuousMode) => {
    set({ continuousMode });
    persistSettings(get());
  },
  setIsListening: (isListening) => set({ isListening }),
  setModelLoaded: (loaded) => set({ modelLoaded: loaded }),
  loadSettings: async () => {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        set({
          enabled: parsed.enabled ?? false,
          sensitivity: parsed.sensitivity ?? 0.5,
          continuousMode: parsed.continuousMode ?? true,
        });
      }
    } catch (e) {
      console.error("Failed to load wake word settings:", e);
    }
  },
}));

function persistSettings(state: WakeWordState) {
  AsyncStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      enabled: state.enabled,
      sensitivity: state.sensitivity,
      continuousMode: state.continuousMode,
    })
  ).catch(console.error);
}
