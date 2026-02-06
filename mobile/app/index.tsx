import { Redirect } from "expo-router";
import { useAuthStore } from "../stores/authStore";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

export default function Index() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingSpinner message="Lädt..." />;
  }

  // Redirect zu Login oder Chat je nach Auth-Status
  return <Redirect href={isAuthenticated ? "/(tabs)/chat" : "/(auth)/login"} />;
}
