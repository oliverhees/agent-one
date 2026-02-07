import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  useColorScheme,
  Keyboard,
  Dimensions,
  Platform,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import Markdown from "react-native-markdown-display";
import { useChatStore } from "../../../stores/chatStore";
import { Message } from "../../../types/chat";
import { useAudioRecorder } from "../../../hooks/useAudioRecorder";
import { useAudioPlayer } from "../../../hooks/useAudioPlayer";
import { voiceService } from "../../../services/voiceService";

const INPUT_BAR_HEIGHT = 68;
const WINDOW_HEIGHT = Dimensions.get("window").height;

// Pre-process AI content: ensure every \n becomes \n\n for Markdown paragraph breaks
function formatMarkdown(content: string): string {
  // Simple approach: replace all \n with \n\n, then collapse excessive newlines
  return content.replace(/\n/g, "\n\n").replace(/\n{3,}/g, "\n\n");
}

// Markdown styles for assistant messages (light mode)
const mdStylesLight = StyleSheet.create({
  body: { color: "#111827", fontSize: 16, lineHeight: 24 },
  strong: { fontWeight: "700" },
  em: { fontStyle: "italic" },
  bullet_list: { marginVertical: 6 },
  ordered_list: { marginVertical: 6 },
  list_item: { marginVertical: 3 },
  paragraph: { marginTop: 0, marginBottom: 10 },
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
    marginVertical: 6,
  },
  heading1: { fontSize: 20, fontWeight: "700", marginTop: 12, marginBottom: 6 },
  heading2: { fontSize: 18, fontWeight: "700", marginTop: 10, marginBottom: 4 },
  heading3: { fontSize: 16, fontWeight: "700", marginTop: 8, marginBottom: 4 },
  hr: { marginVertical: 10, backgroundColor: "#d1d5db" },
  blockquote: { borderLeftWidth: 3, borderLeftColor: "#0284c7", paddingLeft: 12, marginVertical: 6 },
});

// Markdown styles for assistant messages (dark mode)
const mdStylesDark = StyleSheet.create({
  body: { color: "#ffffff", fontSize: 16, lineHeight: 24 },
  strong: { fontWeight: "700" },
  em: { fontStyle: "italic" },
  bullet_list: { marginVertical: 6 },
  ordered_list: { marginVertical: 6 },
  list_item: { marginVertical: 3 },
  paragraph: { marginTop: 0, marginBottom: 10 },
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
    marginVertical: 6,
  },
  heading1: { fontSize: 20, fontWeight: "700", marginTop: 12, marginBottom: 6, color: "#ffffff" },
  heading2: { fontSize: 18, fontWeight: "700", marginTop: 10, marginBottom: 4, color: "#ffffff" },
  heading3: { fontSize: 16, fontWeight: "700", marginTop: 8, marginBottom: 4, color: "#ffffff" },
  hr: { marginVertical: 10, backgroundColor: "#4b5563" },
  blockquote: { borderLeftWidth: 3, borderLeftColor: "#0284c7", paddingLeft: 12, marginVertical: 6 },
});

export default function ChatScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const [inputText, setInputText] = useState("");
  const flatListRef = useRef<FlatList>(null);
  const [keyboardOpen, setKeyboardOpen] = useState(false);
  const parentHeight = useRef(WINDOW_HEIGHT); // Initialize with screen height as fallback
  const hasAutoSelected = useRef(false);

  // Voice features
  const { isRecording, recordingDuration, startRecording, stopRecording, cancelRecording } = useAudioRecorder();
  const { isPlaying, playAudio, stopAudio } = useAudioPlayer();
  const [isTranscribing, setIsTranscribing] = useState(false);

  // Try Keyboard API (works on standard Android, not Expo Go edge-to-edge)
  useEffect(() => {
    const showSub = Keyboard.addListener("keyboardDidShow", () => {
      setKeyboardOpen(true);
    });
    const hideSub = Keyboard.addListener("keyboardDidHide", () => {
      setKeyboardOpen(false);
    });
    return () => {
      showSub.remove();
      hideSub.remove();
    };
  }, []);

  // Fallback: onFocus/onBlur for Expo Go edge-to-edge
  const handleInputFocus = () => {
    setKeyboardOpen(true);
  };

  const handleInputBlur = () => {
    setKeyboardOpen(false);
  };

  const {
    conversations,
    activeConversationId,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    loadConversations,
    loadMessages,
    sendMessage,
    selectConversation,
    clearError,
  } = useChatStore();

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Auto-select the latest conversation only on initial mount
  useEffect(() => {
    if (
      !hasAutoSelected.current &&
      conversations.length > 0 &&
      !activeConversationId &&
      messages.length === 0
    ) {
      hasAutoSelected.current = true;
      selectConversation(conversations[0].id);
    }
  }, [conversations]);

  // Scroll to bottom when messages change or streaming content updates
  const scrollToBottom = () => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 150);
  };

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages.length]);

  useEffect(() => {
    if (streamingContent) {
      scrollToBottom();
    }
  }, [streamingContent]);

  const handleSend = async () => {
    if (!inputText.trim() || isStreaming) return;

    const messageToSend = inputText.trim();
    setInputText("");

    await sendMessage(messageToSend);
  };

  const handleVoiceSend = async () => {
    const uri = await stopRecording();
    if (!uri) return;

    setIsTranscribing(true);
    try {
      // Transcribe
      const text = await voiceService.transcribe(uri);
      if (!text.trim()) {
        console.warn("Empty transcription");
        return;
      }

      // Send as text message
      await sendMessage(text);

      // TTS for ALICE response (optional - try, don't fail)
      // We'll get the last assistant message after sendMessage completes
      // For now, the text response is sufficient
    } catch (error) {
      console.error("Voice send failed:", error);
    } finally {
      setIsTranscribing(false);
    }
  };

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.role === "user";
    const mdStyles = isDark ? mdStylesDark : mdStylesLight;

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
            <Markdown style={mdStyles}>{formatMarkdown(item.content || "")}</Markdown>
          )}
        </View>
      </View>
    );
  };

  const renderStreamingMessage = () => {
    if (!streamingContent) return null;
    const mdStyles = isDark ? mdStylesDark : mdStylesLight;

    return (
      <View className="flex-row mb-4 justify-start">
        <View className="max-w-[80%] px-4 py-3 rounded-2xl bg-gray-200 dark:bg-gray-700 rounded-bl-sm">
          <Markdown style={mdStyles}>{formatMarkdown(streamingContent || "")}</Markdown>
          <View className="mt-2">
            <ActivityIndicator size="small" color="#0284c7" />
          </View>
        </View>
      </View>
    );
  };

  // Keyboard positioning: use parentHeight (initialized from Dimensions, updated by onLayout)
  const effectiveHeight = parentHeight.current;
  const inputBarTop = keyboardOpen ? effectiveHeight * 0.57 : undefined;
  const inputBarBottom = keyboardOpen ? undefined : 0;

  // Adjust FlatList padding based on keyboard state
  const listBottomPadding = keyboardOpen
    ? effectiveHeight * 0.57 + 8
    : INPUT_BAR_HEIGHT + 8;

  return (
    <View
      style={{ flex: 1, backgroundColor: isDark ? "#111827" : "#ffffff" }}
      onLayout={(e) => {
        const h = e.nativeEvent.layout.height;
        if (h > 0 && !keyboardOpen) {
          parentHeight.current = h;
        }
      }}
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

      {/* Loading State — inside main view so onLayout always fires */}
      {isLoading && messages.length === 0 ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator size="large" color="#0284c7" />
          <Text className="text-gray-500 dark:text-gray-400 mt-4">
            Lade Nachrichten...
          </Text>
        </View>
      ) : messages.length === 0 && !streamingContent ? (
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center", paddingHorizontal: 24, paddingBottom: INPUT_BAR_HEIGHT }}>
          <Ionicons name="chatbubbles-outline" size={64} color="#0284c7" />
          <Text className="text-2xl font-bold text-gray-900 dark:text-white mt-4 text-center">
            Hallo! Ich bin ALICE
          </Text>
          <Text className="text-gray-500 dark:text-gray-400 text-base mt-2 text-center">
            Dein persönlicher ADHS-Coach. Stelle mir eine Frage oder erzähle mir,
            wie es dir geht.
          </Text>
          <TouchableOpacity
            onPress={() => router.push("/(tabs)/chat/live")}
            style={{
              flexDirection: "row",
              alignItems: "center",
              backgroundColor: isDark ? "#1e293b" : "#f1f5f9",
              paddingHorizontal: 20,
              paddingVertical: 12,
              borderRadius: 25,
              marginTop: 16,
              gap: 8,
            }}
          >
            <Ionicons name="radio" size={20} color="#0284c7" />
            <Text style={{ color: "#0284c7", fontSize: 16, fontWeight: "500" }}>
              Live-Gespräch starten
            </Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 16, paddingBottom: listBottomPadding }}
          ListFooterComponent={renderStreamingMessage()}
          onContentSizeChange={scrollToBottom}
          keyboardShouldPersistTaps="handled"
        />
      )}

      {/* Input Bar — absolutely positioned */}
      <View
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: inputBarTop,
          bottom: inputBarBottom,
          backgroundColor: isDark ? "#111827" : "#ffffff",
          borderTopWidth: 1,
          borderTopColor: isDark ? "#374151" : "#e5e7eb",
          paddingHorizontal: 16,
          paddingVertical: 12,
        }}
      >
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          {/* Mic Button — toggle: tap to start, tap to stop */}
          <TouchableOpacity
            onPress={isRecording ? handleVoiceSend : startRecording}
            disabled={isStreaming || isTranscribing}
            style={{
              width: 48,
              height: 48,
              borderRadius: 24,
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: isRecording ? "#dc2626" : isTranscribing ? "#d1d5db" : isDark ? "#1f2937" : "#f3f4f6",
            }}
            accessibilityLabel={isRecording ? "Aufnahme stoppen" : "Sprachnachricht aufnehmen"}
          >
            {isTranscribing ? (
              <ActivityIndicator size="small" color="#0284c7" />
            ) : (
              <Ionicons
                name={isRecording ? "stop" : "mic"}
                size={22}
                color={isRecording ? "#ffffff" : "#0284c7"}
              />
            )}
          </TouchableOpacity>

          {/* Show recording indicator instead of text input when recording */}
          {isRecording ? (
            <View style={{ flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center", paddingVertical: 12 }}>
              <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#dc2626", marginRight: 8 }} />
              <Text style={{ color: isDark ? "#ffffff" : "#111827", fontSize: 16 }}>
                {`${Math.floor(recordingDuration / 60)}:${(recordingDuration % 60).toString().padStart(2, "0")}`}
              </Text>
            </View>
          ) : (
            <TextInput
              style={{
                flex: 1,
                backgroundColor: isDark ? "#1f2937" : "#f3f4f6",
                borderWidth: 1,
                borderColor: isDark ? "#374151" : "#d1d5db",
                borderRadius: 9999,
                paddingHorizontal: 16,
                paddingVertical: 12,
                color: isDark ? "#ffffff" : "#111827",
                fontSize: 16,
              }}
              placeholder="Nachricht schreiben..."
              placeholderTextColor="#9ca3af"
              value={inputText}
              onChangeText={setInputText}
              multiline
              maxLength={1000}
              editable={!isStreaming}
              onSubmitEditing={handleSend}
              blurOnSubmit={false}
              onFocus={handleInputFocus}
              onBlur={handleInputBlur}
            />
          )}

          {/* Send Button */}
          <TouchableOpacity
            onPress={handleSend}
            disabled={!inputText.trim() || isStreaming}
            style={{
              width: 48,
              height: 48,
              borderRadius: 24,
              alignItems: "center",
              justifyContent: "center",
              backgroundColor:
                inputText.trim() && !isStreaming ? "#0284c7" : isDark ? "#374151" : "#d1d5db",
            }}
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
    </View>
  );
}
