import React, { useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { EntryCard } from "../../../components/brain/EntryCard";
import { SearchBar } from "../../../components/brain/SearchBar";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { Card } from "../../../components/ui/Card";
import { useBrainEntryList, useBrainSearch } from "../../../hooks/useBrain";
import { BrainEntry } from "../../../types/brain";

export default function BrainScreen() {
  const [searchQuery, setSearchQuery] = useState("");
  const isSearching = searchQuery.length > 0;

  const {
    data: listData,
    isLoading: isListLoading,
    isError: isListError,
    error: listError,
    refetch: refetchList,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useBrainEntryList();

  const {
    data: searchData,
    isLoading: isSearchLoading,
    isError: isSearchError,
  } = useBrainSearch({ q: searchQuery });

  const entries: BrainEntry[] = isSearching
    ? searchData?.results.map((r) => r.entry) ?? []
    : listData?.pages.flatMap((page) => page.items) ?? [];

  const isLoading = isSearching ? isSearchLoading : isListLoading;
  const isError = isSearching ? isSearchError : isListError;

  const handleEndReached = () => {
    if (!isSearching && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  if (isListLoading && !isSearching) {
    return <LoadingSpinner message="Brain wird geladen..." />;
  }

  return (
    <View className="flex-1 bg-gray-50 dark:bg-gray-900">
      {/* Search Bar */}
      <View className="px-4 pt-4 pb-2">
        <SearchBar
          onSearch={setSearchQuery}
          placeholder="Im Brain suchen..."
        />
      </View>

      {/* Search Results Header */}
      {isSearching && searchData && (
        <View className="px-4 pb-2">
          <Text className="text-sm text-gray-500 dark:text-gray-400">
            {searchData.total_results} Ergebnis
            {searchData.total_results !== 1 ? "se" : ""} fuer "{searchQuery}"
          </Text>
        </View>
      )}

      {/* Error State */}
      {isError && (
        <View className="flex-1 items-center justify-center px-6">
          <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
          <Text className="text-red-500 text-center mt-4 text-base">
            Fehler beim Laden
          </Text>
          <TouchableOpacity
            onPress={() => refetchList()}
            className="mt-4 px-4 py-2 bg-primary-600 rounded-lg"
          >
            <Text className="text-white font-medium">Erneut versuchen</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Loading Search */}
      {isSearching && isSearchLoading && (
        <View className="items-center py-8">
          <LoadingSpinner size="small" message="Suche..." />
        </View>
      )}

      {/* Entry List */}
      {!isError && !isLoading && entries.length === 0 ? (
        <View className="flex-1 items-center justify-center px-6">
          <Ionicons name="bulb-outline" size={64} color="#9ca3af" />
          <Text className="text-gray-500 dark:text-gray-400 text-lg mt-4 text-center">
            {isSearching
              ? "Keine Ergebnisse gefunden"
              : "Dein Brain ist noch leer"}
          </Text>
          <Text className="text-gray-400 dark:text-gray-500 text-sm mt-1 text-center">
            {isSearching
              ? "Versuche andere Suchbegriffe"
              : "Speichere Wissen und Notizen hier"}
          </Text>
        </View>
      ) : (
        !isError &&
        !(isSearching && isSearchLoading) && (
          <FlatList
            data={entries}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => <EntryCard entry={item} />}
            contentContainerClassName="px-4 pt-2 pb-24"
            refreshControl={
              !isSearching ? (
                <RefreshControl
                  refreshing={false}
                  onRefresh={() => refetchList()}
                  tintColor="#0284c7"
                />
              ) : undefined
            }
            onEndReached={handleEndReached}
            onEndReachedThreshold={0.5}
          />
        )
      )}

      {/* FAB */}
      <TouchableOpacity
        onPress={() => router.push("/(tabs)/brain/create")}
        className="absolute bottom-6 right-6 w-14 h-14 rounded-full bg-primary-600 items-center justify-center shadow-lg"
        accessibilityLabel="Neuen Eintrag erstellen"
      >
        <Ionicons name="add" size={28} color="#ffffff" />
      </TouchableOpacity>
    </View>
  );
}
