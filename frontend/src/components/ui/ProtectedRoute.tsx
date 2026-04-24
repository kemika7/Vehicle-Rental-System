import { Navigate, Outlet } from "react-router-dom";
import { useCurrentUser } from "@/hooks/useCurrentUser";

interface ProtectedRouteProps {
  requireAdmin?: boolean;
}

export function ProtectedRoute({ requireAdmin = false }: ProtectedRouteProps) {
  const user = useCurrentUser();

  if (!user) return <Navigate to="/login" replace />;

  if (requireAdmin && !user.isAdmin) return <Navigate to="/dashboard" replace />;

  return <Outlet />;
}
