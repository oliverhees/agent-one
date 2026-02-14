import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  useColorScheme,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { useBriefingStore } from "../../../stores/briefingStore";

const PRIORITY_COLORS: Record<string, string> = {
  urgent: "#ef4444",
  high: "#f59e0b",
  medium: "#0284c7",
  low: "#6b7280",
};

export default function BriefingScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const {
    briefing,
    isLoading,
    fetchToday,
    generateBriefing,
    markAsRead,
    submitBrainDump,
  } = useBriefingStore();

  const [brainDumpText, setBrainDumpText] = useState("");
  const [brainDumpResult, setBrainDumpResult] = useState<string | null>(null);

  useEffect(() => {
    fetchToday();
  }, []);

  useEffect(() => {
    if (briefing && briefing.status !== "read") {
      markAsRead();
    }
  }, [briefing?.id]);

  const handleRefresh = useCallback(() => {
    fetchToday();
  }, [fetchToday]);

  const handleGenerate = useCallback(async () => {
    await generateBriefing();
  }, [generateBriefing]);

  const handleBrainDump = useCallback(async () => {
    if (!brainDumpText.trim()) return;
    const result = await submitBrainDump(brainDumpText.trim());
    if (result) {
      setBrainDumpResult(result.message);
      setBrainDumpText("");
      setTimeout(() => setBrainDumpResult(null), 3000);
    }
  }, [brainDumpText, submitBrainDump]);

  if (isLoading && !briefing) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        style={{ flex: 1, backgroundColor: isDark ? "#030712" : "#f9fafb" }}
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={handleRefresh} />
        }
      >
        {!briefing && (
          <Card style={{ marginBottom: 16 }}>
            <View style={{ padding: 20, alignItems: "center" }}>
              <Ionicons
                name="sunny-outline"
                size={48}
                color={isDark ? "#fcd34d" : "#f59e0b"}
              />
              <Text
                style={{
                  fontSize: 18,
                  fontWeight: "700",
                  color: isDark ? "#f9fafb" : "#111827",
                  marginTop: 12,
                }}
              >
                Kein Briefing fuer heute
              </Text>
              <TouchableOpacity
                onPress={handleGenerate}
                style={{
                  marginTop: 16,
                  paddingVertical: 10,
                  paddingHorizontal: 24,
                  borderRadius: 8,
                  backgroundColor: "#0284c7",
                }}
              >
                <Text style={{ color: "#fff", fontWeight: "600" }}>
                  Briefing generieren
                </Text>
              </TouchableOpacity>
            </View>
          </Card>
        )}

        {briefing && (
          <Card style={{ marginBottom: 16 }}>
            <View style={{ padding: 16 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <Ionicons name="sunny" size={24} color="#f59e0b" />
                <Text
                  style={{
                    fontSize: 18,
                    fontWeight: "700",
                    color: isDark ? "#f9fafb" : "#111827",
                  }}
                >
                  Morning Briefing
                </Text>
              </View>
              <Text
                style={{
                  fontSize: 15,
                  lineHeight: 22,
                  color: isDark ? "#d1d5db" : "#374151",
                }}
              >
                {briefing.content}
              </Text>
            </View>
          </Card>
        )}

        {briefing && briefing.tasks_suggested.length > 0 && (
          <View style={{ marginBottom: 16 }}>
            <Text
              style={{
                fontSize: 16,
                fontWeight: "700",
                color: isDark ? "#f9fafb" : "#111827",
                marginBottom: 8,
              }}
            >
              Deine Top-Aufgaben
            </Text>
            {briefing.tasks_suggested.map((task: any, index: number) => (
              <Card key={task.task_id || index} style={{ marginBottom: 8 }}>
                <View style={{ padding: 12, flexDirection: "row", alignItems: "center", gap: 12 }}>
                  <View
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 16,
                      backgroundColor: PRIORITY_COLORS[task.priority] || "#6b7280",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700", fontSize: 14 }}>
                      {index + 1}
                    </Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text
                      style={{
                        fontSize: 15,
                        fontWeight: "600",
                        color: isDark ? "#f9fafb" : "#111827",
                      }}
                    >
                      {task.title}
                    </Text>
                    {task.reason && (
                      <Text
                        style={{
                          fontSize: 12,
                          color: isDark ? "#9ca3af" : "#6b7280",
                          marginTop: 2,
                        }}
                      >
                        {task.reason}
                      </Text>
                    )}
                  </View>
                </View>
              </Card>
            ))}
          </View>
        )}

        <Card style={{ marginBottom: 16 }}>
          <View style={{ padding: 16 }}>
            <Text
              style={{
                fontSize: 16,
                fontWeight: "700",
                color: isDark ? "#f9fafb" : "#111827",
                marginBottom: 8,
              }}
            >
              Brain Dump
            </Text>
            <TextInput
              value={brainDumpText}
              onChangeText={setBrainDumpText}
              placeholder="Gedanken loswerden... (kommagetrennt oder neue Zeile)"
              placeholderTextColor={isDark ? "#6b7280" : "#9ca3af"}
              multiline
              numberOfLines={3}
              style={{
                backgroundColor: isDark ? "#1f2937" : "#f3f4f6",
                borderRadius: 8,
                padding: 12,
                color: isDark ? "#f9fafb" : "#111827",
                fontSize: 14,
                minHeight: 80,
                textAlignVertical: "top",
              }}
            />
            {brainDumpResult && (
              <Text style={{ color: "#16a34a", marginTop: 8, fontSize: 13 }}>
                {brainDumpResult}
              </Text>
            )}
            <TouchableOpacity
              onPress={handleBrainDump}
              disabled={!brainDumpText.trim()}
              style={{
                marginTop: 10,
                paddingVertical: 10,
                borderRadius: 8,
                backgroundColor: brainDumpText.trim() ? "#0284c7" : isDark ? "#374151" : "#e5e7eb",
                alignItems: "center",
              }}
            >
              <Text
                style={{
                  color: brainDumpText.trim() ? "#fff" : isDark ? "#6b7280" : "#9ca3af",
                  fontWeight: "600",
                  fontSize: 14,
                }}
              >
                Aufgaben erstellen
              </Text>
            </TouchableOpacity>
          </View>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
