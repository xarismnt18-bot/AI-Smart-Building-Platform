import { useEffect, useState } from "react";
import { apiGet } from "../config";

const REFRESH_MS = 60_000;

/** Minutes someone was in the room per day (radar), for the last `days` days. */
export function usePresenceDays(days = 7) {
  const [state, setState] = useState({ days: [], inNow: false, since: null, error: null });

  useEffect(() => {
    let cancelled = false;
    const load = () => apiGet(`/presence/daily?days=${days}`)
      .then((r) => !cancelled && setState({ days: r.days, inNow: r.in_now, since: r.since, error: null }))
      .catch((e) => !cancelled && setState((s) => ({ ...s, error: e.message })));
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [days]);

  return state;
}
