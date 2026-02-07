import "../global.css";
import { useEffect, useRef, useState } from "react";
import { Slot, SplashScreen, useRouter, useSegments } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as Notifications from "expo-notifications";
import { useAuthStore } from "../stores/authStore";
import { initializePushNotifications } from "../services/notificationService";
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
  const notificationListener = useRef<Notifications.EventSubscription>();
  const responseListener = useRef<Notifications.EventSubscription>();

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

    // Listener: Notification empfangen (Foreground)
    notificationListener.current =
      Notifications.addNotificationReceivedListener((notification) => {
        const { title, body, data } = notification.request.content;
        addNotification({
          id: notification.request.identifier,
          title: title || "ALICE",
          message: body || "",
          data: data as Record<string, unknown> | undefined,
        });
      });

    // Listener: User tippt auf Notification
    responseListener.current =
      Notifications.addNotificationResponseReceivedListener((response) => {
        const data = response.notification.request.content.data;
        if (data?.type === "deadline" || data?.type === "overdue") {
          router.push("/(tabs)/tasks" as any);
        } else if (data?.type === "streak") {
          router.push("/(tabs)/dashboard" as any);
        }
      });

    return () => {
      if (notificationListener.current) {
        Notifications.removeNotificationSubscription(
          notificationListener.current
        );
      }
      if (responseListener.current) {
        Notifications.removeNotificationSubscription(responseListener.current);
      }
    };
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
