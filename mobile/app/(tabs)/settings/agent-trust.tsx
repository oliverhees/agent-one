import React, { useEffect, useState } from "react";
import { View, Text, ScrollView, TouchableOpacity, RefreshControl } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Card } from "../../../components/ui/Card";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { useTrustStore } from "../../../stores/trustStore";
import { TrustScore } from "../../../services/agents";

interface AgentGroup {
  agentType: string;
  displayName: string;
  scores: TrustScore[];
  currentLevel: number;
  successRate: number;
  totalActions: number;
  successfulActions: number;
}

const TRUST_LEVELS = [
  { level: 1, label: "Basis", description: "Volle Kontrolle", color: "yellow-500" },
  { level: 2, label: "Erweitert", description: "Teilweise autonom", color: "green-500" },
  { level: 3, label: "Autonom", description: "Volle Autonomie", color: "blue-500" },
];

const formatAgentName = (agentType: string): string => {
  return agentType
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

export default function AgentTrustScreen() {
  const { scores, fetchScores, setLevel } = useTrustStore();
  const [refreshing, setRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const loadScores = async () => {
    setIsLoading(true);
    await fetchScores();
    setIsLoading(false);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchScores();
    setRefreshing(false);
  };

  useEffect(() => {
    loadScores();
  }, []);

  const groupedAgents: AgentGroup[] = React.useMemo(() => {
    const groups = new Map<string, TrustScore[]>();

    scores.forEach((score) => {
      if (!groups.has(score.agent_type)) {
        groups.set(score.agent_type, []);
      }
      groups.get(score.agent_type)!.push(score);
    });

    return Array.from(groups.entries()).map(([agentType, agentScores]) => {
      const totalActions = agentScores.reduce((sum, s) => sum + s.total_actions, 0);
      const successfulActions = agentScores.reduce((sum, s) => sum + s.successful_actions, 0);
      const successRate = totalActions > 0 ? (successfulActions / totalActions) * 100 : 0;
      const currentLevel = agentScores[0]?.trust_level || 1;

      return {
        agentType,
        displayName: formatAgentName(agentType),
        scores: agentScores,
        currentLevel,
        successRate,
        totalActions,
        successfulActions,
      };
    });
  }, [scores]);

  const handleSetLevel = async (agentType: string, level: number) => {
    try {
      await setLevel(agentType, level);
    } catch (error) {
      console.error("Failed to set trust level:", error);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Trust Scores werden geladen..." />;
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
        <Text className="text-xl font-bold text-gray-900 dark:text-white flex-1">
          Agent Vertrauen
        </Text>
      </View>

      <ScrollView
        className="flex-1"
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#0284c7"
          />
        }
      >
        <View className="p-6">
          {groupedAgents.length === 0 ? (
            <View className="items-center justify-center py-12">
              <Ionicons
                name="shield-outline"
                size={64}
                color="#9ca3af"
                style={{ marginBottom: 16 }}
              />
              <Text className="text-gray-500 dark:text-gray-400 text-lg text-center">
                Noch keine Agent-Aktivitaet
              </Text>
              <Text className="text-gray-400 dark:text-gray-500 text-sm text-center mt-2">
                Trust Scores werden angezeigt, sobald Agents Aktionen durchfuehren
              </Text>
            </View>
          ) : (
            groupedAgents.map((agent) => (
              <Card key={agent.agentType} className="mb-4">
                {/* Agent Header */}
                <View className="flex-row items-center mb-3">
                  <Ionicons
                    name="shield-checkmark"
                    size={24}
                    color="#0284c7"
                    style={{ marginRight: 10 }}
                  />
                  <Text className="text-lg font-semibold text-gray-900 dark:text-white flex-1">
                    {agent.displayName}
                  </Text>
                </View>

                {/* Trust Level Buttons */}
                <View className="mb-3">
                  <Text className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                    Vertrauensstufe
                  </Text>
                  <View className="flex-row gap-2">
                    {TRUST_LEVELS.map((trustLevel) => {
                      const isActive = agent.currentLevel === trustLevel.level;
                      const colorClass = isActive
                        ? `bg-${trustLevel.color}`
                        : "bg-gray-200 dark:bg-gray-700";

                      return (
                        <TouchableOpacity
                          key={trustLevel.level}
                          onPress={() => handleSetLevel(agent.agentType, trustLevel.level)}
                          className={`flex-1 px-3 py-2 rounded-lg ${
                            isActive
                              ? trustLevel.color === "yellow-500"
                                ? "bg-yellow-500"
                                : trustLevel.color === "green-500"
                                ? "bg-green-500"
                                : "bg-blue-500"
                              : "bg-gray-200 dark:bg-gray-700"
                          }`}
                          accessibilityLabel={`Trust Level ${trustLevel.level}: ${trustLevel.label}`}
                        >
                          <View className="items-center">
                            <Text
                              className={`font-semibold text-xs ${
                                isActive ? "text-white" : "text-gray-600 dark:text-gray-400"
                              }`}
                            >
                              {trustLevel.label}
                            </Text>
                            <Text
                              className={`text-xs mt-0.5 ${
                                isActive ? "text-white opacity-90" : "text-gray-500 dark:text-gray-500"
                              }`}
                            >
                              L{trustLevel.level}
                            </Text>
                          </View>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </View>

                {/* Stats */}
                <View className="border-t border-gray-100 dark:border-gray-700 pt-3">
                  <View className="flex-row items-center justify-between mb-2">
                    <Text className="text-sm text-gray-600 dark:text-gray-400">
                      Erfolgsrate
                    </Text>
                    <Text className="text-sm font-semibold text-gray-900 dark:text-white">
                      {agent.successRate.toFixed(1)}%
                    </Text>
                  </View>

                  {/* Progress Bar */}
                  <View className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-2">
                    <View
                      className="h-full bg-green-500 rounded-full"
                      style={{ width: `${agent.successRate}%` }}
                    />
                  </View>

                  <Text className="text-xs text-gray-500 dark:text-gray-500">
                    {agent.successfulActions} von {agent.totalActions} Aktionen erfolgreich
                  </Text>
                </View>

                {/* Info Box */}
                <View className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <View className="flex-row items-start">
                    <Ionicons
                      name="information-circle"
                      size={16}
                      color="#0284c7"
                      style={{ marginRight: 6, marginTop: 2 }}
                    />
                    <Text className="flex-1 text-xs text-blue-700 dark:text-blue-300">
                      {agent.currentLevel === 1 &&
                        "Bei Level 1 muessen alle Aktionen manuell genehmigt werden."}
                      {agent.currentLevel === 2 &&
                        "Bei Level 2 darf der Agent einfache Aktionen selbststaendig ausfuehren."}
                      {agent.currentLevel === 3 &&
                        "Bei Level 3 arbeitet der Agent vollstaendig autonom."}
                    </Text>
                  </View>
                </View>
              </Card>
            ))
          )}

          {/* Info Card */}
          <Card className="bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20">
            <View className="flex-row items-start">
              <Ionicons
                name="shield-checkmark-outline"
                size={24}
                color="#0284c7"
                style={{ marginRight: 12 }}
              />
              <View className="flex-1">
                <Text className="font-semibold text-gray-900 dark:text-white mb-2">
                  Ueber Trust Levels
                </Text>
                <Text className="text-sm text-gray-700 dark:text-gray-300 leading-5">
                  Trust Levels bestimmen, wie selbststaendig ein Agent arbeiten darf.
                  Agents koennen automatisch hochgestuft werden, wenn sie zuverlaessig
                  arbeiten. Sie koennen jederzeit manuell angepasst werden.
                </Text>
              </View>
            </View>
          </Card>
        </View>
      </ScrollView>
    </View>
  );
}
