import { Platform } from "react-native";
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import Constants from "expo-constants";
import api from "./api";

// Foreground notification handler — show alert + sound + badge
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

/**
 * Request push notification permissions, create Android channel,
 * get Expo push token, and register it with the backend.
 */
export async function registerForPushNotifications(): Promise<string | null> {
  if (!Device.isDevice) {
    console.warn("Push notifications require a physical device");
    return null;
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
    return null;
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

  // Get Expo push token
  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const tokenData = await Notifications.getExpoPushTokenAsync({
    ...(projectId ? { projectId } : {}),
  });

  return tokenData.data;
}

/**
 * Register the push token with the backend.
 */
async function registerTokenWithBackend(token: string): Promise<void> {
  try {
    await api.post("/settings/push-token", { expo_push_token: token });
    console.log("Push token registered with backend");
  } catch (error) {
    console.error("Failed to register push token:", error);
  }
}

/**
 * Initialize push notifications: get token and register with backend.
 */
export async function initializePushNotifications(): Promise<void> {
  const token = await registerForPushNotifications();
  if (token) {
    await registerTokenWithBackend(token);
  }
}
