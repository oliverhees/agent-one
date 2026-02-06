import React from "react";
import { View, Text } from "react-native";

interface TraitSliderProps {
  label: string;
  value: number;
  onValueChange: (value: number) => void;
  minLabel?: string;
  maxLabel?: string;
}

export const TraitSlider: React.FC<TraitSliderProps> = ({
  label,
  value,
  onValueChange,
  minLabel,
  maxLabel,
}) => {
  // Using a simple touchable bar since RN Slider needs separate package
  const steps = [0, 25, 50, 75, 100];

  return (
    <View className="mb-4">
      <View className="flex-row justify-between items-center mb-1">
        <Text className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </Text>
        <Text className="text-sm text-primary-600 dark:text-primary-400 font-semibold">
          {value}
        </Text>
      </View>

      <View className="flex-row items-center h-10">
        {steps.map((step) => (
          <View key={step} className="flex-1 items-center">
            <View
              onTouchEnd={() => onValueChange(step)}
              className={`w-8 h-8 rounded-full items-center justify-center ${
                value >= step
                  ? "bg-primary-600"
                  : "bg-gray-200 dark:bg-gray-700"
              }`}
            >
              <Text
                className={`text-xs font-medium ${
                  value >= step
                    ? "text-white"
                    : "text-gray-500 dark:text-gray-400"
                }`}
              >
                {step}
              </Text>
            </View>
          </View>
        ))}
      </View>

      {(minLabel || maxLabel) && (
        <View className="flex-row justify-between mt-1">
          <Text className="text-xs text-gray-400 dark:text-gray-500">
            {minLabel ?? ""}
          </Text>
          <Text className="text-xs text-gray-400 dark:text-gray-500">
            {maxLabel ?? ""}
          </Text>
        </View>
      )}
    </View>
  );
};
