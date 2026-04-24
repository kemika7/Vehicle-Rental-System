import { useEffect, useRef, useState } from "react";
import { listVehicles } from "@/services/vehicleService";
import { getErrorMessage } from "@/services/api";
import type { VehicleFilters, VehicleResponse } from "@/types";

// Stable JSON key so an identical filter object doesn't trigger a re-fetch
// when the caller creates a new object reference on every render.
function serialize(f?: VehicleFilters) {
  return f ? JSON.stringify(f) : "";
}

export function useVehicles(filters?: VehicleFilters) {
  const [vehicles, setVehicles] = useState<VehicleResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const filterKey = serialize(filters);
  // Keep the last parsed filters so we never pass a new reference to the effect.
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listVehicles(filtersRef.current)
      .then((data) => { if (!cancelled) setVehicles(data); })
      .catch((err) => { if (!cancelled) setError(getErrorMessage(err)); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey]); // re-fetch only when the serialised value changes

  const refetch = () => {
    setLoading(true);
    setError(null);
    listVehicles(filtersRef.current)
      .then(setVehicles)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  return { vehicles, loading, error, refetch };
}
