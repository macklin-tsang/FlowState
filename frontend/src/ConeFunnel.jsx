import { useMemo } from "react"
import * as THREE from "three"

export default function ConeFunnel() {
  // Create a cone geometry: wide top, narrow bottom
  // ConeGeometry(radiusTop, radiusBottom, height, radialSegments, openEnded)
  // We use a custom LatheGeometry for a proper funnel shape
  const funnelGeometry = useMemo(() => {
    const points = []
    const segments = 40
    for (let i = 0; i <= segments; i++) {
      const t = i / segments
      // t=0 is top (wide), t=1 is bottom (narrow)
      const radius = 1.8 - t * 1.5 // from 1.8 down to 0.3
      const y = (1 - t) * 3 // height from 0 to 3, top at 3
      points.push(new THREE.Vector2(radius, y))
    }
    // Add the narrow tube at bottom
    points.push(new THREE.Vector2(0.3, -0.2))
    points.push(new THREE.Vector2(0.3, -0.6))
    return new THREE.LatheGeometry(points, 64)
  }, [])

  return (
    <group position={[0, 0.5, 0]}>
      {/* Glass funnel */}
      <mesh geometry={funnelGeometry}>
        <meshPhysicalMaterial
          color="#b8926a"
          transmission={0.6}
          roughness={0.3}
          thickness={0.15}
          transparent
          opacity={0.45}
          side={THREE.DoubleSide}
          metalness={0.1}
          clearcoat={0.3}
        />
      </mesh>

      {/* Rim ring at top for visual definition */}
      <mesh position={[0, 3, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.8, 0.06, 16, 64]} />
        <meshStandardMaterial color="#8b7355" metalness={0.6} roughness={0.4} />
      </mesh>

      {/* Bottom nozzle ring */}
      <mesh position={[0, -0.6, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.3, 0.04, 16, 64]} />
        <meshStandardMaterial color="#8b7355" metalness={0.6} roughness={0.4} />
      </mesh>
    </group>
  )
}
