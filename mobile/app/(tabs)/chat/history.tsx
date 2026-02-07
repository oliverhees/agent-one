import React from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  useColorScheme,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useChatStore } from "../../../stores/chatStore";
import { Conversation } from "../../../types/chat";

// Helper to format relative dates
function formatRelativeDate(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const msgDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

  if (msgDate.getTime() === today.getTime()) {
    return "Heute";
  } else if (msgDate.getTime() === yesterday.getTime()) {
    return "Gestern";
  } else {
    // Format: DD.MM.YYYY
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
  }
}

export default function ChatHistoryScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const router = useRouter();

  const { conversations, isLoading, selectConversation } = useChatStore();

  // Sort conversations by updated_at (newest first)
  const sortedConversations = [...conversations].sort((a, b) => {
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
  });

  const handleSelectConversation = (id: string) => {
    selectConversation(id);
    router.back();
  };

  const renderConversationItem = ({ item }: { item: Conversation }) => {
    const dateLabel = formatRelativeDate(item.updated_at);
    const title = item.title || "Neue Konversation";
    // Preview: use first 80 chars of title or fallback text
    const preview = title.length > 80 ? `${title.substring(0, 80)}...` : title;

    return (
      <TouchableOpacity
        onPress={() => handleSelectConversation(item.id)}
        className="mb-3 mx-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4"
        activeOpacity={0.7}
        accessibilityLabel={`Konversation vom ${dateLabel}`}
      >
        <View className="flex-row items-center justify-between mb-2">
          <Text className="text-xs text-gray-500 dark:text-gray-400 font-medium">
            {dateLabel}
          </Text>
        </View>
        <Text
          className="text-base text-gray-900 dark:text-white mb-1"
          numberOfLines={2}
        >
          {preview}
        </Text>
      </TouchableOpacity>
    );
  };

  const renderEmptyState = () => (
    <View className="flex-1 items-center justify-center px-6">
      <Ionicons
        name="chatbubbles-outline"
        size={64}
        color={isDark ? "#6b7280" : "#9ca3af"}
      />
      <Text className="text-xl font-semibold text-gray-900 dark:text-white mt-4 text-center">
        Noch keine Gespräche
      </Text>
      <Text className="text-base text-gray-500 dark:text-gray-400 mt-2 text-center">
        Starte eine neue Konversation mit Alice
      </Text>
    </View>
  );

  return (
    <View
      className="flex-1"
      style={{ backgroundColor: isDark ? "#111827" : "#ffffff" }}
    >
      {/* Header */}
      <View
        className="px-4 py-4 border-b border-gray-200 dark:border-gray-700 flex-row items-center"
        style={{ backgroundColor: isDark ? "#111827" : "#ffffff" }}
      >
        <TouchableOpacity
          onPress={() => router.back()}
          className="mr-3"
          accessibilityLabel="Zurück zum Chat"
        >
          <Ionicons
            name="arrow-back"
            size={24}
            color={isDark ? "#ffffff" : "#111827"}
          />
        </TouchableOpacity>
        <Text className="text-xl font-bold text-gray-900 dark:text-white">
          Chat-Verlauf
        </Text>
      </View>

      {/* Content */}
      {isLoading && conversations.length === 0 ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" color="#0284c7" />
          <Text className="text-gray-500 dark:text-gray-400 mt-4">
            Lade Konversationen...
          </Text>
        </View>
      ) : sortedConversations.length === 0 ? (
        renderEmptyState()
      ) : (
        <FlatList
          data={sortedConversations}
          keyExtractor={(item) => item.id}
          renderItem={renderConversationItem}
          contentContainerStyle={{ paddingTop: 16, paddingBottom: 16 }}
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}
