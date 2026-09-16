"""Three.js WebGL Operational Fleet View component for Streamlit.

Implementation grounded in .agents/skills/threejs/SKILL.md:
- Precision telemetry pillars for prioritized dispatches (vertical laser stem + sensor cap).
- Flat ground datum pucks (Y = 0.0m) for undispatched fleet assets.
- Dual elevation iso-planes at p=0.50 (operational deficit) and p=0.70 (critical risk).
- Vertical risk elevation reference ruler (0% to 100% probability).
- Interactive on-canvas viewport presets: Isometric, Top-Down, Focus Top 15, Toggle Filter.
- Calm CAD-style rendering with ZERO disturbing animations, smooth damped OrbitControls.
- Structured high-density telemetry inspection card.
- Explicit label: 'Operational Network / Fleet View — Abstract topology, not geographic coordinates'.
"""

from __future__ import annotations

import json
from typing import Any
import streamlit.components.v1 as components


def render_three_fleet_view(
    nodes: list[dict[str, Any]],
    selected_gateway_id: str | None = None,
    height: int = 560,
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
          user-select: none;
        }}
        #webgl-canvas {{
          width: 100%;
          height: 100%;
          display: block;
        }}
        /* Top-Left Informative HUD Overlay */
        .hud-overlay {{
          position: absolute;
          top: 12px;
          left: 14px;
          background: rgba(19, 23, 34, 0.90);
          border: 1px solid #2A2E39;
          border-radius: 6px;
          padding: 10px 14px;
          font-size: 11px;
          pointer-events: none;
          z-index: 10;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(4px);
        }}
        .hud-title {{
          font-weight: 700;
          color: #F8FAFC;
          font-size: 11px;
          letter-spacing: 0.4px;
          margin-bottom: 2px;
        }}
        .hud-subtitle {{
          color: #94A3B8;
          font-size: 10px;
          margin-bottom: 8px;
        }}
        .hud-legend {{
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          font-size: 10px;
          border-top: 1px solid #2A2E39;
          padding-top: 6px;
        }}
        .legend-item {{
          display: flex;
          align-items: center;
          gap: 5px;
          color: #CBD5E1;
        }}
        .legend-dot {{
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }}
        .legend-ring {{
          width: 9px;
          height: 9px;
          border: 2px solid #8B5CF6;
          border-radius: 50%;
        }}

        /* Top-Right Interactive Viewport Presets Dock */
        .viewport-controls {{
          position: absolute;
          top: 12px;
          right: 14px;
          display: flex;
          gap: 6px;
          z-index: 15;
        }}
        .vp-btn {{
          background: rgba(30, 34, 45, 0.88);
          border: 1px solid #334155;
          color: #E2E8F0;
          font-size: 11px;
          font-weight: 500;
          padding: 6px 10px;
          border-radius: 5px;
          cursor: pointer;
          transition: all 0.15s ease;
          display: flex;
          align-items: center;
          gap: 4px;
          backdrop-filter: blur(4px);
        }}
        .vp-btn:hover {{
          background: #2563EB;
          border-color: #3B82F6;
          color: #FFFFFF;
        }}
        .vp-btn.active {{
          background: #1D4ED8;
          border-color: #60A5FA;
          color: #FFFFFF;
        }}

        /* High-Density CAD Inspection Card */
        #tooltip {{
          position: absolute;
          display: none;
          background: rgba(15, 23, 42, 0.95);
          border: 1px solid #38BDF8;
          border-radius: 6px;
          padding: 10px 14px;
          font-size: 11px;
          pointer-events: none;
          z-index: 25;
          box-shadow: 0 8px 28px rgba(0, 0, 0, 0.75);
          min-width: 250px;
          backdrop-filter: blur(8px);
        }}
        .tt-header {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid #334155;
          padding-bottom: 5px;
          margin-bottom: 6px;
        }}
        .tt-gw {{
          font-family: monospace;
          font-weight: 700;
          color: #38BDF8;
          font-size: 12px;
        }}
        .tt-badge {{
          font-size: 9px;
          font-weight: 700;
          padding: 2px 6px;
          border-radius: 3px;
          text-transform: uppercase;
        }}
        .tt-badge-p15 {{ background: rgba(139, 92, 246, 0.3); color: #C084FC; border: 1px solid #8B5CF6; }}
        .tt-badge-norm {{ background: rgba(71, 85, 105, 0.3); color: #94A3B8; border: 1px solid #475569; }}
        .tt-grid {{
          display: grid;
          grid-template-columns: 105px 1fr;
          row-gap: 3px;
          font-size: 10.5px;
        }}
        .tt-label {{ color: #94A3B8; }}
        .tt-val {{ color: #F1F5F9; font-weight: 600; font-family: monospace; }}
        .tt-reason {{
          margin-top: 6px;
          border-top: 1px solid #334155;
          padding-top: 5px;
          font-size: 10px;
          color: #CBD5E1;
          line-height: 1.35;
        }}
      </style>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
      <!-- Top-Left Operational HUD -->
      <div class="hud-overlay">
        <div class="hud-title">OPERATIONAL NETWORK / FLEET VIEW</div>
        <div class="hud-subtitle">Abstract topology, not geographic coordinates &nbsp;|&nbsp; Primary Risk Encoding: Elevation (Y-Axis)</div>
        <div class="hud-legend">
          <div class="legend-item"><span class="legend-dot" style="background:#EF4444;"></span> High (&ge;0.70)</div>
          <div class="legend-item"><span class="legend-dot" style="background:#F59E0B;"></span> Mod (0.30–0.70)</div>
          <div class="legend-item"><span class="legend-dot" style="background:#3B82F6;"></span> Low (&lt;0.30)</div>
          <div class="legend-item"><span class="legend-dot" style="background:#475569;"></span> Ground Fleet (Datum)</div>
          <div class="legend-item"><span class="legend-ring"></span> Top 15 Priority</div>
        </div>
      </div>

      <!-- Top-Right Viewport Presets Dock -->
      <div class="viewport-controls">
        <button class="vp-btn" id="btn-iso" title="45-Degree Isometric Perspective">📐 Isometric</button>
        <button class="vp-btn" id="btn-top" title="Birds-Eye Orthogonal Fleet View">🗺️ Top-Down</button>
        <button class="vp-btn" id="btn-focus" title="Focus Camera on Prioritized Dispatches">🎯 Focus Top 15</button>
        <button class="vp-btn" id="btn-filter" title="Toggle between Full Fleet and Dispatched Only">👁️ Filter: All (332)</button>
        <button class="vp-btn" id="btn-reset" title="Reset Camera View">🔄 Reset</button>
      </div>

      <!-- High-Density Tooltip -->
      <div id="tooltip"></div>
      <canvas id="webgl-canvas"></canvas>

      <script>
        const nodesData = {nodes_json};
        const activeSelectedId = {selected_id_json};

        const canvas = document.getElementById("webgl-canvas");
        const tooltip = document.getElementById("tooltip");

        // Scene, Camera, Renderer setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0E1117);
        scene.fog = new THREE.FogExp2(0x0E1117, 0.012);

        const camera = new THREE.PerspectiveCamera(42, window.innerWidth / {height}, 0.1, 1000);
        const defaultCamPos = new THREE.Vector3(26, 26, 38);
        const defaultTarget = new THREE.Vector3(0, 3.5, 0);
        camera.position.copy(defaultCamPos);

        const renderer = new THREE.WebGLRenderer({{
          canvas: canvas,
          antialias: true,
          alpha: false,
          powerPreference: "high-performance"
        }});
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(window.innerWidth, {height});
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.15;

        // Smooth OrbitControls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.maxPolarAngle = Math.PI / 2.05;
        controls.minDistance = 8;
        controls.maxDistance = 140;
        controls.target.copy(defaultTarget);

        // Industrial Lighting Rig
        const ambientLight = new THREE.AmbientLight(0x475569, 1.3);
        scene.add(ambientLight);

        const dirLight1 = new THREE.DirectionalLight(0xF8FAFC, 1.5);
        dirLight1.position.set(30, 50, 25);
        scene.add(dirLight1);

        const fillLight = new THREE.DirectionalLight(0x38BDF8, 0.7);
        fillLight.position.set(-30, 20, -25);
        scene.add(fillLight);

        // Ground Reference Grid
        const gridHelper = new THREE.GridHelper(56, 28, 0x334155, 0x1E293B);
        gridHelper.position.y = 0;
        scene.add(gridHelper);

        // =====================================================================
        // DUAL ELEVATION ISO-PLANES (p = 0.50 and p = 0.70)
        // =====================================================================
        // Iso-Plane 1: p = 0.50 (Operational Collection Deficit Line, Elevation = 7.0m)
        const isoGroup = new THREE.Group();
        scene.add(isoGroup);

        const iso50RingGeo = new THREE.RingGeometry(0.1, 24, 64);
        iso50RingGeo.rotateX(-Math.PI / 2);
        const iso50Mat = new THREE.MeshBasicMaterial({{
          color: 0xF59E0B,
          transparent: true,
          opacity: 0.05,
          side: THREE.DoubleSide
        }});
        const iso50Mesh = new THREE.Mesh(iso50RingGeo, iso50Mat);
        iso50Mesh.position.y = 7.0;
        isoGroup.add(iso50Mesh);

        // Outer contour boundary for p = 0.50
        const iso50BoundaryGeo = new THREE.BufferGeometry();
        const pts50 = [];
        for (let i = 0; i <= 64; i++) {{
          const a = (i / 64) * Math.PI * 2;
          pts50.push(new THREE.Vector3(Math.cos(a) * 24, 7.0, Math.sin(a) * 24));
        }}
        iso50BoundaryGeo.setFromPoints(pts50);
        const iso50Line = new THREE.Line(iso50BoundaryGeo, new THREE.LineBasicMaterial({{
          color: 0xF59E0B,
          transparent: true,
          opacity: 0.45
        }}));
        isoGroup.add(iso50Line);

        // Iso-Plane 2: p = 0.70 (Critical Failure Line, Elevation = 9.8m)
        const iso70RingGeo = new THREE.RingGeometry(0.1, 22, 64);
        iso70RingGeo.rotateX(-Math.PI / 2);
        const iso70Mat = new THREE.MeshBasicMaterial({{
          color: 0xEF4444,
          transparent: true,
          opacity: 0.05,
          side: THREE.DoubleSide
        }});
        const iso70Mesh = new THREE.Mesh(iso70RingGeo, iso70Mat);
        iso70Mesh.position.y = 9.8;
        isoGroup.add(iso70Mesh);

        const iso70BoundaryGeo = new THREE.BufferGeometry();
        const pts70 = [];
        for (let i = 0; i <= 64; i++) {{
          const a = (i / 64) * Math.PI * 2;
          pts70.push(new THREE.Vector3(Math.cos(a) * 22, 9.8, Math.sin(a) * 22));
        }}
        iso70BoundaryGeo.setFromPoints(pts70);
        const iso70Line = new THREE.Line(iso70BoundaryGeo, new THREE.LineBasicMaterial({{
          color: 0xEF4444,
          transparent: true,
          opacity: 0.50
        }}));
        isoGroup.add(iso70Line);

        // =====================================================================
        // VERTICAL RISK ELEVATION REFERENCE RULER
        // =====================================================================
        const rulerGroup = new THREE.Group();
        rulerGroup.position.set(-23, 0, -23);
        scene.add(rulerGroup);

        const rulerStemGeo = new THREE.CylinderGeometry(0.08, 0.08, 14.0, 12);
        rulerStemGeo.translate(0, 7.0, 0);
        const rulerStem = new THREE.Mesh(rulerStemGeo, new THREE.MeshBasicMaterial({{ color: 0x64748B }}));
        rulerGroup.add(rulerStem);

        // Tick marks at 0%, 30% (4.2m), 50% (7m), 70% (9.8m), 100% (14m)
        const tickHeights = [
          {{ y: 0.0, label: "0%", color: 0x64748B }},
          {{ y: 4.2, label: "30%", color: 0x3B82F6 }},
          {{ y: 7.0, label: "50%", color: 0xF59E0B }},
          {{ y: 9.8, label: "70%", color: 0xEF4444 }},
          {{ y: 14.0, label: "100%", color: 0xEF4444 }},
        ];
        tickHeights.forEach(th => {{
          const tickGeo = new THREE.BoxGeometry(0.9, 0.05, 0.05);
          const tickMesh = new THREE.Mesh(tickGeo, new THREE.MeshBasicMaterial({{ color: th.color }}));
          tickMesh.position.set(0.45, th.y, 0);
          rulerGroup.add(tickMesh);
        }});

        // =====================================================================
        // BUILD ASSET NODES & TELEMETRY PILLARS
        // =====================================================================
        const meshes = [];
        const dispatchedGroup = new THREE.Group();
        const groundPuckGroup = new THREE.Group();
        scene.add(dispatchedGroup);
        scene.add(groundPuckGroup);

        // Shared geometries
        const puckGeo = new THREE.CylinderGeometry(0.38, 0.38, 0.12, 16);
        const sensorCapGeo = new THREE.CylinderGeometry(0.72, 0.72, 0.42, 24);
        const ringGeo = new THREE.RingGeometry(1.25, 1.45, 32);
        ringGeo.rotateX(-Math.PI / 2);

        nodesData.forEach(item => {{
          const isDispatched = item.is_dispatched;
          const nodeColor = new THREE.Color(item.color);

          if (isDispatched) {{
            // TELEMETRY PILLAR (Vertical Stem + Sensor Cap)
            const elev = Math.max(0.2, item.elevation);

            // 1. Vertical laser stem
            const stemGeo = new THREE.CylinderGeometry(0.09, 0.09, elev, 12);
            stemGeo.translate(0, elev / 2, 0);
            const stemMat = new THREE.MeshBasicMaterial({{
              color: nodeColor,
              transparent: true,
              opacity: 0.65
            }});
            const stemMesh = new THREE.Mesh(stemGeo, stemMat);
            stemMesh.position.set(item.x, 0, item.z);
            dispatchedGroup.add(stemMesh);

            // 2. Base anchor ring on ground plane
            const anchorGeo = new THREE.RingGeometry(0.3, 0.55, 16);
            anchorGeo.rotateX(-Math.PI / 2);
            const anchorMesh = new THREE.Mesh(anchorGeo, new THREE.MeshBasicMaterial({{
              color: nodeColor,
              side: THREE.DoubleSide,
              transparent: true,
              opacity: 0.5
            }}));
            anchorMesh.position.set(item.x, 0.02, item.z);
            dispatchedGroup.add(anchorMesh);

            // 3. Sensor Cap Head (Interactive Raycast Target)
            const capMat = new THREE.MeshStandardMaterial({{
              color: nodeColor,
              roughness: 0.28,
              metalness: 0.42,
              emissive: nodeColor,
              emissiveIntensity: item.is_selected ? 0.7 : 0.25
            }});
            const capMesh = new THREE.Mesh(sensorCapGeo, capMat);
            capMesh.position.set(item.x, elev, item.z);
            capMesh.userData = item;

            // 4. Orbital Priority Reticle Ring
            const ringMat = new THREE.MeshBasicMaterial({{
              color: 0x8B5CF6,
              side: THREE.DoubleSide
            }});
            const reticle = new THREE.Mesh(ringGeo, ringMat);
            reticle.position.set(item.x, elev, item.z);
            dispatchedGroup.add(reticle);

            dispatchedGroup.add(capMesh);
            meshes.push(capMesh);
          }} else {{
            // GROUND DATUM PUCK (Nominal Fleet Asset resting on Y=0)
            const puckMat = new THREE.MeshStandardMaterial({{
              color: 0x334155,
              roughness: 0.6,
              metalness: 0.2
            }});
            const puckMesh = new THREE.Mesh(puckGeo, puckMat);
            puckMesh.position.set(item.x, 0.06, item.z);
            puckMesh.userData = item;

            groundPuckGroup.add(puckMesh);
            meshes.push(puckMesh);
          }}
        }});

        // =====================================================================
        // RAYCASTING FOR POINTER HOVER & CLICK
        // =====================================================================
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
              hoveredMesh.scale.set(1.18, 1.18, 1.18);
            }}

            const d = hit.userData;
            tooltip.style.display = "block";
            tooltip.style.left = Math.min(window.innerWidth - 270, event.clientX + 14) + "px";
            tooltip.style.top = Math.max(10, event.clientY - 20) + "px";

            let riskText = (d.risk !== null && d.risk !== undefined) ? (d.risk * 100).toFixed(1) + "%" : "Unassigned (>15)";
            let elevText = (d.elevation > 0) ? d.elevation.toFixed(1) + "m" : "0.0m (Ground Datum)";
            let badgeHtml = d.is_dispatched 
              ? `<span class="tt-badge tt-badge-p15">PRIORITY #${{d.rank}}</span>`
              : `<span class="tt-badge tt-badge-norm">NOMINAL FLEET</span>`;

            let metersText = d.meter_count !== null && d.meter_count !== undefined ? d.meter_count + " Installed" : "Data unavailable";
            let antennaText = d.antenna_type || "Standard";

            tooltip.innerHTML = `
              <div class="tt-header">
                <span class="tt-gw">${{d.gateway_id}}</span>
                ${{badgeHtml}}
              </div>
              <div class="tt-grid">
                <span class="tt-label">Predicted Risk:</span><span class="tt-val">${{riskText}}</span>
                <span class="tt-label">Elevation Datum:</span><span class="tt-val">${{elevText}}</span>
                <span class="tt-label">Antenna Type:</span><span class="tt-val">${{antennaText}}</span>
                <span class="tt-label">Smart Meters:</span><span class="tt-val">${{metersText}}</span>
              </div>
              <div class="tt-reason"><strong>Status:</strong> ${{d.reason}}</div>
            `;
          }} else {{
            if (hoveredMesh && !hoveredMesh.userData.is_selected) {{
              hoveredMesh.scale.set(1.0, 1.0, 1.0);
            }}
            hoveredMesh = null;
            tooltip.style.display = "none";
          }}
        }});

        // Click to focus camera on selected node
        window.addEventListener("click", (event) => {{
          raycaster.setFromCamera(mouse, camera);
          const intersects = raycaster.intersectObjects(meshes);
          if (intersects.length > 0) {{
            const targetNode = intersects[0].object;
            const pos = targetNode.position;
            targetCamPos = new THREE.Vector3(pos.x + 12, pos.y + 8, pos.z + 14);
            targetLookAt = new THREE.Vector3(pos.x, pos.y, pos.z);
            isTransitioning = true;
          }}
        }});

        // =====================================================================
        // CAMERA EASING & VIEWPORT CONTROLS
        // =====================================================================
        let targetCamPos = defaultCamPos.clone();
        let targetLookAt = defaultTarget.clone();
        let isTransitioning = false;

        function setView(camPos, lookAt) {{
          targetCamPos.copy(camPos);
          targetLookAt.copy(lookAt);
          isTransitioning = true;
        }}

        document.getElementById("btn-iso").addEventListener("click", () => {{
          setView(new THREE.Vector3(26, 26, 38), new THREE.Vector3(0, 3.5, 0));
        }});

        document.getElementById("btn-top").addEventListener("click", () => {{
          setView(new THREE.Vector3(0, 48, 0.1), new THREE.Vector3(0, 0, 0));
        }});

        document.getElementById("btn-focus").addEventListener("click", () => {{
          // Calculate centroid of dispatched nodes
          let sumX = 0, sumY = 0, sumZ = 0, count = 0;
          nodesData.forEach(n => {{
            if (n.is_dispatched) {{
              sumX += n.x; sumY += n.elevation; sumZ += n.z; count++;
            }}
          }});
          if (count > 0) {{
            const cX = sumX / count, cY = sumY / count, cZ = sumZ / count;
            setView(new THREE.Vector3(cX + 14, cY + 12, cZ + 18), new THREE.Vector3(cX, cY, cZ));
          }}
        }});

        let filterOnlyDispatched = false;
        const btnFilter = document.getElementById("btn-filter");
        btnFilter.addEventListener("click", () => {{
          filterOnlyDispatched = !filterOnlyDispatched;
          groundPuckGroup.visible = !filterOnlyDispatched;
          btnFilter.innerHTML = filterOnlyDispatched ? "👁️ Filter: Dispatched (15)" : "👁️ Filter: All (332)";
          btnFilter.classList.toggle("active", filterOnlyDispatched);
        }});

        document.getElementById("btn-reset").addEventListener("click", () => {{
          setView(defaultCamPos, defaultTarget);
          filterOnlyDispatched = false;
          groundPuckGroup.visible = true;
          btnFilter.innerHTML = "👁️ Filter: All (332)";
          btnFilter.classList.remove("active");
        }});

        // Resize handler
        window.addEventListener("resize", () => {{
          camera.aspect = window.innerWidth / {height};
          camera.updateProjectionMatrix();
          renderer.setSize(window.innerWidth, {height});
        }});

        // CALM RENDER LOOP (Zero disturbing motion)
        function animate() {{
          requestAnimationFrame(animate);

          // Smooth camera transition if active
          if (isTransitioning) {{
            camera.position.lerp(targetCamPos, 0.08);
            controls.target.lerp(targetLookAt, 0.08);
            if (camera.position.distanceTo(targetCamPos) < 0.1) {{
              isTransitioning = false;
            }}
          }}

          controls.update();
          renderer.render(scene, camera);
        }}
        animate();
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=False)
