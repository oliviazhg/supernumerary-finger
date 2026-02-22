import React, { useState, useEffect, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stage, Grid } from "@react-three/drei";
import { Cpu, Gamepad2 } from "lucide-react";
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
  const [manualMode, setManualMode] = useState(false);
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

  // Keyboard Event Listeners
  useEffect(() => {
    if (!manualMode) return;

    const handleKeyDown = (e) => {
      let key = null;
      if (e.key === "ArrowUp") key = "up";
      if (e.key === "ArrowDown") key = "down";
      if (e.key === "ArrowLeft") key = "left";
      if (e.key === "ArrowRight") key = "right";

      if (key && !activeKeys[key]) {
        setActiveKeys((prev) => ({ ...prev, [key]: true }));
        // Send command to Python: { type: "manual", motor: 1 or 2, direction: "pos" or "neg" }
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
  }, [manualMode, activeKeys]);

  // Simulation Logic (Unchanged but wrapped in manual check)
  useEffect(() => {
    let interval;
    if (isSimulating && !manualMode) {
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
  }, [isSimulating, manualMode]);

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
            }}
          >
            <Cpu color="#60a5fa" /> FINGER MODEL
          </h1>
          <div style={{ display: "flex", gap: "10px" }}>
            <button
              onClick={() => setIsSimulating(!isSimulating)}
              disabled={manualMode}
              className="btn-primary"
              style={{
                backgroundColor: isSimulating ? "#ef4444" : "#10b981",
                opacity: manualMode ? 0.5 : 1,
              }}
            >
              {isSimulating ? "STOP SIM" : "TEST MODE"}
            </button>
            <button
              onClick={() => {
                setManualMode(!manualMode);
                setIsSimulating(false);
              }}
              className="btn-primary"
              style={{ backgroundColor: manualMode ? "#f59e0b" : "#6366f1" }}
            >
              <Gamepad2 size={14} style={{ marginRight: "5px" }} />
              {manualMode ? "DISABLE MANUAL" : "ENABLE MANUAL"}
            </button>
          </div>
        </div>

        {/* Manual Control Visualizer Overlay */}
        {manualMode && <ControlOverlay activeKeys={activeKeys} />}

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
