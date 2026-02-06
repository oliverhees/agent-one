import React from "react";
import { View, Text, ScrollView } from "react-native";
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
