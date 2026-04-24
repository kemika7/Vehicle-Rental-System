export type VehicleType = "sedan" | "suv" | "van" | "truck" | "hatchback";
export type VehicleStatus = "available" | "rented" | "maintenance";

export interface VehicleResponse {
  id: number;
  plate_number: string;
  vehicle_type: VehicleType;
  capacity: number;
  status: VehicleStatus;
  office_id: number;
}

export interface VehicleCreate {
  plate_number: string;
  vehicle_type: VehicleType;
  capacity: number;
  office_id: number;
}

export interface VehicleUpdate {
  plate_number?: string;
  vehicle_type?: VehicleType;
  capacity?: number;
  status?: VehicleStatus;
  office_id?: number;
}

export interface VehicleFilters {
  office_id?: number;
  vehicle_type?: VehicleType;
  min_capacity?: number;
  max_capacity?: number;
  available_from?: string; // ISO-8601
  available_until?: string;
  status?: VehicleStatus;
}
