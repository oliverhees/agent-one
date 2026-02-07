import React from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Nudge, NudgeLevel } from "../../types/nudge";

interface NudgeBannerProps {
  nudge: Nudge;
  onAcknowledge: (id: string) => void;
  onPress?: (nudge: Nudge) => void;
}

const levelStyles: Record<
  NudgeLevel,
  { bg: string; border: string; icon: string; iconColor: string }
> = {
  gentle: {
    bg: "bg-blue-50 dark:bg-blue-900/30",
    border: "border-blue-200 dark:border-blue-800",
    icon: "information-circle-outline",
    iconColor: "#3b82f6",
  },
  moderate: {
    bg: "bg-orange-50 dark:bg-orange-900/30",
    border: "border-orange-200 dark:border-orange-800",
    icon: "notifications-outline",
    iconColor: "#f97316",
  },
  firm: {
    bg: "bg-red-50 dark:bg-red-900/30",
    border: "border-red-200 dark:border-red-800",
    icon: "alert-circle-outline",
    iconColor: "#ef4444",
  },
};

export const NudgeBanner: React.FC<NudgeBannerProps> = ({
  nudge,
  onAcknowledge,
  onPress,
}) => {
  const style = levelStyles[nudge.nudge_level];

  return (
    <TouchableOpacity
      onPress={() => onPress?.(nudge)}
      activeOpacity={onPress ? 0.7 : 1}
      className={`${style.bg} border ${style.border} rounded-lg p-3 mb-2`}
    >
      <View className="flex-row items-start">
        <Ionicons
          name={style.icon as any}
          size={20}
          color={style.iconColor}
          style={{ marginRight: 10, marginTop: 1 }}
        />
        <View className="flex-1">
          {nudge.task_title && (
            <Text className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-0.5">
              {nudge.task_title}
            </Text>
          )}
          <Text className="text-sm text-gray-800 dark:text-gray-200 leading-5">
            {nudge.message}
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => onAcknowledge(nudge.id)}
          className="ml-2 p-1"
          accessibilityLabel="Gelesen"
        >
          <Ionicons name="close" size={18} color="#9ca3af" />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
};
