import { useCallback, useSyncExternalStore } from "react";

/** true while the media query matches; updates live on resize / setting changes. */
export function useMediaQuery(query) {
  const subscribe = useCallback((onChange) => {
    const media = window.matchMedia(query);
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [query]);
  return useSyncExternalStore(subscribe, () => window.matchMedia(query).matches, () => false);
}
