import React from "react";
import { View, Text, TouchableOpacity, Pressable } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Card } from "../ui/Card";
import { PriorityBadge } from "./PriorityBadge";
import { Task } from "../../types/task";

interface TaskCardProps {
  task: Task;
  onComplete?: (id: string) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task, onComplete }) => {
  const isDone = task.status === "done" || task.status === "cancelled";

  const formatDueDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) return "Heute";
    if (date.toDateString() === tomorrow.toDateString()) return "Morgen";
    return date.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
  };

  const isOverdue =
    task.due_date && !isDone && new Date(task.due_date) < new Date();

  return (
    <Pressable
      onPress={() => router.push(`/(tabs)/tasks/${task.id}`)}
      className="mb-3"
    >
      <Card className="flex-row items-center">
        <TouchableOpacity
          onPress={() => !isDone && onComplete?.(task.id)}
          className="mr-3"
          disabled={isDone}
          accessibilityLabel={isDone ? "Erledigt" : "Als erledigt markieren"}
        >
          <Ionicons
            name={isDone ? "checkmark-circle" : "ellipse-outline"}
            size={24}
            color={isDone ? "#10b981" : "#9ca3af"}
          />
        </TouchableOpacity>

        <View className="flex-1">
          <Text
            className={`text-base font-medium ${
              isDone
                ? "text-gray-400 dark:text-gray-500 line-through"
                : "text-gray-900 dark:text-white"
            }`}
            numberOfLines={1}
          >
            {task.title}
          </Text>

          <View className="flex-row items-center mt-1 gap-2">
            <PriorityBadge priority={task.priority} />
            {task.due_date && (
              <Text
                className={`text-xs ${
                  isOverdue
                    ? "text-red-500 font-semibold"
                    : "text-gray-500 dark:text-gray-400"
                }`}
              >
                {formatDueDate(task.due_date)}
              </Text>
            )}
            {task.tags.length > 0 && (
              <Text
                className="text-xs text-gray-400 dark:text-gray-500"
                numberOfLines={1}
              >
                {task.tags.slice(0, 2).join(", ")}
              </Text>
            )}
          </View>
        </View>

        <Ionicons name="chevron-forward" size={16} color="#9ca3af" />
      </Card>
    </Pressable>
  );
};
