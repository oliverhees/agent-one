import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Card } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import api from "../../../services/api";

interface ApiKeys {
  anthropic: string | null;
  openai: string | null;
  elevenlabs: string | null;
  deepgram: string | null;
  system_anthropic_active: boolean;
}

interface VoiceProviders {
  stt_provider: "deepgram" | "whisper";
  tts_provider: "elevenlabs" | "edge-tts";
}

export default function ApiKeysScreen() {
  const [keys, setKeys] = useState<ApiKeys>({
    anthropic: null,
    openai: null,
    elevenlabs: null,
    deepgram: null,
    system_anthropic_active: false,
  });
  const [providers, setProviders] = useState<VoiceProviders>({
    stt_provider: "deepgram",
    tts_provider: "elevenlabs",
  });
  const [inputValues, setInputValues] = useState({
    anthropic: "",
    openai: "",
    elevenlabs: "",
    deepgram: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [keysRes, provRes] = await Promise.all([
        api.get<ApiKeys>("/settings/api-keys"),
        api.get<VoiceProviders>("/settings/voice-providers"),
      ]);
      setKeys(keysRes.data);
      setProviders(provRes.data);
    } catch (error) {
      console.error("Failed to load settings:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload: Partial<Record<keyof ApiKeys, string>> = {};

      if (inputValues.anthropic.trim()) {
        payload.anthropic = inputValues.anthropic.trim();
      }
      if (inputValues.openai.trim()) {
        payload.openai = inputValues.openai.trim();
      }
      if (inputValues.elevenlabs.trim()) {
        payload.elevenlabs = inputValues.elevenlabs.trim();
      }
      if (inputValues.deepgram.trim()) {
        payload.deepgram = inputValues.deepgram.trim();
      }

      await api.put("/settings/api-keys", payload);
      await loadData();

      setInputValues({
        anthropic: "",
        openai: "",
        elevenlabs: "",
        deepgram: "",
      });

      setSuccessMessage("Gespeichert!");
      setTimeout(() => setSuccessMessage(""), 2000);
    } catch (error) {
      console.error("Failed to save API keys:", error);
    } finally {
      setIsSaving(false);
    }
  };

  // Helper: active provider badge
  const ActiveBadge = () => (
    <View style={{ backgroundColor: "#dbeafe", paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8, marginLeft: 8 }}>
      <Text style={{ color: "#1d4ed8", fontSize: 11, fontWeight: "600" }}>AKTIV</Text>
    </View>
  );

  // Helper: missing key warning
  const MissingKeyWarning = ({ provider }: { provider: string }) => (
    <View style={{ flexDirection: "row", alignItems: "center", marginTop: 8, backgroundColor: "#fef3c7", paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 }}>
      <Ionicons name="warning" size={16} color="#d97706" style={{ marginRight: 6 }} />
      <Text style={{ color: "#92400e", fontSize: 13, flex: 1 }}>
        {provider} ist als aktiver Provider eingestellt, aber kein Key hinterlegt.
      </Text>
    </View>
  );

  if (isLoading) {
    return (
      <View className="flex-1 bg-gray-50 dark:bg-gray-900 items-center justify-center">
        <ActivityIndicator size="large" color="#0284c7" />
      </View>
    );
  }

  const sttIsWhisper = providers.stt_provider === "whisper";
  const sttIsDeepgram = providers.stt_provider === "deepgram";
  const ttsIsElevenlabs = providers.tts_provider === "elevenlabs";

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
          API Keys
        </Text>
      </View>

      <ScrollView className="flex-1">
        <View className="p-6">
          {/* Anthropic Card */}
          <Card className="mb-4">
            <View className="flex-row items-center mb-3">
              <Ionicons
                name="cloud-outline"
                size={24}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                Anthropic (Claude)
              </Text>
            </View>
            <TextInput
              className="bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-3 rounded-lg"
              placeholder={
                keys.anthropic
                  ? `Gespeichert: ${keys.anthropic}`
                  : "API Key eingeben"
              }
              placeholderTextColor="#9ca3af"
              value={inputValues.anthropic}
              onChangeText={(text) =>
                setInputValues({ ...inputValues, anthropic: text })
              }
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
            />
            {keys.system_anthropic_active && !keys.anthropic && (
              <View className="flex-row items-center mt-2 bg-green-50 dark:bg-green-900/30 px-3 py-2 rounded-lg">
                <Ionicons name="checkmark-circle" size={16} color="#16a34a" style={{ marginRight: 6 }} />
                <Text className="text-green-700 dark:text-green-400 text-sm">
                  System-Key aktiv
                </Text>
              </View>
            )}
          </Card>

          {/* OpenAI Card (for Whisper STT) */}
          <Card className="mb-4">
            <View style={{ flexDirection: "row", alignItems: "center", marginBottom: 12 }}>
              <Ionicons
                name="chatbubble-ellipses-outline"
                size={24}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                OpenAI (Whisper STT)
              </Text>
              {sttIsWhisper && <ActiveBadge />}
            </View>
            <Text className="text-sm text-gray-500 dark:text-gray-400 mb-2">
              Fuer Sprache-zu-Text mit Whisper
            </Text>
            <TextInput
              className="bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-3 rounded-lg"
              placeholder={
                keys.openai
                  ? `Gespeichert: ${keys.openai}`
                  : "API Key eingeben"
              }
              placeholderTextColor="#9ca3af"
              value={inputValues.openai}
              onChangeText={(text) =>
                setInputValues({ ...inputValues, openai: text })
              }
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
            />
            {sttIsWhisper && !keys.openai && !inputValues.openai.trim() && (
              <MissingKeyWarning provider="Whisper" />
            )}
          </Card>

          {/* ElevenLabs Card */}
          <Card className="mb-4">
            <View style={{ flexDirection: "row", alignItems: "center", marginBottom: 12 }}>
              <Ionicons
                name="mic-outline"
                size={24}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                ElevenLabs (TTS)
              </Text>
              {ttsIsElevenlabs && <ActiveBadge />}
            </View>
            <Text className="text-sm text-gray-500 dark:text-gray-400 mb-2">
              Fuer Text-zu-Sprache (Premium-Stimmen). Ohne Key wird Edge-TTS (kostenlos) genutzt.
            </Text>
            <TextInput
              className="bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-3 rounded-lg"
              placeholder={
                keys.elevenlabs
                  ? `Gespeichert: ${keys.elevenlabs}`
                  : "API Key eingeben"
              }
              placeholderTextColor="#9ca3af"
              value={inputValues.elevenlabs}
              onChangeText={(text) =>
                setInputValues({ ...inputValues, elevenlabs: text })
              }
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
            />
          </Card>

          {/* Deepgram Card */}
          <Card className="mb-4">
            <View style={{ flexDirection: "row", alignItems: "center", marginBottom: 12 }}>
              <Ionicons
                name="ear-outline"
                size={24}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                Deepgram (STT)
              </Text>
              {sttIsDeepgram && <ActiveBadge />}
            </View>
            <Text className="text-sm text-gray-500 dark:text-gray-400 mb-2">
              Fuer Sprache-zu-Text (Standard STT Provider)
            </Text>
            <TextInput
              className="bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-3 rounded-lg"
              placeholder={
                keys.deepgram
                  ? `Gespeichert: ${keys.deepgram}`
                  : "API Key eingeben"
              }
              placeholderTextColor="#9ca3af"
              value={inputValues.deepgram}
              onChangeText={(text) =>
                setInputValues({ ...inputValues, deepgram: text })
              }
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
            />
            {sttIsDeepgram && !keys.deepgram && !inputValues.deepgram.trim() && (
              <MissingKeyWarning provider="Deepgram" />
            )}
          </Card>

          {/* Success Message */}
          {successMessage && (
            <Text className="text-green-600 dark:text-green-400 text-center mb-4 font-semibold">
              {successMessage}
            </Text>
          )}

          {/* Save Button */}
          <Button
            title="Speichern"
            onPress={handleSave}
            isLoading={isSaving}
          />
        </View>
      </ScrollView>
    </View>
  );
}
