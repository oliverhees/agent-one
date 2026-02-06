import React from "react";
import { View, ActivityIndicator, Text } from "react-native";

interface LoadingSpinnerProps {
  message?: string;
  size?: "small" | "large";
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message,
  size = "large",
}) => {
  return (
    <View className="flex-1 items-center justify-center bg-white dark:bg-gray-900">
      <ActivityIndicator size={size} color="#0284c7" />
      {message && (
        <Text className="text-gray-600 dark:text-gray-400 mt-4">{message}</Text>
      )}
    </View>
  );
};
