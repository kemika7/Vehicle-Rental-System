import { type FormEvent, useState } from "react";
import { useVehicles } from "@/hooks/useVehicles";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { createVehicle, deleteVehicle } from "@/services/vehicleService";
import { getErrorMessage } from "@/services/api";
import type { VehicleCreate, VehicleResponse, VehicleType } from "@/types";

// ── Status badge ─────────────────────────────────────────────────────────────

const STATUS_COLOR: Record<string, string> = {
  available: "#22c55e",
  rented: "#f59e0b",
  maintenance: "#ef4444",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLOR[status] ?? "#94a3b8";
  return (
    <span style={{ ...s.badge, backgroundColor: color + "22", color }}>{status}</span>
  );
}

// ── Create vehicle form (admin only) ─────────────────────────────────────────

const EMPTY_FORM: VehicleCreate = {
  plate_number: "",
  vehicle_type: "sedan",
  capacity: 5,
  office_id: 1,
};

interface CreateFormProps {
  onCreated: () => void;
  onCancel: () => void;
}

function CreateVehicleForm({ onCreated, onCancel }: CreateFormProps) {
  const [form, setForm] = useState<VehicleCreate>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (field: keyof VehicleCreate) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const val = e.target.type === "number" ? Number(e.target.value) : e.target.value;
      setForm((prev) => ({ ...prev, [field]: val }));
    };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createVehicle(form);
      setForm(EMPTY_FORM);
      onCreated();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={s.createForm}>
      <div style={s.formRow}>
        <label style={s.label}>
          Plate number
          <input
            required
            value={form.plate_number}
            onChange={set("plate_number")}
            placeholder="ABC-123"
            style={s.input}
          />
        </label>
        <label style={s.label}>
          Type
          <select value={form.vehicle_type} onChange={set("vehicle_type")} style={s.input}>
            {(["sedan", "suv", "van", "truck", "hatchback"] as VehicleType[]).map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>
        <label style={s.label}>
          Capacity
          <input type="number" min={1} max={100} value={form.capacity} onChange={set("capacity")} style={s.input} />
        </label>
        <label style={s.label}>
          Office ID
          <input type="number" min={1} value={form.office_id} onChange={set("office_id")} style={s.input} />
        </label>
      </div>
      {error && <p style={s.errMsg}>{error}</p>}
      <div style={{ display: "flex", gap: 10 }}>
        <button type="submit" disabled={saving} style={s.btnPrimary}>
          {saving ? "Saving…" : "Add vehicle"}
        </button>
        <button type="button" onClick={onCancel} style={s.btnGhost}>Cancel</button>
      </div>
    </form>
  );
}

// ── Table row ─────────────────────────────────────────────────────────────────

interface RowProps {
  vehicle: VehicleResponse;
  isAdmin: boolean;
  onDelete: (id: number) => void;
}

function VehicleRow({ vehicle: v, isAdmin, onDelete }: RowProps) {
  return (
    <tr>
      <td style={s.td}>{v.id}</td>
      <td style={s.td}><code style={s.plate}>{v.plate_number}</code></td>
      <td style={s.td}>{v.vehicle_type}</td>
      <td style={s.td}>{v.capacity}</td>
      <td style={s.td}><StatusBadge status={v.status} /></td>
      <td style={s.td}>{v.office_id}</td>
      {isAdmin && (
        <td style={s.td}>
          <button
            style={s.btnDanger}
            onClick={() => onDelete(v.id)}
            title="Delete vehicle"
          >
            Delete
          </button>
        </td>
      )}
    </tr>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function VehiclesPage() {
  const user = useCurrentUser();
  const { vehicles, loading, error, refetch } = useVehicles();
  const [showForm, setShowForm] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDelete = async (id: number) => {
    if (!window.confirm(`Delete vehicle #${id}? This cannot be undone.`)) return;
    setDeleteError(null);
    try {
      await deleteVehicle(id);
      refetch();
    } catch (err) {
      setDeleteError(getErrorMessage(err));
    }
  };

  const isAdmin = user?.isAdmin ?? false;

  return (
    <div>
      {/* ── Header ── */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h2 style={s.heading}>Vehicles</h2>
          <p style={s.sub}>{vehicles.length} vehicle{vehicles.length !== 1 ? "s" : ""} in fleet</p>
        </div>
        {isAdmin && !showForm && (
          <button style={s.btnPrimary} onClick={() => setShowForm(true)}>
            + New vehicle
          </button>
        )}
      </div>

      {/* ── Create form (admin only) ── */}
      {isAdmin && showForm && (
        <CreateVehicleForm
          onCreated={() => { setShowForm(false); refetch(); }}
          onCancel={() => setShowForm(false)}
        />
      )}

      {/* ── Errors ── */}
      {(error || deleteError) && (
        <p style={{ ...s.sub, color: "#f87171", marginBottom: 16 }}>{error ?? deleteError}</p>
      )}

      {/* ── Table ── */}
      {loading ? (
        <p style={s.sub}>Loading…</p>
      ) : (
        <div style={s.tableWrap}>
          <table style={s.table}>
            <thead>
              <tr>
                {["ID", "Plate", "Type", "Capacity", "Status", "Office", ...(isAdmin ? ["Actions"] : [])].map(
                  (h) => <th key={h} style={s.th}>{h}</th>
                )}
              </tr>
            </thead>
            <tbody>
              {vehicles.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? 7 : 6} style={{ ...s.td, textAlign: "center", color: "#64748b" }}>
                    No vehicles found.
                  </td>
                </tr>
              ) : (
                vehicles.map((v) => (
                  <VehicleRow key={v.id} vehicle={v} isAdmin={isAdmin} onDelete={handleDelete} />
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const s: Record<string, React.CSSProperties> = {
  heading: { margin: "0 0 6px", fontSize: 24, fontWeight: 700, color: "#f1f5f9" },
  sub: { margin: 0, color: "#94a3b8", fontSize: 14 },
  tableWrap: { backgroundColor: "#1e293b", borderRadius: 10, border: "1px solid #334155", overflow: "hidden" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 14 },
  th: { padding: "12px 16px", textAlign: "left", color: "#64748b", fontWeight: 600, fontSize: 12, textTransform: "uppercase", letterSpacing: "0.06em", borderBottom: "1px solid #334155" },
  td: { padding: "12px 16px", color: "#cbd5e1", borderBottom: "1px solid #1e293b" },
  plate: { backgroundColor: "#0f172a", padding: "2px 8px", borderRadius: 4, fontSize: 12, fontFamily: "monospace", color: "#7dd3fc" },
  badge: { padding: "3px 10px", borderRadius: 999, fontSize: 12, fontWeight: 600 },
  createForm: {
    backgroundColor: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 10,
    padding: 20,
    marginBottom: 24,
  },
  formRow: { display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 14 },
  label: { display: "flex", flexDirection: "column", gap: 5, fontSize: 13, fontWeight: 500, color: "#cbd5e1", flex: "1 1 160px" },
  input: { backgroundColor: "#0f172a", border: "1px solid #334155", borderRadius: 6, padding: "8px 10px", color: "#f1f5f9", fontSize: 14 },
  errMsg: { margin: "0 0 12px", color: "#f87171", fontSize: 13 },
  btnPrimary: { backgroundColor: "#3b82f6", color: "#fff", border: "none", borderRadius: 6, padding: "8px 18px", fontSize: 13, fontWeight: 600, cursor: "pointer" },
  btnGhost: { backgroundColor: "transparent", color: "#94a3b8", border: "1px solid #334155", borderRadius: 6, padding: "8px 18px", fontSize: 13, cursor: "pointer" },
  btnDanger: { backgroundColor: "transparent", color: "#f87171", border: "1px solid #7f1d1d", borderRadius: 5, padding: "4px 10px", fontSize: 12, cursor: "pointer" },
};
