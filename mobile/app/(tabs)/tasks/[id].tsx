import React from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
} from "react-native";
import { useLocalSearchParams, router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { PriorityBadge } from "../../../components/tasks/PriorityBadge";
import { TaskCard } from "../../../components/tasks/TaskCard";
import {
  useTask,
  useCompleteTask,
  useDeleteTask,
} from "../../../hooks/useTasks";

export default function TaskDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: task, isLoading, isError, error } = useTask(id);
  const completeTask = useCompleteTask();
  const deleteTask = useDeleteTask();

  const handleComplete = () => {
    if (!task) return;
    completeTask.mutate(task.id, {
      onSuccess: (response) => {
        Alert.alert(
          "Erledigt!",
          `+${response.xp_earned} XP verdient${
            response.level_up ? " - Level Up!" : ""
          }`,
          [{ text: "Super!", style: "default" }]
        );
      },
    });
  };

  const handleDelete = () => {
    if (!task) return;
    Alert.alert(
      "Aufgabe loeschen",
      "Bist du sicher? Diese Aktion kann nicht rueckgaengig gemacht werden.",
      [
        { text: "Abbrechen", style: "cancel" },
        {
          text: "Loeschen",
          style: "destructive",
          onPress: () => {
            deleteTask.mutate(task.id, {
              onSuccess: () => router.back(),
            });
          },
        },
      ]
    );
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  const statusLabel: Record<string, string> = {
    open: "Offen",
    in_progress: "In Arbeit",
    done: "Erledigt",
    cancelled: "Abgebrochen",
  };

  if (isLoading) {
    return <LoadingSpinner message="Aufgabe wird geladen..." />;
  }

  if (isError || !task) {
    return (
      <View className="flex-1 items-center justify-center bg-white dark:bg-gray-900 p-6">
        <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
        <Text className="text-red-500 text-center mt-4 text-base">
          Aufgabe nicht gefunden
        </Text>
        <Text className="text-gray-400 text-center mt-1 text-sm">
          {error?.message}
        </Text>
        <TouchableOpacity
          onPress={() => router.back()}
          className="mt-4 px-4 py-2 bg-primary-600 rounded-lg"
        >
          <Text className="text-white font-medium">Zurueck</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const isDone = task.status === "done" || task.status === "cancelled";

  return (
    <View className="flex-1 bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <View className="flex-row items-center justify-between px-4 pt-4 pb-2">
        <TouchableOpacity
          onPress={() => router.back()}
          className="p-2"
          accessibilityLabel="Zurueck"
        >
          <Ionicons name="arrow-back" size={24} color="#0284c7" />
        </TouchableOpacity>
        <View className="flex-row gap-2">
          <TouchableOpacity
            onPress={() =>
              router.push({
                pathname: "/(tabs)/tasks/create",
                params: { editId: task.id },
              })
            }
            className="p-2"
            accessibilityLabel="Bearbeiten"
          >
            <Ionicons name="create-outline" size={24} color="#0284c7" />
          </TouchableOpacity>
          <TouchableOpacity
            onPress={handleDelete}
            className="p-2"
            accessibilityLabel="Loeschen"
          >
            <Ionicons name="trash-outline" size={24} color="#ef4444" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView className="flex-1 px-4">
        {/* Title & Status */}
        <Card className="mb-3">
          <Text
            className={`text-xl font-bold mb-2 ${
              isDone
                ? "text-gray-400 dark:text-gray-500 line-through"
                : "text-gray-900 dark:text-white"
            }`}
          >
            {task.title}
          </Text>

          <View className="flex-row items-center gap-2 mb-3">
            <PriorityBadge priority={task.priority} />
            <View className="px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700">
              <Text className="text-xs font-medium text-gray-600 dark:text-gray-300">
                {statusLabel[task.status]}
              </Text>
            </View>
            {task.xp_earned > 0 && (
              <View className="px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900">
                <Text className="text-xs font-medium text-green-700 dark:text-green-300">
                  +{task.xp_earned} XP
                </Text>
              </View>
            )}
          </View>

          {task.description && (
            <Text className="text-gray-600 dark:text-gray-300 text-base leading-6">
              {task.description}
            </Text>
          )}
        </Card>

        {/* Details */}
        <Card className="mb-3">
          {task.due_date && (
            <View className="flex-row items-center mb-2">
              <Ionicons
                name="calendar-outline"
                size={16}
                color="#6b7280"
                style={{ marginRight: 8 }}
              />
              <Text className="text-gray-600 dark:text-gray-400 text-sm">
                Faellig: {formatDate(task.due_date)}
              </Text>
            </View>
          )}
          {task.estimated_minutes && (
            <View className="flex-row items-center mb-2">
              <Ionicons
                name="time-outline"
                size={16}
                color="#6b7280"
                style={{ marginRight: 8 }}
              />
              <Text className="text-gray-600 dark:text-gray-400 text-sm">
                Geschaetzt: {task.estimated_minutes} Minuten
              </Text>
            </View>
          )}
          {task.completed_at && (
            <View className="flex-row items-center mb-2">
              <Ionicons
                name="checkmark-circle-outline"
                size={16}
                color="#10b981"
                style={{ marginRight: 8 }}
              />
              <Text className="text-green-600 dark:text-green-400 text-sm">
                Erledigt: {formatDate(task.completed_at)}
              </Text>
            </View>
          )}
          <View className="flex-row items-center">
            <Ionicons
              name="time-outline"
              size={16}
              color="#6b7280"
              style={{ marginRight: 8 }}
            />
            <Text className="text-gray-400 dark:text-gray-500 text-xs">
              Erstellt: {formatDate(task.created_at)}
            </Text>
          </View>
        </Card>

        {/* Tags */}
        {task.tags.length > 0 && (
          <Card className="mb-3">
            <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tags
            </Text>
            <View className="flex-row flex-wrap gap-2">
              {task.tags.map((tag) => (
                <View
                  key={tag}
                  className="px-3 py-1 rounded-full bg-primary-100 dark:bg-primary-900"
                >
                  <Text className="text-primary-700 dark:text-primary-300 text-sm">
                    {tag}
                  </Text>
                </View>
              ))}
            </View>
          </Card>
        )}

        {/* Sub-Tasks */}
        {task.sub_tasks && task.sub_tasks.length > 0 && (
          <View className="mb-3">
            <Text className="text-base font-semibold text-gray-900 dark:text-white mb-2">
              Unteraufgaben ({task.sub_tasks.length})
            </Text>
            {task.sub_tasks.map((subTask) => (
              <TaskCard key={subTask.id} task={subTask} />
            ))}
          </View>
        )}

        {/* Complete Button */}
        {!isDone && (
          <View className="mb-8">
            <Button
              title="Als erledigt markieren"
              onPress={handleComplete}
              isLoading={completeTask.isPending}
            />
          </View>
        )}
      </ScrollView>
    </View>
  );
}
