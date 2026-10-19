import { useCallback, useEffect, useState } from "react";
import { apiGet, setLampAuto, switchLamp } from "../config";

/** The IKEA alert lamp: lights up on alerts; switch it or its automation here. */
export default function LampCard({ apiOnline }) {
  const [lamp, setLamp] = useState(null);
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    apiGet("/lamp").then(setLamp).catch(() => setLamp(null));
  }, []);

  useEffect(() => {
    if (apiOnline) refresh();
  }, [apiOnline, refresh]);

  const run = async (action, done) => {
    setBusy(true);
    setMessage(null);
    try {
      await action();
      setMessage({ ok: true, text: done });
      refresh();
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="module-card telegram-card">
      <h3>ALERT LAMP</h3>
      {lamp === null && <p className="telegram-card__text">Status unknown: backend unreachable.</p>}
      {lamp && !lamp.enabled && (
        <p className="telegram-card__text">
          Off. Run <code>setup_ikea.bat</code> in the project folder and press the button under the IKEA hub.
        </p>
      )}
      {lamp?.enabled && (
        <>
          <p className="telegram-card__text">
            {lamp.lit_by_alert ? "On because of an alert. " : ""}
            {lamp.auto
              ? `Lights up on temperature or humidity alerts, never during ${lamp.quiet_hours.replace("-", "\u2013")}.`
              : "Automatic mode is off: the lamp only changes when you switch it."}
          </p>
          <div className="lamp-card__actions">
            <button type="button" className="export-btn" disabled={busy}
              onClick={() => run(() => switchLamp(true), "Lamp on.")}>TURN ON</button>
            <button type="button" className="export-btn secondary" disabled={busy}
              onClick={() => run(() => switchLamp(false), "Lamp off.")}>TURN OFF</button>
            <button type="button" className="export-btn secondary" disabled={busy} aria-pressed={lamp.auto}
              onClick={() => run(() => setLampAuto(!lamp.auto), lamp.auto ? "Automatic lamp off." : "Automatic lamp on.")}>
              {lamp.auto ? "TURN AUTO OFF" : "TURN AUTO ON"}
            </button>
          </div>
        </>
      )}
      {message && (
        <p className="settings-message" role="status" style={{ color: message.ok ? "#22c55e" : "#ef4444" }}>{message.text}</p>
      )}
    </div>
  );
}
