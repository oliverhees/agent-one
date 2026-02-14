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
import { usePredictionStore } from "../../../stores/predictionStore";

const PATTERN_LABELS: Record<string, string> = {
  energy_crash: "Energie-Einbruch",
  procrastination: "Prokrastinations-Spirale",
  hyperfocus: "Hyperfokus-Falle",
  decision_fatigue: "Entscheidungsmuedigkeit",
  sleep_disruption: "Schlafproblem",
  social_masking: "Social Masking",
};

const PATTERN_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  energy_crash: "flash-outline",
  procrastination: "hourglass-outline",
  hyperfocus: "eye-outline",
  decision_fatigue: "help-circle-outline",
  sleep_disruption: "moon-outline",
  social_masking: "people-outline",
};

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.8) return "#ef4444"; // red
  if (confidence >= 0.6) return "#f59e0b"; // orange
  return "#10b981"; // green
};

const getConfidenceLabel = (confidence: number): string => {
  if (confidence >= 0.8) return "Hoch";
  if (confidence >= 0.6) return "Mittel";
  return "Niedrig";
};

export default function InsightsScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const {
    activePredictions,
    history,
    isLoading,
    fetchActive,
    fetchHistory,
    resolve,
  } = usePredictionStore();

  useEffect(() => {
    fetchActive();
    fetchHistory();
  }, []);

  const handleRefresh = useCallback(() => {
    fetchActive();
    fetchHistory();
  }, [fetchActive, fetchHistory]);

  const handleResolve = async (id: string, status: "confirmed" | "avoided") => {
    await resolve(id, status);
    await fetchHistory();
  };

  if (isLoading && activePredictions.length === 0 && history.length === 0) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner />
      </View>
    );
  }

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: isDark ? "#030712" : "#f9fafb" }}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={
        <RefreshControl refreshing={isLoading} onRefresh={handleRefresh} />
      }
    >
      {/* Header */}
      <View style={{ marginBottom: 20 }}>
        <Text
          style={{
            fontSize: 24,
            fontWeight: "800",
            color: isDark ? "#f9fafb" : "#111827",
            marginBottom: 4,
          }}
        >
          Pattern Insights
        </Text>
        <Text
          style={{
            fontSize: 14,
            color: isDark ? "#9ca3af" : "#6b7280",
          }}
        >
          KI-Vorhersagen basierend auf deinen Mustern
        </Text>
      </View>

      {/* Active Predictions */}
      {activePredictions.length > 0 && (
        <View style={{ marginBottom: 24 }}>
          <Text
            style={{
              fontSize: 18,
              fontWeight: "700",
              color: isDark ? "#f9fafb" : "#111827",
              marginBottom: 12,
            }}
          >
            Aktive Vorhersagen
          </Text>
          {activePredictions.map((prediction) => {
            const confidenceColor = getConfidenceColor(prediction.confidence);
            const confidenceLabel = getConfidenceLabel(prediction.confidence);
            const patternLabel =
              PATTERN_LABELS[prediction.pattern_type] || prediction.pattern_type;
            const icon =
              PATTERN_ICONS[prediction.pattern_type] || "alert-circle-outline";

            return (
              <Card
                key={prediction.id}
                style={{
                  marginBottom: 12,
                  borderLeftWidth: 4,
                  borderLeftColor: confidenceColor,
                }}
              >
                <View style={{ padding: 16 }}>
                  {/* Header with Icon and Pattern Type */}
                  <View
                    style={{
                      flexDirection: "row",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: 8,
                    }}
                  >
                    <View style={{ flexDirection: "row", alignItems: "center", gap: 8, flex: 1 }}>
                      <Ionicons
                        name={icon}
                        size={24}
                        color={confidenceColor}
                      />
                      <Text
                        style={{
                          fontSize: 16,
                          fontWeight: "700",
                          color: isDark ? "#f9fafb" : "#111827",
                          flex: 1,
                        }}
                      >
                        {patternLabel}
                      </Text>
                    </View>
                    <View
                      style={{
                        paddingHorizontal: 10,
                        paddingVertical: 4,
                        borderRadius: 12,
                        backgroundColor: `${confidenceColor}20`,
                      }}
                    >
                      <Text
                        style={{
                          color: confidenceColor,
                          fontWeight: "700",
                          fontSize: 12,
                        }}
                      >
                        {confidenceLabel}
                      </Text>
                    </View>
                  </View>

                  {/* Confidence Score */}
                  <View style={{ marginBottom: 8 }}>
                    <Text
                      style={{
                        fontSize: 13,
                        color: isDark ? "#9ca3af" : "#6b7280",
                        marginBottom: 4,
                      }}
                    >
                      Konfidenz: {Math.round(prediction.confidence * 100)}%
                    </Text>
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
                          width: `${Math.round(prediction.confidence * 100)}%`,
                          backgroundColor: confidenceColor,
                        }}
                      />
                    </View>
                  </View>

                  {/* Time Horizon */}
                  <View
                    style={{
                      flexDirection: "row",
                      alignItems: "center",
                      gap: 4,
                      marginBottom: 8,
                    }}
                  >
                    <Ionicons
                      name="time-outline"
                      size={14}
                      color={isDark ? "#9ca3af" : "#6b7280"}
                    />
                    <Text
                      style={{
                        fontSize: 13,
                        color: isDark ? "#9ca3af" : "#6b7280",
                      }}
                    >
                      {prediction.time_horizon}
                    </Text>
                  </View>

                  {/* Trigger Factors */}
                  {prediction.trigger_factors &&
                    Object.keys(prediction.trigger_factors).length > 0 && (
                      <View
                        style={{
                          marginBottom: 12,
                          padding: 10,
                          borderRadius: 8,
                          backgroundColor: isDark ? "#1f2937" : "#f3f4f6",
                        }}
                      >
                        <Text
                          style={{
                            fontSize: 12,
                            fontWeight: "600",
                            color: isDark ? "#d1d5db" : "#374151",
                            marginBottom: 4,
                          }}
                        >
                          Ausloeser:
                        </Text>
                        <Text
                          style={{
                            fontSize: 12,
                            color: isDark ? "#9ca3af" : "#6b7280",
                          }}
                        >
                          {Object.entries(prediction.trigger_factors)
                            .slice(0, 3)
                            .map(([key, value]) => `${key}: ${value}`)
                            .join(" • ")}
                        </Text>
                      </View>
                    )}

                  {/* Action Buttons */}
                  <View style={{ flexDirection: "row", gap: 8 }}>
                    <TouchableOpacity
                      onPress={() => handleResolve(prediction.id, "confirmed")}
                      style={{
                        flex: 1,
                        paddingVertical: 10,
                        borderRadius: 8,
                        backgroundColor: "#ef4444",
                        alignItems: "center",
                      }}
                    >
                      <Text
                        style={{ color: "#fff", fontWeight: "600", fontSize: 13 }}
                      >
                        Eingetreten
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      onPress={() => handleResolve(prediction.id, "avoided")}
                      style={{
                        flex: 1,
                        paddingVertical: 10,
                        borderRadius: 8,
                        backgroundColor: "#10b981",
                        alignItems: "center",
                      }}
                    >
                      <Text
                        style={{ color: "#fff", fontWeight: "600", fontSize: 13 }}
                      >
                        Vermieden
                      </Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </Card>
            );
          })}
        </View>
      )}

      {/* History Section */}
      {history.length > 0 && (
        <View style={{ marginBottom: 16 }}>
          <Text
            style={{
              fontSize: 18,
              fontWeight: "700",
              color: isDark ? "#f9fafb" : "#111827",
              marginBottom: 12,
            }}
          >
            Verlauf
          </Text>
          {history.map((prediction) => {
            const patternLabel =
              PATTERN_LABELS[prediction.pattern_type] || prediction.pattern_type;
            const icon =
              PATTERN_ICONS[prediction.pattern_type] || "alert-circle-outline";
            const isConfirmed = prediction.status === "confirmed";

            return (
              <Card
                key={prediction.id}
                style={{
                  marginBottom: 8,
                  opacity: 0.8,
                }}
              >
                <View style={{ padding: 12 }}>
                  <View
                    style={{
                      flexDirection: "row",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <Ionicons
                      name={icon}
                      size={20}
                      color={isDark ? "#9ca3af" : "#6b7280"}
                    />
                    <Text
                      style={{
                        fontSize: 14,
                        fontWeight: "600",
                        color: isDark ? "#d1d5db" : "#374151",
                        flex: 1,
                      }}
                    >
                      {patternLabel}
                    </Text>
                    <View
                      style={{
                        paddingHorizontal: 8,
                        paddingVertical: 3,
                        borderRadius: 10,
                        backgroundColor: isConfirmed
                          ? "#fef2f2"
                          : "#f0fdf4",
                      }}
                    >
                      <Text
                        style={{
                          color: isConfirmed ? "#dc2626" : "#16a34a",
                          fontWeight: "600",
                          fontSize: 11,
                        }}
                      >
                        {isConfirmed ? "Eingetreten" : "Vermieden"}
                      </Text>
                    </View>
                  </View>
                </View>
              </Card>
            );
          })}
        </View>
      )}

      {/* Empty State */}
      {activePredictions.length === 0 && history.length === 0 && (
        <Card style={{ marginBottom: 16 }}>
          <View style={{ padding: 32, alignItems: "center" }}>
            <Ionicons
              name="analytics-outline"
              size={48}
              color={isDark ? "#4b5563" : "#9ca3af"}
            />
            <Text
              style={{
                fontSize: 16,
                fontWeight: "600",
                color: isDark ? "#d1d5db" : "#374151",
                marginTop: 12,
                textAlign: "center",
              }}
            >
              Noch keine Vorhersagen
            </Text>
            <Text
              style={{
                fontSize: 14,
                color: isDark ? "#9ca3af" : "#6b7280",
                marginTop: 8,
                textAlign: "center",
              }}
            >
              Nutze Alice regelmaessig, damit sie deine Muster erkennen kann.
            </Text>
          </View>
        </Card>
      )}
    </ScrollView>
  );
}
