import { create } from "zustand";
import { User } from "../types/auth";
import * as authService from "../services/auth";
import {
  getSecure,
  setSecure,
  clearAllSecure,
  STORAGE_KEYS,
} from "../utils/storage";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    displayName: string
  ) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  loadStoredAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authService.login({ email, password });

      await setSecure(STORAGE_KEYS.ACCESS_TOKEN, response.access_token);
      await setSecure(STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token);

      set({
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        "Anmeldung fehlgeschlagen. Bitte überprüfen Sie Ihre Eingaben.";
      set({
        error: errorMessage,
        isLoading: false,
        isAuthenticated: false,
      });
      throw error;
    }
  },

  register: async (email: string, password: string, displayName: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authService.register({
        email,
        password,
        display_name: displayName,
      });

      await setSecure(STORAGE_KEYS.ACCESS_TOKEN, response.access_token);
      await setSecure(STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token);

      set({
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        "Registrierung fehlgeschlagen. Bitte versuchen Sie es erneut.";
      set({
        error: errorMessage,
        isLoading: false,
        isAuthenticated: false,
      });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await authService.logout();
      await clearAllSecure();

      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      console.error("Logout error:", error);
      // Auch bei Fehler Tokens löschen
      await clearAllSecure();
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  refreshAccessToken: async () => {
    const refreshToken = get().refreshToken;
    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await authService.refreshToken(refreshToken);

      await setSecure(STORAGE_KEYS.ACCESS_TOKEN, response.access_token);
      await setSecure(STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token);

      set({
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      });
    } catch (error) {
      // Refresh fehlgeschlagen → Logout
      await get().logout();
      throw error;
    }
  },

  loadStoredAuth: async () => {
    set({ isLoading: true });
    try {
      const accessToken = await getSecure(STORAGE_KEYS.ACCESS_TOKEN);
      const refreshToken = await getSecure(STORAGE_KEYS.REFRESH_TOKEN);

      if (accessToken && refreshToken) {
        // Versuche User-Daten zu laden
        try {
          const user = await authService.getMe();
          set({
            user,
            accessToken,
            refreshToken,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Token ungültig → Clear
          await clearAllSecure();
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      console.error("Error loading stored auth:", error);
      set({ isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
