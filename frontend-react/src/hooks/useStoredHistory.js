import { useEffect, useState } from "react";
import { apiGet } from "../config";

const REFRESH_MS = 60_000;

/**
 * Readings stored by the backend (SQLite), averaged per `stepSec`, for the last
 * `seconds`. Returns { points, error, loading }; disabled when seconds is null.
 */
export function useStoredHistory(seconds, stepSec) {
  const [state, setState] = useState({ points: [], error: null, loading: false });

  useEffect(() => {
    if (!seconds) return undefined;
    let cancelled = false;
    const load = () => {
      setState((s) => ({ ...s, loading: true }));
      apiGet(`/history/range?hours=${seconds / 3600}&step=${stepSec}`)
        .then((rows) => !cancelled && setState({ points: rows, error: null, loading: false }))
        .catch((e) => !cancelled && setState({ points: [], error: e.message, loading: false }));
    };
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [seconds, stepSec]);

  return state;
}
