import { useAuthStore } from "../stores/authStore";

/**
 * Custom Hook für Auth-Zugriff
 * Kann später erweitert werden mit zusätzlicher Logik
 */
export const useAuth = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
  } = useAuthStore();

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
  };
};
