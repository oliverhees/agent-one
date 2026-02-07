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

export default function VoiceProvidersScreen() {
  const [providers, setProviders] = useState<VoiceProviders>({
    stt_provider: "deepgram",
    tts_provider: "elevenlabs",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      const response = await api.get<VoiceProviders>(
        "/api/v1/settings/voice-providers"
      );
      setProviders(response.data);
      setIsLoading(false);
    } catch (error) {
      console.error("Failed to load voice providers:", error);
      setIsLoading(false);
    }
  };

  const updateProvider = async (
    key: keyof VoiceProviders,
    value: string
  ) => {
    setIsSaving(true);
    try {
      await api.put("/api/v1/settings/voice-providers", {
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
              <Text className="text-base text-gray-900 dark:text-white">
                Deepgram
              </Text>
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
              <Text className="text-base text-gray-900 dark:text-white">
                Whisper
              </Text>
            </TouchableOpacity>
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
              <Text className="text-base text-gray-900 dark:text-white">
                ElevenLabs
              </Text>
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
              <Text className="text-base text-gray-900 dark:text-white">
                Edge-TTS (kostenlos)
              </Text>
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
