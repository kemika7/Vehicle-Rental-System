import { api } from "./api";
import type {
  RentalCreate,
  RentalDetailResponse,
  RentalFilters,
  RentalResponse,
  RentalUpdate,
} from "@/types";

export async function listRentals(filters?: RentalFilters): Promise<RentalResponse[]> {
  const { data } = await api.get<RentalResponse[]>("/rentals", { params: filters });
  return data;
}

export async function getRental(id: number): Promise<RentalDetailResponse> {
  const { data } = await api.get<RentalDetailResponse>(`/rentals/${id}`);
  return data;
}

export async function createRental(payload: RentalCreate): Promise<RentalResponse> {
  const { data } = await api.post<RentalResponse>("/rentals", payload);
  return data;
}

export async function updateRental(id: number, payload: RentalUpdate): Promise<RentalResponse> {
  const { data } = await api.patch<RentalResponse>(`/rentals/${id}`, payload);
  return data;
}

export async function deleteRental(id: number): Promise<void> {
  await api.delete(`/rentals/${id}`);
}
