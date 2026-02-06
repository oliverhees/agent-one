import React from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { TaskForm } from "../../../components/tasks/TaskForm";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import {
  useCreateTask,
  useUpdateTask,
  useTask,
} from "../../../hooks/useTasks";
import { TaskCreate } from "../../../types/task";

export default function CreateTaskScreen() {
  const { editId } = useLocalSearchParams<{ editId?: string }>();
  const isEdit = !!editId;

  const { data: existingTask, isLoading: isLoadingTask } = useTask(
    editId ?? ""
  );
  const createTask = useCreateTask();
  const updateTask = useUpdateTask();

  const handleSubmit = (data: TaskCreate) => {
    if (isEdit && editId) {
      updateTask.mutate(
        { id: editId, data },
        { onSuccess: () => router.back() }
      );
    } else {
      createTask.mutate(data, { onSuccess: () => router.back() });
    }
  };

  if (isEdit && isLoadingTask) {
    return <LoadingSpinner message="Aufgabe wird geladen..." />;
  }

  return (
    <View className="flex-1 bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <View className="flex-row items-center px-4 pt-4 pb-2">
        <TouchableOpacity
          onPress={() => router.back()}
          className="p-2 mr-2"
          accessibilityLabel="Zurueck"
        >
          <Ionicons name="arrow-back" size={24} color="#0284c7" />
        </TouchableOpacity>
        <Text className="text-xl font-bold text-gray-900 dark:text-white">
          {isEdit ? "Aufgabe bearbeiten" : "Neue Aufgabe"}
        </Text>
      </View>

      <TaskForm
        initialData={isEdit ? existingTask ?? undefined : undefined}
        onSubmit={handleSubmit}
        isLoading={createTask.isPending || updateTask.isPending}
        submitLabel={isEdit ? "Aktualisieren" : "Erstellen"}
      />
    </View>
  );
}
