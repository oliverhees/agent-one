import React from "react";
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  TouchableOpacityProps,
} from "react-native";

interface ButtonProps extends TouchableOpacityProps {
  title: string;
  variant?: "primary" | "secondary" | "outline";
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  variant = "primary",
  isLoading = false,
  disabled,
  className,
  ...props
}) => {
  const baseClasses = "px-6 py-3 rounded-lg items-center justify-center";
  const variantClasses = {
    primary: "bg-primary-600",
    secondary: "bg-gray-600",
    outline: "bg-transparent border-2 border-primary-600",
  };

  const textClasses = {
    primary: "text-white font-semibold text-base",
    secondary: "text-white font-semibold text-base",
    outline: "text-primary-600 font-semibold text-base",
  };

  const disabledClasses = disabled || isLoading ? "opacity-50" : "";

  return (
    <TouchableOpacity
      className={`${baseClasses} ${variantClasses[variant]} ${disabledClasses} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <ActivityIndicator
          color={variant === "outline" ? "#0284c7" : "#ffffff"}
        />
      ) : (
        <Text className={textClasses[variant]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};
