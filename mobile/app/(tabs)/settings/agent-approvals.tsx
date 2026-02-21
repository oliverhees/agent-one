import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  TextInput,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { useAgentStore } from "../../../stores/agentStore";

const getAgentIcon = (agentType: string): string => {
  const icons: Record<string, string> = {
    email: "mail-outline",
    calendar: "calendar-outline",
    research: "search-outline",
    briefing: "sunny-outline",
  };
  return icons[agentType] || "cube-outline";
};

const getAgentName = (agentType: string): string => {
  const names: Record<string, string> = {
    email: "Email-Agent",
    calendar: "Kalender-Agent",
    research: "Research-Agent",
    briefing: "Briefing-Agent",
  };
  return names[agentType] || agentType;
};

const calculateTimeRemaining = (expiresAt: string | null): string | null => {
  if (!expiresAt) return null;

  const now = new Date();
  const expiry = new Date(expiresAt);
  const diff = expiry.getTime() - now.getTime();

  if (diff <= 0) return "Abgelaufen";

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `Noch ${hours}h ${minutes % 60}min`;
  }
  return `Noch ${minutes} Min`;
};

export default function AgentApprovalsScreen() {
  const { pendingApprovals, isLoading, fetchPendingApprovals, approveAction } =
    useAgentStore();

  const [refreshing, setRefreshing] = useState(false);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  useEffect(() => {
    fetchPendingApprovals();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchPendingApprovals();
    setRefreshing(false);
  };

  const handleApprove = async (id: string) => {
    try {
      await approveAction(id, true);
      Alert.alert("Erfolg", "Aktion wurde genehmigt.");
    } catch (error) {
      Alert.alert("Fehler", "Genehmigung fehlgeschlagen.");
    }
  };

  const handleReject = async (id: string) => {
    try {
      await approveAction(id, false, rejectReason || undefined);
      setRejectingId(null);
      setRejectReason("");
      Alert.alert("Erfolg", "Aktion wurde abgelehnt.");
    } catch (error) {
      Alert.alert("Fehler", "Ablehnung fehlgeschlagen.");
    }
  };

  const startReject = (id: string) => {
    setRejectingId(id);
  };

  const cancelReject = () => {
    setRejectingId(null);
    setRejectReason("");
  };

  if (isLoading && pendingApprovals.length === 0) {
    return <LoadingSpinner message="Lade Genehmigungen..." />;
  }

  return (
    <ScrollView
      className="flex-1 bg-gray-50 dark:bg-gray-900"
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View className="p-6">
        {/* Header */}
        <View className="flex-row items-center justify-between mb-6">
          <Text className="text-2xl font-bold text-gray-900 dark:text-white">
            Genehmigungen
          </Text>
          {pendingApprovals.length > 0 && (
            <View className="bg-sky-600 rounded-full w-8 h-8 items-center justify-center">
              <Text className="text-white font-bold text-sm">
                {pendingApprovals.length}
              </Text>
            </View>
          )}
        </View>

        {/* Empty State */}
        {pendingApprovals.length === 0 ? (
          <Card className="items-center py-8">
            <Ionicons
              name="checkmark-circle-outline"
              size={64}
              color="#22c55e"
              style={{ marginBottom: 16 }}
            />
            <Text className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Keine ausstehenden Genehmigungen
            </Text>
            <Text className="text-sm text-gray-500 dark:text-gray-400 text-center">
              Alle Agent-Aktionen wurden bearbeitet.
            </Text>
          </Card>
        ) : (
          /* Approval List */
          <View className="gap-4">
            {pendingApprovals.map((approval) => {
              const timeRemaining = calculateTimeRemaining(approval.expires_at);
              const isExpired = timeRemaining === "Abgelaufen";
              const isRejecting = rejectingId === approval.id;

              return (
                <Card key={approval.id} className="gap-3">
                  {/* Agent Header */}
                  <View className="flex-row items-center gap-3">
                    <View className="bg-sky-100 dark:bg-sky-900 rounded-full w-10 h-10 items-center justify-center">
                      <Ionicons
                        name={getAgentIcon(approval.agent_type) as any}
                        size={20}
                        color="#0284c7"
                      />
                    </View>
                    <View className="flex-1">
                      <Text className="font-semibold text-gray-900 dark:text-white">
                        {getAgentName(approval.agent_type)}
                      </Text>
                      <Text className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(approval.created_at).toLocaleString("de-DE")}
                      </Text>
                    </View>
                    {timeRemaining && (
                      <View
                        className={`px-2 py-1 rounded ${
                          isExpired
                            ? "bg-red-100 dark:bg-red-900"
                            : "bg-orange-100 dark:bg-orange-900"
                        }`}
                      >
                        <Text
                          className={`text-xs font-medium ${
                            isExpired
                              ? "text-red-700 dark:text-red-300"
                              : "text-orange-700 dark:text-orange-300"
                          }`}
                        >
                          {timeRemaining}
                        </Text>
                      </View>
                    )}
                  </View>

                  {/* Action Description */}
                  <View className="border-t border-gray-100 dark:border-gray-700 pt-3">
                    <Text className="font-bold text-gray-900 dark:text-white mb-2">
                      {approval.action}
                    </Text>

                    {/* Action Details */}
                    {Object.keys(approval.action_details).length > 0 && (
                      <View className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 gap-2">
                        {Object.entries(approval.action_details).map(
                          ([key, value]) => (
                            <View key={key} className="flex-row">
                              <Text className="text-sm text-gray-600 dark:text-gray-400 font-medium min-w-24">
                                {key}:
                              </Text>
                              <Text className="text-sm text-gray-900 dark:text-white flex-1">
                                {String(value)}
                              </Text>
                            </View>
                          )
                        )}
                      </View>
                    )}
                  </View>

                  {/* Reject Reason Input */}
                  {isRejecting && (
                    <View className="border-t border-gray-100 dark:border-gray-700 pt-3 gap-2">
                      <Text className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Grund der Ablehnung (optional):
                      </Text>
                      <TextInput
                        className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-gray-900 dark:text-white"
                        placeholder="z.B. Falscher Empfänger"
                        placeholderTextColor="#9ca3af"
                        value={rejectReason}
                        onChangeText={setRejectReason}
                        multiline
                        numberOfLines={2}
                      />
                    </View>
                  )}

                  {/* Action Buttons */}
                  <View className="flex-row gap-2 border-t border-gray-100 dark:border-gray-700 pt-3">
                    {isRejecting ? (
                      <>
                        <TouchableOpacity
                          onPress={cancelReject}
                          className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-lg py-3 items-center"
                        >
                          <Text className="font-semibold text-gray-700 dark:text-gray-300">
                            Abbrechen
                          </Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          onPress={() => handleReject(approval.id)}
                          className="flex-1 bg-red-600 rounded-lg py-3 items-center"
                        >
                          <Text className="font-semibold text-white">
                            Bestätigen
                          </Text>
                        </TouchableOpacity>
                      </>
                    ) : (
                      <>
                        <TouchableOpacity
                          onPress={() => startReject(approval.id)}
                          className="flex-1 border-2 border-red-600 rounded-lg py-3 items-center"
                          disabled={isExpired}
                        >
                          <Text className="font-semibold text-red-600">
                            Ablehnen
                          </Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          onPress={() => handleApprove(approval.id)}
                          className="flex-1 bg-green-600 rounded-lg py-3 items-center"
                          disabled={isExpired}
                        >
                          <Text className="font-semibold text-white">
                            Genehmigen
                          </Text>
                        </TouchableOpacity>
                      </>
                    )}
                  </View>
                </Card>
              );
            })}
          </View>
        )}
      </View>
    </ScrollView>
  );
}
