import { create } from "zustand";
import api from "../services/api";

interface OnboardingState {
  onboardingComplete: boolean | null; // null = not checked yet
  isLoading: boolean;
  checkOnboardingStatus: () => Promise<void>;
  markOnboardingComplete: () => void;
}

export const useOnboardingStore = create<OnboardingState>((set) => ({
  onboardingComplete: null,
  isLoading: false,

  checkOnboardingStatus: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get("/settings/adhs");
      const onboardingComplete = response.data.onboarding_complete ?? false;
      set({ onboardingComplete, isLoading: false });
    } catch (error) {
      console.error("Failed to check onboarding status:", error);
      // On error, assume onboarding is incomplete (safe default)
      set({ onboardingComplete: false, isLoading: false });
    }
  },

  markOnboardingComplete: () => {
    set({ onboardingComplete: true });
  },
}));
