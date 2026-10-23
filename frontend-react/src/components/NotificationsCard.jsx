import { useNotificationSettings } from "../hooks/useNotificationSettings";

const PAUSES = [[60, "1 hour"], [8 * 60, "8 hours"], [24 * 60, "24 hours"]];

function QuietHours({ id, value, onChange, disabled }) {
  return (
    <fieldset className="nc-quiet" disabled={disabled}>
      <legend>Quiet hours</legend>
      <label className="nc-check">
        <input type="checkbox" checked={value.never} onChange={(e) => onChange("never", e.target.checked)} />
        No quiet hours
      </label>
      {!value.never && (
        <div className="nc-times">
          <label htmlFor={`${id}-start`}>From</label>
          <input id={`${id}-start`} type="time" value={value.start} onChange={(e) => onChange("start", e.target.value)} />
          <label htmlFor={`${id}-end`}>to</label>
          <input id={`${id}-end`} type="time" value={value.end} onChange={(e) => onChange("end", e.target.value)} />
        </div>
      )}
    </fieldset>
  );
}

function PauseRow({ mutedUntil, busy, onPause, onResume }) {
  const until = mutedUntil ? new Date(mutedUntil * 1000) : null;
  return (
    <div className="nc-block">
      <h4>Pause all alerts</h4>
      <p className="nc-text" role="status">
        {until
          ? `Paused until ${until.toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" })}. Telegram and Alexa stay silent; the dashboard still shows alerts.`
          : "Alerts are on. Pausing silences Telegram and Alexa (same as /mute in Telegram)."}
      </p>
      <div className="nc-actions">
        {until ? (
          <button type="button" className="export-btn" onClick={onResume} disabled={busy}>Resume alerts</button>
        ) : PAUSES.map(([min, label]) => (
          <button key={min} type="button" className="export-btn secondary" onClick={() => onPause(min)} disabled={busy}>
            Pause {label}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Settings page: pause alerts, Alexa and lamp on/off and their quiet hours. */
export default function NotificationsCard({ apiOnline }) {
  const n = useNotificationSettings(apiOnline);

  if (!n.server || !n.form) {
    return (
      <div className="module-card nc">
        <h3>ALERTS & QUIET HOURS</h3>
        <p className="nc-text">{apiOnline ? "Loading…" : "Backend unreachable: start AIOS to change these."}</p>
      </div>
    );
  }

  const { server, form } = n;
  return (
    <div className="module-card nc">
      <h3>ALERTS & QUIET HOURS</h3>

      <PauseRow mutedUntil={server.muted_until} busy={n.busy} onPause={n.pause} onResume={n.resume} />

      <div className="nc-grid">
        <div className="nc-block">
          <h4>Alexa announcements</h4>
          {server.voice_enabled ? (
            <>
              <label className="nc-check">
                <input type="checkbox" checked={form.voice_on} onChange={(e) => n.edit("voice_on", e.target.checked)} />
                Alexa announces new alerts
              </label>
              <QuietHours id="voice" value={form.voice} disabled={!form.voice_on}
                onChange={(part, v) => n.editHours("voice", part, v)} />
            </>
          ) : (
            <p className="nc-text">Not set up. Run <code>setup_voice.bat</code> on the PC.</p>
          )}
        </div>

        <div className="nc-block">
          <h4>Alert lamp</h4>
          {server.lamp_enabled ? (
            <>
              <label className="nc-check">
                <input type="checkbox" checked={form.lamp_auto} onChange={(e) => n.edit("lamp_auto", e.target.checked)} />
                Light the lamp during alerts
              </label>
              <QuietHours id="lamp" value={form.lamp} disabled={!form.lamp_auto}
                onChange={(part, v) => n.editHours("lamp", part, v)} />
            </>
          ) : (
            <p className="nc-text">Not set up (needs an IKEA hub and <code>setup_ikea.bat</code>).</p>
          )}
        </div>
      </div>

      {(server.voice_enabled || server.lamp_enabled) && (
        <div className="nc-actions">
          <button type="button" className="export-btn" onClick={n.save} disabled={n.busy || !apiOnline}>
            {n.busy ? "Saving…" : "Save alert settings"}
          </button>
        </div>
      )}
      {n.message && (
        <p className="settings-message" role="status" style={{ color: n.message.ok ? "#22c55e" : "#ef4444" }}>{n.message.text}</p>
      )}
    </div>
  );
}
