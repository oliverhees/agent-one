import React from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { EntryForm } from "../../../components/brain/EntryForm";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import {
  useCreateBrainEntry,
  useUpdateBrainEntry,
  useBrainEntry,
} from "../../../hooks/useBrain";
import { BrainEntryCreate } from "../../../types/brain";

export default function CreateBrainEntryScreen() {
  const { editId } = useLocalSearchParams<{ editId?: string }>();
  const isEdit = !!editId;

  const { data: existingEntry, isLoading: isLoadingEntry } = useBrainEntry(
    editId ?? ""
  );
  const createEntry = useCreateBrainEntry();
  const updateEntry = useUpdateBrainEntry();

  const handleSubmit = (data: BrainEntryCreate) => {
    if (isEdit && editId) {
      updateEntry.mutate(
        { id: editId, data },
        { onSuccess: () => router.back() }
      );
    } else {
      createEntry.mutate(data, { onSuccess: () => router.back() });
    }
  };

  if (isEdit && isLoadingEntry) {
    return <LoadingSpinner message="Eintrag wird geladen..." />;
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
          {isEdit ? "Eintrag bearbeiten" : "Neuer Eintrag"}
        </Text>
      </View>

      <EntryForm
        initialData={isEdit ? existingEntry ?? undefined : undefined}
        onSubmit={handleSubmit}
        isLoading={createEntry.isPending || updateEntry.isPending}
        submitLabel={isEdit ? "Aktualisieren" : "Erstellen"}
      />
    </View>
  );
}
