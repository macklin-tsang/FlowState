import * as THREE from "three"

export function createVessel() {
  const geometry = new THREE.CylinderGeometry(1, 1, 2, 64, 1, true)

  const material = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    transmission: 1.0,
    roughness: 0.05,
    thickness: 0.1,
    transparent: true,
    opacity: 0.9
  })

  const cylinder = new THREE.Mesh(geometry, material)
  cylinder.position.y = 1

  return cylinder
}
