import { useState } from "react";

const MAX_ROWS = 7;

function row(source) {
  return {
    key: `${source.ts ?? source.last_update}-${source.temperature}-${source.humidity}`,
    time: source.timestamp ?? source.last_update,
    temperature: source.temperature,
    humidity: source.humidity,
  };
}

/**
 * Newest-first list of recent packets. Grows on every new packet (packetSeq)
 * and falls back to the backend history until the first live packet lands.
 */
export function usePacketLog(latest, packetSeq, history) {
  const [log, setLog] = useState([]);
  const [seenSeq, setSeenSeq] = useState(packetSeq);

  if (packetSeq !== seenSeq) {
    setSeenSeq(packetSeq);
    if (latest.temperature != null) {
      setLog((rows) => [{ ...row(latest), fresh: true }, ...rows.map((r) => ({ ...r, fresh: false }))].slice(0, MAX_ROWS));
    }
  }

  if (log.length > 0) return log;
  return history.slice(-MAX_ROWS).reverse().map(row);
}
