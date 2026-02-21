// EXPO_PUBLIC_API_URL is set via eas.json env for preview/production builds.
// Falls back to __DEV__ check for local development (expo start).
const apiUrl =
  process.env.EXPO_PUBLIC_API_URL ||
  (__DEV__
    ? "http://192.168.1.164:8000/api/v1"
    : "http://89.167.90.18/api/v1");

export default { apiUrl };
