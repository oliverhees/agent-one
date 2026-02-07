import React, { useEffect, useRef } from "react";
import { View, Text, Animated } from "react-native";

interface XPBarProps {
  currentXP: number;
  xpForNextLevel: number;
  progressPercent: number;
}

export const XPBar: React.FC<XPBarProps> = ({
  currentXP,
  xpForNextLevel,
  progressPercent,
}) => {
  const animatedWidth = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animatedWidth, {
      toValue: progressPercent,
      duration: 800,
      useNativeDriver: false,
    }).start();
  }, [progressPercent]);

  const widthInterpolation = animatedWidth.interpolate({
    inputRange: [0, 100],
    outputRange: ["0%", "100%"],
    extrapolate: "clamp",
  });

  return (
    <View>
      <View className="flex-row justify-between mb-1">
        <Text className="text-xs text-gray-500 dark:text-gray-400">
          {currentXP} XP
        </Text>
        <Text className="text-xs text-gray-500 dark:text-gray-400">
          {xpForNextLevel} XP
        </Text>
      </View>
      <View className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <Animated.View
          className="h-full bg-primary-500 rounded-full"
          style={{ width: widthInterpolation }}
        />
      </View>
    </View>
  );
};
