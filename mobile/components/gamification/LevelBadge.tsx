import React from "react";
import { View, Text } from "react-native";

interface LevelBadgeProps {
  level: number;
  size?: "sm" | "md" | "lg";
}

const sizeClasses = {
  sm: { container: "w-8 h-8", text: "text-xs" },
  md: { container: "w-10 h-10", text: "text-sm" },
  lg: { container: "w-14 h-14", text: "text-lg" },
};

export const LevelBadge: React.FC<LevelBadgeProps> = ({
  level,
  size = "md",
}) => {
  const classes = sizeClasses[size];

  return (
    <View
      className={`${classes.container} rounded-full bg-primary-600 items-center justify-center`}
    >
      <Text className={`${classes.text} font-bold text-white`}>{level}</Text>
    </View>
  );
};
