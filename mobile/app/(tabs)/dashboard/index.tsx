import React, { useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Card } from "../../../components/ui/Card";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { XPBar } from "../../../components/gamification/XPBar";
import { LevelBadge } from "../../../components/gamification/LevelBadge";
import { StreakDisplay } from "../../../components/gamification/StreakDisplay";
import { QuoteCard } from "../../../components/dashboard/QuoteCard";
import { DeadlineWidget } from "../../../components/dashboard/DeadlineWidget";
import { TodayTaskItem } from "../../../components/dashboard/TodayTaskItem";
import { NudgeBanner } from "../../../components/nudges/NudgeBanner";
import { useDashboardSummary } from "../../../hooks/useDashboard";
import { useActiveNudges, useAcknowledgeNudge } from "../../../hooks/useNudges";
import { useCompleteTask } from "../../../hooks/useTasks";
import { useAuthStore } from "../../../stores/authStore";

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Guten Morgen";
  if (hour < 18) return "Guten Nachmittag";
  return "Guten Abend";
}

export default function DashboardScreen() {
  const { user } = useAuthStore();
  const {
    data: summary,
    isLoading,
    isError,
    error,
    refetch,
  } = useDashboardSummary();
  const { data: nudgeData } = useActiveNudges();
  const acknowledgeNudge = useAcknowledgeNudge();
  const completeTask = useCompleteTask();

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleCompleteTask = useCallback(
    (id: string) => {
      completeTask.mutate(id);
    },
    [completeTask]
  );

  const handleAcknowledgeNudge = useCallback(
    (id: string) => {
      acknowledgeNudge.mutate(id);
    },
    [acknowledgeNudge]
  );

  const handleTaskPress = useCallback((id: string) => {
    router.push(`/(tabs)/tasks/${id}`);
  }, []);

  if (isLoading) {
    return <LoadingSpinner message="Dashboard wird geladen..." />;
  }

  if (isError) {
    return (
      <View className="flex-1 items-center justify-center bg-white dark:bg-gray-900 p-6">
        <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
        <Text className="text-red-500 text-center mt-4 text-base">
          Fehler beim Laden des Dashboards
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

  const nudges = nudgeData?.nudges ?? [];
  const displayName = user?.display_name?.split(" ")[0] || "du";

  return (
    <ScrollView
      className="flex-1 bg-gray-50 dark:bg-gray-900"
      refreshControl={
        <RefreshControl
          refreshing={false}
          onRefresh={handleRefresh}
          tintColor="#0284c7"
        />
      }
      contentContainerClassName="pb-8"
    >
      {/* Greeting Header */}
      <View className="px-4 pt-6 pb-2">
        <Text className="text-2xl font-bold text-gray-900 dark:text-white">
          {getGreeting()}, {displayName}!
        </Text>
      </View>

      {/* Motivational Quote */}
      {summary?.motivational_quote && (
        <View className="px-4 mb-3">
          <QuoteCard quote={summary.motivational_quote} />
        </View>
      )}

      {/* Active Nudges */}
      {nudges.length > 0 && (
        <View className="px-4 mb-3">
          {nudges.slice(0, 3).map((nudge) => (
            <NudgeBanner
              key={nudge.id}
              nudge={nudge}
              onAcknowledge={handleAcknowledgeNudge}
              onPress={(n) =>
                n.task_id && router.push(`/(tabs)/tasks/${n.task_id}`)
              }
            />
          ))}
        </View>
      )}

      {/* Gamification Widget */}
      {summary?.gamification && (
        <View className="px-4 mb-3">
          <Card>
            <View className="flex-row items-center justify-between mb-3">
              <View className="flex-row items-center">
                <LevelBadge level={summary.gamification.level} />
                <View className="ml-3">
                  <Text className="text-base font-semibold text-gray-900 dark:text-white">
                    Level {summary.gamification.level}
                  </Text>
                  <Text className="text-xs text-gray-500 dark:text-gray-400">
                    {summary.gamification.total_xp} XP gesamt
                  </Text>
                </View>
              </View>
              <StreakDisplay currentStreak={summary.gamification.streak} />
            </View>
            <XPBar
              currentXP={summary.gamification.total_xp}
              xpForNextLevel={
                summary.gamification.total_xp +
                Math.round(
                  (summary.gamification.total_xp *
                    (100 - summary.gamification.progress_percent)) /
                    Math.max(summary.gamification.progress_percent, 1)
                )
              }
              progressPercent={summary.gamification.progress_percent}
            />
          </Card>
        </View>
      )}

      {/* Next Deadline */}
      {summary?.next_deadline && (
        <View className="px-4 mb-3">
          <DeadlineWidget deadline={summary.next_deadline} />
        </View>
      )}

      {/* Today Tasks */}
      <View className="px-4 mb-3">
        <Card>
          <View className="flex-row items-center justify-between mb-2">
            <Text className="text-base font-semibold text-gray-900 dark:text-white">
              Heutige Aufgaben
            </Text>
            <TouchableOpacity
              onPress={() => router.push("/(tabs)/tasks")}
              accessibilityLabel="Alle Aufgaben anzeigen"
            >
              <Text className="text-sm text-primary-600">Alle anzeigen</Text>
            </TouchableOpacity>
          </View>

          {summary?.today_tasks && summary.today_tasks.length > 0 ? (
            summary.today_tasks.map((task) => (
              <TodayTaskItem
                key={task.id}
                task={task}
                onComplete={handleCompleteTask}
                onPress={handleTaskPress}
              />
            ))
          ) : (
            <View className="items-center py-4">
              <Ionicons
                name="checkmark-done-outline"
                size={32}
                color="#9ca3af"
              />
              <Text className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                Keine Aufgaben fuer heute
              </Text>
            </View>
          )}
        </Card>
      </View>
    </ScrollView>
  );
}
