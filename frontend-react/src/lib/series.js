/** History rows -> [{ ts, value }] for one field, oldest first, invalid rows dropped. */
export function toSeries(history, field) {
  return history
    .map((row) => ({
      ts: row.ts ?? Date.parse(row.timestamp) / 1000,
      value: Number(row[field]),
    }))
    .filter((p) => Number.isFinite(p.ts) && Number.isFinite(p.value));
}

/** Keep only points newer than `seconds` before the latest one (null = all). */
export function lastSeconds(points, seconds) {
  if (!seconds || points.length === 0) return points;
  const cutoff = points[points.length - 1].ts - seconds;
  return points.filter((p) => p.ts >= cutoff);
}

/** Change per 10 minutes over the last 10 minutes of points, or null if too few. */
export function trendPer10Min(points) {
  const recent = lastSeconds(points, 600);
  if (recent.length < 3) return null;
  const first = recent[0];
  const last = recent[recent.length - 1];
  const span = last.ts - first.ts;
  if (span < 60) return null;
  return ((last.value - first.value) / span) * 600;
}
