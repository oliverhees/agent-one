import React from "react";
import { View, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface StreakDisplayProps {
  currentStreak: number;
  longestStreak?: number;
}

export const StreakDisplay: React.FC<StreakDisplayProps> = ({
  currentStreak,
  longestStreak,
}) => {
  const flameColor = currentStreak >= 7 ? "#f97316" : currentStreak >= 3 ? "#eab308" : "#9ca3af";

  return (
    <View className="flex-row items-center">
      <Ionicons name="flame" size={20} color={flameColor} />
      <Text className="text-base font-bold text-gray-900 dark:text-white ml-1">
        {currentStreak}
      </Text>
      <Text className="text-xs text-gray-500 dark:text-gray-400 ml-1">
        Tage
      </Text>
      {longestStreak !== undefined && longestStreak > currentStreak && (
        <Text className="text-xs text-gray-400 dark:text-gray-500 ml-2">
          (Rekord: {longestStreak})
        </Text>
      )}
    </View>
  );
};
