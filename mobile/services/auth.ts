import api from "./api";
import {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  TokenRefreshResponse,
  User,
} from "../types/auth";

export const login = async (
  credentials: LoginRequest
): Promise<AuthResponse> => {
  const response = await api.post<AuthResponse>("/auth/login", credentials);
  return response.data;
};

export const register = async (
  data: RegisterRequest
): Promise<AuthResponse> => {
  const response = await api.post<AuthResponse>("/auth/register", data);
  return response.data;
};

export const refreshToken = async (
  refresh_token: string
): Promise<TokenRefreshResponse> => {
  const response = await api.post<TokenRefreshResponse>("/auth/refresh", {
    refresh_token,
  });
  return response.data;
};

export const logout = async (): Promise<void> => {
  // Optional: Backend call to invalidate token
  // await api.post("/auth/logout");
};

export const getMe = async (): Promise<User> => {
  const response = await api.get<User>("/auth/me");
  return response.data;
};
