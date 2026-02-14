import React, { useEffect, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  useColorScheme,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { useWellbeingStore } from "../../../stores/wellbeingStore";

const ZONE_COLORS = {
  red: { bg: "#fef2f2", border: "#ef4444", text: "#dc2626", label: "Kritisch" },
  yellow: { bg: "#fffbeb", border: "#f59e0b", text: "#d97706", label: "Achtung" },
  green: { bg: "#f0fdf4", border: "#22c55e", text: "#16a34a", label: "Gut" },
};

const ZONE_COLORS_DARK = {
  red: { bg: "#450a0a", border: "#ef4444", text: "#fca5a5", label: "Kritisch" },
  yellow: { bg: "#451a03", border: "#f59e0b", text: "#fcd34d", label: "Achtung" },
  green: { bg: "#052e16", border: "#22c55e", text: "#86efac", label: "Gut" },
};

const INTERVENTION_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  hyperfocus: "eye-outline",
  procrastination: "trending-down-outline",
  decision_fatigue: "git-branch-outline",
  transition: "swap-horizontal-outline",
  energy_crash: "battery-dead-outline",
  sleep_disruption: "moon-outline",
  social_masking: "happy-outline",
};

export default function WellnessScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const {
    score,
    interventions,
    isLoading,
    fetchScore,
    fetchInterventions,
    dismissIntervention,
    actOnIntervention,
  } = useWellbeingStore();

  useEffect(() => {
    fetchScore();
    fetchInterventions();
  }, []);

  const handleRefresh = useCallback(() => {
    fetchScore();
    fetchInterventions();
  }, [fetchScore, fetchInterventions]);

  if (isLoading && !score) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner />
      </View>
    );
  }

  const zone = score?.zone || "yellow";
  const colors = isDark ? ZONE_COLORS_DARK[zone] : ZONE_COLORS[zone];

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: isDark ? "#030712" : "#f9fafb" }}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={
        <RefreshControl refreshing={isLoading} onRefresh={handleRefresh} />
      }
    >
      {/* Wellbeing Score Card */}
      <Card style={{ marginBottom: 16, borderColor: colors.border, borderWidth: 2 }}>
        <View style={{ alignItems: "center", padding: 20 }}>
          <Text
            style={{
              fontSize: 48,
              fontWeight: "800",
              color: colors.text,
            }}
          >
            {score ? Math.round(score.score) : "—"}
          </Text>
          <Text
            style={{
              fontSize: 14,
              color: isDark ? "#9ca3af" : "#6b7280",
              marginTop: 4,
            }}
          >
            Wellbeing Score
          </Text>
          <View
            style={{
              marginTop: 8,
              paddingHorizontal: 12,
              paddingVertical: 4,
              borderRadius: 12,
              backgroundColor: colors.bg,
            }}
          >
            <Text style={{ color: colors.text, fontWeight: "600", fontSize: 13 }}>
              {colors.label}
            </Text>
          </View>
        </View>

        {/* Component Bars */}
        {score?.components && (
          <View style={{ paddingHorizontal: 16, paddingBottom: 16, gap: 8 }}>
            {Object.entries(score.components)
              .filter(([key]) => key !== "note")
              .map(([key, value]) => (
                <View key={key}>
                  <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 2 }}>
                    <Text style={{ fontSize: 12, color: isDark ? "#9ca3af" : "#6b7280", textTransform: "capitalize" }}>
                      {key === "task_completion" ? "Aufgaben" : key === "streak" ? "Streak" : key === "consistency" ? "Regelmaessigkeit" : key}
                    </Text>
                    <Text style={{ fontSize: 12, color: isDark ? "#d1d5db" : "#374151" }}>
                      {Math.round((value as number) * 100)}%
                    </Text>
                  </View>
                  <View
                    style={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: isDark ? "#374151" : "#e5e7eb",
                    }}
                  >
                    <View
                      style={{
                        height: 6,
                        borderRadius: 3,
                        width: `${Math.round((value as number) * 100)}%`,
                        backgroundColor: colors.border,
                      }}
                    />
                  </View>
                </View>
              ))}
          </View>
        )}
      </Card>

      {/* Interventions */}
      {interventions.length > 0 && (
        <View style={{ marginBottom: 16 }}>
          <Text
            style={{
              fontSize: 18,
              fontWeight: "700",
              color: isDark ? "#f9fafb" : "#111827",
              marginBottom: 12,
            }}
          >
            Guardian Angel
          </Text>
          {interventions.map((intervention) => (
            <Card key={intervention.id} style={{ marginBottom: 8 }}>
              <View style={{ padding: 16 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <Ionicons
                    name={INTERVENTION_ICONS[intervention.type] || "alert-circle-outline"}
                    size={20}
                    color="#f59e0b"
                  />
                  <Text
                    style={{
                      fontSize: 15,
                      fontWeight: "600",
                      color: isDark ? "#f9fafb" : "#111827",
                      flex: 1,
                    }}
                  >
                    {intervention.message}
                  </Text>
                </View>
                <View style={{ flexDirection: "row", gap: 8, marginTop: 8 }}>
                  <TouchableOpacity
                    onPress={() => actOnIntervention(intervention.id)}
                    style={{
                      flex: 1,
                      paddingVertical: 8,
                      borderRadius: 8,
                      backgroundColor: "#0284c7",
                      alignItems: "center",
                    }}
                  >
                    <Text style={{ color: "#fff", fontWeight: "600", fontSize: 13 }}>
                      Annehmen
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => dismissIntervention(intervention.id)}
                    style={{
                      flex: 1,
                      paddingVertical: 8,
                      borderRadius: 8,
                      backgroundColor: isDark ? "#374151" : "#e5e7eb",
                      alignItems: "center",
                    }}
                  >
                    <Text
                      style={{
                        color: isDark ? "#9ca3af" : "#6b7280",
                        fontWeight: "600",
                        fontSize: 13,
                      }}
                    >
                      Spaeter
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            </Card>
          ))}
        </View>
      )}

      {/* Empty State */}
      {interventions.length === 0 && (
        <Card style={{ marginBottom: 16 }}>
          <View style={{ padding: 20, alignItems: "center" }}>
            <Ionicons
              name="shield-checkmark-outline"
              size={40}
              color={isDark ? "#4ade80" : "#16a34a"}
            />
            <Text
              style={{
                fontSize: 15,
                color: isDark ? "#d1d5db" : "#6b7280",
                marginTop: 8,
                textAlign: "center",
              }}
            >
              Alles im gruenen Bereich! Keine Interventionen noetig.
            </Text>
          </View>
        </Card>
      )}
    </ScrollView>
  );
}
