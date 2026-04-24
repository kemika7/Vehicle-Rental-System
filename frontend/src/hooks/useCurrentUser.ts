import { decodeTokenPayload, getStoredToken } from "@/services/authService";
import type { Role } from "@/types";

export interface CurrentUser {
  employeeId: number;
  role: Role;
  isAdmin: boolean;
}

// Pure synchronous read from localStorage — no router dependency.
// Returns null when there is no valid, unexpired token.
export function useCurrentUser(): CurrentUser | null {
  const token = getStoredToken();
  if (!token) return null;

  const payload = decodeTokenPayload(token);
  if (!payload || payload.exp * 1000 < Date.now()) {
    localStorage.removeItem("access_token");
    return null;
  }

  return {
    employeeId: Number(payload.sub),
    role: payload.role as Role,
    isAdmin: payload.role === "admin",
  };
}
