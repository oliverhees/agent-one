import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import config from "../constants/config";
import { getSecure, setSecure, STORAGE_KEYS } from "../utils/storage";

const api = axios.create({
  baseURL: config.apiUrl,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Attach access token
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await getSecure(STORAGE_KEYS.ACCESS_TOKEN);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle 401 and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Skip refresh for auth endpoints (they handle their own auth)
    const isAuthEndpoint = originalRequest.url?.includes('/auth/login') ||
                           originalRequest.url?.includes('/auth/register') ||
                           originalRequest.url?.includes('/auth/refresh');

    // Wenn 401 und noch nicht retried und kein Auth-Endpoint
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      try {
        const refreshTokenValue = await getSecure(STORAGE_KEYS.REFRESH_TOKEN);
        if (!refreshTokenValue) {
          throw new Error("No refresh token available");
        }

        // Refresh token (inline to avoid circular import with auth.ts)
        const response = await axios.post(`${config.apiUrl}/auth/refresh`, {
          refresh_token: refreshTokenValue,
        });

        // Update stored tokens
        await setSecure(STORAGE_KEYS.ACCESS_TOKEN, response.data.access_token);
        await setSecure(STORAGE_KEYS.REFRESH_TOKEN, response.data.refresh_token);

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh fehlgeschlagen → Logout
        // (wird im authStore behandelt)
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
