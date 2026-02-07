import { Platform } from "react-native";
import Constants from "expo-constants";
import api from "./api";

/**
 * Check if we're running in Expo Go (where remote push is unsupported since SDK 53).
 */
function isExpoGo(): boolean {
  return Constants.appOwnership === "expo";
}

/**
 * Initialize push notifications: get token and register with backend.
 * Silently skips in Expo Go where remote push isn't supported.
 */
export async function initializePushNotifications(): Promise<void> {
  if (isExpoGo()) {
    console.log(
      "Push notifications skipped — not supported in Expo Go. Use a development build."
    );
    return;
  }

  try {
    const Notifications = await import("expo-notifications");
    const Device = await import("expo-device");

    // Foreground notification handler
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });

    if (!Device.isDevice) {
      console.warn("Push notifications require a physical device");
      return;
    }

    // Request permissions
    const { status: existingStatus } =
      await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== "granted") {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== "granted") {
      console.warn("Push notification permission not granted");
      return;
    }

    // Create Android notification channel
    if (Platform.OS === "android") {
      await Notifications.setNotificationChannelAsync("alice-notifications", {
        name: "ALICE Benachrichtigungen",
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: "#0284c7",
        sound: "default",
      });
    }

    // Get Expo push token — requires projectId in dev builds
    const projectId =
      Constants.expoConfig?.extra?.eas?.projectId ??
      Constants.easConfig?.projectId;

    if (!projectId) {
      console.warn(
        "No EAS projectId found — push token registration skipped. " +
          "Run 'eas init' or set extra.eas.projectId in app.json."
      );
      return;
    }

    const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
    const token = tokenData.data;

    // Register with backend
    try {
      await api.post("/settings/push-token", { expo_push_token: token });
      console.log("Push token registered with backend");
    } catch (error) {
      console.error("Failed to register push token:", error);
    }
  } catch (error) {
    console.warn("Push notification setup failed:", error);
  }
}

/**
 * Set up notification listeners (foreground receive + tap response).
 * Returns a cleanup function. Silently no-ops in Expo Go.
 */
export function setupNotificationListeners(callbacks: {
  onReceived: (notification: any) => void;
  onResponse: (response: any) => void;
}): () => void {
  if (isExpoGo()) {
    return () => {};
  }

  let receivedSub: { remove: () => void } | undefined;
  let responseSub: { remove: () => void } | undefined;

  (async () => {
    try {
      const Notifications = await import("expo-notifications");

      receivedSub = Notifications.addNotificationReceivedListener(
        callbacks.onReceived
      );
      responseSub = Notifications.addNotificationResponseReceivedListener(
        callbacks.onResponse
      );
    } catch (error) {
      console.warn("Failed to set up notification listeners:", error);
    }
  })();

  return () => {
    receivedSub?.remove();
    responseSub?.remove();
  };
}
