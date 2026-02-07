import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  Switch,
  TouchableOpacity,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import Slider from "@react-native-community/slider";
import { Card } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { useADHSSettings, useUpdateADHSSettings } from "../../../hooks/useSettings";
import { ADHSSettings, NudgeIntensity } from "../../../types/settings";

const INTENSITY_OPTIONS: { value: NudgeIntensity; label: string }[] = [
  { value: "low", label: "Niedrig" },
  { value: "medium", label: "Mittel" },
  { value: "high", label: "Hoch" },
];

export default function ADHSSettingsScreen() {
  const { data: settings, isLoading, isError, error, refetch } = useADHSSettings();
  const updateSettings = useUpdateADHSSettings();

  const [form, setForm] = useState<ADHSSettings>({
    adhs_mode: false,
    nudge_intensity: "medium",
    auto_breakdown: true,
    gamification_enabled: true,
    focus_timer_minutes: 25,
    quiet_hours_start: "22:00",
    quiet_hours_end: "08:00",
    preferred_reminder_times: ["09:00", "13:00", "18:00"],
  });

  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (settings) {
      setForm(settings);
      setHasChanges(false);
    }
  }, [settings]);

  const updateField = <K extends keyof ADHSSettings>(
    key: K,
    value: ADHSSettings[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    updateSettings.mutate(form, {
      onSuccess: () => {
        setHasChanges(false);
        Alert.alert("Gespeichert", "ADHS-Einstellungen wurden aktualisiert.");
      },
      onError: (err) => {
        Alert.alert(
          "Fehler",
          err.message || "Einstellungen konnten nicht gespeichert werden."
        );
      },
    });
  };

  const removeReminderTime = (index: number) => {
    const updated = form.preferred_reminder_times.filter(
      (_, i) => i !== index
    );
    updateField("preferred_reminder_times", updated);
  };

  const addReminderTime = () => {
    if (form.preferred_reminder_times.length >= 10) {
      Alert.alert("Maximum", "Maximal 10 Erinnerungszeiten moeglich.");
      return;
    }
    const newTimes = [...form.preferred_reminder_times, "12:00"];
    updateField("preferred_reminder_times", newTimes);
  };

  if (isLoading) {
    return <LoadingSpinner message="Einstellungen werden geladen..." />;
  }

  if (isError) {
    return (
      <View className="flex-1 items-center justify-center bg-white dark:bg-gray-900 p-6">
        <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
        <Text className="text-red-500 text-center mt-4 text-base">
          Fehler beim Laden der Einstellungen
        </Text>
        <Text className="text-gray-400 text-center mt-1 text-sm">
          {error?.message}
        </Text>
        <TouchableOpacity
          onPress={() => refetch()}
          className="mt-4 px-4 py-2 bg-primary-600 rounded-lg"
        >
          <Text className="text-white font-medium">Erneut versuchen</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View className="flex-1 bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <View className="flex-row items-center px-4 pt-4 pb-2">
        <TouchableOpacity
          onPress={() => router.back()}
          className="p-2 mr-2"
          accessibilityLabel="Zurueck"
        >
          <Ionicons name="arrow-back" size={24} color="#0284c7" />
        </TouchableOpacity>
        <Text className="text-xl font-bold text-gray-900 dark:text-white">
          ADHS-Einstellungen
        </Text>
      </View>

      <ScrollView className="flex-1 px-4" contentContainerClassName="pb-8">
        {/* ADHS Mode Toggle */}
        <Card className="mb-3">
          <View className="flex-row items-center justify-between">
            <View className="flex-1 mr-3">
              <Text className="text-base font-semibold text-gray-900 dark:text-white">
                ADHS-Modus
              </Text>
              <Text className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                Aktiviert Nudges, Task-Breakdown und Gamification
              </Text>
            </View>
            <Switch
              value={form.adhs_mode}
              onValueChange={(v) => updateField("adhs_mode", v)}
              trackColor={{ false: "#e5e7eb", true: "#0284c7" }}
              thumbColor="#ffffff"
            />
          </View>
        </Card>

        {/* Nudge Intensity */}
        <Card className="mb-3">
          <Text className="text-base font-semibold text-gray-900 dark:text-white mb-3">
            Nudge-Intensitaet
          </Text>
          <View className="flex-row rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
            {INTENSITY_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.value}
                onPress={() => updateField("nudge_intensity", option.value)}
                className={`flex-1 py-2.5 items-center ${
                  form.nudge_intensity === option.value
                    ? "bg-primary-600"
                    : "bg-white dark:bg-gray-800"
                }`}
                accessibilityLabel={`Nudge-Intensitaet: ${option.label}`}
              >
                <Text
                  className={`text-sm font-medium ${
                    form.nudge_intensity === option.value
                      ? "text-white"
                      : "text-gray-600 dark:text-gray-300"
                  }`}
                >
                  {option.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </Card>

        {/* Auto Breakdown Toggle */}
        <Card className="mb-3">
          <View className="flex-row items-center justify-between">
            <View className="flex-1 mr-3">
              <Text className="text-base font-semibold text-gray-900 dark:text-white">
                Auto Task-Breakdown
              </Text>
              <Text className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                Grosse Aufgaben automatisch aufteilen
              </Text>
            </View>
            <Switch
              value={form.auto_breakdown}
              onValueChange={(v) => updateField("auto_breakdown", v)}
              trackColor={{ false: "#e5e7eb", true: "#0284c7" }}
              thumbColor="#ffffff"
            />
          </View>
        </Card>

        {/* Gamification Toggle */}
        <Card className="mb-3">
          <View className="flex-row items-center justify-between">
            <View className="flex-1 mr-3">
              <Text className="text-base font-semibold text-gray-900 dark:text-white">
                Gamification
              </Text>
              <Text className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                XP, Level und Achievements anzeigen
              </Text>
            </View>
            <Switch
              value={form.gamification_enabled}
              onValueChange={(v) => updateField("gamification_enabled", v)}
              trackColor={{ false: "#e5e7eb", true: "#0284c7" }}
              thumbColor="#ffffff"
            />
          </View>
        </Card>

        {/* Focus Timer */}
        <Card className="mb-3">
          <Text className="text-base font-semibold text-gray-900 dark:text-white mb-1">
            Fokus-Timer
          </Text>
          <Text className="text-sm text-gray-500 dark:text-gray-400 mb-3">
            Standard-Dauer: {form.focus_timer_minutes} Minuten
          </Text>
          <Slider
            minimumValue={5}
            maximumValue={60}
            step={5}
            value={form.focus_timer_minutes}
            onValueChange={(v) => updateField("focus_timer_minutes", v)}
            minimumTrackTintColor="#0284c7"
            maximumTrackTintColor="#e5e7eb"
            thumbTintColor="#0284c7"
          />
          <View className="flex-row justify-between mt-1">
            <Text className="text-xs text-gray-400">5 min</Text>
            <Text className="text-xs text-gray-400">60 min</Text>
          </View>
        </Card>

        {/* Quiet Hours */}
        <Card className="mb-3">
          <Text className="text-base font-semibold text-gray-900 dark:text-white mb-3">
            Ruhezeiten
          </Text>
          <Text className="text-sm text-gray-500 dark:text-gray-400 mb-3">
            Keine Nudges in dieser Zeit
          </Text>
          <View className="flex-row items-center gap-3">
            <View className="flex-1">
              <Text className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                Von
              </Text>
              <View className="bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2.5 items-center">
                <Text className="text-base font-medium text-gray-900 dark:text-white">
                  {form.quiet_hours_start}
                </Text>
              </View>
            </View>
            <Ionicons
              name="arrow-forward"
              size={16}
              color="#9ca3af"
              style={{ marginTop: 14 }}
            />
            <View className="flex-1">
              <Text className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                Bis
              </Text>
              <View className="bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2.5 items-center">
                <Text className="text-base font-medium text-gray-900 dark:text-white">
                  {form.quiet_hours_end}
                </Text>
              </View>
            </View>
          </View>
        </Card>

        {/* Reminder Times */}
        <Card className="mb-3">
          <Text className="text-base font-semibold text-gray-900 dark:text-white mb-3">
            Erinnerungszeiten
          </Text>
          <View className="flex-row flex-wrap gap-2 mb-3">
            {form.preferred_reminder_times.map((time, index) => (
              <View
                key={`${time}-${index}`}
                className="flex-row items-center bg-primary-100 dark:bg-primary-900/30 rounded-full px-3 py-1.5"
              >
                <Text className="text-sm text-primary-700 dark:text-primary-300 mr-1">
                  {time}
                </Text>
                <TouchableOpacity
                  onPress={() => removeReminderTime(index)}
                  accessibilityLabel={`${time} entfernen`}
                >
                  <Ionicons name="close-circle" size={16} color="#0284c7" />
                </TouchableOpacity>
              </View>
            ))}
          </View>
          <TouchableOpacity
            onPress={addReminderTime}
            className="flex-row items-center"
          >
            <Ionicons name="add-circle-outline" size={20} color="#0284c7" />
            <Text className="text-sm text-primary-600 ml-1">
              Zeit hinzufuegen
            </Text>
          </TouchableOpacity>
        </Card>

        {/* Save Button */}
        <Button
          title="Speichern"
          onPress={handleSave}
          isLoading={updateSettings.isPending}
          disabled={!hasChanges}
        />
      </ScrollView>
    </View>
  );
}
