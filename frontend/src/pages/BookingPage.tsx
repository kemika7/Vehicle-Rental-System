import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useVehicles } from "@/hooks/useVehicles";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { createRental } from "@/services/rentalService";
import { getErrorMessage } from "@/services/api";

// datetime-local inputs return "YYYY-MM-DDTHH:MM" (no timezone).
// Appending ":00Z" makes it a valid UTC ISO-8601 string that FastAPI/Pydantic
// accepts and stores consistently. (Fix #9)
function toUtcIso(localDt: string): string {
  return localDt ? `${localDt}:00Z` : "";
}

// Minimum value for datetime-local (prevents booking in the past).
function nowLocalIso(): string {
  const d = new Date();
  d.setSeconds(0, 0);
  return d.toISOString().slice(0, 16); // "YYYY-MM-DDTHH:MM"
}

export function BookingPage() {
  const navigate = useNavigate();
  const user = useCurrentUser();

  // Only show available vehicles in the selector.
  const { vehicles, loading: vehiclesLoading } = useVehicles({ status: "available" });

  const [vehicleId, setVehicleId] = useState<number | "">("");
  const [startTime, setStartTime] = useState(nowLocalIso());
  const [endTime, setEndTime] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (!user) return null; // ProtectedRoute handles the redirect

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (vehicleId === "") return;

    setSubmitting(true);
    setApiError(null);

    try {
      await createRental({
        vehicle_id: vehicleId,
        employee_id: user.employeeId,
        start_time: toUtcIso(startTime),
        ...(endTime ? { end_time: toUtcIso(endTime) } : {}),
      });
      setSuccess(true);
    } catch (err) {
      setApiError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div style={s.page}>
        <div style={s.successBox}>
          <span style={{ fontSize: 36 }}>✅</span>
          <h3 style={{ margin: "12px 0 6px", color: "#f1f5f9" }}>Booking confirmed!</h3>
          <p style={{ margin: "0 0 20px", color: "#94a3b8", fontSize: 14 }}>
            Your rental has been created successfully.
          </p>
          <div style={{ display: "flex", gap: 12 }}>
            <button style={s.btnPrimary} onClick={() => navigate("/rentals")}>
              View rentals
            </button>
            <button
              style={s.btnGhost}
              onClick={() => { setSuccess(false); setVehicleId(""); setEndTime(""); }}
            >
              Book another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <h2 style={s.heading}>New booking</h2>
        <p style={{ ...s.sub, marginBottom: 28 }}>
          Choose an available vehicle and select your rental window.
        </p>

        <form onSubmit={handleSubmit} style={s.form}>
          {/* Vehicle selector */}
          <label style={s.label}>
            Vehicle
            <select
              required
              value={vehicleId}
              onChange={(e) => setVehicleId(Number(e.target.value))}
              style={s.input}
              disabled={vehiclesLoading}
            >
              <option value="">
                {vehiclesLoading ? "Loading vehicles…" : "— select a vehicle —"}
              </option>
              {vehicles.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.plate_number} · {v.vehicle_type} · {v.capacity} seats · office #{v.office_id}
                </option>
              ))}
            </select>
            {vehicles.length === 0 && !vehiclesLoading && (
              <span style={s.hint}>No vehicles currently available.</span>
            )}
          </label>

          {/* Start time */}
          <label style={s.label}>
            Start time <span style={s.hint}>(your local time, stored as UTC)</span>
            <input
              type="datetime-local"
              required
              value={startTime}
              min={nowLocalIso()}
              onChange={(e) => setStartTime(e.target.value)}
              style={s.input}
            />
          </label>

          {/* End time */}
          <label style={s.label}>
            End time <span style={s.hint}>(optional — leave blank for open-ended)</span>
            <input
              type="datetime-local"
              value={endTime}
              min={startTime}
              onChange={(e) => setEndTime(e.target.value)}
              style={s.input}
            />
          </label>

          {/* Booking details summary */}
          <div style={s.summary}>
            <span>Employee</span>
            <span style={{ color: "#f1f5f9" }}>#{user.employeeId}</span>
            <span>Role</span>
            <span style={{ color: "#f1f5f9" }}>{user.role}</span>
          </div>

          {/* API error from backend (e.g. overlap, cross-office) */}
          {apiError && (
            <div style={s.errorBox}>
              <strong>Booking failed</strong>
              <p style={{ margin: "4px 0 0" }}>{apiError}</p>
            </div>
          )}

          <div style={{ display: "flex", gap: 12 }}>
            <button type="submit" disabled={submitting || vehicleId === ""} style={s.btnPrimary}>
              {submitting ? "Booking…" : "Confirm booking"}
            </button>
            <button type="button" style={s.btnGhost} onClick={() => navigate("/rentals")}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { display: "flex", justifyContent: "center" },
  card: {
    backgroundColor: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 12,
    padding: "36px 40px",
    width: "100%",
    maxWidth: 560,
  },
  successBox: {
    backgroundColor: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 12,
    padding: "48px 40px",
    width: "100%",
    maxWidth: 420,
    textAlign: "center",
  },
  heading: { margin: "0 0 6px", fontSize: 22, fontWeight: 700, color: "#f1f5f9" },
  sub: { margin: 0, color: "#94a3b8", fontSize: 14 },
  form: { display: "flex", flexDirection: "column", gap: 18 },
  label: { display: "flex", flexDirection: "column", gap: 5, fontSize: 13, fontWeight: 500, color: "#cbd5e1" },
  hint: { fontSize: 12, color: "#64748b", fontWeight: 400 },
  input: {
    backgroundColor: "#0f172a",
    border: "1px solid #334155",
    borderRadius: 7,
    padding: "9px 11px",
    color: "#f1f5f9",
    fontSize: 14,
    colorScheme: "dark",
  },
  summary: {
    display: "grid",
    gridTemplateColumns: "max-content 1fr",
    gap: "8px 20px",
    backgroundColor: "#0f172a",
    borderRadius: 8,
    padding: "14px 16px",
    fontSize: 13,
    color: "#64748b",
  },
  errorBox: {
    backgroundColor: "#450a0a",
    border: "1px solid #7f1d1d",
    borderRadius: 8,
    padding: "12px 14px",
    color: "#fca5a5",
    fontSize: 13,
  },
  btnPrimary: { backgroundColor: "#3b82f6", color: "#fff", border: "none", borderRadius: 7, padding: "10px 22px", fontSize: 14, fontWeight: 600, cursor: "pointer" },
  btnGhost: { backgroundColor: "transparent", color: "#94a3b8", border: "1px solid #334155", borderRadius: 7, padding: "10px 22px", fontSize: 14, cursor: "pointer" },
};
