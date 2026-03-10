import { useRef, useMemo, useEffect } from "react"
import * as THREE from "three"
import { useFrame } from "@react-three/fiber"

// Radius of funnel at a given normalized height (0=bottom, 1=top of cone)
// Cone profile: radius 1.8 at top (h=1) down to 0.3 at bottom (h=0)
function funnelRadiusAt(h) {
  return 0.3 + h * 1.5
}

// ---- Volumetric water body inside the funnel (conforms to cone shape) ----
function FunnelWater({ waterHeight, draining }) {
  const meshRef = useRef()
  const originalPositions = useRef(null)
  const topY = useRef(0)

  // Build a truncated-cone water body via LatheGeometry that fills
  // from the nozzle bottom up to the current waterHeight.
  // The top face is built into the geometry — no separate disc needed.
  const waterGeometry = useMemo(() => {
    if (waterHeight < 0.01) return null
    const segments = 32
    const inset = 0.08
    const points = []
    // Center bottom point
    points.push(new THREE.Vector2(0, 0))
    // Bottom edge at nozzle radius
    const bottomR = Math.max(funnelRadiusAt(0) - inset, 0.01)
    points.push(new THREE.Vector2(bottomR, 0))
    // Trace up the cone wall
    for (let i = 1; i <= segments; i++) {
      const t = i / segments
      const h = t * waterHeight
      const r = Math.max(funnelRadiusAt(h) - inset, 0.01)
      const y = h * 3
      points.push(new THREE.Vector2(r, y))
    }
    // Close top surface inward to center
    points.push(new THREE.Vector2(0, waterHeight * 3))
    topY.current = waterHeight * 3
    const geo = new THREE.LatheGeometry(points, 64)
    geo.computeVertexNormals()
    return geo
  }, [waterHeight])

  // Reset cached positions whenever the geometry is rebuilt so wave
  // animation baselines don't go stale.
  useEffect(() => {
    originalPositions.current = null
  }, [waterGeometry])

  // Animate wave ripples on the top surface vertices of the LatheGeometry
  useFrame((state) => {
    if (!meshRef.current || !waterGeometry) return
    const time = state.clock.elapsedTime
    const pos = meshRef.current.geometry.attributes.position

    if (!originalPositions.current || originalPositions.current.length !== pos.count * 3) {
      originalPositions.current = new Float32Array(pos.array)
    }

    const surfaceY = topY.current
    const turbulence = draining ? 0.025 : 0.006
    for (let i = 0; i < pos.count; i++) {
      const oy = originalPositions.current[i * 3 + 1]
      // Only animate vertices near the top surface
      if (Math.abs(oy - surfaceY) < 0.01) {
        const ox = originalPositions.current[i * 3]
        const oz = originalPositions.current[i * 3 + 2]
        const wave = Math.sin(time * 3 + ox * 5) * Math.cos(time * 2 + oz * 5) * turbulence
        pos.setY(i, oy + wave)
      }
    }
    pos.needsUpdate = true
  })

  if (waterHeight < 0.01 || !waterGeometry) return null

  return (
    <group position={[0, 0.5, 0]}>
      <mesh ref={meshRef} geometry={waterGeometry}>
        <meshPhysicalMaterial
          color="#1a55cc"
          transparent
          opacity={0.6}
          roughness={0.1}
          metalness={0.05}
          transmission={0.25}
          thickness={0.8}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>
    </group>
  )
}

// ---- Caustic light pattern projected onto the water ----
function Caustics({ waterHeight, draining }) {
  const lightRef = useRef()
  const targetRef = useRef()

  useFrame((state) => {
    if (!lightRef.current) return
    const time = state.clock.elapsedTime
    const y = 0.5 + waterHeight * 3
    lightRef.current.position.set(
      Math.sin(time * 0.5) * 0.3,
      y + 2,
      Math.cos(time * 0.5) * 0.3
    )
    if (targetRef.current) {
      targetRef.current.position.set(0, y - 0.5, 0)
    }
  })

  if (waterHeight < 0.05) return null

  return (
    <>
      <spotLight
        ref={lightRef}
        color="#44aaff"
        intensity={draining ? 3 : 1.5}
        angle={0.6}
        penumbra={0.8}
        distance={8}
        castShadow
        target={targetRef.current || undefined}
      />
      <mesh ref={targetRef} visible={false}>
        <sphereGeometry args={[0.01]} />
      </mesh>
    </>
  )
}

// ---- Water droplets falling from the nozzle ----
function WaterDroplets({ active, speed = 1 }) {
  const dropletsRef = useRef()
  const COUNT = 30

  const { positions, velocities, lifetimes } = useMemo(() => {
    const positions = new Float32Array(COUNT * 3)
    const velocities = new Float32Array(COUNT)
    const lifetimes = new Float32Array(COUNT)
    for (let i = 0; i < COUNT; i++) {
      resetDroplet(positions, velocities, lifetimes, i)
    }
    return { positions, velocities, lifetimes }
  }, [])

  function resetDroplet(pos, vel, life, i) {
    const angle = Math.random() * Math.PI * 2
    const r = Math.random() * 0.15
    pos[i * 3] = Math.cos(angle) * r
    pos[i * 3 + 1] = -0.1 + Math.random() * 0.2
    pos[i * 3 + 2] = Math.sin(angle) * r
    vel[i] = 0.5 + Math.random() * 1.5
    life[i] = Math.random()
  }

  useFrame((_, delta) => {
    if (!dropletsRef.current || !active) return
    const pos = dropletsRef.current.geometry.attributes.position
    const arr = pos.array

    for (let i = 0; i < COUNT; i++) {
      lifetimes[i] += delta * speed
      arr[i * 3 + 1] -= velocities[i] * delta * 3

      if (arr[i * 3 + 1] < -3.5 || lifetimes[i] > 2) {
        resetDroplet(arr, velocities, lifetimes, i)
      }
    }
    pos.needsUpdate = true
  })

  if (!active) return null

  return (
    <points ref={dropletsRef} position={[0, 0, 0]}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={COUNT}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        color="#88ccff"
        size={0.08}
        transparent
        opacity={0.8}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}

// ---- Splash particles at bucket surface ----
function SplashParticles({ active, bucketWaterLevel }) {
  const ref = useRef()
  const COUNT = 20

  const { positions, velocities, lifetimes } = useMemo(() => {
    const positions = new Float32Array(COUNT * 3)
    const velocities = new Float32Array(COUNT * 3)
    const lifetimes = new Float32Array(COUNT)
    for (let i = 0; i < COUNT; i++) {
      resetSplash(positions, velocities, lifetimes, i)
    }
    return { positions, velocities, lifetimes }
  }, [])

  function resetSplash(pos, vel, life, i) {
    const angle = Math.random() * Math.PI * 2
    const r = Math.random() * 0.15
    pos[i * 3] = Math.cos(angle) * r
    pos[i * 3 + 1] = 0
    pos[i * 3 + 2] = Math.sin(angle) * r
    vel[i * 3] = (Math.random() - 0.5) * 0.8
    vel[i * 3 + 1] = Math.random() * 2 + 0.5
    vel[i * 3 + 2] = (Math.random() - 0.5) * 0.8
    life[i] = Math.random()
  }

  useFrame((_, delta) => {
    if (!ref.current || !active) return
    const pos = ref.current.geometry.attributes.position
    const arr = pos.array

    for (let i = 0; i < COUNT; i++) {
      lifetimes[i] += delta * 2
      arr[i * 3] += velocities[i * 3] * delta
      arr[i * 3 + 1] += velocities[i * 3 + 1] * delta
      arr[i * 3 + 2] += velocities[i * 3 + 2] * delta
      velocities[i * 3 + 1] -= 5 * delta

      if (lifetimes[i] > 1) {
        resetSplash(arr, velocities, lifetimes, i)
      }
    }
    pos.needsUpdate = true
  })

  if (!active) return null

  return (
    <points ref={ref} position={[0, -3.2 + bucketWaterLevel * 1.2, 0]}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={COUNT}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        color="#aaddff"
        size={0.04}
        transparent
        opacity={0.6}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}

// ---- Main water system combining everything ----
export default function WaterSystem({ draining, waterHeight, bucketWaterLevel }) {
  return (
    <group>
      <FunnelWater waterHeight={waterHeight} draining={draining} />
      <Caustics waterHeight={waterHeight} draining={draining} />
      <WaterDroplets active={draining} speed={1.2} />
      <SplashParticles active={draining} bucketWaterLevel={bucketWaterLevel} />
    </group>
  )
}
