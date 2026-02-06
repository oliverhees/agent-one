import * as SecureStore from "expo-secure-store";

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
} as const;

export const setSecure = async (key: string, value: string): Promise<void> => {
  try {
    await SecureStore.setItemAsync(key, value);
  } catch (error) {
    console.error("Error saving to SecureStore:", error);
    throw error;
  }
};

export const getSecure = async (key: string): Promise<string | null> => {
  try {
    return await SecureStore.getItemAsync(key);
  } catch (error) {
    console.error("Error reading from SecureStore:", error);
    return null;
  }
};

export const removeSecure = async (key: string): Promise<void> => {
  try {
    await SecureStore.deleteItemAsync(key);
  } catch (error) {
    console.error("Error deleting from SecureStore:", error);
    throw error;
  }
};

export const clearAllSecure = async (): Promise<void> => {
  try {
    await removeSecure(STORAGE_KEYS.ACCESS_TOKEN);
    await removeSecure(STORAGE_KEYS.REFRESH_TOKEN);
  } catch (error) {
    console.error("Error clearing SecureStore:", error);
    throw error;
  }
};
