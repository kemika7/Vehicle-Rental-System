import { useNavigate } from "react-router-dom";
import { logout } from "@/services/authService";

interface NavbarProps {
  role: string | null;
}

export function Navbar({ role }: NavbarProps) {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header style={styles.header}>
      <div style={styles.brand}>
        <span style={styles.logo}>🚗</span>
        <span style={styles.title}>Vehicle Rental System</span>
      </div>

      <div style={styles.right}>
        {role && (
          <span style={styles.badge}>
            {role.charAt(0).toUpperCase() + role.slice(1)}
          </span>
        )}
        <button style={styles.logoutBtn} onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    height: 56,
    backgroundColor: "#1e293b",
    color: "#f8fafc",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 24px",
    zIndex: 100,
    boxShadow: "0 1px 4px rgba(0,0,0,0.3)",
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: 10,
  },
  logo: {
    fontSize: 22,
  },
  title: {
    fontWeight: 700,
    fontSize: 17,
    letterSpacing: "0.01em",
  },
  right: {
    display: "flex",
    alignItems: "center",
    gap: 14,
  },
  badge: {
    backgroundColor: "#334155",
    color: "#94a3b8",
    fontSize: 12,
    fontWeight: 600,
    padding: "3px 10px",
    borderRadius: 999,
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  logoutBtn: {
    backgroundColor: "transparent",
    border: "1px solid #475569",
    color: "#cbd5e1",
    padding: "6px 14px",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 500,
    transition: "background 0.15s",
  },
};
