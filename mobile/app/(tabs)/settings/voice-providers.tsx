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

interface VoiceProviders {
  stt_provider: "deepgram" | "whisper";
  tts_provider: "elevenlabs" | "edge-tts";
}

interface ApiKeys {
  openai: string | null;
  deepgram: string | null;
  elevenlabs: string | null;
  [key: string]: string | null | boolean;
}

export default function VoiceProvidersScreen() {
  const [providers, setProviders] = useState<VoiceProviders>({
    stt_provider: "deepgram",
    tts_provider: "elevenlabs",
  });
  const [keys, setKeys] = useState<ApiKeys>({
    openai: null,
    deepgram: null,
    elevenlabs: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [provRes, keysRes] = await Promise.all([
        api.get<VoiceProviders>("/settings/voice-providers"),
        api.get<ApiKeys>("/settings/api-keys"),
      ]);
      setProviders(provRes.data);
      setKeys(keysRes.data);
    } catch (error) {
      console.error("Failed to load voice providers:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateProvider = async (
    key: keyof VoiceProviders,
    value: string
  ) => {
    setIsSaving(true);
    try {
      await api.put("/settings/voice-providers", {
        [key]: value,
      });

      setProviders({ ...providers, [key]: value });
    } catch (error) {
      console.error("Failed to update voice provider:", error);
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

  // Check if required keys are present
  const sttKeyMissing =
    (providers.stt_provider === "whisper" && !keys.openai) ||
    (providers.stt_provider === "deepgram" && !keys.deepgram);
  const sttKeyName = providers.stt_provider === "whisper" ? "OpenAI" : "Deepgram";

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
          Voice Provider
        </Text>
      </View>

      <ScrollView className="flex-1">
        <View className="p-6">
          {/* STT Provider Card */}
          <Card className="mb-4">
            <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              STT (Sprache-zu-Text)
            </Text>

            <TouchableOpacity
              onPress={() => updateProvider("stt_provider", "deepgram")}
              disabled={isSaving}
              className="flex-row items-center mb-3"
              accessibilityLabel="Deepgram auswaehlen"
            >
              <View
                className={`w-6 h-6 rounded-full border-2 items-center justify-center mr-3 ${
                  providers.stt_provider === "deepgram"
                    ? "border-primary-600"
                    : "border-gray-400"
                }`}
              >
                {providers.stt_provider === "deepgram" && (
                  <View className="w-3 h-3 rounded-full bg-primary-600" />
                )}
              </View>
              <View style={{ flex: 1 }}>
                <Text className="text-base text-gray-900 dark:text-white">
                  Deepgram
                </Text>
                <Text className="text-xs text-gray-500 dark:text-gray-400">
                  Benoetigt Deepgram API Key
                </Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => updateProvider("stt_provider", "whisper")}
              disabled={isSaving}
              className="flex-row items-center"
              accessibilityLabel="Whisper auswaehlen"
            >
              <View
                className={`w-6 h-6 rounded-full border-2 items-center justify-center mr-3 ${
                  providers.stt_provider === "whisper"
                    ? "border-primary-600"
                    : "border-gray-400"
                }`}
              >
                {providers.stt_provider === "whisper" && (
                  <View className="w-3 h-3 rounded-full bg-primary-600" />
                )}
              </View>
              <View style={{ flex: 1 }}>
                <Text className="text-base text-gray-900 dark:text-white">
                  Whisper (OpenAI)
                </Text>
                <Text className="text-xs text-gray-500 dark:text-gray-400">
                  Benoetigt OpenAI API Key
                </Text>
              </View>
            </TouchableOpacity>

            {/* Warning if key missing */}
            {sttKeyMissing && (
              <TouchableOpacity
                onPress={() => router.push("/(tabs)/settings/api-keys")}
                style={{ flexDirection: "row", alignItems: "center", marginTop: 12, backgroundColor: "#fef3c7", paddingHorizontal: 12, paddingVertical: 10, borderRadius: 8 }}
              >
                <Ionicons name="warning" size={16} color="#d97706" style={{ marginRight: 8 }} />
                <Text style={{ color: "#92400e", fontSize: 13, flex: 1 }}>
                  Kein {sttKeyName} Key hinterlegt. Tippe hier um einen einzugeben.
                </Text>
                <Ionicons name="chevron-forward" size={16} color="#d97706" />
              </TouchableOpacity>
            )}
          </Card>

          {/* TTS Provider Card */}
          <Card className="mb-4">
            <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              TTS (Text-zu-Sprache)
            </Text>

            <TouchableOpacity
              onPress={() => updateProvider("tts_provider", "elevenlabs")}
              disabled={isSaving}
              className="flex-row items-center mb-3"
              accessibilityLabel="ElevenLabs auswaehlen"
            >
              <View
                className={`w-6 h-6 rounded-full border-2 items-center justify-center mr-3 ${
                  providers.tts_provider === "elevenlabs"
                    ? "border-primary-600"
                    : "border-gray-400"
                }`}
              >
                {providers.tts_provider === "elevenlabs" && (
                  <View className="w-3 h-3 rounded-full bg-primary-600" />
                )}
              </View>
              <View style={{ flex: 1 }}>
                <Text className="text-base text-gray-900 dark:text-white">
                  ElevenLabs
                </Text>
                <Text className="text-xs text-gray-500 dark:text-gray-400">
                  Premium-Stimmen, benoetigt ElevenLabs Key. Ohne Key wird Edge-TTS genutzt.
                </Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => updateProvider("tts_provider", "edge-tts")}
              disabled={isSaving}
              className="flex-row items-center"
              accessibilityLabel="Edge-TTS auswaehlen"
            >
              <View
                className={`w-6 h-6 rounded-full border-2 items-center justify-center mr-3 ${
                  providers.tts_provider === "edge-tts"
                    ? "border-primary-600"
                    : "border-gray-400"
                }`}
              >
                {providers.tts_provider === "edge-tts" && (
                  <View className="w-3 h-3 rounded-full bg-primary-600" />
                )}
              </View>
              <View style={{ flex: 1 }}>
                <Text className="text-base text-gray-900 dark:text-white">
                  Edge-TTS (kostenlos)
                </Text>
                <Text className="text-xs text-gray-500 dark:text-gray-400">
                  Kein API Key erforderlich
                </Text>
              </View>
            </TouchableOpacity>
          </Card>

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
