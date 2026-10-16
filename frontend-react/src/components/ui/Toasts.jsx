import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-react";

const ICONS = { good: CheckCircle2, warning: AlertTriangle, critical: XCircle, info: Info };

/** Status changes announced politely to screen readers as well as on screen. */
export default function Toasts({ toasts, onDismiss }) {
  return (
    <div className="toasts" role="status" aria-live="polite">
      {toasts.map((t) => {
        const Icon = ICONS[t.tone] ?? Info;
        return (
          <div key={t.id} className={`toast toast--${t.tone}`}>
            <Icon size={18} aria-hidden="true" />
            <p>{t.text}</p>
            <button type="button" className="icon-button" onClick={() => onDismiss(t.id)} aria-label="Dismiss notification" title="Dismiss">
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
