import { useEffect, useRef, useState } from "react";
import { listRentals } from "@/services/rentalService";
import { getErrorMessage } from "@/services/api";
import type { RentalFilters, RentalResponse } from "@/types";

function serialize(f?: RentalFilters) {
  return f ? JSON.stringify(f) : "";
}

export function useRentals(filters?: RentalFilters) {
  const [rentals, setRentals] = useState<RentalResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const filterKey = serialize(filters);
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listRentals(filtersRef.current)
      .then((data) => { if (!cancelled) setRentals(data); })
      .catch((err) => { if (!cancelled) setError(getErrorMessage(err)); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey]);

  const refetch = () => {
    setLoading(true);
    setError(null);
    listRentals(filtersRef.current)
      .then(setRentals)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  return { rentals, loading, error, refetch };
}
