import React from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { DashboardTask } from "../../types/dashboard";

interface TodayTaskItemProps {
  task: DashboardTask;
  onComplete: (id: string) => void;
  onPress: (id: string) => void;
}

const priorityColors: Record<string, string> = {
  urgent: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#6b7280",
};

export const TodayTaskItem: React.FC<TodayTaskItemProps> = ({
  task,
  onComplete,
  onPress,
}) => {
  const isDone = task.status === "done";

  return (
    <TouchableOpacity
      onPress={() => onPress(task.id)}
      className="flex-row items-center py-2.5"
      accessibilityLabel={`Aufgabe: ${task.title}`}
    >
      <TouchableOpacity
        onPress={() => !isDone && onComplete(task.id)}
        className="mr-3"
        disabled={isDone}
        accessibilityLabel={isDone ? "Erledigt" : "Als erledigt markieren"}
      >
        <Ionicons
          name={isDone ? "checkmark-circle" : "ellipse-outline"}
          size={22}
          color={isDone ? "#10b981" : "#9ca3af"}
        />
      </TouchableOpacity>

      <View className="flex-1">
        <Text
          className={`text-sm ${
            isDone
              ? "text-gray-400 dark:text-gray-500 line-through"
              : "text-gray-900 dark:text-white"
          }`}
          numberOfLines={1}
        >
          {task.title}
        </Text>
      </View>

      <View
        className="w-2 h-2 rounded-full ml-2"
        style={{ backgroundColor: priorityColors[task.priority] || "#6b7280" }}
      />
    </TouchableOpacity>
  );
};
