import { Link } from "react-router-dom";
import { useRentals } from "@/hooks/useRentals";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { deleteRental } from "@/services/rentalService";
import { getErrorMessage } from "@/services/api";
import { useState } from "react";
import type { RentalStatus } from "@/types";

const STATUS_COLOR: Record<RentalStatus, string> = {
  active: "#22c55e",
  completed: "#3b82f6",
  cancelled: "#94a3b8",
};

function fmt(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function RentalsPage() {
  const user = useCurrentUser();
  const { rentals, loading, error, refetch } = useRentals();
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const isAdmin = user?.isAdmin ?? false;

  const handleDelete = async (id: number) => {
    if (!window.confirm(`Permanently delete rental #${id}?`)) return;
    setDeleteError(null);
    try {
      await deleteRental(id);
      refetch();
    } catch (err) {
      setDeleteError(getErrorMessage(err));
    }
  };

  return (
    <div>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h2 style={s.heading}>Rentals</h2>
          <p style={s.sub}>{rentals.length} rental{rentals.length !== 1 ? "s" : ""} total</p>
        </div>
        <Link to="/booking" style={s.btnPrimary}>+ New booking</Link>
      </div>

      {(error || deleteError) && (
        <p style={{ ...s.sub, color: "#f87171", marginBottom: 16 }}>{error ?? deleteError}</p>
      )}

      {loading ? (
        <p style={s.sub}>Loading…</p>
      ) : (
        <div style={s.tableWrap}>
          <table style={s.table}>
            <thead>
              <tr>
                {["ID", "Vehicle", "Employee", "Start", "End", "Status", ...(isAdmin ? ["Actions"] : [])].map(
                  (h) => <th key={h} style={s.th}>{h}</th>
                )}
              </tr>
            </thead>
            <tbody>
              {rentals.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? 7 : 6} style={{ ...s.td, textAlign: "center", color: "#64748b" }}>
                    No rentals found.
                  </td>
                </tr>
              ) : (
                rentals.map((r) => (
                  <tr key={r.id}>
                    <td style={s.td}>{r.id}</td>
                    <td style={s.td}>#{r.vehicle_id}</td>
                    <td style={s.td}>#{r.employee_id}</td>
                    <td style={s.td}>{fmt(r.start_time)}</td>
                    <td style={s.td}>{fmt(r.end_time)}</td>
                    <td style={s.td}>
                      <span style={{
                        ...s.badge,
                        backgroundColor: STATUS_COLOR[r.status] + "22",
                        color: STATUS_COLOR[r.status],
                      }}>
                        {r.status}
                      </span>
                    </td>
                    {isAdmin && (
                      <td style={s.td}>
                        <button style={s.btnDanger} onClick={() => handleDelete(r.id)}>
                          Delete
                        </button>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  heading: { margin: "0 0 6px", fontSize: 24, fontWeight: 700, color: "#f1f5f9" },
  sub: { margin: 0, color: "#94a3b8", fontSize: 14 },
  tableWrap: { backgroundColor: "#1e293b", borderRadius: 10, border: "1px solid #334155", overflow: "hidden" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 14 },
  th: { padding: "12px 16px", textAlign: "left", color: "#64748b", fontWeight: 600, fontSize: 12, textTransform: "uppercase", letterSpacing: "0.06em", borderBottom: "1px solid #334155" },
  td: { padding: "12px 16px", color: "#cbd5e1", borderBottom: "1px solid #1e293b" },
  badge: { padding: "3px 10px", borderRadius: 999, fontSize: 12, fontWeight: 600 },
  btnPrimary: { backgroundColor: "#3b82f6", color: "#fff", border: "none", borderRadius: 6, padding: "8px 18px", fontSize: 13, fontWeight: 600, cursor: "pointer", textDecoration: "none", display: "inline-block" },
  btnDanger: { backgroundColor: "transparent", color: "#f87171", border: "1px solid #7f1d1d", borderRadius: 5, padding: "4px 10px", fontSize: 12, cursor: "pointer" },
};
