import { Activity, Zap, Terminal } from "lucide-react";

export default function DataSidebar({ data }) {
  return (
    <div className="data-sidebar">
      <section className="card">
        <h3 style={{ color: "#60a5fa", fontSize: "12px" }}>
          <Activity size={14} /> FINGER SENSORS
        </h3>
        <div className="sensor-grid">
          <div className="sensor-box">
            <div style={{ fontSize: "10px", color: "#64748b" }}>FLEX</div>
            <div style={{ fontSize: "24px", fontWeight: "bold" }}>
              {data.sensors.flex}°
            </div>
          </div>
          <div className="sensor-box">
            <div style={{ fontSize: "10px", color: "#64748b" }}>FORCE</div>
            <div style={{ fontSize: "24px", fontWeight: "bold" }}>
              {data.sensors.force}N
            </div>
          </div>
        </div>
      </section>

      <section className="card">
        <h3 style={{ color: "#34d399", fontSize: "12px" }}>
          <Zap size={14} /> MYO BAND EMG
        </h3>
        <div className="emg-container">
          {data.myo.emg.map((val, i) => (
            <div key={i} className="emg-bar-bg">
              <div className="emg-bar-fill" style={{ height: `${val}%` }} />
            </div>
          ))}
        </div>
      </section>

      <section
        className="card"
        style={{ flex: 1, display: "flex", flexDirection: "column" }}
      >
        <h3 style={{ color: "#fbbf24", fontSize: "12px" }}>
          <Terminal size={14} /> DATA LOG
        </h3>
        <div className="log-stream">
          {data.logs.map((log, i) => (
            <div
              key={i}
              style={{
                marginBottom: "4px",
                borderLeft: "1px solid #334155",
                paddingLeft: "8px",
              }}
            >
              {log}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
