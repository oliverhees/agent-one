import React, { useState, useRef, useCallback } from "react";
import { View, TextInput, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  debounceMs?: number;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  placeholder = "Suchen...",
  debounceMs = 400,
}) => {
  const [value, setValue] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleChange = useCallback(
    (text: string) => {
      setValue(text);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        onSearch(text.trim());
      }, debounceMs);
    },
    [onSearch, debounceMs]
  );

  const handleClear = () => {
    setValue("");
    onSearch("");
  };

  return (
    <View className="flex-row items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2">
      <Ionicons
        name="search-outline"
        size={20}
        color="#9ca3af"
        style={{ marginRight: 8 }}
      />
      <TextInput
        className="flex-1 text-base text-gray-900 dark:text-white"
        placeholder={placeholder}
        placeholderTextColor="#9ca3af"
        value={value}
        onChangeText={handleChange}
        returnKeyType="search"
        accessibilityLabel="Suchfeld"
      />
      {value.length > 0 && (
        <TouchableOpacity onPress={handleClear} accessibilityLabel="Suche loeschen">
          <Ionicons name="close-circle" size={20} color="#9ca3af" />
        </TouchableOpacity>
      )}
    </View>
  );
};
