"""Three.js WebGL Operational Fleet View component for Streamlit.

Implementation grounded in MengTo Three.js and WebGL skills:
- Real PBR WebGL scene (THREE.WebGLRenderer, ACESFilmicToneMapping, sRGB).
- Primary visual risk encoding: ELEVATION (Y-axis height corresponds to risk).
- Secondary visual risk encoding: COLOR (Muted Blue, Amber, Crimson).
- Orbital reticle ring for Top 15 priority dispatches.
- Restrained animation reserved for active selection.
- OrbitControls with smooth damping, pointer raycasting, hover tooltip, and click-to-select camera easing.
- Explicit label: 'Operational Network / Fleet View — Abstract topology, not geographic coordinates'.
"""

from __future__ import annotations

import json
from typing import Any
import streamlit.components.v1 as components


def render_three_fleet_view(
    nodes: list[dict[str, Any]],
    selected_gateway_id: str | None = None,
    height: int = 540,
) -> None:
    """Render the interactive Three.js 3D Operational Fleet View."""
    nodes_json = json.dumps(nodes)
    selected_id_json = json.dumps(selected_gateway_id or "")

    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
          background-color: #0E1117;
          color: #F1F5F9;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
          overflow: hidden;
          width: 100vw;
          height: {height}px;
          position: relative;
        }}
        #webgl-canvas {{
          width: 100%;
          height: 100%;
          display: block;
        }}
        .hud-overlay {{
          position: absolute;
          top: 12px;
          left: 14px;
          background: rgba(19, 23, 34, 0.85);
          border: 1px solid #2A2E39;
          border-radius: 6px;
          padding: 8px 14px;
          font-size: 11px;
          pointer-events: none;
          z-index: 10;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}
        .hud-title {{
          font-weight: 600;
          color: #94A3B8;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 2px;
        }}
        .hud-legend {{
          display: flex;
          gap: 12px;
          margin-top: 6px;
          font-size: 10px;
        }}
        .legend-item {{
          display: flex;
          align-items: center;
          gap: 4px;
        }}
        .legend-dot {{
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }}
        #tooltip {{
          position: absolute;
          display: none;
          background: #1E222D;
          border: 1px solid #3B82F6;
          border-radius: 6px;
          padding: 8px 12px;
          font-size: 12px;
          pointer-events: none;
          z-index: 20;
          box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        }}
        .tooltip-row {{
          display: flex;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 2px;
        }}
        .tooltip-label {{ color: #94A3B8; }}
        .tooltip-val {{ font-weight: 600; color: #F1F5F9; font-family: monospace; }}
        .badge-dispatched {{
          color: #C084FC;
          font-weight: bold;
          font-size: 10px;
          border-top: 1px solid #2A2E39;
          padding-top: 4px;
          margin-top: 4px;
        }}
      </style>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
      <div class="hud-overlay">
        <div class="hud-title">Operational Network / Fleet View — Abstract topology, not geographic coordinates.</div>
        <div style="color: #94A3B8; font-size: 10px;">Primary Visual Encoding: Elevation = Risk Probability &nbsp;|&nbsp; Secondary: Color &nbsp;|&nbsp; Reticles: Top 15 Priority</div>
        <div class="hud-legend">
          <div class="legend-item"><span class="legend-dot" style="background:#3B82F6;"></span> Low (&lt;0.30)</div>
          <div class="legend-item"><span class="legend-dot" style="background:#F59E0B;"></span> Mod (0.30–0.70)</div>
          <div class="legend-item"><span class="legend-dot" style="background:#EF4444;"></span> High (&ge;0.70)</div>
          <div class="legend-item"><span class="legend-dot" style="background:#475569;"></span> Unassigned (Ground)</div>
          <div class="legend-item"><span class="legend-dot" style="border: 2px solid #8B5CF6; border-radius: 50%;"></span> Top 15 Priority</div>
        </div>
      </div>
      <div id="tooltip"></div>
      <canvas id="webgl-canvas"></canvas>

      <script>
        const nodesData = {nodes_json};
        const activeSelectedId = {selected_id_json};

        const container = document.body;
        const canvas = document.getElementById("webgl-canvas");
        const tooltip = document.getElementById("tooltip");

        // Scene, Camera, Renderer setup (PBR & Performance best practices)
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0E1117);
        scene.fog = new THREE.FogExp2(0x0E1117, 0.015);

        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / {height}, 0.1, 1000);
        camera.position.set(0, 32, 48);

        const renderer = new THREE.WebGLRenderer({{
          canvas: canvas,
          antialias: true,
          alpha: false,
          powerPreference: "high-performance"
        }});
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(window.innerWidth, {height});
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.1;

        // OrbitControls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.maxPolarAngle = Math.PI / 2.1;
        controls.minDistance = 10;
        controls.maxDistance = 120;
        controls.target.set(0, 4, 0);

        // Industrial Lighting
        const ambientLight = new THREE.AmbientLight(0x334155, 1.2);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xF8FAFC, 1.4);
        dirLight.position.set(25, 45, 20);
        scene.add(dirLight);

        const fillLight = new THREE.DirectionalLight(0x38BDF8, 0.6);
        fillLight.position.set(-25, 15, -20);
        scene.add(fillLight);

        // Ground Reference Grid (Restrained operational datum plane)
        const gridHelper = new THREE.GridHelper(60, 30, 0x2A2E39, 0x1E222D);
        gridHelper.position.y = 0;
        scene.add(gridHelper);

        // Build Gateway Nodes
        const meshes = [];
        const baseSphereGeo = new THREE.SphereGeometry(0.85, 24, 24);
        const ringGeo = new THREE.RingGeometry(1.2, 1.4, 32);
        ringGeo.rotateX(-Math.PI / 2);

        const nodeGroup = new THREE.Group();
        scene.add(nodeGroup);

        nodesData.forEach(item => {{
          const nodeColor = new THREE.Color(item.color);
          const mat = new THREE.MeshStandardMaterial({{
            color: nodeColor,
            roughness: 0.35,
            metalness: 0.25,
            emissive: item.is_selected ? 0x60A5FA : (item.is_dispatched ? nodeColor : 0x000000),
            emissiveIntensity: item.is_selected ? 0.6 : (item.is_dispatched ? 0.3 : 0.0)
          }});

          const mesh = new THREE.Mesh(baseSphereGeo, mat);
          mesh.position.set(item.x, item.elevation, item.z);
          mesh.userData = item;

          // Vertical tether to baseline ground plane to accentuate elevation encoding
          const tetherGeo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(item.x, 0, item.z),
            new THREE.Vector3(item.x, item.elevation, item.z)
          ]);
          const tetherMat = new THREE.LineBasicMaterial({{
            color: item.is_dispatched ? 0x8B5CF6 : 0x2A2E39,
            transparent: true,
            opacity: item.is_dispatched ? 0.8 : 0.4
          }});
          const tether = new THREE.Line(tetherGeo, tetherMat);
          nodeGroup.add(tether);

          // If prioritized in Top 15, add an orbital indicator ring
          if (item.is_dispatched) {{
            const ringMat = new THREE.MeshBasicMaterial({{
              color: 0x8B5CF6,
              side: THREE.DoubleSide
            }});
            const ringMesh = new THREE.Mesh(ringGeo, ringMat);
            ringMesh.position.set(item.x, item.elevation, item.z);
            nodeGroup.add(ringMesh);
            mesh.userData.ringMesh = ringMesh;
          }}

          nodeGroup.add(mesh);
          meshes.push(mesh);
        }});

        // Raycasting for pointer hover and click
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        let hoveredMesh = null;

        window.addEventListener("pointermove", (event) => {{
          const rect = canvas.getBoundingClientRect();
          mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
          mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

          raycaster.setFromCamera(mouse, camera);
          const intersects = raycaster.intersectObjects(meshes);

          if (intersects.length > 0) {{
            const hit = intersects[0].object;
            if (hoveredMesh !== hit) {{
              if (hoveredMesh && !hoveredMesh.userData.is_selected) {{
                hoveredMesh.scale.set(1.0, 1.0, 1.0);
              }}
              hoveredMesh = hit;
              hoveredMesh.scale.set(1.25, 1.25, 1.25);
            }}

            const d = hit.userData;
            tooltip.style.display = "block";
            tooltip.style.left = (event.clientX + 14) + "px";
            tooltip.style.top = (event.clientY - 10) + "px";

            let riskText = (d.risk !== null && d.risk !== undefined) ? (d.risk * 100).toFixed(1) + "%" : "Unassigned (>15)";
            let elevationText = (d.risk !== null && d.risk !== undefined) ? d.elevation.toFixed(1) + "m" : "0.0m (Ground Datum)";

            let html = `
              <div class="tooltip-row"><span class="tooltip-label">Gateway:</span><span class="tooltip-val">${{d.gateway_id}}</span></div>
              <div class="tooltip-row"><span class="tooltip-label">Risk Probability:</span><span class="tooltip-val">${{riskText}}</span></div>
              <div class="tooltip-row"><span class="tooltip-label">Elevation (Risk):</span><span class="tooltip-val">${{elevationText}}</span></div>
            `;
            if (d.is_dispatched) {{
              html += `<div class="badge-dispatched">★ PRIORITY DISPATCH — Rank #${{d.rank}}</div>`;
            }}
            tooltip.innerHTML = html;
          }} else {{
            if (hoveredMesh && !hoveredMesh.userData.is_selected) {{
              hoveredMesh.scale.set(1.0, 1.0, 1.0);
            }}
            hoveredMesh = null;
            tooltip.style.display = "none";
          }}
        }});

        // Click to focus camera smoothly on the node
        window.addEventListener("click", (event) => {{
          raycaster.setFromCamera(mouse, camera);
          const intersects = raycaster.intersectObjects(meshes);
          if (intersects.length > 0) {{
            const targetNode = intersects[0].object;
            const pos = targetNode.position;
            // Ease controls target towards node
            controls.target.set(pos.x, pos.y, pos.z);
          }}
        }});

        // Resize handler
        window.addEventListener("resize", () => {{
          camera.aspect = window.innerWidth / {height};
          camera.updateProjectionMatrix();
          renderer.setSize(window.innerWidth, {height});
        }});

        // Render loop with subtle breathing pulse on selected node
        let clock = new THREE.Clock();
        function animate() {{
          requestAnimationFrame(animate);
          const elapsed = clock.getElapsedTime();

          controls.update();

          // Subtle pulse on dispatched or selected nodes
          meshes.forEach(m => {{
            if (m.userData.is_selected) {{
              const s = 1.2 + 0.1 * Math.sin(elapsed * 4.0);
              m.scale.set(s, s, s);
            }} else if (m.userData.is_dispatched && hoveredMesh !== m) {{
              const s = 1.0 + 0.04 * Math.sin(elapsed * 2.5);
              m.scale.set(s, s, s);
            }}
          }});

          renderer.render(scene, camera);
        }}
        animate();
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=False)
