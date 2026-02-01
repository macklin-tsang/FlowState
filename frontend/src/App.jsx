import { useState, useCallback, useRef, useMemo } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls, Environment, Stars } from "@react-three/drei"
import ConeFunnel from "./ConeFunnel"
import Bucket from "./Bucket"
import WaterSystem from "./WaterSystem"
import useFlowState from "./useFlowState"

// ---- 3D Scene driven by backend state or local fallback ----
function Scene({ draining, apiState }) {
  const [localWaterHeight, setLocalWaterHeight] = useState(0.85)
  const [localBucketLevel, setLocalBucketLevel] = useState(0)
  const drainingRef = useRef(draining)
  drainingRef.current = draining

  useFrame((_, delta) => {
    if (!drainingRef.current) return
    setLocalWaterHeight((h) => Math.max(h - delta * 0.06, 0))
    setLocalBucketLevel((b) => Math.min(b + delta * 0.04, 1))
  })

  // When connected to backend, map basin water_height to visual range
  // Basin max is ~0.375m, upper vessel drains as basin fills
  const waterHeight = apiState
    ? Math.max(0, 0.85 - Math.min(apiState.water_height / 0.375, 1) * 0.85)
    : localWaterHeight
  const bucketWaterLevel = apiState
    ? Math.min(apiState.water_height / 0.375, 1)
    : localBucketLevel

  return (
    <>
      <ConeFunnel />
      <Bucket waterLevel={bucketWaterLevel} />
      <WaterSystem
        draining={draining || !!apiState}
        waterHeight={waterHeight < 0.01 ? 0 : waterHeight}
        bucketWaterLevel={bucketWaterLevel}
      />
    </>
  )
}

// ---- Sparkline mini chart (pure div-based) ----
function Sparkline({ data, color = "#4af", height = 40, label }) {
  if (!data || data.length < 2) return null
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  return (
    <div style={{ marginBottom: 8 }}>
      {label && (
        <div style={{ fontSize: 10, color: "#889", marginBottom: 2, letterSpacing: 1 }}>
          {label}
        </div>
      )}
      <div style={{ display: "flex", alignItems: "flex-end", height, gap: 1 }}>
        {data.slice(-60).map((v, i) => {
          const h = ((v - min) / range) * height
          return (
            <div
              key={i}
              style={{
                flex: 1,
                height: Math.max(h, 1),
                background: color,
                borderRadius: 1,
                opacity: 0.7 + (i / 60) * 0.3,
              }}
            />
          )
        })}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "#667", marginTop: 2 }}>
        <span>{min.toFixed(2)}</span>
        <span>{max.toFixed(2)}</span>
      </div>
    </div>
  )
}

// ---- Metrics Panel ----
function MetricsPanel({ state, drift, stats, connected }) {
  const driftValues = useMemo(() => drift.map((d) => d.drift), [drift])
  const correctionErrors = useMemo(() => drift.map((d) => d.correction_error), [drift])
  const temperatures = useMemo(() => drift.map((d) => d.temperature), [drift])
  const rawTimes = useMemo(() => drift.map((d) => d.raw_time), [drift])
  const correctedTimes = useMemo(() => drift.map((d) => d.corrected_time), [drift])

  return (
    <div style={panelStyle}>
      {/* Connection indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <div
          style={{
            width: 8, height: 8, borderRadius: "50%",
            background: connected ? "#4f4" : "#f44",
            boxShadow: connected ? "0 0 6px #4f4" : "0 0 6px #f44",
          }}
        />
        <span style={{ fontSize: 11, color: connected ? "#8a8" : "#a66", letterSpacing: 1 }}>
          {connected ? "LIVE" : "OFFLINE"}
        </span>
      </div>

      <div style={{ fontSize: 14, color: "#c4a46c", letterSpacing: 2, marginBottom: 16, fontFamily: "Georgia, serif" }}>
        ML CALIBRATION
      </div>

      {/* Current state metrics */}
      {state && (
        <div style={{ marginBottom: 20 }}>
          <MetricRow label="Raw Time" value={`${state.raw_time?.toFixed(2)}s`} color="#fa4" />
          <MetricRow label="Corrected" value={`${state.corrected_time?.toFixed(2)}s`} color="#4f4" />
          <MetricRow label="True Elapsed" value={`${state.elapsed_time?.toFixed(2)}s`} color="#4af" />
          <MetricRow
            label="Drift"
            value={`${(state.raw_time - state.elapsed_time)?.toFixed(3)}s`}
            color={Math.abs(state.raw_time - state.elapsed_time) < 1 ? "#4f4" : "#fa4"}
          />
          <MetricRow
            label="ML Error"
            value={`${(state.corrected_time - state.elapsed_time)?.toFixed(4)}s`}
            color={Math.abs(state.corrected_time - state.elapsed_time) < 0.5 ? "#4f4" : "#f44"}
          />
          <MetricRow label="Temperature" value={`${state.temperature?.toFixed(2)} C`} color="#88f" />
          <MetricRow label="Flow Rate" value={state.flow_rate?.toExponential(3)} color="#4af" />
          <MetricRow label="Water Height" value={`${state.water_height?.toFixed(6)} m`} color="#4af" />
          <MetricRow label="Erosion" value={state.erosion?.toExponential(3)} color="#a86" />
          <MetricRow label="Sediment" value={state.sediment?.toExponential(3)} color="#86a" />
        </div>
      )}

      {/* Drift sparklines */}
      {drift.length > 1 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: "#998", letterSpacing: 1, marginBottom: 10 }}>
            DRIFT TIMELINE
          </div>
          <Sparkline data={driftValues} color="#fa4" height={35} label="RAW DRIFT (s)" />
          <Sparkline data={correctionErrors} color="#4f4" height={35} label="ML CORRECTION ERROR (s)" />
          <Sparkline data={temperatures} color="#88f" height={30} label="TEMPERATURE (C)" />
        </div>
      )}

      {/* Raw vs corrected comparison */}
      {drift.length > 1 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: "#998", letterSpacing: 1, marginBottom: 8 }}>
            RAW vs CORRECTED
          </div>
          <Sparkline data={rawTimes} color="#fa4" height={30} label="RAW TIME" />
          <Sparkline data={correctedTimes} color="#4f4" height={30} label="ML CORRECTED" />
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div style={{ borderTop: "1px solid #333", paddingTop: 12, marginTop: 8 }}>
          <MetricRow label="Total Ticks" value={stats.total_ticks} color="#889" />
          <MetricRow label="Loop Active" value={stats.loop_running ? "YES" : "NO"} color={stats.loop_running ? "#4f4" : "#f44"} />
          <MetricRow label="Next Retrain" value={`${stats.ticks_until_retrain} ticks`} color="#889" />
        </div>
      )}

      {!connected && (
        <div style={{ marginTop: 16, padding: 12, background: "#221", borderRadius: 6, fontSize: 11, color: "#a86", lineHeight: 1.6 }}>
          Backend not running. Start with:<br />
          <code style={{ color: "#fa4" }}>cd backend/src && python main.py serve</code>
        </div>
      )}
    </div>
  )
}

function MetricRow({ label, value, color }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: 12 }}>
      <span style={{ color: "#778" }}>{label}</span>
      <span style={{ color, fontFamily: "monospace", fontWeight: "bold" }}>{value}</span>
    </div>
  )
}

// ---- Main App ----
export default function App() {
  const [draining, setDraining] = useState(false)
  const { state, drift, stats, connected, trainModel, resetSimulator } = useFlowState()
  const [training, setTraining] = useState(false)
  const [resetting, setResetting] = useState(false)

  const handleStart = useCallback(() => setDraining(true), [])
  const handleReset = useCallback(() => setDraining(false), [])
  const handleTrain = useCallback(async () => {
    setTraining(true)
    await trainModel(500)
    setTraining(false)
  }, [trainModel])
  const handleResetSim = useCallback(async () => {
    setResetting(true)
    await resetSimulator()
    setResetting(false)
  }, [resetSimulator])

  return (
    <div style={{ width: "100vw", height: "100vh", display: "flex", background: "#0b0b0f" }}>
      {/* Left: 3D Water Clock */}
      <div style={{ flex: 1, position: "relative", minWidth: 0 }}>
        <Canvas
          camera={{ position: [0, 1, 7], fov: 50 }}
          shadows
          gl={{ antialias: true, alpha: false }}
          onCreated={({ gl }) => gl.setClearColor("#111118")}
        >
          <ambientLight intensity={0.5} />
          <directionalLight position={[3, 6, 2]} intensity={1.0} castShadow />
          <directionalLight position={[-2, 4, -3]} intensity={0.4} color="#8888ff" />
          <pointLight position={[0, -2, 2]} intensity={0.6} color="#4488ff" />
          {/* Warm fill light aimed at the bucket area */}
          <pointLight position={[0, -3, 3]} intensity={0.8} color="#ffddaa" distance={8} />
          <pointLight position={[2, -2, -1]} intensity={0.4} color="#aabbcc" distance={6} />
          <Stars radius={50} depth={30} count={1000} factor={3} fade speed={0.5} />
          <Scene draining={draining} apiState={connected ? state : null} />
          <OrbitControls
            enablePan={false}
            minDistance={4}
            maxDistance={14}
            maxPolarAngle={Math.PI * 0.85}
            target={[0, 0, 0]}
          />
          <Environment preset="night" />
        </Canvas>

        {/* Title overlay */}
        <div style={{ position: "absolute", top: 24, left: "50%", transform: "translateX(-50%)", zIndex: 10, textAlign: "center" }}>
          <div style={{ color: "#c4a46c", fontFamily: "Georgia, serif", fontSize: 28, letterSpacing: 4, textShadow: "0 0 20px rgba(196,164,108,0.3)", userSelect: "none" }}>
            FLOWSTATE
          </div>
          <div style={{ color: "#887755", fontFamily: "Georgia, serif", fontSize: 13, letterSpacing: 2, userSelect: "none", marginTop: 4 }}>
            ANCIENT WATER CLOCK SIMULATION
          </div>
        </div>

        {/* Controls */}
        <div style={{ position: "absolute", bottom: 40, left: "50%", transform: "translateX(-50%)", display: "flex", gap: 12, zIndex: 10 }}>
          {!connected && !draining && (
            <button onClick={handleStart} style={buttonStyle}>Start Water Flow</button>
          )}
          {!connected && draining && (
            <button onClick={handleReset} style={{ ...buttonStyle, background: "#663333" }}>Reset</button>
          )}
          {connected && (
            <>
              <button onClick={handleResetSim} disabled={resetting} style={{ ...buttonStyle, background: resetting ? "#444" : "#663333" }}>
                {resetting ? "Resetting..." : "Reset Clock"}
              </button>
              <button onClick={handleTrain} disabled={training} style={{ ...buttonStyle, background: training ? "#444" : "#335566" }}>
                {training ? "Training..." : "Train ML Model"}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Right: Metrics Panel */}
      <MetricsPanel state={state} drift={drift} stats={stats} connected={connected} />
    </div>
  )
}

const buttonStyle = {
  padding: "14px 36px",
  fontSize: 16,
  fontFamily: "Georgia, serif",
  background: "#335566",
  color: "#c4d4e4",
  border: "1px solid #556677",
  borderRadius: 6,
  cursor: "pointer",
  letterSpacing: 2,
  transition: "all 0.2s",
  userSelect: "none",
}

const panelStyle = {
  width: 320,
  padding: 20,
  background: "#111114",
  borderLeft: "1px solid #222",
  overflowY: "auto",
  fontFamily: "'SF Mono', 'Fira Code', monospace",
  scrollbarWidth: "thin",
  scrollbarColor: "#333 #111",
}
