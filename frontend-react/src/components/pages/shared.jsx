import { CLIENT, SERVER } from "../../config";

export function MqttPanel({ room, latest, health, lastUpdate, connected }) {
  const payload = { room: latest.room, temperature: latest.temperature, humidity: latest.humidity };

  return (
    <div className="mqtt panel">
      <h3>
        MQTT packet stream{" "}
        <b className={connected ? "" : "status-off"}>● {connected ? "live" : "offline"}</b>
      </h3>

      <div className="mqtt-terminal">
        <div><span>[API]</span> {CLIENT.API_URL}</div>
        <div><span>[TOPIC]</span> {SERVER.mqttTopic}</div>
        <div><span>[ROOM]</span> {room}</div>
        <div><span>[TEMP]</span> {latest.temperature ?? "--"} °C</div>
        <div><span>[HUMIDITY]</span> {latest.humidity ?? "--"} %</div>
        <div><span>[AI_HEALTH]</span> {health}/100</div>
        <div><span>[LAST_PACKET]</span> {lastUpdate}</div>
        <div><span>[BAD_PACKETS]</span> {latest.invalid_packets ?? 0}</div>
        <br />
        <div><span>last payload</span></div>
        <div className="mqtt-terminal__payload">{JSON.stringify(payload)}</div>
      </div>
    </div>
  );
}
