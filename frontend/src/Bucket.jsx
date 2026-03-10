import { useRef, useMemo } from "react"
import * as THREE from "three"
import { useFrame } from "@react-three/fiber"

export default function Bucket({ waterLevel = 0 }) {
  const waterRef = useRef()

  // Bucket shape via LatheGeometry
  const bucketGeometry = useMemo(() => {
    const points = [
      new THREE.Vector2(0.9, 1.4),  // top rim
      new THREE.Vector2(0.85, 1.35), // inner rim
      new THREE.Vector2(0.85, 0.05), // inner wall bottom
      new THREE.Vector2(0.0, 0.05),  // bottom center
      new THREE.Vector2(0.0, 0.0),   // bottom outside
      new THREE.Vector2(0.9, 0.0),   // outer wall bottom
      new THREE.Vector2(0.95, 0.05), // outer wall
      new THREE.Vector2(0.95, 1.4),  // outer wall top
      new THREE.Vector2(0.9, 1.4),   // close loop
    ]
    return new THREE.LatheGeometry(points, 64)
  }, [])

  useFrame((_, delta) => {
    if (waterRef.current) {
      // Gentle ripple on the bucket water surface
      waterRef.current.position.y = waterLevel * 1.2 + Math.sin(Date.now() * 0.002) * 0.005
    }
  })

  return (
    <group position={[0, -3.2, 0]}>
      {/* Wooden bucket */}
      <mesh geometry={bucketGeometry}>
        <meshStandardMaterial
          color="#6b4226"
          roughness={0.85}
          metalness={0.05}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Metal bands */}
      {[0.3, 0.8, 1.2].map((y, i) => (
        <mesh key={i} position={[0, y, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.92, 0.025, 8, 64]} />
          <meshStandardMaterial color="#555" metalness={0.8} roughness={0.3} />
        </mesh>
      ))}

      {/* Collected water */}
      {waterLevel > 0.01 && (
        <mesh ref={waterRef} position={[0, waterLevel * 1.2, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <circleGeometry args={[0.82, 64]} />
          <meshStandardMaterial
            color="#2255cc"
            transparent
            opacity={0.75}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}
    </group>
  )
}
