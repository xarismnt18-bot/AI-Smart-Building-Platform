import { useCallback, useEffect, useRef, useState } from "react";
import { CLIENT, apiGet, loadServerConfig } from "../config";

const HISTORY_REFRESH_FACTOR = 5; // history changes slowly; poll it 5x less often
export const NO_ALERTS = "No active alerts.";

const EMPTY_LATEST = { temperature: null, humidity: null, last_update: null, room: null };

function describeTransitions(prev, next, prevAlerts, nextAlerts) {
  const events = [];
  if (prev.api !== next.api) {
    events.push(next.api ? ["good", "Backend is back online."] : ["critical", "Backend unreachable. Check that the API window is running."]);
  } else if (next.api && prev.broker !== next.broker) {
    events.push(next.broker ? ["good", "Connected to the MQTT broker."] : ["critical", "Lost the MQTT broker. Retrying automatically."]);
  } else if (next.broker && prev.sensor !== next.sensor) {
    events.push(next.sensor ? ["good", "Sensor is reporting again."] : ["warning", "Sensor went quiet: no recent packets."]);
  }
  nextAlerts
    .filter((a) => a !== NO_ALERTS && !prevAlerts.includes(a) && !/offline|unreachable/i.test(a))
    .forEach((a) => events.push(["warning", a]));
  return events;
}

/**
 * Polls the backend and exposes the live state of the room.
 * `packetSeq` increments every time a new sensor packet arrives, so views can
 * react to the packet itself (e.g. the 3D pulse) rather than to polling ticks.
 */
export function useTelemetry({ onEvent } = {}) {
  const [latest, setLatest] = useState(EMPTY_LATEST);
  const [healthInfo, setHealthInfo] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [apiOnline, setApiOnline] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [packetSeq, setPacketSeq] = useState(0);
  const [configVersion, setConfigVersion] = useState(0);

  const previous = useRef({ status: null, alerts: [], lastUpdate: null });
  const onEventRef = useRef(onEvent);
  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const refreshConfig = useCallback(() => setConfigVersion((v) => v + 1), []);

  const applySnapshot = useCallback((status, nextAlerts, lastUpdate) => {
    const prev = previous.current;
    if (prev.status) {
      describeTransitions(prev.status, status, prev.alerts, nextAlerts)
        .forEach(([tone, text]) => onEventRef.current?.(tone, text));
    }
    if (lastUpdate && lastUpdate !== prev.lastUpdate) setPacketSeq((s) => s + 1);
    previous.current = { status, alerts: nextAlerts, lastUpdate };
  }, []);

  const loadLive = useCallback(async () => {
    try {
      const [latestJson, healthJson, alertsJson] = await Promise.all([
        apiGet("/latest"),
        apiGet("/health"),
        apiGet("/alerts"),
      ]);
      const nextAlerts = alertsJson.alerts || [];
      setLatest(latestJson);
      setHealthInfo(healthJson);
      setAlerts(nextAlerts);
      setApiOnline(true);
      applySnapshot(
        { api: true, broker: Boolean(latestJson.broker_connected), sensor: Boolean(latestJson.connected) },
        nextAlerts,
        latestJson.last_update,
      );
    } catch (error) {
      console.warn("API offline:", error);
      setApiOnline(false);
      applySnapshot({ api: false, broker: false, sensor: false }, [], previous.current.lastUpdate);
    } finally {
      setLoaded(true);
    }
  }, [applySnapshot]);

  const loadHistory = useCallback(async () => {
    try {
      const json = await apiGet("/history");
      setHistory(Array.isArray(json) ? json : []);
    } catch {
      // loadLive already reports the outage
    }
  }, []);

  useEffect(() => {
    loadServerConfig().then(refreshConfig).catch(() => {});
    const first = setTimeout(() => {
      loadLive();
      loadHistory();
    }, 0);

    const interval = Number(CLIENT.REFRESH_INTERVAL) || 2000;
    const live = setInterval(loadLive, interval);
    const hist = setInterval(loadHistory, interval * HISTORY_REFRESH_FACTOR);
    return () => {
      clearTimeout(first);
      clearInterval(live);
      clearInterval(hist);
    };
  }, [loadLive, loadHistory, refreshConfig]);

  const status = {
    api: apiOnline,
    broker: apiOnline && Boolean(latest.broker_connected),
    sensor: apiOnline && Boolean(latest.connected),
  };

  return {
    latest,
    healthInfo,
    alerts,
    activeAlerts: apiOnline ? alerts.filter((a) => a !== NO_ALERTS) : [],
    history,
    status,
    loaded,
    packetSeq,
    configVersion,
    refreshConfig,
  };
}
