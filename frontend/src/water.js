import * as THREE from "three"

export function createWater() {
    const geometry = new THREE.CircleGeometry(1.1, 64)
    geometry.computeVertexNormals()


  const material = new THREE.MeshStandardMaterial({
    color: 0x3366ff,
    transparent: true,
    opacity: 0.85,
    side: THREE.DoubleSide
  })

  const water = new THREE.Mesh(geometry, material)
  
  water.rotation.x = -Math.PI / 2
  water.position.y = 0

  return water
}
