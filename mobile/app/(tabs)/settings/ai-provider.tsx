import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Card } from "../../../components/ui/Card";
import api from "../../../services/api";

interface AIProviderInfo {
  ai_provider: "anthropic" | "custom";
  custom_llm_available: boolean;
  custom_llm_model: string | null;
}

export default function AIProviderScreen() {
  const [providerInfo, setProviderInfo] = useState<AIProviderInfo>({
    ai_provider: "anthropic",
    custom_llm_available: false,
    custom_llm_model: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadProvider();
  }, []);

  const loadProvider = async () => {
    try {
      const res = await api.get<AIProviderInfo>("/settings/ai-provider");
      setProviderInfo(res.data);
    } catch (error) {
      console.error("Failed to load AI provider:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateProvider = async (value: "anthropic" | "custom") => {
    setIsSaving(true);
    try {
      const res = await api.put<AIProviderInfo>("/settings/ai-provider", {
        ai_provider: value,
      });
      setProviderInfo(res.data);
    } catch (error) {
      console.error("Failed to update AI provider:", error);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <View className="flex-1 bg-gray-50 dark:bg-gray-900 items-center justify-center">
        <ActivityIndicator size="large" color="#0284c7" />
      </View>
    );
  }

  return (
    <View className="flex-1 bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <View className="bg-white dark:bg-gray-800 px-4 py-3 flex-row items-center border-b border-gray-200 dark:border-gray-700">
        <TouchableOpacity
          onPress={() => router.back()}
          className="mr-3"
          accessibilityLabel="Zurueck"
        >
          <Ionicons name="arrow-back" size={24} color="#0284c7" />
        </TouchableOpacity>
        <Text className="text-xl font-semibold text-gray-900 dark:text-white">
          KI-Modell
        </Text>
      </View>

      <ScrollView className="flex-1">
        <View className="p-6">
          <Card className="mb-4">
            <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              KI-Provider
            </Text>

            {/* Anthropic Option */}
            <TouchableOpacity
              onPress={() => updateProvider("anthropic")}
              disabled={isSaving}
              className="flex-row items-center mb-3"
              accessibilityLabel="Anthropic Claude auswaehlen"
            >
              <View
                className={`w-6 h-6 rounded-full border-2 items-center justify-center mr-3 ${
                  providerInfo.ai_provider === "anthropic"
                    ? "border-primary-600"
                    : "border-gray-400"
                }`}
              >
                {providerInfo.ai_provider === "anthropic" && (
                  <View className="w-3 h-3 rounded-full bg-primary-600" />
                )}
              </View>
              <View style={{ flex: 1 }}>
                <Text className="text-base text-gray-900 dark:text-white">
                  Anthropic Claude
                </Text>
                <Text className="text-xs text-gray-500 dark:text-gray-400">
                  Claude Sonnet / Haiku via Anthropic API
                </Text>
              </View>
            </TouchableOpacity>

            {/* Custom LLM Option */}
            <TouchableOpacity
              onPress={() => updateProvider("custom")}
              disabled={isSaving || !providerInfo.custom_llm_available}
              className="flex-row items-center"
              accessibilityLabel="Custom LLM auswaehlen"
            >
              <View
                className={`w-6 h-6 rounded-full border-2 items-center justify-center mr-3 ${
                  providerInfo.ai_provider === "custom"
                    ? "border-primary-600"
                    : "border-gray-400"
                }`}
              >
                {providerInfo.ai_provider === "custom" && (
                  <View className="w-3 h-3 rounded-full bg-primary-600" />
                )}
              </View>
              <View style={{ flex: 1 }}>
                <Text
                  className={`text-base ${
                    providerInfo.custom_llm_available
                      ? "text-gray-900 dark:text-white"
                      : "text-gray-400 dark:text-gray-600"
                  }`}
                >
                  Custom LLM (vLLM)
                </Text>
                <Text className="text-xs text-gray-500 dark:text-gray-400">
                  {providerInfo.custom_llm_available
                    ? providerInfo.custom_llm_model || "Custom Modell"
                    : "Nicht konfiguriert auf dem Server"}
                </Text>
              </View>
            </TouchableOpacity>
          </Card>

          {/* Info Card */}
          <Card className="mb-4">
            <View className="flex-row items-start">
              <Ionicons
                name="information-circle-outline"
                size={20}
                color="#0284c7"
                style={{ marginRight: 8, marginTop: 2 }}
              />
              <View style={{ flex: 1 }}>
                <Text className="text-sm text-gray-600 dark:text-gray-400">
                  {providerInfo.ai_provider === "anthropic"
                    ? "Claude wird fuer Chat, Sprachassistenz und Tool-Nutzung verwendet. " +
                      "Sonnet fuer Text-Chat, Haiku fuer schnelle Sprachantworten."
                    : `Das Custom-Modell (${providerInfo.custom_llm_model || "unbekannt"}) wird fuer alle Interaktionen verwendet. ` +
                      "Tool-Nutzung wird im OpenAI-kompatiblen Format unterstuetzt."}
                </Text>
              </View>
            </View>
          </Card>

          {/* Warning if custom not available but selected */}
          {!providerInfo.custom_llm_available && (
            <Card className="mb-4">
              <View
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  backgroundColor: "#fef3c7",
                  paddingHorizontal: 12,
                  paddingVertical: 10,
                  borderRadius: 8,
                }}
              >
                <Ionicons
                  name="warning"
                  size={16}
                  color="#d97706"
                  style={{ marginRight: 8 }}
                />
                <Text style={{ color: "#92400e", fontSize: 13, flex: 1 }}>
                  Kein Custom LLM Server konfiguriert. Bitte CUSTOM_LLM_BASE_URL
                  in der Server-Konfiguration setzen.
                </Text>
              </View>
            </Card>
          )}

          {isSaving && (
            <View className="flex-row items-center justify-center mt-4">
              <ActivityIndicator size="small" color="#0284c7" />
              <Text className="ml-2 text-gray-600 dark:text-gray-400">
                Wird gespeichert...
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    </View>
  );
}
