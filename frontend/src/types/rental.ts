import type { VehicleResponse } from "./vehicle";
import type { EmployeeResponse } from "./auth";

export type RentalStatus = "active" | "completed" | "cancelled";

export interface RentalResponse {
  id: number;
  vehicle_id: number;
  employee_id: number;
  start_time: string;
  end_time: string | null;
  status: RentalStatus;
}

// GET /rentals/:id returns nested objects, NOT bare vehicle_id / employee_id.
// The ids are accessible via rental.vehicle.id and rental.employee.id.
export interface RentalDetailResponse {
  id: number;
  start_time: string;
  end_time: string | null;
  status: RentalStatus;
  vehicle: VehicleResponse;
  employee: EmployeeResponse;
}

export interface RentalCreate {
  vehicle_id: number;
  employee_id: number;
  // Always send a timezone-aware ISO-8601 string (append "Z" to datetime-local values).
  start_time: string;
  end_time?: string;
}

export interface RentalUpdate {
  end_time?: string;
  status?: RentalStatus;
}

export interface RentalFilters {
  vehicle_id?: number;
  employee_id?: number;
  office_id?: number;
  status?: RentalStatus;
  active_from?: string;
  active_until?: string;
}
