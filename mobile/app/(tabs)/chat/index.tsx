import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  useColorScheme,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router, useFocusEffect } from "expo-router";
import Markdown from "react-native-markdown-display";
import { useChatStore } from "../../../stores/chatStore";
import { Message } from "../../../types/chat";
import { useAudioRecorder } from "../../../hooks/useAudioRecorder";
import { useAudioPlayer } from "../../../hooks/useAudioPlayer";
import { voiceService } from "../../../services/voiceService";
import { useWakeWord } from "../../../hooks/useWakeWord";
import { useWakeWordStore } from "../../../stores/wakeWordStore";

function formatMarkdown(content: string): string {
  return content.replace(/\n/g, "\n\n").replace(/\n{3,}/g, "\n\n");
}

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

// Typing indicator dots
function TypingIndicator() {
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 4, paddingVertical: 4 }}>
      <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: "#9ca3af", opacity: 0.6 }} />
      <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: "#9ca3af", opacity: 0.8 }} />
      <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: "#9ca3af", opacity: 1.0 }} />
    </View>
  );
}

export default function ChatScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const [inputText, setInputText] = useState("");
  const flatListRef = useRef<FlatList>(null);
  const hasAutoSelected = useRef(false);

  const { isRecording, recordingDuration, startRecording, stopRecording, cancelRecording } = useAudioRecorder();
  const { isPlaying, playAudio, stopAudio } = useAudioPlayer();
  const [isTranscribing, setIsTranscribing] = useState(false);

  const wakeWordEnabled = useWakeWordStore((s) => s.enabled);
  const { start: startWakeWord, stop: stopWakeWord, isListening: isWakeWordListening } = useWakeWord({
    onDetected: () => {
      router.push({ pathname: "/(tabs)/chat/live", params: { fromWakeWord: "true" } });
    },
  });

  useFocusEffect(
    useCallback(() => {
      if (wakeWordEnabled) {
        startWakeWord();
      }
      return () => {
        stopWakeWord();
      };
    }, [wakeWordEnabled])
  );

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

  // Reload conversations on every screen focus (e.g. returning from live chat)
  useFocusEffect(
    useCallback(() => {
      loadConversations();
    }, [])
  );

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

  // Build display data: messages reversed for inverted FlatList + streaming bubble
  const displayData = useMemo(() => {
    const items: (Message | { id: string; role: "assistant"; content: string; created_at: string; isStreaming: true })[] = [];

    // Add streaming message as first item (shows at bottom in inverted list)
    if (isStreaming) {
      items.push({
        id: "streaming",
        role: "assistant",
        content: streamingContent || "",
        created_at: new Date().toISOString(),
        isStreaming: true as const,
      });
    }

    // Messages in reverse order (newest first for inverted list)
    for (let i = messages.length - 1; i >= 0; i--) {
      items.push(messages[i]);
    }

    return items;
  }, [messages, isStreaming, streamingContent]);

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
      const text = await voiceService.transcribe(uri);
      if (!text.trim()) {
        console.warn("Empty transcription");
        return;
      }
      await sendMessage(text);
    } catch (error) {
      console.error("Voice send failed:", error);
    } finally {
      setIsTranscribing(false);
    }
  };

  const renderMessage = ({ item }: { item: any }) => {
    const isUser = item.role === "user";
    const isStreamingMsg = "isStreaming" in item;
    const mdStyles = isDark ? mdStylesDark : mdStylesLight;

    return (
      <View style={{ flexDirection: "row", marginBottom: 12, justifyContent: isUser ? "flex-end" : "flex-start" }}>
        <View
          style={{
            maxWidth: "80%",
            paddingHorizontal: 14,
            paddingVertical: 10,
            borderRadius: 18,
            ...(isUser
              ? {
                  backgroundColor: "#0284c7",
                  borderBottomRightRadius: 4,
                }
              : {
                  backgroundColor: isDark ? "#374151" : "#e5e7eb",
                  borderBottomLeftRadius: 4,
                }),
          }}
        >
          {isUser ? (
            <Text style={{ fontSize: 16, color: "#ffffff", lineHeight: 22 }}>{item.content}</Text>
          ) : isStreamingMsg && !item.content ? (
            <TypingIndicator />
          ) : (
            <Markdown style={mdStyles}>{formatMarkdown(item.content || "")}</Markdown>
          )}
          {isStreamingMsg && item.content ? (
            <View style={{ marginTop: 4 }}>
              <TypingIndicator />
            </View>
          ) : null}
        </View>
      </View>
    );
  };

  const hasMessages = messages.length > 0 || isStreaming;

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: isDark ? "#111827" : "#ffffff" }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
    >
      {/* Error Banner */}
      {error && (
        <View style={{ backgroundColor: "#ef4444", paddingHorizontal: 16, paddingVertical: 12, flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <Text style={{ color: "#ffffff", flex: 1, marginRight: 8 }}>{error}</Text>
          <TouchableOpacity onPress={clearError}>
            <Ionicons name="close" size={20} color="#ffffff" />
          </TouchableOpacity>
        </View>
      )}

      {/* Loading State */}
      {isLoading && messages.length === 0 ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator size="large" color="#0284c7" />
          <Text style={{ color: "#9ca3af", marginTop: 16 }}>Lade Nachrichten...</Text>
        </View>
      ) : !hasMessages ? (
        /* Empty State */
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center", paddingHorizontal: 24 }}>
          <Ionicons name="chatbubbles-outline" size={64} color="#0284c7" />
          <Text style={{ fontSize: 24, fontWeight: "700", color: isDark ? "#ffffff" : "#111827", marginTop: 16, textAlign: "center" }}>
            Hallo! Ich bin ALICE
          </Text>
          <Text style={{ color: "#9ca3af", fontSize: 16, marginTop: 8, textAlign: "center" }}>
            Dein persönlicher ADHS-Coach. Stelle mir eine Frage oder erzähle mir, wie es dir geht.
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
        /* Message List — inverted so newest messages are at bottom */
        <FlatList
          ref={flatListRef}
          data={displayData}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          inverted
          style={{ flex: 1 }}
          contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8 }}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="interactive"
        />
      )}

      {/* Wake Word Indicator */}
      {isWakeWordListening && (
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "center",
            paddingVertical: 4,
            backgroundColor: isDark ? "#111827" : "#ffffff",
          }}
        >
          <View
            style={{
              width: 8,
              height: 8,
              borderRadius: 4,
              backgroundColor: "#22c55e",
              marginRight: 6,
            }}
          />
          <Text style={{ color: "#22c55e", fontSize: 12, fontWeight: "500" }}>
            Hey Alice
          </Text>
        </View>
      )}

      {/* Input Bar — part of the layout flow, not absolute */}
      <View
        style={{
          backgroundColor: isDark ? "#111827" : "#ffffff",
          borderTopWidth: 1,
          borderTopColor: isDark ? "#374151" : "#e5e7eb",
          paddingHorizontal: 12,
          paddingTop: 8,
          paddingBottom: 8,
        }}
      >
        <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 8 }}>
          {/* Mic Button */}
          <TouchableOpacity
            onPress={isRecording ? handleVoiceSend : startRecording}
            disabled={isStreaming || isTranscribing}
            style={{
              width: 44,
              height: 44,
              borderRadius: 22,
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: isRecording ? "#dc2626" : isTranscribing ? "#d1d5db" : isDark ? "#1f2937" : "#f3f4f6",
              marginBottom: 2,
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

          {/* Recording indicator or Text input */}
          {isRecording ? (
            <View style={{ flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center", height: 44 }}>
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
                borderRadius: 22,
                paddingHorizontal: 16,
                paddingTop: 10,
                paddingBottom: 10,
                color: isDark ? "#ffffff" : "#111827",
                fontSize: 16,
                maxHeight: 120,
              }}
              placeholder="Nachricht schreiben..."
              placeholderTextColor="#9ca3af"
              value={inputText}
              onChangeText={setInputText}
              multiline
              maxLength={1000}
              editable={!isStreaming}
              blurOnSubmit={false}
            />
          )}

          {/* Send Button */}
          <TouchableOpacity
            onPress={handleSend}
            disabled={!inputText.trim() || isStreaming}
            style={{
              width: 44,
              height: 44,
              borderRadius: 22,
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: inputText.trim() && !isStreaming ? "#0284c7" : isDark ? "#374151" : "#d1d5db",
              marginBottom: 2,
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
    </KeyboardAvoidingView>
  );
}
