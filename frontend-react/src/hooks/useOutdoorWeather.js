import { useCallback, useEffect, useState } from "react";
import { DEMO } from "../config";
import { fetchOutdoor, ipLocation, placeName } from "../lib/weather";

const PLACE_KEY = "thalpos_weather_place"; // a place chosen by hand (overrides the device's position)
const LAST_KEY = "thalpos_weather_last";   // last known position, so the card fills in instantly

// keep a place saved before the app was renamed from AIOS
try {
  for (const [from, to] of [["aios_weather_place", PLACE_KEY], ["aios_weather_last", LAST_KEY]]) {
    const old = localStorage.getItem(from);
    if (old !== null && localStorage.getItem(to) === null) localStorage.setItem(to, old);
    localStorage.removeItem(from);
  }
} catch {
  // storage blocked: nothing to move
}
const REFRESH_MS = 10 * 60 * 1000;
const DEMO_PLACE = { lat: 37.97, lon: 23.73, name: "Athens", source: "demo" };

function read(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "null");
  } catch {
    return null;
  }
}

function write(key, value) {
  try {
    if (value == null) localStorage.removeItem(key);
    else localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // storage unavailable: works until reload
  }
}

function currentPosition() {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator) || !window.isSecureContext) {
      reject(Object.assign(new Error("unsupported"), { code: "unsupported" }));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
      (e) => reject(Object.assign(new Error(e.message), {
        code: e.code === 1 ? "denied" : e.code === 3 ? "timeout" : "unavailable",
      })),
      // a laptop has no GPS: Windows works the position out from nearby Wi-Fi, which can take a while
      { enableHighAccuracy: false, maximumAge: REFRESH_MS, timeout: 45000 },
    );
  });
}

/** Finds where to show the weather for and fetches it. Never throws. */
async function locateAndFetch() {
  let where = read(PLACE_KEY) || (DEMO ? DEMO_PLACE : null);
  let problem = null;
  if (!where) {
    try {
      const pos = await currentPosition();
      const previous = read(LAST_KEY);
      const moved = !previous || Math.hypot(previous.lat - pos.lat, previous.lon - pos.lon) > 0.02;
      const name = moved ? await placeName(pos).catch(() => null) : previous.name;
      where = { ...pos, name: name || "Your location", source: "device" };
      write(LAST_KEY, where);
    } catch (e) {
      problem = e.code || "unavailable";
      // no device position: use the town of the internet connection, then the last known place
      where = await ipLocation().catch(() => null) || read(LAST_KEY);
      if (!where) return { status: "needs-place", problem };
    }
  }
  try {
    return { status: "ready", place: where, weather: await fetchOutdoor(where), problem };
  } catch {
    return { status: "error", place: where, problem };
  }
}

/**
 * Weather where the viewer is. Uses the device's position (browser permission);
 * a place picked by hand wins until cleared. status: "locating" | "ready" |
 * "needs-place" (no permission / no GPS) | "error".
 */
export function useOutdoorWeather() {
  const [state, setState] = useState(() => ({
    status: "locating", problem: null, weather: null,
    place: read(PLACE_KEY) || (DEMO ? DEMO_PLACE : read(LAST_KEY)),
  }));
  const [manual, setManual] = useState(() => Boolean(read(PLACE_KEY)));
  const [version, setVersion] = useState(0); // bumped to look again after a place change

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      locateAndFetch().then((next) => {
        if (cancelled) return;
        // keep the last good reading if only this refresh failed
        setState((prev) => ({ ...prev, ...next, weather: next.weather ?? (next.status === "error" ? prev.weather : null) }));
      });
    };
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [version]);

  // look again as soon as location is allowed (or blocked) in the browser
  useEffect(() => {
    let status = null;
    const again = () => setVersion((v) => v + 1);
    navigator.permissions?.query({ name: "geolocation" })
      .then((s) => { status = s; s.addEventListener("change", again); })
      .catch(() => {});
    return () => status?.removeEventListener("change", again);
  }, []);

  const retry = useCallback(() => {
    setState((prev) => ({ ...prev, status: "locating" }));
    setVersion((v) => v + 1);
  }, []);

  const choosePlace = useCallback((picked) => {
    write(PLACE_KEY, picked ? { ...picked, source: "manual" } : null);
    setManual(Boolean(picked));
    setState((prev) => ({ ...prev, status: "locating", weather: null, place: picked || prev.place }));
    setVersion((v) => v + 1);
  }, []);

  return { ...state, choosePlace, retry, manual };
}
