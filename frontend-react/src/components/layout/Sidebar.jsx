import { Brain, Menu, X } from "lucide-react";
import { DEMO, REPO_URL, SERVER } from "../../config";
import { PAGES } from "../../lib/pages";

function connectionLabel(status) {
  if (!status.api) return { text: "API offline", ok: false };
  if (!status.broker) return { text: "Broker offline", ok: false };
  if (!status.sensor) return { text: "Sensor offline", ok: false };
  return { text: "All systems live", ok: true };
}

function Brand({ room }) {
  return (
    <div className="brand">
      <Brain size={40} aria-hidden="true" />
      <div>
        <h1>AI OS v6</h1>
        <p>{room} monitoring</p>
      </div>
    </div>
  );
}

/** Top bar shown on narrow screens; opens the same navigation as the sidebar. */
export function MobileBar({ room, open, onToggle, status }) {
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
      <Brand room={room} />
      <span className={`status-dot ${net.ok ? "" : "status-dot--off"}`} title={net.text} aria-label={net.text} />
    </header>
  );
}

export default function Sidebar({ active, onNavigate, room, status, open }) {
  const net = connectionLabel(status);

  return (
    <aside className="sidebar" id="main-nav" data-open={open}>
      <Brand room={room} />

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
      </div>
    </aside>
  );
}
