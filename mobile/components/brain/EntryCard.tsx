import React from "react";
import { View, Text, Pressable } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Card } from "../ui/Card";
import { BrainEntry, BrainEntryType } from "../../types/brain";

interface EntryCardProps {
  entry: BrainEntry;
}

const TYPE_ICON: Record<BrainEntryType, string> = {
  manual: "create-outline",
  chat_extract: "chatbubble-outline",
  url_import: "link-outline",
  file_import: "document-outline",
  voice_note: "mic-outline",
};

const TYPE_LABEL: Record<BrainEntryType, string> = {
  manual: "Manuell",
  chat_extract: "Chat-Extrakt",
  url_import: "URL-Import",
  file_import: "Datei-Import",
  voice_note: "Sprachnotiz",
};

export const EntryCard: React.FC<EntryCardProps> = ({ entry }) => {
  const iconName = TYPE_ICON[entry.entry_type] as keyof typeof Ionicons.glyphMap;

  return (
    <Pressable
      onPress={() => router.push(`/(tabs)/brain/${entry.id}`)}
      className="mb-3"
    >
      <Card>
        <View className="flex-row items-start">
          <View className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 items-center justify-center mr-3 mt-0.5">
            <Ionicons name={iconName} size={16} color="#0284c7" />
          </View>
          <View className="flex-1">
            <Text
              className="text-base font-medium text-gray-900 dark:text-white"
              numberOfLines={1}
            >
              {entry.title}
            </Text>
            <Text
              className="text-sm text-gray-500 dark:text-gray-400 mt-1"
              numberOfLines={2}
            >
              {entry.content}
            </Text>
            <View className="flex-row items-center mt-2 gap-2">
              <Text className="text-xs text-gray-400 dark:text-gray-500">
                {TYPE_LABEL[entry.entry_type]}
              </Text>
              {entry.tags.length > 0 && (
                <Text
                  className="text-xs text-primary-600 dark:text-primary-400"
                  numberOfLines={1}
                >
                  {entry.tags.slice(0, 3).join(", ")}
                </Text>
              )}
            </View>
          </View>
          <Ionicons name="chevron-forward" size={16} color="#9ca3af" />
        </View>
      </Card>
    </Pressable>
  );
};
