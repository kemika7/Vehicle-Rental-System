import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { useCurrentUser } from "@/hooks/useCurrentUser";

export function Layout() {
  const user = useCurrentUser();

  return (
    <div style={styles.root}>
      <Navbar role={user?.role ?? null} />
      <Sidebar />
      <main style={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  root: {
    minHeight: "100vh",
    backgroundColor: "#0f172a",
    color: "#f1f5f9",
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  main: {
    marginLeft: 220,
    marginTop: 56,
    padding: 32,
    minHeight: "calc(100vh - 56px)",
  },
};
