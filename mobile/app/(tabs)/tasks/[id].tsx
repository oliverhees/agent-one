import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  Modal,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
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
import {
  useTaskBreakdown,
  useConfirmBreakdown,
} from "../../../hooks/useBreakdown";
import { SuggestedSubtask } from "../../../types/breakdown";

export default function TaskDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: task, isLoading, isError, error } = useTask(id);
  const completeTask = useCompleteTask();
  const deleteTask = useDeleteTask();
  const taskBreakdown = useTaskBreakdown();
  const confirmBreakdown = useConfirmBreakdown();

  const [breakdownModalVisible, setBreakdownModalVisible] = useState(false);
  const [editableSubtasks, setEditableSubtasks] = useState<
    SuggestedSubtask[]
  >([]);

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

  const handleBreakdown = () => {
    if (!task) return;
    taskBreakdown.mutate(task.id, {
      onSuccess: (response) => {
        setEditableSubtasks(response.suggested_subtasks);
        setBreakdownModalVisible(true);
      },
      onError: (err: any) => {
        const message =
          err.response?.data?.detail || "Aufteilen fehlgeschlagen.";
        Alert.alert("Fehler", message);
      },
    });
  };

  const handleConfirmBreakdown = () => {
    if (!task) return;
    confirmBreakdown.mutate(
      {
        taskId: task.id,
        data: {
          subtasks: editableSubtasks.map((s) => ({
            title: s.title,
            description: s.description,
            estimated_minutes: s.estimated_minutes,
          })),
        },
      },
      {
        onSuccess: () => {
          setBreakdownModalVisible(false);
          setEditableSubtasks([]);
          Alert.alert(
            "Aufgeteilt",
            "Die Unteraufgaben wurden erfolgreich erstellt."
          );
        },
        onError: (err: any) => {
          const message =
            err.response?.data?.detail || "Bestaetigung fehlgeschlagen.";
          Alert.alert("Fehler", message);
        },
      }
    );
  };

  const updateSubtaskTitle = (index: number, title: string) => {
    setEditableSubtasks((prev) =>
      prev.map((s, i) => (i === index ? { ...s, title } : s))
    );
  };

  const updateSubtaskDescription = (index: number, description: string) => {
    setEditableSubtasks((prev) =>
      prev.map((s, i) => (i === index ? { ...s, description } : s))
    );
  };

  const removeSubtask = (index: number) => {
    setEditableSubtasks((prev) => prev.filter((_, i) => i !== index));
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
  const hasSubTasks = task.sub_tasks && task.sub_tasks.length > 0;
  const canBreakdown = !isDone && !hasSubTasks && !task.parent_id;

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

        {/* Breakdown Button */}
        {canBreakdown && (
          <View className="mb-3">
            <Button
              title={
                taskBreakdown.isPending
                  ? "Wird analysiert..."
                  : "Aufgabe aufteilen"
              }
              variant="outline"
              onPress={handleBreakdown}
              isLoading={taskBreakdown.isPending}
            />
          </View>
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

      {/* Breakdown Modal */}
      <Modal
        visible={breakdownModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setBreakdownModalVisible(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : undefined}
          className="flex-1 bg-white dark:bg-gray-900"
        >
          {/* Modal Header */}
          <View className="flex-row items-center justify-between px-4 pt-4 pb-3 border-b border-gray-200 dark:border-gray-700">
            <TouchableOpacity
              onPress={() => setBreakdownModalVisible(false)}
              className="p-2"
              accessibilityLabel="Abbrechen"
            >
              <Text className="text-base text-gray-500">Abbrechen</Text>
            </TouchableOpacity>
            <Text className="text-lg font-semibold text-gray-900 dark:text-white">
              Aufgabe aufteilen
            </Text>
            <TouchableOpacity
              onPress={handleConfirmBreakdown}
              disabled={
                editableSubtasks.length === 0 || confirmBreakdown.isPending
              }
              className="p-2"
              accessibilityLabel="Bestaetigen"
            >
              {confirmBreakdown.isPending ? (
                <ActivityIndicator size="small" color="#0284c7" />
              ) : (
                <Text
                  className={`text-base font-semibold ${
                    editableSubtasks.length === 0
                      ? "text-gray-300"
                      : "text-primary-600"
                  }`}
                >
                  Erstellen
                </Text>
              )}
            </TouchableOpacity>
          </View>

          {/* Modal Content */}
          <ScrollView className="flex-1 px-4 pt-4">
            <Text className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              ALICE schlaegt folgende Unteraufgaben vor. Du kannst sie
              bearbeiten oder entfernen.
            </Text>

            {editableSubtasks.map((subtask, index) => (
              <Card key={`subtask-${index}`} className="mb-3">
                <View className="flex-row items-start justify-between mb-2">
                  <View className="w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900 items-center justify-center mr-2">
                    <Text className="text-xs font-bold text-primary-700 dark:text-primary-300">
                      {index + 1}
                    </Text>
                  </View>
                  <View className="flex-1">
                    <TextInput
                      value={subtask.title}
                      onChangeText={(text) =>
                        updateSubtaskTitle(index, text)
                      }
                      className="text-base font-medium text-gray-900 dark:text-white bg-transparent border-b border-gray-200 dark:border-gray-700 pb-1 mb-2"
                      placeholderTextColor="#9ca3af"
                    />
                    <TextInput
                      value={subtask.description}
                      onChangeText={(text) =>
                        updateSubtaskDescription(index, text)
                      }
                      className="text-sm text-gray-600 dark:text-gray-400 bg-transparent"
                      multiline
                      numberOfLines={2}
                      placeholderTextColor="#9ca3af"
                    />
                    {subtask.estimated_minutes > 0 && (
                      <Text className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        ~{subtask.estimated_minutes} Min.
                      </Text>
                    )}
                  </View>
                  <TouchableOpacity
                    onPress={() => removeSubtask(index)}
                    className="ml-2 p-1"
                    accessibilityLabel="Unteraufgabe entfernen"
                  >
                    <Ionicons name="close-circle" size={20} color="#ef4444" />
                  </TouchableOpacity>
                </View>
              </Card>
            ))}

            {editableSubtasks.length === 0 && (
              <View className="items-center py-8">
                <Ionicons
                  name="document-text-outline"
                  size={48}
                  color="#9ca3af"
                />
                <Text className="text-gray-400 text-center mt-2">
                  Alle Unteraufgaben entfernt
                </Text>
              </View>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}
