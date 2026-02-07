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
  elevenlabs: string | null;
  deepgram: string | null;
  system_anthropic_active: boolean;
}

export default function ApiKeysScreen() {
  const [keys, setKeys] = useState<ApiKeys>({
    anthropic: null,
    elevenlabs: null,
    deepgram: null,
    system_anthropic_active: false,
  });
  const [inputValues, setInputValues] = useState({
    anthropic: "",
    elevenlabs: "",
    deepgram: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      const response = await api.get<ApiKeys>("/api/v1/settings/api-keys");
      setKeys(response.data);
      setIsLoading(false);
    } catch (error) {
      console.error("Failed to load API keys:", error);
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload: Partial<Record<keyof ApiKeys, string>> = {};

      // Only send keys that were changed/entered
      if (inputValues.anthropic.trim()) {
        payload.anthropic = inputValues.anthropic.trim();
      }
      if (inputValues.elevenlabs.trim()) {
        payload.elevenlabs = inputValues.elevenlabs.trim();
      }
      if (inputValues.deepgram.trim()) {
        payload.deepgram = inputValues.deepgram.trim();
      }

      await api.put("/api/v1/settings/api-keys", payload);

      // Reload to get masked keys
      await loadApiKeys();

      // Clear input fields
      setInputValues({
        anthropic: "",
        elevenlabs: "",
        deepgram: "",
      });

      // Show success message
      setSuccessMessage("Gespeichert!");
      setTimeout(() => setSuccessMessage(""), 2000);
    } catch (error) {
      console.error("Failed to save API keys:", error);
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

          {/* ElevenLabs Card */}
          <Card className="mb-4">
            <View className="flex-row items-center mb-3">
              <Ionicons
                name="mic-outline"
                size={24}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                ElevenLabs
              </Text>
            </View>
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
            <View className="flex-row items-center mb-3">
              <Ionicons
                name="ear-outline"
                size={24}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                Deepgram
              </Text>
            </View>
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
