import React from "react";
import { View, Text, ScrollView, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { useAuthStore } from "../../../stores/authStore";
import { router } from "expo-router";

export default function SettingsScreen() {
  const { user, logout, isLoading } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    router.replace("/(auth)/login");
  };

  return (
    <ScrollView className="flex-1 bg-gray-50 dark:bg-gray-900">
      <View className="p-6">
        <Card className="mb-4">
          <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Benutzerprofil
          </Text>
          <Text className="text-gray-600 dark:text-gray-400 mb-1">
            Name: {user?.display_name}
          </Text>
          <Text className="text-gray-600 dark:text-gray-400">
            E-Mail: {user?.email}
          </Text>
        </Card>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/personality")}
          accessibilityLabel="Persoenlichkeit anpassen"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="sparkles-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    Persoenlichkeit
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    ALICEs Verhalten anpassen
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/adhs")}
          accessibilityLabel="ADHS-Einstellungen"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="flash-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    ADHS-Einstellungen
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    Nudges, Timer und Gamification
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/achievements")}
          accessibilityLabel="Achievements anzeigen"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="trophy-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    Achievements
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    Abzeichen und Fortschritt
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/api-keys")}
          accessibilityLabel="API Keys verwalten"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="key-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    API Keys
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    Eigene API-Schluessel verwalten
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/voice-providers")}
          accessibilityLabel="Voice Provider konfigurieren"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="volume-medium-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    Voice Provider
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    Sprach-Provider konfigurieren
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <Card className="mb-4">
          <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            App-Version
          </Text>
          <Text className="text-gray-600 dark:text-gray-400">
            Version 1.0.0
          </Text>
        </Card>

        <Button
          title="Abmelden"
          variant="outline"
          onPress={handleLogout}
          isLoading={isLoading}
        />
      </View>
    </ScrollView>
  );
}
