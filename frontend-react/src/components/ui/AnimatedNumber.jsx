import { useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "../../hooks/usePrefersReducedMotion";

const DURATION_MS = 500;
const easeOut = (t) => 1 - (1 - t) ** 3;

/**
 * Rolls from the previous value to the new one. Tabular digits keep the width
 * steady so nothing around it shifts. Instant under reduced motion.
 */
export default function AnimatedNumber({ value, decimals = 1, suffix = "" }) {
  const reducedMotion = usePrefersReducedMotion();
  const [shown, setShown] = useState(value);
  const fromRef = useRef(value);

  useEffect(() => {
    if (value == null || reducedMotion) return undefined;
    const from = fromRef.current ?? value;
    let frame = 0;
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min((now - start) / DURATION_MS, 1);
      const current = from + (value - from) * easeOut(t);
      fromRef.current = current;
      setShown(current);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, reducedMotion]);

  const display = reducedMotion || shown == null ? value : shown;
  return (
    <span className="num">
      {display == null ? "--" : Number(display).toFixed(decimals)}
      {suffix}
    </span>
  );
}
