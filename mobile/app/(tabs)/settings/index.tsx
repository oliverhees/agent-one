import React, { useEffect } from "react";
import { View, Text, ScrollView, TouchableOpacity, Switch } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { useAuthStore } from "../../../stores/authStore";
import { useModuleStore } from "../../../stores/moduleStore";
import { router } from "expo-router";

export default function SettingsScreen() {
  const { user, logout, isLoading } = useAuthStore();
  const { availableModules, activeModules, updateModules, fetchModules } =
    useModuleStore();

  useEffect(() => {
    fetchModules();
  }, []);

  const toggleModule = (moduleName: string) => {
    const newModules = activeModules.includes(moduleName)
      ? activeModules.filter((m) => m !== moduleName)
      : [...activeModules, moduleName];
    updateModules(newModules);
  };

  const handleLogout = async () => {
    await logout();
    router.replace("/(auth)/login");
  };

  return (
    <ScrollView className="flex-1 bg-gray-50 dark:bg-gray-900">
      <View className="p-6">
        <Card className="mb-4">
          <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Meine Module
          </Text>
          {availableModules.map((mod) => (
            <View
              key={mod.name}
              className="flex-row items-center justify-between py-3 border-b border-gray-100 dark:border-gray-800 last:border-0"
            >
              <View className="flex-row items-center flex-1">
                <Ionicons
                  name={mod.icon as any}
                  size={22}
                  color={mod.active ? "#0284c7" : "#9ca3af"}
                  style={{ marginRight: 10 }}
                />
                <View className="flex-1">
                  <Text className="font-semibold text-gray-900 dark:text-white">
                    {mod.label}
                  </Text>
                  {mod.name === "core" && (
                    <Text className="text-xs text-gray-400">Immer aktiv</Text>
                  )}
                </View>
              </View>
              <Switch
                value={mod.active}
                onValueChange={() => toggleModule(mod.name)}
                disabled={mod.name === "core"}
                trackColor={{ false: "#767577", true: "#0284c7" }}
                thumbColor="#ffffff"
              />
            </View>
          ))}
        </Card>

        <Card className="mb-4">
          <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Benutzerprofil
          </Text>
          <Text className="text-gray-600 dark:text-gray-400 mb-1">
            Name: {user?.display_name}
          </Text>
          <Text className="text-gray-600 dark:text-gray-400">
            E-Mail: {user?.email}
          </Text>
        </Card>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/personality")}
          accessibilityLabel="Persoenlichkeit anpassen"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="sparkles-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    Persoenlichkeit
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    ALICEs Verhalten anpassen
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/adhs")}
          accessibilityLabel="ADHS-Einstellungen"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="flash-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    ADHS-Einstellungen
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    Nudges, Timer und Gamification
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/achievements")}
          accessibilityLabel="Achievements anzeigen"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="trophy-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    Achievements
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    Abzeichen und Fortschritt
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/api-keys")}
          accessibilityLabel="API Keys verwalten"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="key-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    API Keys
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    Eigene API-Schluessel verwalten
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/ai-provider")}
          accessibilityLabel="KI-Modell auswaehlen"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="hardware-chip-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    KI-Modell
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    Anthropic oder Custom LLM
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/voice-providers")}
          accessibilityLabel="Voice Provider konfigurieren"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="volume-medium-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    Voice Provider
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    Sprach-Provider konfigurieren
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/wake-word")}
          accessibilityLabel="Wake Word konfigurieren"
        >
          <Card className="mb-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-row items-center">
                <Ionicons
                  name="ear-outline"
                  size={20}
                  color="#0284c7"
                  style={{ marginRight: 10 }}
                />
                <View>
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                    Wake Word
                  </Text>
                  <Text className="text-sm text-gray-500 dark:text-gray-400">
                    "Hey Alice" Aktivierung
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
            </View>
          </Card>
        </TouchableOpacity>

        <Card className="mb-4">
          <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Agent-System
          </Text>

          <TouchableOpacity
            onPress={() => router.push("/(tabs)/settings/agent-trust")}
            accessibilityLabel="Agent Vertrauen verwalten"
            className="flex-row items-center justify-between py-3 border-b border-gray-100 dark:border-gray-800"
          >
            <View className="flex-row items-center">
              <Ionicons
                name="shield-checkmark-outline"
                size={20}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <View>
                <Text className="font-semibold text-gray-900 dark:text-white">
                  Vertrauen & Autonomie
                </Text>
                <Text className="text-sm text-gray-500 dark:text-gray-400">
                  Trust Levels der Agents steuern
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => router.push("/(tabs)/settings/agent-approvals")}
            accessibilityLabel="Agent Genehmigungen"
            className="flex-row items-center justify-between py-3 border-b border-gray-100 dark:border-gray-800"
          >
            <View className="flex-row items-center">
              <Ionicons
                name="checkmark-circle-outline"
                size={20}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <View>
                <Text className="font-semibold text-gray-900 dark:text-white">
                  Genehmigungen
                </Text>
                <Text className="text-sm text-gray-500 dark:text-gray-400">
                  Ausstehende Agent-Aktionen pruefen
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => router.push("/(tabs)/settings/email-config")}
            accessibilityLabel="Email Konfiguration"
            className="flex-row items-center justify-between py-3"
          >
            <View className="flex-row items-center">
              <Ionicons
                name="mail-outline"
                size={20}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <View>
                <Text className="font-semibold text-gray-900 dark:text-white">
                  Email-Agent
                </Text>
                <Text className="text-sm text-gray-500 dark:text-gray-400">
                  SMTP/IMAP Konfiguration
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
          </TouchableOpacity>
        </Card>

        <Card className="mb-4">
          <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            App-Version
          </Text>
          <Text className="text-gray-600 dark:text-gray-400">
            Version 1.0.0
          </Text>
        </Card>

        <Button
          title="Abmelden"
          variant="outline"
          onPress={handleLogout}
          isLoading={isLoading}
        />
      </View>
    </ScrollView>
  );
}
