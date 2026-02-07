import React from "react";
import { View, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../ui/Card";
import { DashboardDeadline } from "../../types/dashboard";

interface DeadlineWidgetProps {
  deadline: DashboardDeadline | null;
}

export const DeadlineWidget: React.FC<DeadlineWidgetProps> = ({
  deadline,
}) => {
  if (!deadline) return null;

  const dueDate = new Date(deadline.due_date);
  const now = new Date();
  const diffMs = dueDate.getTime() - now.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const isOverdue = diffMs < 0;

  let timeText: string;
  if (isOverdue) {
    timeText = "Ueberfaellig";
  } else if (diffHours < 1) {
    timeText = "In weniger als 1 Stunde";
  } else if (diffHours < 24) {
    timeText = `In ${diffHours} Stunde${diffHours !== 1 ? "n" : ""}`;
  } else {
    timeText = `In ${diffDays} Tag${diffDays !== 1 ? "en" : ""}`;
  }

  return (
    <Card
      className={
        isOverdue
          ? "bg-red-50 dark:bg-red-900/30"
          : "bg-orange-50 dark:bg-orange-900/30"
      }
    >
      <View className="flex-row items-center">
        <Ionicons
          name="alarm-outline"
          size={20}
          color={isOverdue ? "#ef4444" : "#f97316"}
          style={{ marginRight: 10 }}
        />
        <View className="flex-1">
          <Text className="text-xs text-gray-500 dark:text-gray-400">
            Naechste Deadline
          </Text>
          <Text
            className="text-sm font-semibold text-gray-900 dark:text-white"
            numberOfLines={1}
          >
            {deadline.task_title}
          </Text>
          <Text
            className={`text-xs font-medium ${
              isOverdue
                ? "text-red-600 dark:text-red-400"
                : "text-orange-600 dark:text-orange-400"
            }`}
          >
            {timeText}
          </Text>
        </View>
      </View>
    </Card>
  );
};
