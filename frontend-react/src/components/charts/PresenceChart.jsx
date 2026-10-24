import { usePresenceDays } from "../../hooks/usePresenceDays";

const W = 560;
const H = 180;
const PAD = { top: 22, right: 8, bottom: 26, left: 8 };

const hoursText = (minutes) => {
  if (!minutes) return "0";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (!h) return `${m} min`;
  return m ? `${h} h ${m} min` : `${h} h`;
};

const dayLabel = (iso, isToday) => (isToday ? "Today"
  : new Date(`${iso}T12:00:00`).toLocaleDateString([], { weekday: "short" }));

/** Time someone was in the room on each of the last 7 days (mmWave radar). */
export default function PresenceChart() {
  const { days, inNow, since, error } = usePresenceDays(7);
  const max = Math.max(60, ...days.map((d) => d.minutes));
  const plotH = H - PAD.top - PAD.bottom;
  const slot = (W - PAD.left - PAD.right) / Math.max(days.length, 1);
  const barW = Math.min(36, slot * 0.5);
  const total = days.reduce((sum, d) => sum + d.minutes, 0);
  const today = days[days.length - 1];

  let summary = "No radar data yet.";
  if (error) summary = `Time in the room unavailable: ${error}`;
  else if (days.length) {
    summary = `Today ${hoursText(today.minutes)}, this week ${hoursText(total)}.`;
    if (inNow) summary += since
      ? ` Someone is in now, since ${new Date(since * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}.`
      : " Someone is in now.";
  }

  return (
    <div className="presence-chart">
      <h3>Time in the room</h3>
      <p className="presence-chart__summary">{summary}</p>
      {days.length > 0 && (
        <svg viewBox={`0 0 ${W} ${H}`} role="img"
          aria-label={`Time someone was in the room, last 7 days: ${days.map((d) => `${d.date} ${hoursText(d.minutes)}`).join(", ")}`}>
          <line x1={PAD.left} x2={W - PAD.right} y1={H - PAD.bottom} y2={H - PAD.bottom} className="presence-chart__axis" />
          {days.map((d, i) => {
            const isToday = i === days.length - 1;
            const h = d.minutes ? Math.max(3, (d.minutes / max) * plotH) : 0;
            const x = PAD.left + slot * i + (slot - barW) / 2;
            const y = H - PAD.bottom - h;
            return (
              <g key={d.date} className={isToday ? "is-today" : ""}>
                <title>{`${d.date}: ${hoursText(d.minutes)}`}</title>
                {h > 0 && <rect x={x} y={y} width={barW} height={h} rx="4" className="presence-chart__bar" />}
                {d.minutes > 0 && (
                  <text x={x + barW / 2} y={y - 6} textAnchor="middle" className="presence-chart__value">
                    {d.minutes >= 60 ? `${(d.minutes / 60).toFixed(1)}h` : `${d.minutes}m`}
                  </text>
                )}
                <text x={x + barW / 2} y={H - 8} textAnchor="middle" className="presence-chart__day">
                  {dayLabel(d.date, isToday)}
                </text>
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}
