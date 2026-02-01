import * as THREE from "three"

import { createScene } from "./scene"
import { createVessel } from "./vessel"
import { createWater } from "./water"
import { state } from "./state"
import { updateWorld } from "./updateWorld"

const { scene, camera, renderer } = createScene()

const vessel = createVessel()
const water = createWater()

scene.add(vessel)
scene.add(water)

// Lights
scene.add(new THREE.AmbientLight(0xffffff, 0.4))

const light = new THREE.DirectionalLight(0xffffff, 0.8)
light.position.set(3, 5, 2)
scene.add(light)

let t = 0

function animate() {
  t += 0.016

  // Fake learning (for now)
  state.confidence = Math.min(1, state.confidence + 0.0005)
  state.turbulence = 1 - state.confidence

  updateWorld({ state, water, vessel, time: t })

  renderer.render(scene, camera)
  requestAnimationFrame(animate)
}

animate()
