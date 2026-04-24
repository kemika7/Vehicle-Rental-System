import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  decodeTokenPayload,
  getStoredToken,
  login as apiLogin,
  logout as apiLogout,
} from "@/services/authService";
import type { LoginRequest, Role } from "@/types";

interface AuthState {
  token: string | null;
  employeeId: number | null;
  role: Role | null;
  isAuthenticated: boolean;
}

function buildAuthState(token: string | null): AuthState {
  if (!token) return { token: null, employeeId: null, role: null, isAuthenticated: false };

  const payload = decodeTokenPayload(token);
  if (!payload || payload.exp * 1000 < Date.now()) {
    localStorage.removeItem("access_token");
    return { token: null, employeeId: null, role: null, isAuthenticated: false };
  }

  return {
    token,
    employeeId: Number(payload.sub),
    role: payload.role as Role,
    isAuthenticated: true,
  };
}

export function useAuth() {
  const navigate = useNavigate();
  const [auth, setAuth] = useState<AuthState>(() => buildAuthState(getStoredToken()));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Re-sync state if another tab logs in/out.
  useEffect(() => {
    const handleStorage = () => setAuth(buildAuthState(getStoredToken()));
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      setLoading(true);
      setError(null);
      try {
        const tokenResponse = await apiLogin(credentials);
        setAuth(buildAuthState(tokenResponse.access_token));
        navigate("/dashboard");
      } catch {
        setError("Invalid email or password.");
      } finally {
        setLoading(false);
      }
    },
    [navigate]
  );

  const logout = useCallback(() => {
    apiLogout();
    setAuth({ token: null, employeeId: null, role: null, isAuthenticated: false });
    navigate("/login");
  }, [navigate]);

  return { ...auth, loading, error, login, logout };
}
