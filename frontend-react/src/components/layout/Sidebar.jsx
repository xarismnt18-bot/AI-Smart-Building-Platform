import { Menu, X } from "lucide-react";
import { AUTHOR, DEMO, REPO_URL, SERVER } from "../../config";
import { PAGES } from "../../lib/pages";

function connectionLabel(status) {
  if (!status.api) return { text: "API offline", ok: false };
  if (!status.broker) return { text: "Broker offline", ok: false };
  if (!status.sensor) return { text: "Sensor offline", ok: false };
  return { text: "All systems live", ok: true };
}

/** The app icon: a house outline with the live room lit (same drawing as public/icon-512.png). */
function LogoMark() {
  return (
    <svg className="brand__mark" viewBox="0 0 48 48" width="40" height="40" aria-hidden="true">
      <path d="M8 21 24 7l16 14M12 20v20h24V20" fill="none" stroke="currentColor" strokeWidth="3.4"
        strokeLinecap="round" strokeLinejoin="round" />
      <rect x="20.5" y="25.5" width="7" height="7" rx="1.4" fill="#F59E0B" />
    </svg>
  );
}

/** Wordmark: "Thαlpoς" (θάλπος, warmth) with the two Greek letters in the accent colour. */
function Brand() {
  return (
    <div className="brand">
      <LogoMark />
      <div>
        <h1 className="brand__name">
          <span aria-hidden="true">Th<em>α</em>lpo<em>ς</em></span>
          <span className="sr-only">Thalpos</span>
        </h1>
        <p>Smart room monitor</p>
      </div>
    </div>
  );
}

function LinkedInIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" fill="currentColor">
      <path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5ZM3 9.75h4v11H3v-11Zm6.5 0h3.8v1.5h.06c.53-1 1.83-2.06 3.77-2.06 4.03 0 4.77 2.65 4.77 6.1v5.46h-4v-4.84c0-1.15-.02-2.64-1.61-2.64-1.61 0-1.86 1.26-1.86 2.56v4.92h-3.93v-11Z" />
    </svg>
  );
}

/** Top bar shown on narrow screens; opens the same navigation as the sidebar. */
export function MobileBar({ open, onToggle, status }) {
  const net = connectionLabel(status);
  return (
    <header className="mobile-bar">
      <button
        type="button"
        className="icon-button"
        onClick={onToggle}
        aria-expanded={open}
        aria-controls="main-nav"
        aria-label={open ? "Close menu" : "Open menu"}
      >
        {open ? <X size={22} /> : <Menu size={22} />}
      </button>
      <Brand />
      <span className={`status-dot ${net.ok ? "" : "status-dot--off"}`} title={net.text} aria-label={net.text} />
    </header>
  );
}

export default function Sidebar({ active, onNavigate, status, open }) {
  const net = connectionLabel(status);

  return (
    <aside className="sidebar" id="main-nav" data-open={open}>
      <Brand />

      <nav aria-label="Pages">
        {PAGES.map(([name, Icon]) => (
          <button
            key={name}
            type="button"
            className={active === name ? "active" : ""}
            aria-current={active === name ? "page" : undefined}
            onClick={() => onNavigate(name)}
          >
            <Icon aria-hidden="true" />
            {name}
          </button>
        ))}
      </nav>

      <div className="system">
        <p>Version <b>v6.15</b></p>
        {DEMO && <p>Mode <b>Demo, simulated</b></p>}
        <p>Sensor <b>DHT11</b></p>
        <p>Topic <b>{SERVER.mqttTopic}</b></p>
        <p className="system__status">
          <span className={`status-dot ${net.ok ? "" : "status-dot--off"}`} aria-hidden="true" />
          <strong className={net.ok ? "" : "status-off"}>{net.text}</strong>
        </p>
        {DEMO && <a className="system__source" href={REPO_URL} target="_blank" rel="noreferrer">View source on GitHub</a>}
        <a className="system__author" href={AUTHOR.linkedin} target="_blank" rel="noreferrer">
          <LinkedInIcon />
          <span>Built by <b>{AUTHOR.name}</b></span>
        </a>
      </div>
    </aside>
  );
}
