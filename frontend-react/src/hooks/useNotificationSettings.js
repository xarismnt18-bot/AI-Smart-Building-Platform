import { useCallback, useEffect, useState } from "react";
import { apiGet, muteAlerts, saveNotificationSettings, unmuteAlerts } from "../config";

const splitHours = (value) => {
  const [start = "", end = ""] = (value || "").split("-");
  return { start, end, never: !value };
};

const joinHours = ({ start, end, never }) => (never || !start || !end ? "" : `${start}-${end}`);

function toForm(json) {
  return {
    voice_on: json.voice_on,
    voice: splitHours(json.voice_quiet_hours),
    lamp_auto: json.lamp_auto,
    lamp: splitHours(json.lamp_quiet_hours),
    presence_on: json.presence_on,
    presence: splitHours(json.presence_quiet_hours),
  };
}

/** Alert channels, quiet hours and pause, loaded from and saved to the backend. */
export function useNotificationSettings(apiOnline) {
  const [server, setServer] = useState(null);
  const [form, setForm] = useState(null);
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);

  const apply = useCallback((json) => {
    setServer(json);
    setForm(toForm(json));
  }, []);

  useEffect(() => {
    if (!apiOnline) return;
    apiGet("/notifications").then(apply).catch(() => setServer(null));
  }, [apiOnline, apply]);

  const run = async (action, done) => {
    setBusy(true);
    setMessage(null);
    try {
      const json = await action();
      setServer(json);
      setMessage({ ok: true, text: done(json) });
      return json;
    } catch (e) {
      setMessage({ ok: false, text: `Not saved: ${e.message}` });
      return null;
    } finally {
      setBusy(false);
    }
  };

  const save = async () => {
    const json = await run(() => saveNotificationSettings({
      voice_on: form.voice_on,
      voice_quiet_hours: joinHours(form.voice),
      lamp_auto: form.lamp_auto,
      lamp_quiet_hours: joinHours(form.lamp),
      ...(server.presence_on !== undefined && {
        presence_on: form.presence_on,
        presence_quiet_hours: joinHours(form.presence),
      }),
    }), () => "Saved. The new quiet hours apply from now on.");
    if (json) setForm(toForm(json));
  };

  const pause = (minutes) => run(() => muteAlerts(minutes), (json) =>
    `Alerts paused until ${new Date(json.muted_until * 1000).toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" })}.`);

  const resume = () => run(unmuteAlerts, () => "Alerts are on again.");

  const edit = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const editHours = (key, part, value) => setForm((f) => {
    const next = { ...f[key], [part]: value };
    if (part === "never" && !value && !next.start) Object.assign(next, { start: "23:00", end: "08:00" });
    return { ...f, [key]: next };
  });

  return { server, form, message, busy, save, pause, resume, edit, editHours };
}
