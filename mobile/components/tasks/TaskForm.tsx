import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Platform,
} from "react-native";
import { useForm, Controller } from "react-hook-form";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { PriorityBadge } from "./PriorityBadge";
import { TaskCreate, TaskPriority, Task } from "../../types/task";

interface TaskFormProps {
  initialData?: Partial<Task>;
  onSubmit: (data: TaskCreate) => void;
  isLoading: boolean;
  submitLabel?: string;
}

const PRIORITIES: TaskPriority[] = ["low", "medium", "high", "urgent"];

export const TaskForm: React.FC<TaskFormProps> = ({
  initialData,
  onSubmit,
  isLoading,
  submitLabel = "Speichern",
}) => {
  const [tagInput, setTagInput] = useState("");

  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<TaskCreate>({
    defaultValues: {
      title: initialData?.title ?? "",
      description: initialData?.description ?? undefined,
      priority: initialData?.priority ?? "medium",
      due_date: initialData?.due_date ?? undefined,
      tags: initialData?.tags ?? [],
      estimated_minutes: initialData?.estimated_minutes ?? undefined,
    },
  });

  const selectedPriority = watch("priority");
  const tags = watch("tags") ?? [];

  const addTag = () => {
    const trimmed = tagInput.trim();
    if (trimmed && !tags.includes(trimmed) && tags.length < 20) {
      setValue("tags", [...tags, trimmed]);
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    setValue(
      "tags",
      tags.filter((t) => t !== tag)
    );
  };

  return (
    <ScrollView className="flex-1 bg-gray-50 dark:bg-gray-900">
      <View className="p-4">
        <Controller
          control={control}
          name="title"
          rules={{ required: "Titel ist erforderlich" }}
          render={({ field: { onChange, value } }) => (
            <Input
              label="Titel *"
              placeholder="Was ist zu tun?"
              value={value}
              onChangeText={onChange}
              error={errors.title?.message}
              accessibilityLabel="Task-Titel"
            />
          )}
        />

        <Controller
          control={control}
          name="description"
          render={({ field: { onChange, value } }) => (
            <Input
              label="Beschreibung"
              placeholder="Weitere Details..."
              value={value ?? ""}
              onChangeText={onChange}
              multiline
              numberOfLines={3}
              className="min-h-[80px] text-top"
              accessibilityLabel="Task-Beschreibung"
            />
          )}
        />

        <Text className="text-gray-700 dark:text-gray-300 font-medium mb-2">
          Prioritaet
        </Text>
        <View className="flex-row gap-2 mb-4">
          {PRIORITIES.map((p) => (
            <TouchableOpacity
              key={p}
              onPress={() => setValue("priority", p)}
              className={`rounded-lg px-3 py-2 border ${
                selectedPriority === p
                  ? "border-primary-600"
                  : "border-gray-300 dark:border-gray-700"
              }`}
              accessibilityLabel={`Prioritaet ${p}`}
            >
              <PriorityBadge priority={p} />
            </TouchableOpacity>
          ))}
        </View>

        <Controller
          control={control}
          name="due_date"
          render={({ field: { onChange, value } }) => (
            <Input
              label="Faelligkeitsdatum"
              placeholder="JJJJ-MM-TT (z.B. 2026-02-10)"
              value={value ?? ""}
              onChangeText={onChange}
              accessibilityLabel="Faelligkeitsdatum"
            />
          )}
        />

        <Controller
          control={control}
          name="estimated_minutes"
          render={({ field: { onChange, value } }) => (
            <Input
              label="Geschaetzte Dauer (Minuten)"
              placeholder="z.B. 30"
              value={value ? String(value) : ""}
              onChangeText={(text) => {
                const num = parseInt(text, 10);
                onChange(isNaN(num) ? undefined : num);
              }}
              keyboardType="numeric"
              accessibilityLabel="Geschaetzte Dauer in Minuten"
            />
          )}
        />

        <Text className="text-gray-700 dark:text-gray-300 font-medium mb-2">
          Tags
        </Text>
        <View className="flex-row items-center mb-2">
          <View className="flex-1 mr-2">
            <Input
              placeholder="Tag hinzufuegen"
              value={tagInput}
              onChangeText={setTagInput}
              onSubmitEditing={addTag}
              returnKeyType="done"
              accessibilityLabel="Tag-Eingabe"
            />
          </View>
          <Button title="+" onPress={addTag} className="px-4 py-3" />
        </View>

        {tags.length > 0 && (
          <View className="flex-row flex-wrap gap-2 mb-4">
            {tags.map((tag) => (
              <TouchableOpacity
                key={tag}
                onPress={() => removeTag(tag)}
                className="flex-row items-center bg-primary-100 dark:bg-primary-900 px-3 py-1 rounded-full"
                accessibilityLabel={`Tag ${tag} entfernen`}
              >
                <Text className="text-primary-700 dark:text-primary-300 text-sm mr-1">
                  {tag}
                </Text>
                <Text className="text-primary-500 font-bold text-xs">x</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <View className="mt-4">
          <Button
            title={submitLabel}
            onPress={handleSubmit(onSubmit)}
            isLoading={isLoading}
          />
        </View>
      </View>
    </ScrollView>
  );
};
