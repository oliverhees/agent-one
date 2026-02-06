import React from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../ui/Card";
import { PersonalityTemplate } from "../../types/personality";

interface TemplateCardProps {
  template: PersonalityTemplate;
  isSelected?: boolean;
  onSelect: (template: PersonalityTemplate) => void;
}

export const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  isSelected = false,
  onSelect,
}) => {
  return (
    <TouchableOpacity onPress={() => onSelect(template)} className="mb-3">
      <Card
        className={`${
          isSelected ? "border-2 border-primary-600" : ""
        }`}
      >
        <View className="flex-row items-start">
          <View className="flex-1">
            <View className="flex-row items-center mb-1">
              <Text className="text-base font-semibold text-gray-900 dark:text-white">
                {template.name}
              </Text>
              {isSelected && (
                <Ionicons
                  name="checkmark-circle"
                  size={18}
                  color="#0284c7"
                  style={{ marginLeft: 6 }}
                />
              )}
            </View>
            <Text
              className="text-sm text-gray-500 dark:text-gray-400 mb-2"
              numberOfLines={2}
            >
              {template.description}
            </Text>
            {template.preview_message && (
              <View className="bg-gray-100 dark:bg-gray-700 rounded-lg p-2 mt-1">
                <Text
                  className="text-xs text-gray-600 dark:text-gray-300 italic"
                  numberOfLines={2}
                >
                  "{template.preview_message}"
                </Text>
              </View>
            )}
          </View>
        </View>
      </Card>
    </TouchableOpacity>
  );
};
