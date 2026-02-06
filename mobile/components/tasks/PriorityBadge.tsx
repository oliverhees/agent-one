import React from "react";
import { View, Text } from "react-native";
import { TaskPriority } from "../../types/task";

interface PriorityBadgeProps {
  priority: TaskPriority;
}

const PRIORITY_CONFIG: Record<
  TaskPriority,
  { label: string; bgClass: string; textClass: string }
> = {
  low: {
    label: "Niedrig",
    bgClass: "bg-gray-200 dark:bg-gray-700",
    textClass: "text-gray-600 dark:text-gray-300",
  },
  medium: {
    label: "Mittel",
    bgClass: "bg-blue-100 dark:bg-blue-900",
    textClass: "text-blue-700 dark:text-blue-300",
  },
  high: {
    label: "Hoch",
    bgClass: "bg-orange-100 dark:bg-orange-900",
    textClass: "text-orange-700 dark:text-orange-300",
  },
  urgent: {
    label: "Dringend",
    bgClass: "bg-red-100 dark:bg-red-900",
    textClass: "text-red-700 dark:text-red-300",
  },
};

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
  const config = PRIORITY_CONFIG[priority];
  return (
    <View className={`px-2 py-0.5 rounded-full ${config.bgClass}`}>
      <Text className={`text-xs font-medium ${config.textClass}`}>
        {config.label}
      </Text>
    </View>
  );
};
