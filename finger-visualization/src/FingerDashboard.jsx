import React, { useState, useEffect, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stage, Grid } from "@react-three/drei";
import { Cpu, Gamepad2, Settings2 } from "lucide-react";
import "./App.css";
import DataSidebar from "./components/DataSidebar";
import FingerModel from "./components/FingerModel";
import ControlOverlay from "./components/ControlOverlay";

export default function FingerDashboard() {
  const [data, setData] = useState({
    angles: { j1: 0, j2: 0, j3: 0 },
    sensors: { flex: 0, force: 0 },
    myo: { emg: [0, 0, 0, 0, 0, 0, 0, 0] },
    logs: ["Started..."],
  });

  const [isSimulating, setIsSimulating] = useState(false);
  const [controlMode, setControlMode] = useState("myo"); // 'ui', 'myo', 'fsr'

  const [activeKeys, setActiveKeys] = useState({
    up: false,
    down: false,
    left: false,
    right: false,
  });
  const socket = useRef(null);

  // WebSocket Logic
  useEffect(() => {
    socket.current = new WebSocket("ws://localhost:8765");
    socket.current.onmessage = (event) => {
      const incoming = JSON.parse(event.data);
      setData((prev) => ({
        ...prev,
        ...incoming,
        logs: [
          `[${new Date().toLocaleTimeString()}] Data Received`,
          ...prev.logs,
        ].slice(0, 15),
      }));
    };
    return () => socket.current.close();
  }, []);

  const handleModeChange = (newMode) => {
    setControlMode(newMode);
    setIsSimulating(false);
    if (socket.current && socket.current.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify({ type: "set_mode", mode: newMode }));
    }
  };

  // Keyboard Event Listeners (Only active if controlMode === 'ui')
  useEffect(() => {
    if (controlMode !== "ui") return;

    const handleKeyDown = (e) => {
      let key = null;
      if (e.key === "ArrowUp") key = "up";
      if (e.key === "ArrowDown") key = "down";
      if (e.key === "ArrowLeft") key = "left";
      if (e.key === "ArrowRight") key = "right";

      if (key && !activeKeys[key]) {
        setActiveKeys((prev) => ({ ...prev, [key]: true }));
        const motor = key === "up" || key === "down" ? 1 : 2;
        const dir = key === "up" || key === "right" ? "forward" : "backward";
        socket.current.send(
          JSON.stringify({ type: "control", motor, dir, action: "start" }),
        );
      }
    };

    const handleKeyUp = (e) => {
      let key = null;
      if (e.key === "ArrowUp") key = "up";
      if (e.key === "ArrowDown") key = "down";
      if (e.key === "ArrowLeft") key = "left";
      if (e.key === "ArrowRight") key = "right";

      if (key) {
        setActiveKeys((prev) => ({ ...prev, [key]: false }));
        const motor = key === "up" || key === "down" ? 1 : 2;
        socket.current.send(
          JSON.stringify({ type: "control", motor, action: "stop" }),
        );
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [controlMode, activeKeys]);

  // Simulation Logic
  useEffect(() => {
    let interval;
    if (isSimulating && controlMode === "ui") {
      interval = setInterval(() => {
        const time = Date.now() * 0.002;
        setData((prev) => ({
          ...prev,
          angles: {
            j1: Math.sin(time) * 0.5,
            j2: Math.sin(time * 0.8) * 0.7,
            j3: Math.sin(time * 1.2) * 0.4,
          },
          sensors: {
            flex: Math.floor(Math.random() * 90),
            force: (Math.random() * 5).toFixed(2),
          },
          myo: { emg: prev.myo.emg.map(() => Math.floor(Math.random() * 100)) },
        }));
      }, 50);
    }
    return () => clearInterval(interval);
  }, [isSimulating, controlMode]);

  return (
    <div className="dashboard-root">
      <div className="viewer-container">
        <div
          style={{
            position: "absolute",
            top: "24px",
            left: "24px",
            zIndex: 10,
          }}
        >
          <h1
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              margin: 0,
              fontSize: "20px",
              marginBottom: "15px",
            }}
          >
            <Cpu color="#60a5fa" /> FINGER MODEL
          </h1>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                background: "#1e293b",
                padding: "8px 12px",
                borderRadius: "8px",
                border: "1px solid #334155",
              }}
            >
              <Settings2
                size={16}
                color="#94a3b8"
                style={{ marginRight: "8px" }}
              />
              <select
                value={controlMode}
                onChange={(e) => {
                  handleModeChange(e.target.value);
                  e.target.blur();
                }}
                style={{
                  background: "transparent",
                  color: "#94a3b8",
                  border: "none",
                  outline: "none",
                  cursor: "pointer",
                  fontSize: "14px",
                }}
              >
                <option value="ui">Arrow keys</option>
                <option value="fsr">FSR sensor</option>
                <option value="myo">Myo band</option>
              </select>
            </div>

            <button
              onClick={() => setIsSimulating(!isSimulating)}
              disabled={controlMode !== "ui"}
              className="btn-primary"
              style={{
                backgroundColor: isSimulating ? "#ef4444" : "#10b981",
                opacity: controlMode !== "ui" ? 0.5 : 1,
              }}
            >
              {isSimulating ? "STOP SIM" : "TEST MODE"}
            </button>
          </div>
        </div>

        {/* Manual Control Visualizer Overlay - Only show if UI mode is active */}
        {controlMode === "ui" && <ControlOverlay activeKeys={activeKeys} />}

        <div className="canvas-wrapper">
          <Canvas camera={{ position: [3, 3, 3], fov: 30 }}>
            <Stage environment="city" intensity={0.5} adjustCamera={false}>
              <FingerModel angles={data.angles} />
            </Stage>
            <Grid infiniteGrid sectionColor="#334155" cellColor="#1f2937" />
            <OrbitControls makeDefault />
          </Canvas>
        </div>
      </div>
      <DataSidebar data={data} />
    </div>
  );
}
