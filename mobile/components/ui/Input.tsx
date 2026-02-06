import React from "react";
import { TextInput, View, Text, TextInputProps } from "react-native";

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  className,
  ...props
}) => {
  return (
    <View className="mb-4">
      {label && (
        <Text className="text-gray-700 dark:text-gray-300 font-medium mb-2">
          {label}
        </Text>
      )}
      <TextInput
        className={`bg-white dark:bg-gray-800 border ${
          error ? "border-red-500" : "border-gray-300 dark:border-gray-700"
        } rounded-lg px-4 py-3 text-gray-900 dark:text-white ${className}`}
        placeholderTextColor="#9ca3af"
        {...props}
      />
      {error && <Text className="text-red-500 text-sm mt-1">{error}</Text>}
    </View>
  );
};
