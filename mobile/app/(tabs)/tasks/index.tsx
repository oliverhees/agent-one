import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { TaskCard } from "../../../components/tasks/TaskCard";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { useTaskList, useCompleteTask } from "../../../hooks/useTasks";
import { TaskPriority, TaskStatus, Task } from "../../../types/task";

type FilterStatus = TaskStatus | "all";
type FilterPriority = TaskPriority | "all";

const STATUS_FILTERS: { value: FilterStatus; label: string }[] = [
  { value: "all", label: "Alle" },
  { value: "open", label: "Offen" },
  { value: "in_progress", label: "In Arbeit" },
  { value: "done", label: "Erledigt" },
];

const PRIORITY_FILTERS: { value: FilterPriority; label: string }[] = [
  { value: "all", label: "Alle" },
  { value: "urgent", label: "Dringend" },
  { value: "high", label: "Hoch" },
  { value: "medium", label: "Mittel" },
  { value: "low", label: "Niedrig" },
];

export default function TasksScreen() {
  const [statusFilter, setStatusFilter] = useState<FilterStatus>("all");
  const [priorityFilter, setPriorityFilter] = useState<FilterPriority>("all");

  const params = {
    ...(statusFilter !== "all" && { status: statusFilter as TaskStatus }),
    ...(priorityFilter !== "all" && { priority: priorityFilter as TaskPriority }),
  };

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useTaskList(params);

  const completeTask = useCompleteTask();

  const tasks: Task[] =
    data?.pages.flatMap((page) => page.items) ?? [];

  const handleComplete = useCallback(
    (id: string) => {
      completeTask.mutate(id);
    },
    [completeTask]
  );

  const handleEndReached = () => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Aufgaben werden geladen..." />;
  }

  if (isError) {
    return (
      <View className="flex-1 items-center justify-center bg-white dark:bg-gray-900 p-6">
        <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
        <Text className="text-red-500 text-center mt-4 text-base">
          Fehler beim Laden der Aufgaben
        </Text>
        <Text className="text-gray-400 text-center mt-1 text-sm">
          {error?.message}
        </Text>
        <TouchableOpacity
          onPress={() => refetch()}
          className="mt-4 px-4 py-2 bg-primary-600 rounded-lg"
        >
          <Text className="text-white font-medium">Erneut versuchen</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View className="flex-1 bg-gray-50 dark:bg-gray-900">
      {/* Filter Bar */}
      <View className="px-4 pt-4 pb-2">
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={STATUS_FILTERS}
          keyExtractor={(item) => item.value}
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => setStatusFilter(item.value)}
              className={`mr-2 px-3 py-1.5 rounded-full ${
                statusFilter === item.value
                  ? "bg-primary-600"
                  : "bg-gray-200 dark:bg-gray-700"
              }`}
              accessibilityLabel={`Filter: ${item.label}`}
            >
              <Text
                className={`text-sm font-medium ${
                  statusFilter === item.value
                    ? "text-white"
                    : "text-gray-600 dark:text-gray-300"
                }`}
              >
                {item.label}
              </Text>
            </TouchableOpacity>
          )}
        />
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={PRIORITY_FILTERS}
          keyExtractor={(item) => item.value}
          className="mt-2"
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => setPriorityFilter(item.value)}
              className={`mr-2 px-3 py-1.5 rounded-full ${
                priorityFilter === item.value
                  ? "bg-primary-600"
                  : "bg-gray-200 dark:bg-gray-700"
              }`}
              accessibilityLabel={`Prioritaet: ${item.label}`}
            >
              <Text
                className={`text-sm font-medium ${
                  priorityFilter === item.value
                    ? "text-white"
                    : "text-gray-600 dark:text-gray-300"
                }`}
              >
                {item.label}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* Task List */}
      {tasks.length === 0 ? (
        <View className="flex-1 items-center justify-center px-6">
          <Ionicons name="checkbox-outline" size={64} color="#9ca3af" />
          <Text className="text-gray-500 dark:text-gray-400 text-lg mt-4 text-center">
            Keine Aufgaben gefunden
          </Text>
          <Text className="text-gray-400 dark:text-gray-500 text-sm mt-1 text-center">
            Erstelle eine neue Aufgabe mit dem + Button
          </Text>
        </View>
      ) : (
        <FlatList
          data={tasks}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TaskCard task={item} onComplete={handleComplete} />
          )}
          contentContainerClassName="px-4 pt-2 pb-24"
          refreshControl={
            <RefreshControl
              refreshing={false}
              onRefresh={() => refetch()}
              tintColor="#0284c7"
            />
          }
          onEndReached={handleEndReached}
          onEndReachedThreshold={0.5}
        />
      )}

      {/* FAB */}
      <TouchableOpacity
        onPress={() => router.push("/(tabs)/tasks/create")}
        className="absolute bottom-6 right-6 w-14 h-14 rounded-full bg-primary-600 items-center justify-center shadow-lg"
        accessibilityLabel="Neue Aufgabe erstellen"
      >
        <Ionicons name="add" size={28} color="#ffffff" />
      </TouchableOpacity>
    </View>
  );
}
