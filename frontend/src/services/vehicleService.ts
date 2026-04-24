import { api } from "./api";
import type {
  VehicleCreate,
  VehicleFilters,
  VehicleResponse,
  VehicleUpdate,
} from "@/types";

export async function listVehicles(filters?: VehicleFilters): Promise<VehicleResponse[]> {
  const { data } = await api.get<VehicleResponse[]>("/vehicles", { params: filters });
  return data;
}

export async function getVehicle(id: number): Promise<VehicleResponse> {
  const { data } = await api.get<VehicleResponse>(`/vehicles/${id}`);
  return data;
}

export async function createVehicle(payload: VehicleCreate): Promise<VehicleResponse> {
  const { data } = await api.post<VehicleResponse>("/vehicles", payload);
  return data;
}

export async function updateVehicle(id: number, payload: VehicleUpdate): Promise<VehicleResponse> {
  const { data } = await api.patch<VehicleResponse>(`/vehicles/${id}`, payload);
  return data;
}

export async function deleteVehicle(id: number): Promise<void> {
  await api.delete(`/vehicles/${id}`);
}
