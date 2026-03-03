import { Activity, Zap, Terminal } from "lucide-react";

export default function DataSidebar({ data }) {
  return (
    <div className="data-sidebar">
      <section className="card">
        <h3 style={{ color: "#60a5fa", fontSize: "12px" }}>FINGER SENSORS</h3>
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
        <h3 style={{ color: "#60a5fa", fontSize: "12px" }}>MYO BAND STATUS</h3>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            padding: "10px 0",
          }}
        >
          <div
            style={{
              fontSize: "24px",
              fontWeight: "bold",
              letterSpacing: "2px",
              padding: "10px 20px",
              borderRadius: "8px",
              backgroundColor: "rgba(96, 165, 250, 0.2)",
              border: `1px solid #60a5fa`,
              minWidth: "120px",
              textAlign: "center",
            }}
          >
            {data.myo.state || "UNKNOWN"}
          </div>
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
