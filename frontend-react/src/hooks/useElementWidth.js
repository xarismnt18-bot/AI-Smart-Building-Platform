import { useCallback, useState } from "react";

/** Callback ref + live pixel width of the element (ResizeObserver). */
export function useElementWidth() {
  const [width, setWidth] = useState(0);

  const ref = useCallback((node) => {
    if (!node) return undefined;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.round(entry.contentRect.width)));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return [ref, width];
}
