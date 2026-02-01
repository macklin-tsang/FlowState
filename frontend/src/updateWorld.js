export function updateWorld({ state, water, vessel, time }) {
  // Water level
  water.position.y = state.water_height * 1.8

  // Turbulence (fake via scale jitter)
  const jitter = 1 + Math.sin(time * 4) * state.turbulence * 0.02
  water.scale.set(jitter, 1, jitter)

  // Confidence = calmness
  water.material.opacity = 0.5 + state.confidence * 0.4

  // Vessel subtle distortion (future erosion hook)
  vessel.scale.y = 1 - state.erosion * 0.05

  const pos = water.geometry.attributes.position

    for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i)
    const z = pos.getZ(i)

    const wave =
        Math.sin(time * 2 + x * 4) *
        Math.cos(time * 2 + z * 4) *
        state.turbulence * 0.02

    pos.setY(i, wave)
    }

    pos.needsUpdate = true
    water.geometry.computeVertexNormals()
    water.geometry.computeBoundingSphere() // 👈 THIS LINE

}
