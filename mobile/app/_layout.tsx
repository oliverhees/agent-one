import "../global.css";
import { useEffect } from "react";
import { Slot, SplashScreen, useRouter, useSegments } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "../stores/authStore";

// Query Client für TanStack Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 Minuten
    },
  },
});

// SplashScreen so lange anzeigen, bis Auth-State geladen ist
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const router = useRouter();
  const segments = useSegments();
  const { isAuthenticated, isLoading, loadStoredAuth } = useAuthStore();

  // Auth-State beim Start laden
  useEffect(() => {
    loadStoredAuth();
  }, []);

  // Navigation basierend auf Auth-Status
  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === "(auth)";

    if (!isAuthenticated && !inAuthGroup) {
      // Nicht authentifiziert → zur Login-Seite
      router.replace("/(auth)/login");
    } else if (isAuthenticated && inAuthGroup) {
      // Authentifiziert → zu den Tabs
      router.replace("/(tabs)/chat");
    }

    // SplashScreen verstecken
    SplashScreen.hideAsync();
  }, [isAuthenticated, isLoading, segments]);

  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <StatusBar style="auto" />
        <Slot />
      </SafeAreaProvider>
    </QueryClientProvider>
  );
}
