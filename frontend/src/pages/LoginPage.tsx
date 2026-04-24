import { Navigate } from "react-router-dom";
import { useLoginForm } from "@/hooks/useLoginForm";
import { useCurrentUser } from "@/hooks/useCurrentUser";

export function LoginPage() {
  const user = useCurrentUser();
  const { email, setEmail, password, setPassword, loading, error, handleSubmit } =
    useLoginForm();

  if (user) return <Navigate to="/dashboard" replace />;

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.header}>
          <span style={styles.logo}>🚗</span>
          <h1 style={styles.title}>Vehicle Rental System</h1>
          <p style={styles.subtitle}>Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              autoComplete="email"
              style={styles.input}
            />
          </label>

          <label style={styles.label}>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
              style={styles.input}
            />
          </label>

          {error && <p style={styles.error}>{error}</p>}

          <button type="submit" disabled={loading} style={styles.btn}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    backgroundColor: "#0f172a",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  card: {
    backgroundColor: "#1e293b",
    borderRadius: 12,
    padding: "40px 36px",
    width: "100%",
    maxWidth: 400,
    boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
    border: "1px solid #334155",
  },
  header: { textAlign: "center", marginBottom: 32 },
  logo: { fontSize: 40 },
  title: { margin: "12px 0 6px", fontSize: 20, fontWeight: 700, color: "#f1f5f9" },
  subtitle: { margin: 0, color: "#94a3b8", fontSize: 14 },
  form: { display: "flex", flexDirection: "column", gap: 18 },
  label: { display: "flex", flexDirection: "column", gap: 6, fontSize: 13, fontWeight: 500, color: "#cbd5e1" },
  input: {
    backgroundColor: "#0f172a",
    border: "1px solid #334155",
    borderRadius: 7,
    padding: "10px 12px",
    color: "#f1f5f9",
    fontSize: 14,
    outline: "none",
  },
  error: {
    margin: 0,
    padding: "10px 12px",
    backgroundColor: "#450a0a",
    border: "1px solid #7f1d1d",
    borderRadius: 7,
    color: "#fca5a5",
    fontSize: 13,
  },
  btn: {
    backgroundColor: "#3b82f6",
    color: "#fff",
    border: "none",
    borderRadius: 7,
    padding: "11px 0",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    marginTop: 4,
    opacity: 1,
  },
};
