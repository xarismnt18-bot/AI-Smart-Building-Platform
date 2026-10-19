import { useEffect, useState } from "react";
import { apiGet, sendTestNotification } from "../config";

/** Telegram alert status + a button that sends a test message to the phone. */
export default function TelegramCard({ apiOnline }) {
  const [enabled, setEnabled] = useState(null);
  const [result, setResult] = useState(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!apiOnline) return;
    apiGet("/notifications")
      .then((json) => setEnabled(Boolean(json.telegram_enabled)))
      .catch(() => setEnabled(null));
  }, [apiOnline]);

  const sendTest = async () => {
    setSending(true);
    setResult(null);
    try {
      await sendTestNotification();
      setResult({ ok: true, text: "Sent. Check Telegram on your phone." });
    } catch (e) {
      setResult({ ok: false, text: e.message });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="module-card telegram-card">
      <h3>TELEGRAM ALERTS</h3>
      {enabled === null && <p className="telegram-card__text">Status unknown: backend unreachable.</p>}
      {enabled === false && (
        <p className="telegram-card__text">
          Off. Run <code>setup_telegram.bat</code> in the project folder, then restart AIOS.
        </p>
      )}
      {enabled && (
        <>
          <p className="telegram-card__text">
            On. You get a message when an alert starts or clears, and when the sensor stops sending.
            Each alert is sent once; if it clears and returns within 30 minutes it is not sent again.
          </p>
          <button type="button" className="export-btn secondary" onClick={sendTest} disabled={sending || !apiOnline}>
            {sending ? "SENDING..." : "SEND TEST MESSAGE"}
          </button>
        </>
      )}
      {result && (
        <p className="settings-message" role="status" style={{ color: result.ok ? "#22c55e" : "#ef4444" }}>{result.text}</p>
      )}
    </div>
  );
}
