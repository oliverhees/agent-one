import React from "react";
import { View, Text } from "react-native";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { registerSchema, RegisterFormData } from "../../utils/validation";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { useAuthStore } from "../../stores/authStore";
import { router } from "expo-router";

export const RegisterForm: React.FC = () => {
  const { register, isLoading, error, clearError } = useAuthStore();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    clearError();
    try {
      await register(data.email, data.password, data.display_name);
      router.replace("/(tabs)/chat");
    } catch (error) {
      // Error wird im Store gesetzt
    }
  };

  return (
    <View className="w-full">
      <Controller
        control={control}
        name="display_name"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Name"
            placeholder="Ihr Name"
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            error={errors.display_name?.message}
            autoCapitalize="words"
          />
        )}
      />

      <Controller
        control={control}
        name="email"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="E-Mail"
            placeholder="ihre.email@example.com"
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            error={errors.email?.message}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
          />
        )}
      />

      <Controller
        control={control}
        name="password"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Passwort"
            placeholder="••••••••"
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            error={errors.password?.message}
            secureTextEntry
            autoCapitalize="none"
          />
        )}
      />

      <View className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-4">
        <Text className="text-blue-800 dark:text-blue-200 text-sm font-medium mb-1">
          Passwort-Anforderungen:
        </Text>
        <Text className="text-blue-700 dark:text-blue-300 text-xs">
          • Mindestens 8 Zeichen
        </Text>
        <Text className="text-blue-700 dark:text-blue-300 text-xs">
          • Mindestens ein Großbuchstabe
        </Text>
        <Text className="text-blue-700 dark:text-blue-300 text-xs">
          • Mindestens eine Zahl
        </Text>
      </View>

      {error && (
        <View className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-4">
          <Text className="text-red-600 dark:text-red-400 text-sm">{error}</Text>
        </View>
      )}

      <Button
        title="Registrieren"
        onPress={handleSubmit(onSubmit)}
        isLoading={isLoading}
      />
    </View>
  );
};
