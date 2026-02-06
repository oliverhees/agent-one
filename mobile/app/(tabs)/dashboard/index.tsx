import React from "react";
import { View, Text } from "react-native";

export default function DashboardScreen() {
  return (
    <View className="flex-1 items-center justify-center bg-white dark:bg-gray-900">
      <Text className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        Dashboard
      </Text>
      <Text className="text-gray-500 dark:text-gray-400 text-lg">
        Kommt in Phase 1
      </Text>
    </View>
  );
}
