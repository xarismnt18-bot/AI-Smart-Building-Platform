import { useCallback, useState } from "react";

const TOAST_LIFETIME_MS = 5000;
const MAX_TOASTS = 4;
let nextId = 1;

/** Short-lived status messages. tone: "good" | "warning" | "critical" | "info". */
export function useToasts() {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id));
  }, []);

  const push = useCallback((tone, text) => {
    const id = nextId++;
    setToasts((list) => [...list, { id, tone, text }].slice(-MAX_TOASTS));
    setTimeout(() => dismiss(id), TOAST_LIFETIME_MS);
  }, [dismiss]);

  return { toasts, push, dismiss };
}
