import { DEMO, historyCsvUrl } from "../config";

const hoursSinceMidnight = () => {
  const now = new Date();
  return (now - new Date(now.getFullYear(), now.getMonth(), now.getDate())) / 3600000;
};

const RANGES = [
  ["Today", hoursSinceMidnight],
  ["Last 24 hours", () => 24],
  ["Last 7 days", () => 7 * 24],
  ["Last 30 days", () => 30 * 24],
];

/** Reports page: every stored reading (one per 30 s, kept 30 days) as a CSV for Excel. */
export default function StoredExport() {
  return (
    <section className="module-card se" aria-labelledby="se-title">
      <h3 id="se-title">DOWNLOAD STORED READINGS (CSV)</h3>
      <p className="se-text">
        {DEMO
          ? "Available on your own Thalpos install: the online demo has no stored history."
          : "One reading every 30 seconds, kept for 30 days. Opens in Excel or Google Sheets."}
      </p>
      <div className="se-actions">
        {RANGES.map(([label, hours]) => (DEMO ? (
          <button key={label} type="button" className="export-btn" disabled>{label}</button>
        ) : (
          <a key={label} className="export-btn" href={historyCsvUrl(hours())} download
            onClick={(e) => { e.currentTarget.href = historyCsvUrl(hours()); }}>{label}</a>
        )))}
      </div>
    </section>
  );
}
