import React, { useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Switch,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import Slider from "@react-native-community/slider";
import { Card } from "../../../components/ui/Card";
import { useWakeWordStore } from "../../../stores/wakeWordStore";

export default function WakeWordScreen() {
  const {
    enabled,
    sensitivity,
    continuousMode,
    isListening,
    modelLoaded,
    setEnabled,
    setSensitivity,
    setContinuousMode,
    loadSettings,
  } = useWakeWordStore();

  useEffect(() => {
    loadSettings();
  }, []);

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
          Wake Word
        </Text>
      </View>

      <ScrollView className="flex-1">
        <View className="p-6">
          {/* Status Card */}
          <Card className="mb-4">
            <View className="flex-row items-center justify-between mb-2">
              <View className="flex-row items-center">
                {isListening ? (
                  <View
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: 5,
                      backgroundColor: "#22c55e",
                      marginRight: 8,
                    }}
                  />
                ) : (
                  <View
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: 5,
                      backgroundColor: "#9ca3af",
                      marginRight: 8,
                    }}
                  />
                )}
                <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                  {isListening ? "Aktiv - Hoert zu..." : "Inaktiv"}
                </Text>
              </View>
            </View>
            <Text className="text-sm text-gray-500 dark:text-gray-400">
              {isListening
                ? 'Sage "Hey Alice" um ein Live-Gespraech zu starten.'
                : "Aktiviere Wake Word Detection um ALICE per Sprache zu wecken."}
            </Text>
          </Card>

          {/* Enable/Disable Card */}
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center flex-1">
                <Ionicons
                  name="ear-outline"
                  size={22}
                  color={enabled ? "#0284c7" : "#9ca3af"}
                  style={{ marginRight: 10 }}
                />
                <View className="flex-1">
                  <Text className="font-semibold text-gray-900 dark:text-white">
                    Wake Word aktivieren
                  </Text>
                  <Text className="text-xs text-gray-500 dark:text-gray-400">
                    "Hey Alice" Erkennung einschalten
                  </Text>
                </View>
              </View>
              <Switch
                value={enabled}
                onValueChange={setEnabled}
                trackColor={{ false: "#767577", true: "#0284c7" }}
                thumbColor="#ffffff"
              />
            </View>
          </Card>

          {/* ONNX Model Status Card */}
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center flex-1">
                <Ionicons
                  name={modelLoaded ? "checkmark-circle" : "alert-circle-outline"}
                  size={22}
                  color={modelLoaded ? "#22c55e" : "#f59e0b"}
                  style={{ marginRight: 10 }}
                />
                <View className="flex-1">
                  <Text className="font-semibold text-gray-900 dark:text-white">
                    ONNX Modelle
                  </Text>
                  <Text className="text-xs text-gray-500 dark:text-gray-400">
                    {modelLoaded
                      ? "Alle Modelle geladen und bereit"
                      : "Modelle werden beim Start geladen"}
                  </Text>
                </View>
              </View>
            </View>
          </Card>

          {/* Sensitivity Card */}
          <Card className="mb-4">
            <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Empfindlichkeit
            </Text>
            <Text className="text-sm text-gray-500 dark:text-gray-400 mb-3">
              Hoehere Empfindlichkeit erkennt leiser gesprochene Wake Words,
              kann aber zu Fehlerkennungen fuehren.
            </Text>
            <View className="flex-row items-center">
              <Text className="text-sm text-gray-500 dark:text-gray-400 w-8">
                0%
              </Text>
              <Slider
                style={{ flex: 1, height: 40 }}
                minimumValue={0}
                maximumValue={1}
                step={0.05}
                value={sensitivity}
                onSlidingComplete={setSensitivity}
                minimumTrackTintColor="#0284c7"
                maximumTrackTintColor="#d1d5db"
                thumbTintColor="#0284c7"
              />
              <Text className="text-sm text-gray-500 dark:text-gray-400 w-10 text-right">
                100%
              </Text>
            </View>
            <Text className="text-center text-base font-semibold text-primary-600 mt-1">
              {Math.round(sensitivity * 100)}%
            </Text>
          </Card>

          {/* Continuous Mode Card */}
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center flex-1">
                <Ionicons
                  name="repeat-outline"
                  size={22}
                  color={continuousMode ? "#0284c7" : "#9ca3af"}
                  style={{ marginRight: 10 }}
                />
                <View className="flex-1">
                  <Text className="font-semibold text-gray-900 dark:text-white">
                    Dauerhaft aktiv
                  </Text>
                  <Text className="text-xs text-gray-500 dark:text-gray-400">
                    Wake Word Detection bleibt nach Erkennung aktiv
                  </Text>
                </View>
              </View>
              <Switch
                value={continuousMode}
                onValueChange={setContinuousMode}
                trackColor={{ false: "#767577", true: "#0284c7" }}
                thumbColor="#ffffff"
              />
            </View>
          </Card>

          {/* Info Card */}
          <Card className="mb-4">
            <View className="flex-row items-start">
              <Ionicons
                name="information-circle-outline"
                size={22}
                color="#0284c7"
                style={{ marginRight: 10, marginTop: 2 }}
              />
              <View className="flex-1">
                <Text className="text-sm text-gray-600 dark:text-gray-400">
                  Powered by openWakeWord (Apache 2.0). Wake Words werden mit
                  openWakeWord trainiert. Die Erkennung laeuft vollstaendig auf
                  dem Geraet - keine Audiodaten werden uebertragen.
                </Text>
              </View>
            </View>
          </Card>
        </View>
      </ScrollView>
    </View>
  );
}
