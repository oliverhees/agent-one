import React from "react";
import { View, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../ui/Card";

interface QuoteCardProps {
  quote: string;
}

export const QuoteCard: React.FC<QuoteCardProps> = ({ quote }) => {
  return (
    <Card className="bg-primary-50 dark:bg-primary-900/30">
      <View className="flex-row">
        <Ionicons
          name="chatbubble-ellipses-outline"
          size={20}
          color="#0284c7"
          style={{ marginRight: 10, marginTop: 2 }}
        />
        <Text className="flex-1 text-sm text-primary-800 dark:text-primary-200 italic leading-5">
          "{quote}"
        </Text>
      </View>
    </Card>
  );
};
