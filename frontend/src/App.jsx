import React, { useState, useCallback, useRef } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls, Environment, Stars } from "@react-three/drei"
import ConeFunnel from "./ConeFunnel"
import Bucket from "./Bucket"
import WaterSystem from "./WaterSystem"

function Scene({ draining }) {
  const [waterHeight, setWaterHeight] = useState(0.85)
  const [bucketWaterLevel, setBucketWaterLevel] = useState(0)
  const drainingRef = useRef(draining)
  drainingRef.current = draining

  useFrame((_, delta) => {
    if (!drainingRef.current) return

    setWaterHeight((h) => {
      const next = h - delta * 0.06
      return Math.max(next, 0)
    })

    setBucketWaterLevel((b) => {
      const next = b + delta * 0.04
      return Math.min(next, 1)
    })
  })

  return (
    <>
      <ConeFunnel />
      <Bucket waterLevel={bucketWaterLevel} />
      <WaterSystem
        draining={draining}
        waterHeight={waterHeight}
        bucketWaterLevel={bucketWaterLevel}
      />
    </>
  )
}

export default function App() {
  const [draining, setDraining] = useState(false)

  const handleStart = useCallback(() => {
    setDraining(true)
  }, [])

  const handleReset = useCallback(() => {
    setDraining(false)
  }, [])

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <Canvas
        camera={{ position: [0, 1, 7], fov: 50 }}
        shadows
        gl={{ antialias: true, alpha: false }}
        onCreated={({ gl }) => gl.setClearColor("#0b0b0f")}
      >
        <ambientLight intensity={0.3} />
        <directionalLight position={[3, 6, 2]} intensity={0.8} castShadow />
        <directionalLight position={[-2, 4, -3]} intensity={0.3} color="#8888ff" />
        <pointLight position={[0, -2, 2]} intensity={0.4} color="#4488ff" />

        <Stars radius={50} depth={30} count={1000} factor={3} fade speed={0.5} />

        <Scene draining={draining} />

        <OrbitControls
          enablePan={false}
          minDistance={4}
          maxDistance={14}
          maxPolarAngle={Math.PI * 0.85}
          target={[0, 0, 0]}
        />

        <Environment preset="night" />
      </Canvas>

      {/* UI Overlay */}
      <div
        style={{
          position: "absolute",
          bottom: 40,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: 16,
          zIndex: 10,
        }}
      >
        {!draining ? (
          <button onClick={handleStart} style={buttonStyle}>
            Start Water Flow
          </button>
        ) : (
          <button onClick={handleReset} style={{ ...buttonStyle, background: "#663333" }}>
            Reset
          </button>
        )}
      </div>

      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 24,
          left: "50%",
          transform: "translateX(-50%)",
          color: "#c4a46c",
          fontFamily: "Georgia, serif",
          fontSize: 28,
          letterSpacing: 4,
          textShadow: "0 0 20px rgba(196,164,108,0.3)",
          userSelect: "none",
          zIndex: 10,
        }}
      >
        ANCIENT WATER CLOCK
      </div>

      {/* Subtitle */}
      <div
        style={{
          position: "absolute",
          top: 64,
          left: "50%",
          transform: "translateX(-50%)",
          color: "#887755",
          fontFamily: "Georgia, serif",
          fontSize: 13,
          letterSpacing: 2,
          userSelect: "none",
          zIndex: 10,
        }}
      >
        CLEPSYDRA
      </div>
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
