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
import {
  useBrainEntry,
  useDeleteBrainEntry,
} from "../../../hooks/useBrain";
import { BrainEntryType } from "../../../types/brain";

const TYPE_LABEL: Record<BrainEntryType, string> = {
  manual: "Manuell",
  chat_extract: "Chat-Extrakt",
  url_import: "URL-Import",
  file_import: "Datei-Import",
  voice_note: "Sprachnotiz",
};

const EMBEDDING_LABEL: Record<string, { label: string; color: string }> = {
  pending: { label: "Wartend", color: "text-yellow-600" },
  processing: { label: "Wird verarbeitet", color: "text-blue-600" },
  completed: { label: "Bereit", color: "text-green-600" },
  failed: { label: "Fehlgeschlagen", color: "text-red-600" },
};

export default function BrainEntryDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: entry, isLoading, isError, error } = useBrainEntry(id);
  const deleteEntry = useDeleteBrainEntry();

  const handleDelete = () => {
    if (!entry) return;
    Alert.alert(
      "Eintrag loeschen",
      "Bist du sicher? Diese Aktion kann nicht rueckgaengig gemacht werden.",
      [
        { text: "Abbrechen", style: "cancel" },
        {
          text: "Loeschen",
          style: "destructive",
          onPress: () => {
            deleteEntry.mutate(entry.id, {
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

  if (isLoading) {
    return <LoadingSpinner message="Eintrag wird geladen..." />;
  }

  if (isError || !entry) {
    return (
      <View className="flex-1 items-center justify-center bg-white dark:bg-gray-900 p-6">
        <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
        <Text className="text-red-500 text-center mt-4 text-base">
          Eintrag nicht gefunden
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

  const embeddingInfo = EMBEDDING_LABEL[entry.embedding_status] ?? {
    label: entry.embedding_status,
    color: "text-gray-500",
  };

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
                pathname: "/(tabs)/brain/create",
                params: { editId: entry.id },
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
        {/* Title & Type */}
        <Card className="mb-3">
          <Text className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            {entry.title}
          </Text>
          <View className="flex-row items-center gap-2 mb-3">
            <View className="px-2 py-0.5 rounded-full bg-primary-100 dark:bg-primary-900">
              <Text className="text-xs font-medium text-primary-700 dark:text-primary-300">
                {TYPE_LABEL[entry.entry_type]}
              </Text>
            </View>
            <Text className={`text-xs ${embeddingInfo.color}`}>
              Embedding: {embeddingInfo.label}
            </Text>
          </View>
        </Card>

        {/* Content */}
        <Card className="mb-3">
          <Text className="text-base text-gray-700 dark:text-gray-300 leading-6">
            {entry.content}
          </Text>
        </Card>

        {/* Source URL */}
        {entry.source_url && (
          <Card className="mb-3">
            <View className="flex-row items-center">
              <Ionicons
                name="link-outline"
                size={16}
                color="#6b7280"
                style={{ marginRight: 8 }}
              />
              <Text
                className="text-primary-600 dark:text-primary-400 text-sm flex-1"
                numberOfLines={1}
              >
                {entry.source_url}
              </Text>
            </View>
          </Card>
        )}

        {/* Tags */}
        {entry.tags.length > 0 && (
          <Card className="mb-3">
            <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tags
            </Text>
            <View className="flex-row flex-wrap gap-2">
              {entry.tags.map((tag) => (
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

        {/* Meta */}
        <Card className="mb-8">
          <View className="flex-row items-center mb-1">
            <Ionicons
              name="time-outline"
              size={14}
              color="#6b7280"
              style={{ marginRight: 6 }}
            />
            <Text className="text-gray-400 dark:text-gray-500 text-xs">
              Erstellt: {formatDate(entry.created_at)}
            </Text>
          </View>
          <View className="flex-row items-center">
            <Ionicons
              name="refresh-outline"
              size={14}
              color="#6b7280"
              style={{ marginRight: 6 }}
            />
            <Text className="text-gray-400 dark:text-gray-500 text-xs">
              Aktualisiert: {formatDate(entry.updated_at)}
            </Text>
          </View>
        </Card>
      </ScrollView>
    </View>
  );
}
