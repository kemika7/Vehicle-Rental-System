import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

// In dev, Vite proxies /api → http://localhost:8000 to avoid CORS.
// In production, set VITE_API_BASE_URL to your backend origin.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor ───────────────────────────────────────────────────────
// Attach the JWT stored in localStorage to every outgoing request.
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor ──────────────────────────────────────────────────────
// 401 → clear stale token and redirect to /login.
// All other errors are re-thrown so call-site handlers can react.
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      // Avoid importing React Router here — use the native API so this module
      // stays framework-agnostic and testable.
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// Helper that extracts a human-readable message from an Axios error.
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg ?? String(d)).join("; ");
    }
    return error.message;
  }
  return "An unexpected error occurred.";
}
