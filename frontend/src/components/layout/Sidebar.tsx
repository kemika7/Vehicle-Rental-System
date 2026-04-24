import { NavLink } from "react-router-dom";
import { useCurrentUser } from "@/hooks/useCurrentUser";

interface NavItem {
  to: string;
  label: string;
  icon: string;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
  { to: "/vehicles", label: "Vehicles", icon: "🚗" },
  { to: "/rentals", label: "Rentals", icon: "📋" },
  { to: "/booking", label: "Book a vehicle", icon: "➕" },
];

export function Sidebar() {
  const user = useCurrentUser();
  const isAdmin = user?.isAdmin ?? false;
  const items = NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin);

  return (
    <aside style={styles.sidebar}>
      <nav>
        <ul style={styles.list}>
          {items.map(({ to, label, icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                style={({ isActive }) => ({
                  ...styles.link,
                  ...(isActive ? styles.linkActive : {}),
                })}
              >
                <span style={styles.icon}>{icon}</span>
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Role indicator at the bottom */}
      {user && (
        <div style={styles.roleTag}>
          <span style={styles.roleLabel}>
            {isAdmin ? "🔑 Admin" : "👤 Employee"}
          </span>
          <span style={styles.employeeId}>ID #{user.employeeId}</span>
        </div>
      )}
    </aside>
  );
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    position: "fixed",
    top: 56,
    left: 0,
    bottom: 0,
    width: 220,
    backgroundColor: "#0f172a",
    borderRight: "1px solid #1e293b",
    overflowY: "auto",
    padding: "16px 0",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
  },
  list: { listStyle: "none", margin: 0, padding: 0 },
  link: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "10px 20px",
    color: "#94a3b8",
    textDecoration: "none",
    fontSize: 14,
    fontWeight: 500,
    borderLeft: "3px solid transparent",
    transition: "background 0.15s, color 0.15s",
  },
  linkActive: {
    color: "#f1f5f9",
    backgroundColor: "#1e293b",
    borderLeftColor: "#3b82f6",
  },
  icon: { fontSize: 17, width: 22, textAlign: "center" },
  roleTag: {
    padding: "14px 20px",
    borderTop: "1px solid #1e293b",
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  roleLabel: { fontSize: 13, fontWeight: 600, color: "#cbd5e1" },
  employeeId: { fontSize: 12, color: "#475569" },
};
