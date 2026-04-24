import { api } from "./api";
import type { EmployeeResponse, LoginRequest, RegisterRequest, TokenResponse } from "@/types";

// FastAPI's login endpoint expects application/x-www-form-urlencoded
// (OAuth2PasswordRequestForm), not JSON.
export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const form = new URLSearchParams();
  form.append("username", credentials.username);
  form.append("password", credentials.password);

  const { data } = await api.post<TokenResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  localStorage.setItem("access_token", data.access_token);
  return data;
}

export async function register(payload: RegisterRequest): Promise<EmployeeResponse> {
  const { data } = await api.post<EmployeeResponse>("/auth/register", payload);
  return data;
}

export function logout(): void {
  localStorage.removeItem("access_token");
}

export function getStoredToken(): string | null {
  return localStorage.getItem("access_token");
}

interface TokenPayload {
  sub: string;
  role: string;
  exp: number;
}

// Decode JWT payload without signature verification (client-side only).
// Returns null on any parse error so callers never need try/catch.
export function decodeTokenPayload(token: string): TokenPayload | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    // atob requires standard base64; JWT uses base64url — patch padding + chars.
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(padded)) as TokenPayload;
  } catch {
    return null;
  }
}
