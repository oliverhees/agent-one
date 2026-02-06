import React, { useState } from "react";
import { View, Text, ScrollView, TouchableOpacity } from "react-native";
import { useForm, Controller } from "react-hook-form";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { BrainEntryCreate, BrainEntryType, BrainEntry } from "../../types/brain";

interface EntryFormProps {
  initialData?: Partial<BrainEntry>;
  onSubmit: (data: BrainEntryCreate) => void;
  isLoading: boolean;
  submitLabel?: string;
}

const ENTRY_TYPES: { value: BrainEntryType; label: string }[] = [
  { value: "manual", label: "Manuell" },
  { value: "url_import", label: "URL" },
  { value: "voice_note", label: "Sprachnotiz" },
];

export const EntryForm: React.FC<EntryFormProps> = ({
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
  } = useForm<BrainEntryCreate>({
    defaultValues: {
      title: initialData?.title ?? "",
      content: initialData?.content ?? "",
      entry_type: initialData?.entry_type ?? "manual",
      tags: initialData?.tags ?? [],
      source_url: initialData?.source_url ?? undefined,
    },
  });

  const selectedType = watch("entry_type");
  const tags = watch("tags") ?? [];

  const addTag = () => {
    const trimmed = tagInput.trim();
    if (trimmed && !tags.includes(trimmed) && tags.length < 30) {
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
              placeholder="Titel des Eintrags"
              value={value}
              onChangeText={onChange}
              error={errors.title?.message}
              accessibilityLabel="Eintrag-Titel"
            />
          )}
        />

        <Controller
          control={control}
          name="content"
          rules={{ required: "Inhalt ist erforderlich" }}
          render={({ field: { onChange, value } }) => (
            <Input
              label="Inhalt *"
              placeholder="Wissen, Notizen, Informationen..."
              value={value}
              onChangeText={onChange}
              multiline
              numberOfLines={6}
              className="min-h-[150px] text-top"
              error={errors.content?.message}
              accessibilityLabel="Eintrag-Inhalt"
            />
          )}
        />

        <Text className="text-gray-700 dark:text-gray-300 font-medium mb-2">
          Typ
        </Text>
        <View className="flex-row gap-2 mb-4">
          {ENTRY_TYPES.map((type) => (
            <TouchableOpacity
              key={type.value}
              onPress={() => setValue("entry_type", type.value)}
              className={`px-3 py-2 rounded-lg border ${
                selectedType === type.value
                  ? "border-primary-600 bg-primary-50 dark:bg-primary-900"
                  : "border-gray-300 dark:border-gray-700"
              }`}
              accessibilityLabel={`Typ: ${type.label}`}
            >
              <Text
                className={`text-sm ${
                  selectedType === type.value
                    ? "text-primary-700 dark:text-primary-300 font-medium"
                    : "text-gray-600 dark:text-gray-400"
                }`}
              >
                {type.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {selectedType === "url_import" && (
          <Controller
            control={control}
            name="source_url"
            render={({ field: { onChange, value } }) => (
              <Input
                label="Quell-URL"
                placeholder="https://..."
                value={value ?? ""}
                onChangeText={onChange}
                keyboardType="url"
                autoCapitalize="none"
                accessibilityLabel="Quell-URL"
              />
            )}
          />
        )}

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
