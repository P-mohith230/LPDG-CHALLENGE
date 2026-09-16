---
name: threejs
description: Use when building or debugging interactive 3D scenes on the web with Three.js (scene/camera/renderer, lights/materials, raycasting, controls, performance).
---

# Three.js — WebGL 3D Scenes Skill

## When to use
- Real 3D: interactive gateway networks, node topologies, 3D data viz, camera transitions
- You need full control beyond CSS or static charts
- Realtime interaction: raycasting, hover, click-to-select, orbit controls

## Core mental model
- Create:
  - `Scene` (root graph)
  - `Camera` (PerspectiveCamera with proper FOV and aspect)
  - `Renderer` (`WebGLRenderer` with antialias, alpha, sRGB, ACESFilmicToneMapping)
  - `Mesh` = `Geometry` + `Material` (prefer `MeshStandardMaterial` or `InstancedMesh` for multi-nodes)
  - `Raycaster` for pointer interaction (hover, click, selection)
  - Lights: DirectionalLight + AmbientLight / HemisphereLight
- Render loop:
  - `requestAnimationFrame(animate)`
  - Update animations, controls, transitions, then `renderer.render(scene, camera)`

## Key APIs/patterns
- Setup:
  ```js
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  ```
- Camera & Controls:
  ```js
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  ```
- Cleanup & Performance:
  - Call `.dispose()` on geometries, materials, textures, renderer.
  - Cancel RAF on teardown.
  - Use InstancedMesh or shared geometries when rendering hundreds of gateway nodes.
