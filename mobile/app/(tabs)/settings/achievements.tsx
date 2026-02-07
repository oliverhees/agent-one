import React, { useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  useWindowDimensions,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { AchievementCard } from "../../../components/gamification/AchievementCard";
import { useAchievements } from "../../../hooks/useGamification";
import { Achievement } from "../../../types/gamification";

type CategoryFilter = "all" | "beginner" | "streak" | "tasks" | "brain" | "special";

const CATEGORY_FILTERS: { value: CategoryFilter; label: string }[] = [
  { value: "all", label: "Alle" },
  { value: "beginner", label: "Anfaenger" },
  { value: "tasks", label: "Aufgaben" },
  { value: "streak", label: "Streak" },
  { value: "brain", label: "Brain" },
  { value: "special", label: "Spezial" },
];

export default function AchievementsScreen() {
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("all");
  const { data, isLoading, isError, error, refetch } = useAchievements();
  const { width } = useWindowDimensions();

  const numColumns = 3;
  const padding = 16;
  const gap = 8;
  const itemWidth = (width - padding * 2 - gap * (numColumns - 1)) / numColumns;

  const achievements =
    categoryFilter === "all"
      ? data?.achievements ?? []
      : (data?.achievements ?? []).filter(
          (a) => a.category === categoryFilter
        );

  if (isLoading) {
    return <LoadingSpinner message="Achievements werden geladen..." />;
  }

  if (isError) {
    return (
      <View className="flex-1 items-center justify-center bg-white dark:bg-gray-900 p-6">
        <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
        <Text className="text-red-500 text-center mt-4 text-base">
          Fehler beim Laden der Achievements
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
        <Text className="text-xl font-bold text-gray-900 dark:text-white flex-1">
          Achievements
        </Text>
        {data && (
          <Text className="text-sm text-gray-500 dark:text-gray-400">
            {data.unlocked_count}/{data.total_count}
          </Text>
        )}
      </View>

      {/* Category Filter */}
      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        data={CATEGORY_FILTERS}
        keyExtractor={(item) => item.value}
        contentContainerClassName="px-4 pb-3"
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => setCategoryFilter(item.value)}
            className={`mr-2 px-3 py-1.5 rounded-full ${
              categoryFilter === item.value
                ? "bg-primary-600"
                : "bg-gray-200 dark:bg-gray-700"
            }`}
            accessibilityLabel={`Kategorie: ${item.label}`}
          >
            <Text
              className={`text-sm font-medium ${
                categoryFilter === item.value
                  ? "text-white"
                  : "text-gray-600 dark:text-gray-300"
              }`}
            >
              {item.label}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* Achievement Grid */}
      {achievements.length === 0 ? (
        <View className="flex-1 items-center justify-center px-6">
          <Ionicons name="trophy-outline" size={64} color="#9ca3af" />
          <Text className="text-gray-500 dark:text-gray-400 text-lg mt-4 text-center">
            Keine Achievements in dieser Kategorie
          </Text>
        </View>
      ) : (
        <FlatList
          data={achievements}
          keyExtractor={(item) => item.id}
          numColumns={numColumns}
          contentContainerClassName="px-4 pb-8"
          columnWrapperClassName="gap-2 mb-2"
          renderItem={({ item }) => (
            <View style={{ width: itemWidth }}>
              <AchievementCard achievement={item} />
            </View>
          )}
        />
      )}
    </View>
  );
}
