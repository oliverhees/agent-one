import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  useColorScheme,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Switch,
} from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import api from "../services/api";
import { modulesApi } from "../services/modules";
import { useOnboardingStore } from "../stores/onboardingStore";

type OnboardingStep = "welcome" | "modules" | "name" | "settings" | "complete";

const FOCUS_TIMER_OPTIONS = [
  { value: 15, label: "15 Min" },
  { value: 25, label: "25 Min" },
  { value: 45, label: "45 Min" },
  { value: 60, label: "60 Min" },
];

const NUDGE_INTENSITY_OPTIONS = [
  { value: "low", label: "Sanft", icon: "volume-low" as const },
  { value: "medium", label: "Moderat", icon: "volume-medium" as const },
  { value: "high", label: "Bestimmt", icon: "volume-high" as const },
];

const MODULE_OPTIONS = [
  {
    name: "adhs",
    label: "ADHS-Coaching",
    icon: "bulb-outline" as const,
    description: "Pattern-Erkennung, Nudges, Task-Breakdown und Gamification",
  },
  {
    name: "wellness",
    label: "Wellness & Guardian Angel",
    icon: "heart-outline" as const,
    description: "Wellbeing-Score, Energie-Tracking und proaktive Interventionen",
  },
  {
    name: "productivity",
    label: "Produktivitaet & Planung",
    icon: "calendar-outline" as const,
    description: "Morning Briefing, adaptive Tagesplanung",
  },
];

export default function OnboardingScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";

  const [step, setStep] = useState<OnboardingStep>("welcome");
  const [displayName, setDisplayName] = useState("");
  const [focusTimerMinutes, setFocusTimerMinutes] = useState(25);
  const [nudgeIntensity, setNudgeIntensity] = useState<"low" | "medium" | "high">("medium");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModules, setSelectedModules] = useState<string[]>(["adhs"]);

  const markOnboardingComplete = useOnboardingStore(
    (s) => s.markOnboardingComplete
  );

  const handleCompleteOnboarding = async () => {
    setIsLoading(true);
    try {
      await modulesApi.updateModules(["core", ...selectedModules]);
      await api.post("/settings/onboarding", {
        display_name: displayName.trim() || null,
        focus_timer_minutes: focusTimerMinutes,
        nudge_intensity: nudgeIntensity,
      });
    } catch (error) {
      console.error("Onboarding failed:", error);
    } finally {
      setIsLoading(false);
    }

    // Mark complete in store BEFORE navigating (prevents redirect loop)
    markOnboardingComplete();
    router.replace("/(tabs)/chat");
  };

  const renderWelcome = () => (
    <View className="flex-1 items-center justify-center px-8">
      <Image
        source={require("../assets/alice-avatar.png")}
        style={{
          width: 120,
          height: 120,
          borderRadius: 60,
          borderWidth: 3,
          borderColor: "#0284c7",
          marginBottom: 32,
        }}
      />
      <Text
        className={`text-4xl font-bold mb-4 ${
          isDark ? "text-white" : "text-gray-900"
        }`}
      >
        Hallo! Ich bin ALICE
      </Text>
      <Text
        className={`text-lg text-center mb-8 ${
          isDark ? "text-gray-300" : "text-gray-600"
        }`}
      >
        Dein persönlicher ADHS-Coach. Lass uns gemeinsam starten!
      </Text>
      <TouchableOpacity
        onPress={() => setStep("modules")}
        className="bg-primary-600 px-8 py-4 rounded-lg w-full max-w-xs"
      >
        <Text className="text-white text-center text-lg font-semibold">
          Weiter
        </Text>
      </TouchableOpacity>
    </View>
  );

  const toggleModule = (moduleName: string) => {
    setSelectedModules((prev) =>
      prev.includes(moduleName)
        ? prev.filter((m) => m !== moduleName)
        : [...prev, moduleName]
    );
  };

  const renderModules = () => (
    <ScrollView
      className="flex-1 px-8 pt-12"
      contentContainerStyle={{ paddingBottom: 40 }}
      showsVerticalScrollIndicator={false}
    >
      <Text
        className={`text-3xl font-bold mb-2 text-center ${
          isDark ? "text-white" : "text-gray-900"
        }`}
      >
        Was soll Alice fuer dich tun?
      </Text>
      <Text
        className={`text-base text-center mb-8 ${
          isDark ? "text-gray-400" : "text-gray-500"
        }`}
      >
        Du kannst Module jederzeit in den Einstellungen aendern.
      </Text>

      {MODULE_OPTIONS.map((mod) => {
        const isActive = selectedModules.includes(mod.name);
        return (
          <TouchableOpacity
            key={mod.name}
            onPress={() => toggleModule(mod.name)}
            className={`flex-row items-center px-4 py-4 rounded-lg mb-3 border-2 ${
              isActive
                ? "border-primary-600 bg-primary-600/10"
                : isDark
                ? "bg-gray-800 border-gray-700"
                : "bg-white border-gray-300"
            }`}
          >
            <Ionicons
              name={mod.icon}
              size={28}
              color={isActive ? "#0284c7" : isDark ? "#9ca3af" : "#6b7280"}
              style={{ marginRight: 12 }}
            />
            <View className="flex-1 mr-3">
              <Text
                className={`text-lg font-bold ${
                  isDark ? "text-white" : "text-gray-900"
                }`}
              >
                {mod.label}
              </Text>
              <Text
                className={`text-sm ${
                  isDark ? "text-gray-400" : "text-gray-500"
                }`}
              >
                {mod.description}
              </Text>
            </View>
            <Switch
              value={isActive}
              onValueChange={() => toggleModule(mod.name)}
              trackColor={{ false: "#767577", true: "#0284c7" }}
              thumbColor={isActive ? "#ffffff" : "#f4f3f4"}
            />
          </TouchableOpacity>
        );
      })}

      <TouchableOpacity
        onPress={() => setStep("name")}
        className="bg-primary-600 px-8 py-4 rounded-lg mt-4"
      >
        <Text className="text-white text-center text-lg font-semibold">
          Weiter
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );

  const renderName = () => (
    <View className="flex-1 items-center justify-center px-8">
      <Text
        className={`text-3xl font-bold mb-8 ${
          isDark ? "text-white" : "text-gray-900"
        }`}
      >
        Wie heißt du?
      </Text>
      <TextInput
        value={displayName}
        onChangeText={setDisplayName}
        placeholder="Dein Name (optional)"
        placeholderTextColor={isDark ? "#9ca3af" : "#6b7280"}
        className={`w-full max-w-xs px-4 py-3 rounded-lg mb-6 text-lg ${
          isDark
            ? "bg-gray-800 text-white border border-gray-700"
            : "bg-white text-gray-900 border border-gray-300"
        }`}
        autoFocus
        returnKeyType="next"
        onSubmitEditing={() => setStep("settings")}
      />
      <TouchableOpacity
        onPress={() => setStep("settings")}
        disabled={displayName.trim().length === 0}
        className={`px-8 py-4 rounded-lg w-full max-w-xs mb-4 ${
          displayName.trim().length > 0
            ? "bg-primary-600"
            : "bg-gray-400 opacity-50"
        }`}
      >
        <Text className="text-white text-center text-lg font-semibold">
          Weiter
        </Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => setStep("settings")}>
        <Text className="text-primary-600 text-center">Überspringen</Text>
      </TouchableOpacity>
    </View>
  );

  const renderSettings = () => (
    <ScrollView
      className="flex-1 px-8 pt-12"
      contentContainerStyle={{ paddingBottom: 40 }}
      showsVerticalScrollIndicator={false}
    >
      <Text
        className={`text-3xl font-bold mb-8 text-center ${
          isDark ? "text-white" : "text-gray-900"
        }`}
      >
        Deine Einstellungen
      </Text>

      {/* Focus Timer */}
      <View className="mb-8">
        <Text
          className={`text-lg font-semibold mb-3 ${
            isDark ? "text-white" : "text-gray-900"
          }`}
        >
          Focus-Timer Dauer
        </Text>
        <View className="flex-row gap-3">
          {FOCUS_TIMER_OPTIONS.map((option) => (
            <TouchableOpacity
              key={option.value}
              onPress={() => setFocusTimerMinutes(option.value)}
              className={`flex-1 px-4 py-3 rounded-lg border-2 ${
                focusTimerMinutes === option.value
                  ? "bg-primary-600 border-primary-600"
                  : isDark
                  ? "bg-gray-800 border-gray-700"
                  : "bg-white border-gray-300"
              }`}
            >
              <Text
                className={`text-center font-semibold ${
                  focusTimerMinutes === option.value
                    ? "text-white"
                    : isDark
                    ? "text-gray-300"
                    : "text-gray-700"
                }`}
              >
                {option.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Nudge Intensity */}
      <View className="mb-8">
        <Text
          className={`text-lg font-semibold mb-3 ${
            isDark ? "text-white" : "text-gray-900"
          }`}
        >
          Erinnerungs-Intensität
        </Text>
        {NUDGE_INTENSITY_OPTIONS.map((option) => (
          <TouchableOpacity
            key={option.value}
            onPress={() => setNudgeIntensity(option.value)}
            className={`flex-row items-center px-4 py-4 rounded-lg mb-3 border-2 ${
              nudgeIntensity === option.value
                ? "bg-primary-600 border-primary-600"
                : isDark
                ? "bg-gray-800 border-gray-700"
                : "bg-white border-gray-300"
            }`}
          >
            <Ionicons
              name={option.icon}
              size={24}
              color={
                nudgeIntensity === option.value
                  ? "#ffffff"
                  : isDark
                  ? "#d1d5db"
                  : "#374151"
              }
            />
            <Text
              className={`ml-3 text-lg font-semibold ${
                nudgeIntensity === option.value
                  ? "text-white"
                  : isDark
                  ? "text-gray-300"
                  : "text-gray-700"
              }`}
            >
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity
        onPress={() => setStep("complete")}
        className="bg-primary-600 px-8 py-4 rounded-lg"
      >
        <Text className="text-white text-center text-lg font-semibold">
          Weiter
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );

  const renderComplete = () => (
    <View className="flex-1 items-center justify-center px-8">
      <View className="items-center mb-8">
        <Ionicons
          name="checkmark-circle"
          size={80}
          color="#0284c7"
          style={{ marginBottom: 24 }}
        />
        <Text
          className={`text-3xl font-bold mb-4 text-center ${
            isDark ? "text-white" : "text-gray-900"
          }`}
        >
          {displayName.trim()
            ? `Schön dich kennenzulernen, ${displayName.trim()}!`
            : "Schön, dass du da bist!"}
        </Text>
        <Text
          className={`text-lg text-center ${
            isDark ? "text-gray-300" : "text-gray-600"
          }`}
        >
          Alles ist bereit. Lass uns loslegen!
        </Text>
      </View>
      <TouchableOpacity
        onPress={handleCompleteOnboarding}
        disabled={isLoading}
        className={`px-8 py-4 rounded-lg w-full max-w-xs ${
          isLoading ? "bg-gray-400 opacity-50" : "bg-primary-600"
        }`}
      >
        <Text className="text-white text-center text-lg font-semibold">
          {isLoading ? "Einen Moment..." : "Los geht's!"}
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      className={`flex-1 ${isDark ? "bg-gray-900" : "bg-gray-50"}`}
    >
      {/* Progress Indicator */}
      {step !== "welcome" && (
        <View className="px-8 pt-12 pb-4">
          <View className="flex-row gap-2">
            {["modules", "name", "settings", "complete"].map((s, idx) => {
              const currentIdx = ["modules", "name", "settings", "complete"].indexOf(step);
              const isActive = idx <= currentIdx;
              return (
                <View
                  key={s}
                  className={`flex-1 h-1 rounded ${
                    isActive ? "bg-primary-600" : "bg-gray-300"
                  }`}
                />
              );
            })}
          </View>
        </View>
      )}

      {step === "welcome" && renderWelcome()}
      {step === "modules" && renderModules()}
      {step === "name" && renderName()}
      {step === "settings" && renderSettings()}
      {step === "complete" && renderComplete()}
    </KeyboardAvoidingView>
  );
}
