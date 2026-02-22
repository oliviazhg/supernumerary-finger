import React from "react";
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from "lucide-react";

export default function ControlOverlay({ activeKeys }) {
  const getKeyStyle = (isActive) => ({
    padding: "10px",
    borderRadius: "8px",
    backgroundColor: isActive ? "#60a5fa" : "#1e293b",
    border: "1px solid #334155",
    color: isActive ? "#fff" : "#64748b",
    transition: "all 0.1s",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "5px",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: "40px",
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 20,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "10px",
        background: "rgba(15, 23, 42, 0.8)",
        padding: "20px",
        borderRadius: "15px",
        border: "1px solid #334155",
      }}
    >
      <div
        style={{
          fontSize: "12px",
          color: "#60a5fa",
          fontWeight: "bold",
          marginBottom: "5px",
        }}
      >
        MANUAL MOTOR CONTROL
      </div>

      {/* Motor 1: Vertical keys */}
      <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div
            style={{ fontSize: "10px", color: "#94a3b8", marginBottom: "5px" }}
          >
            MOTOR 1
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
            <div style={getKeyStyle(activeKeys.up)}>
              <ArrowUp size={20} />
            </div>
            <div style={getKeyStyle(activeKeys.down)}>
              <ArrowDown size={20} />
            </div>
          </div>
        </div>

        {/* Motor 2: Horizontal keys */}
        <div style={{ textAlign: "center" }}>
          <div
            style={{ fontSize: "10px", color: "#94a3b8", marginBottom: "5px" }}
          >
            MOTOR 2
          </div>
          <div style={{ display: "flex", gap: "5px" }}>
            <div style={getKeyStyle(activeKeys.left)}>
              <ArrowLeft size={20} />
            </div>
            <div style={getKeyStyle(activeKeys.right)}>
              <ArrowRight size={20} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
