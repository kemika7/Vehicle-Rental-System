import { getStoredToken } from "@/services/authService";
import { decodeTokenPayload } from "@/services/authService";

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function DashboardPage() {
  const token = getStoredToken();
  const payload = token ? decodeTokenPayload(token) : null;

  const cards = [
    { label: "Total Vehicles", value: "—", icon: "🚗", color: "#3b82f6" },
    { label: "Active Rentals", value: "—", icon: "📋", color: "#22c55e" },
    { label: "Available Now", value: "—", icon: "✅", color: "#a855f7" },
    { label: "Under Maintenance", value: "—", icon: "🔧", color: "#f59e0b" },
  ];

  return (
    <div>
      <div style={styles.pageHeader}>
        <h2 style={styles.heading}>
          {getGreeting()}{payload ? `, Employee #${payload.sub}` : ""}
        </h2>
        <p style={styles.sub}>Here's a summary of your fleet.</p>
      </div>

      <div style={styles.grid}>
        {cards.map(({ label, value, icon, color }) => (
          <div key={label} style={styles.card}>
            <div style={{ ...styles.iconBox, backgroundColor: color + "22", color }}>
              {icon}
            </div>
            <div>
              <p style={styles.cardLabel}>{label}</p>
              <p style={styles.cardValue}>{value}</p>
            </div>
          </div>
        ))}
      </div>

      <p style={styles.note}>
        Navigate to <strong>Vehicles</strong> or <strong>Rentals</strong> using the
        sidebar to manage your fleet.
      </p>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  pageHeader: {
    marginBottom: 32,
  },
  heading: {
    margin: "0 0 6px",
    fontSize: 24,
    fontWeight: 700,
    color: "#f1f5f9",
  },
  sub: {
    margin: 0,
    color: "#94a3b8",
    fontSize: 14,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
    gap: 20,
    marginBottom: 32,
  },
  card: {
    backgroundColor: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 10,
    padding: "20px 24px",
    display: "flex",
    alignItems: "center",
    gap: 16,
  },
  iconBox: {
    width: 46,
    height: 46,
    borderRadius: 10,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 22,
    flexShrink: 0,
  },
  cardLabel: {
    margin: "0 0 4px",
    fontSize: 12,
    color: "#94a3b8",
    fontWeight: 500,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  cardValue: {
    margin: 0,
    fontSize: 24,
    fontWeight: 700,
    color: "#f1f5f9",
  },
  note: {
    color: "#64748b",
    fontSize: 14,
    backgroundColor: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 8,
    padding: "14px 18px",
  },
};
