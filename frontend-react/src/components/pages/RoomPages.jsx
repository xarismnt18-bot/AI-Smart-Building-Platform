import AlertHistory from "../AlertHistory";

export function Floorplan({ room, temp, humidity, health }) {
  return (
    <div className="module-page">
      <h1>Floorplan</h1>
      <p className="module-subtitle">{room} has a sensor. The other rooms are ready for one.</p>

      <div className="floorplan-grid">
        <div className="zone zone-green">
          <h3>{room}</h3>
          <p>{temp}°C | {humidity}%</p>
          <span>Health: {health}/100</span>
        </div>
        {["Room 2", "Room 3", "Room 4"].map((name) => (
          <div key={name} className="zone zone-empty">
            <h3>{name}</h3>
            <p>--</p>
            <span>Add an ESP8266 node to start monitoring</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Alerts({ room, health, alerts, apiOnline, healthInfo }) {
  const active = apiOnline ? alerts : ["Backend unreachable: alerts unknown."];

  return (
    <div className="module-page">
      <h1>Alerts</h1>
      <p className="module-subtitle">{room}. Thresholds come from the backend and can be changed in Settings.</p>

      <div className="alerts-list">
        {active.length === 0 ? (
          <div className="alert-module good">
            <h3>All clear</h3>
            <p>No active alerts for {room}.</p>
          </div>
        ) : (
          active.map((a) => (
            <div key={a} className="alert-module bad">
              <h3>Alert</h3>
              <p>{a}</p>
            </div>
          ))
        )}

        <div className="alert-module blue">
          <h3>Diagnosis</h3>
          <p>
            {room} health score is {health}/100.
            {healthInfo.dew_point != null && ` Dew point ${healthInfo.dew_point}°C, mold risk ${healthInfo.mold_risk}.`}
          </p>
        </div>
      </div>

      <AlertHistory apiOnline={apiOnline} />
    </div>
  );
}
