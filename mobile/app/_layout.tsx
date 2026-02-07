import "../global.css";
import { useEffect, useState } from "react";
import { Slot, SplashScreen, useRouter, useSegments } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "../stores/authStore";
import {
  initializePushNotifications,
  setupNotificationListeners,
} from "../services/notificationService";
import { useNotificationStore } from "../stores/notificationStore";

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
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [mounted, setMounted] = useState(false);

  // Auth-State beim Start laden
  useEffect(() => {
    loadStoredAuth();
  }, []);

  // Warten bis Layout gemountet ist
  useEffect(() => {
    setMounted(true);
  }, []);

  // Push Notifications initialisieren wenn authentifiziert
  useEffect(() => {
    if (!isAuthenticated) return;

    initializePushNotifications();

    const cleanup = setupNotificationListeners({
      onReceived: (notification: any) => {
        const { title, body, data } = notification.request.content;
        addNotification({
          id: notification.request.identifier,
          title: title || "ALICE",
          message: body || "",
          data: data as Record<string, unknown> | undefined,
        });
      },
      onResponse: (response: any) => {
        const data = response.notification.request.content.data;
        if (data?.type === "deadline" || data?.type === "overdue") {
          router.push("/(tabs)/tasks" as any);
        } else if (data?.type === "streak") {
          router.push("/(tabs)/dashboard" as any);
        }
      },
    });

    return cleanup;
  }, [isAuthenticated]);

  // Navigation basierend auf Auth-Status
  useEffect(() => {
    if (!mounted || isLoading) return;

    const inAuthGroup = segments[0] === "(auth)";

    if (!isAuthenticated && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (isAuthenticated && inAuthGroup) {
      router.replace("/(tabs)/chat");
    }

    SplashScreen.hideAsync();
  }, [mounted, isAuthenticated, isLoading, segments]);

  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <StatusBar style="auto" />
        <Slot />
      </SafeAreaProvider>
    </QueryClientProvider>
  );
}
