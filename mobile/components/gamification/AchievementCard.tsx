import React from "react";
import { View, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Achievement } from "../../types/gamification";

interface AchievementCardProps {
  achievement: Achievement;
}

const iconMap: Record<string, keyof typeof Ionicons.glyphMap> = {
  rocket: "rocket-outline",
  fire: "flame-outline",
  trophy: "trophy-outline",
  brain: "bulb-outline",
  star: "star-outline",
  heart: "heart-outline",
  shield: "shield-outline",
  medal: "medal-outline",
};

export const AchievementCard: React.FC<AchievementCardProps> = ({
  achievement,
}) => {
  const iconName = iconMap[achievement.icon] || "ribbon-outline";
  const isUnlocked = achievement.unlocked;

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
    });

  return (
    <View
      className={`items-center p-3 rounded-xl ${
        isUnlocked
          ? "bg-primary-50 dark:bg-primary-900/30"
          : "bg-gray-100 dark:bg-gray-800"
      }`}
    >
      <View
        className={`w-12 h-12 rounded-full items-center justify-center mb-2 ${
          isUnlocked
            ? "bg-primary-100 dark:bg-primary-800"
            : "bg-gray-200 dark:bg-gray-700"
        }`}
      >
        {isUnlocked ? (
          <Ionicons name={iconName} size={24} color="#0284c7" />
        ) : (
          <Ionicons name="lock-closed" size={24} color="#9ca3af" />
        )}
      </View>

      <Text
        className={`text-xs font-semibold text-center ${
          isUnlocked
            ? "text-gray-900 dark:text-white"
            : "text-gray-400 dark:text-gray-500"
        }`}
        numberOfLines={2}
      >
        {achievement.name}
      </Text>

      <Text
        className="text-[10px] text-gray-500 dark:text-gray-400 text-center mt-0.5"
        numberOfLines={2}
      >
        {achievement.description}
      </Text>

      <Text
        className={`text-[10px] mt-1 font-medium ${
          isUnlocked
            ? "text-primary-600 dark:text-primary-400"
            : "text-gray-400 dark:text-gray-500"
        }`}
      >
        +{achievement.xp_reward} XP
      </Text>

      {isUnlocked && achievement.unlocked_at && (
        <Text className="text-[9px] text-gray-400 dark:text-gray-500 mt-0.5">
          {formatDate(achievement.unlocked_at)}
        </Text>
      )}
    </View>
  );
};
