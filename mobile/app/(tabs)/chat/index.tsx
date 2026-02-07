import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  StyleSheet,
  useColorScheme,
  Keyboard,
} from "react-native";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";
import Markdown from "react-native-markdown-display";
import { useChatStore } from "../../../stores/chatStore";
import { Message } from "../../../types/chat";

// Markdown styles for assistant messages (light mode)
const mdStylesLight = StyleSheet.create({
  body: { color: "#111827", fontSize: 16, lineHeight: 22 },
  strong: { fontWeight: "700" },
  bullet_list: { marginVertical: 4 },
  ordered_list: { marginVertical: 4 },
  list_item: { marginVertical: 2 },
  paragraph: { marginVertical: 2 },
  code_inline: {
    backgroundColor: "#e5e7eb",
    borderRadius: 4,
    paddingHorizontal: 4,
    fontFamily: "monospace",
    fontSize: 14,
  },
  fence: {
    backgroundColor: "#e5e7eb",
    borderRadius: 8,
    padding: 8,
    marginVertical: 4,
  },
  heading1: { fontSize: 20, fontWeight: "700", marginVertical: 4 },
  heading2: { fontSize: 18, fontWeight: "700", marginVertical: 4 },
  heading3: { fontSize: 16, fontWeight: "700", marginVertical: 4 },
});

// Markdown styles for assistant messages (dark mode)
const mdStylesDark = StyleSheet.create({
  body: { color: "#ffffff", fontSize: 16, lineHeight: 22 },
  strong: { fontWeight: "700" },
  bullet_list: { marginVertical: 4 },
  ordered_list: { marginVertical: 4 },
  list_item: { marginVertical: 2 },
  paragraph: { marginVertical: 2 },
  code_inline: {
    backgroundColor: "#374151",
    borderRadius: 4,
    paddingHorizontal: 4,
    fontFamily: "monospace",
    fontSize: 14,
    color: "#ffffff",
  },
  fence: {
    backgroundColor: "#374151",
    borderRadius: 8,
    padding: 8,
    marginVertical: 4,
  },
  heading1: { fontSize: 20, fontWeight: "700", marginVertical: 4, color: "#ffffff" },
  heading2: { fontSize: 18, fontWeight: "700", marginVertical: 4, color: "#ffffff" },
  heading3: { fontSize: 16, fontWeight: "700", marginVertical: 4, color: "#ffffff" },
});

export default function ChatScreen() {
  const colorScheme = useColorScheme();
  const [inputText, setInputText] = useState("");
  const flatListRef = useRef<FlatList>(null);
  const tabBarHeight = useBottomTabBarHeight();

  const {
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    sendMessage,
    clearError,
  } = useChatStore();

  // Scroll to bottom when new messages arrive or keyboard opens
  useEffect(() => {
    if (messages.length > 0 || streamingContent) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length, streamingContent]);

  // Scroll to bottom when keyboard shows
  useEffect(() => {
    const keyboardDidShow = Keyboard.addListener("keyboardDidShow", () => {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    });
    return () => keyboardDidShow.remove();
  }, []);

  const handleSend = async () => {
    if (!inputText.trim() || isStreaming) return;

    const messageToSend = inputText.trim();
    setInputText("");

    await sendMessage(messageToSend);
  };

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.role === "user";
    const mdStyles = colorScheme === "dark" ? mdStylesDark : mdStylesLight;

    return (
      <View
        className={`flex-row mb-4 ${isUser ? "justify-end" : "justify-start"}`}
      >
        <View
          className={`max-w-[80%] px-4 py-3 rounded-2xl ${
            isUser
              ? "bg-primary-600 rounded-br-sm"
              : "bg-gray-200 dark:bg-gray-700 rounded-bl-sm"
          }`}
        >
          {isUser ? (
            <Text className="text-base text-white">{item.content}</Text>
          ) : (
            <Markdown style={mdStyles}>{item.content || ""}</Markdown>
          )}
        </View>
      </View>
    );
  };

  const renderStreamingMessage = () => {
    if (!streamingContent) return null;
    const mdStyles = colorScheme === "dark" ? mdStylesDark : mdStylesLight;

    return (
      <View className="flex-row mb-4 justify-start">
        <View className="max-w-[80%] px-4 py-3 rounded-2xl bg-gray-200 dark:bg-gray-700 rounded-bl-sm">
          <Markdown style={mdStyles}>{streamingContent || ""}</Markdown>
          <View className="mt-2">
            <ActivityIndicator size="small" color="#0284c7" />
          </View>
        </View>
      </View>
    );
  };

  const renderWelcomeScreen = () => (
    <View className="flex-1 items-center justify-center px-6">
      <Ionicons name="chatbubbles-outline" size={64} color="#0284c7" />
      <Text className="text-2xl font-bold text-gray-900 dark:text-white mt-4 text-center">
        Hallo! Ich bin ALICE
      </Text>
      <Text className="text-gray-500 dark:text-gray-400 text-base mt-2 text-center">
        Dein persönlicher ADHS-Coach. Stelle mir eine Frage oder erzähle mir,
        wie es dir geht.
      </Text>
    </View>
  );

  if (isLoading && messages.length === 0) {
    return (
      <View className="flex-1 items-center justify-center bg-white dark:bg-gray-900">
        <ActivityIndicator size="large" color="#0284c7" />
        <Text className="text-gray-500 dark:text-gray-400 mt-4">
          Lade Nachrichten...
        </Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      behavior="padding"
      className="flex-1 bg-white dark:bg-gray-900"
      keyboardVerticalOffset={Platform.OS === "ios" ? tabBarHeight : 0}
    >
      {/* Error Banner */}
      {error && (
        <View className="bg-red-500 px-4 py-3 flex-row items-center justify-between">
          <Text className="text-white flex-1 mr-2">{error}</Text>
          <TouchableOpacity onPress={clearError}>
            <Ionicons name="close" size={20} color="#ffffff" />
          </TouchableOpacity>
        </View>
      )}

      {/* Messages or Welcome Screen */}
      {messages.length === 0 && !streamingContent ? (
        renderWelcomeScreen()
      ) : (
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          contentContainerClassName="px-4 pt-4 pb-4"
          ListFooterComponent={renderStreamingMessage()}
          onContentSizeChange={() =>
            flatListRef.current?.scrollToEnd({ animated: true })
          }
        />
      )}

      {/* Input Bar */}
      <View className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <View className="flex-row items-center space-x-2">
          <TextInput
            className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-full px-4 py-3 text-gray-900 dark:text-white"
            placeholder="Nachricht schreiben..."
            placeholderTextColor="#9ca3af"
            value={inputText}
            onChangeText={setInputText}
            multiline
            maxLength={1000}
            editable={!isStreaming}
            onSubmitEditing={handleSend}
            blurOnSubmit={false}
          />
          <TouchableOpacity
            onPress={handleSend}
            disabled={!inputText.trim() || isStreaming}
            className={`w-12 h-12 rounded-full items-center justify-center ${
              inputText.trim() && !isStreaming
                ? "bg-primary-600"
                : "bg-gray-300 dark:bg-gray-700"
            }`}
            accessibilityLabel="Nachricht senden"
          >
            {isStreaming ? (
              <ActivityIndicator size="small" color="#ffffff" />
            ) : (
              <Ionicons
                name="send"
                size={20}
                color={inputText.trim() ? "#ffffff" : "#9ca3af"}
              />
            )}
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
