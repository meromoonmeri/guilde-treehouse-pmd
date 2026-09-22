#!/usr/bin/env python3
"""Générateur du visualiseur web interactif pour GB1 Grotte Brumeuse."""
import base64, json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
O = R / 'renders/grotte_brumeuse_v1'

def b64(p):
    return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode('ascii')

def main():
    order = [
        ('01_sol', '01 - Sol clairière continu (100% opaque)'),
        ('02_parois_grotte_crooked', '02 - Parois rocheuses et arche Crooked Cavern harmonisée'),
        ('03_arbres_lisiere_fond', '03 - Arbres de lisière et sous-bois Foggy Forest'),
        ('04_lianes_et_verdure', '04 - Lianes suspendues tombantes et buissons moussus'),
        ('05_canopee_avant_plan', '05 - Canopée haute de frondaisons avant-plan'),
        ('06_brume_atmospherique', '06 - Voile de brume et rai de lumière doré')
    ]

    data = {
        'order': [lid for lid, _ in order],
        'titles': {lid: title for lid, title in order},
        'jour': {lid: b64(O / f'calques_jour/GB1_grotte_brumeuse_{lid}_jour.png') for lid, _ in order},
        'nuit': {lid: b64(O / f'calques_nuit/GB1_grotte_brumeuse_{lid}_nuit.png') for lid, _ in order},
        'magenta': {lid: b64(O / f'bruts_magenta/GB1_grotte_brumeuse_{lid}_magenta.png') for lid, _ in order},
        'carte_jour': b64(O / 'GB1_grotte_brumeuse_carte_jour.png'),
        'carte_nuit': b64(O / 'GB1_grotte_brumeuse_carte_nuit.png'),
        'planche_magenta': b64(O / 'GB1_grotte_brumeuse_planche_magenta.png'),
        'calques_board': b64(O / 'GB1_grotte_brumeuse_calques.png'),
        'viewport_board': b64(O / 'GB1_grotte_brumeuse_viewport.png')
    }

    html = f'''<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GB1 — Grotte Brumeuse PMDO (Foggy Forest & Crooked Cavern)</title>
  <style>
    :root {{
      --bg: #0d151c;
      --card: #182430;
      --card-border: #2b3d4f;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --green: #4ade80;
      --magenta: #f43f5e;
      --amber: #fbbf24;
      --purple: #c084fc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      margin: 0;
      padding: 24px;
      line-height: 1.5;
    }}
    header {{
      max-width: 1280px;
      margin: 0 auto 20px auto;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 16px;
    }}
    h1 {{
      margin: 0 0 6px 0;
      font-size: 24px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .badge {{
      font-size: 13px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 999px;
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}
    .lead {{ color: var(--muted); margin: 0; font-size: 15px; }}
    .main-grid {{
      max-width: 1280px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 24px;
      align-items: start;
    }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 16px;
    }}
    .panel-title {{
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
      margin: 0 0 12px 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .btn-group {{
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }}
    .btn {{
      background: #243444;
      color: var(--text);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 8px 14px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .btn:hover {{ background: #2f4457; }}
    .btn.active {{
      background: var(--accent);
      color: #0b131b;
      border-color: var(--accent);
    }}
    .btn-magenta.active {{
      background: #f43f5e;
      color: white;
      border-color: #f43f5e;
    }}
    .layer-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 6px;
      border-radius: 6px;
      font-size: 13px;
      border-bottom: 1px solid rgba(255,255,255,0.05);
    }}
    .layer-row:hover {{ background: rgba(255,255,255,0.03); }}
    .layer-row input[type="checkbox"] {{
      width: 16px;
      height: 16px;
      cursor: pointer;
      accent-color: var(--accent);
    }}
    .layer-info {{
      flex: 1;
      display: flex;
      flex-direction: column;
    }}
    .layer-name {{ font-weight: 600; }}
    .layer-sub {{ font-size: 11px; color: var(--muted); }}
    .canvas-container {{
      background: #090e13;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .viewport-meta {{
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      font-size: 13px;
      color: var(--muted);
    }}
    .canvas-wrapper {{
      position: relative;
      background: repeating-conic-gradient(#151f28 0% 25%, #0f171e 0% 50%) 50% / 16px 16px;
      border: 2px solid var(--card-border);
      border-radius: 6px;
      overflow: hidden;
      cursor: crosshair;
    }}
    .canvas-wrapper.magenta-bg {{
      background: #ff00ff !important;
    }}
    canvas {{
      display: block;
      image-rendering: pixelated;
    }}
    .download-links {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .download-btn {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: #243444;
      color: var(--text);
      text-decoration: none;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      border: 1px solid var(--card-border);
      transition: background 0.15s ease;
    }}
    .download-btn:hover {{ background: #2f4457; }}
    .download-btn span.size {{ font-size: 11px; color: var(--muted); }}
    table.specs {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    table.specs td {{
      padding: 6px 4px;
      border-bottom: 1px solid rgba(255,255,255,0.05);
    }}
    table.specs td:first-child {{ color: var(--muted); font-weight: 500; }}
    table.specs td:last-child {{ text-align: right; font-weight: 600; }}
    .guide-callout {{
      background: rgba(244, 63, 94, 0.1);
      border: 1px solid rgba(244, 63, 94, 0.3);
      border-radius: 8px;
      padding: 12px;
      margin-top: 12px;
      font-size: 12px;
      color: #fca5a5;
    }}
  </style>
</head>
<body>
  <header>
    <h1>GB1 — Grotte Brumeuse PMDO <span class="badge">Foggy Forest & Crooked Cavern</span></h1>
    <p class="lead">Progression Sud vers Nord : clairière moussue traversée par un sentier naturel convergeant vers un portail rocheux de Crooked Cavern harmonisé, drapé de lianes suspendues et baigné de brume dorée.</p>
  </header>

  <div class="main-grid">
    <aside>
      <!-- CONTROLES D'AMBIANCE & FOND -->
      <div class="panel">
        <div class="panel-title">Ambiance & Fond</div>
        <div class="btn-group">
          <button class="btn active" id="btn-jour" onclick="setMode('jour')">☀️ Jour</button>
          <button class="btn" id="btn-nuit" onclick="setMode('nuit')">🌙 Nuit (Abyss)</button>
        </div>
        <div class="btn-group">
          <button class="btn active" id="btn-bg-check" onclick="setBg('damier')">🏁 Damier</button>
          <button class="btn btn-magenta" id="btn-bg-mag" onclick="setBg('magenta')">🟪 Fond Magenta #FF00FF</button>
        </div>
        <div class="guide-callout">
          <strong>Validation Guides Magenta :</strong> Les calques sont générés sur fond magenta pur <code>#FF00FF</code> pour isolation pixel-perfect puis emballés avec alpha propre pour PMDO.
        </div>
      </div>

      <!-- CALQUES SEMANTIQUES -->
      <div class="panel">
        <div class="panel-title">
          <span>6 Calques Sémantiques</span>
          <button class="btn" style="padding: 2px 8px; font-size: 11px;" onclick="toggleAllLayers()">Tous</button>
        </div>
        <div id="layer-list"></div>
      </div>

      <!-- CAMERA VIEWPORT & NAVIGATION -->
      <div class="panel">
        <div class="panel-title">Caméra PMDO 320×240 & Repères</div>
        <div class="btn-group">
          <button class="btn" onclick="focusCamera(240, 296)">📍 Spawn Sud [240, 296]</button>
          <button class="btn" onclick="focusCamera(240, 95)">🚪 Grotte Nord [240, 95]</button>
          <button class="btn" onclick="focusCamera(240, 168)">🎯 Centre [240, 168]</button>
        </div>
        <div class="layer-row">
          <input type="checkbox" id="chk-viewport" checked onchange="draw()">
          <label for="chk-viewport" class="layer-info" style="cursor:pointer;">
            <span class="layer-name">Rectangle Caméra 320×240 (x1)</span>
            <span class="layer-sub">Zone visible à l'écran dans PMDO</span>
          </label>
        </div>
        <div class="layer-row">
          <input type="checkbox" id="chk-walkable" onchange="draw()">
          <label for="chk-walkable" class="layer-info" style="cursor:pointer;">
            <span class="layer-name">Trajectoire & Praticabilité (17px)</span>
            <span class="layer-sub">43 217 px praticables continus Sud->Nord</span>
          </label>
        </div>
      </div>

      <!-- TELECHARGEMENTS -->
      <div class="panel">
        <div class="panel-title">Packs & Livrables</div>
        <div class="download-links">
          <a class="download-btn" href="renders/grotte_brumeuse_v1/GB1_grotte_brumeuse_calques.zip" download>
            <span>📦 Pack Calques & Magenta (ZIP)</span>
            <span class="size">1.44 MB</span>
          </a>
          <a class="download-btn" href="renders/grotte_brumeuse_v1/GB1_grotte_brumeuse_PMDO.zip" download>
            <span>🎮 Pack PMDO 0.8.12 (.rsground)</span>
            <span class="size">1.72 MB</span>
          </a>
          <a class="download-btn" href="renders/grotte_brumeuse_v1/GB1_grotte_brumeuse_planche_magenta.png" target="_blank">
            <span>🖼️ Planche Calques Magenta</span>
            <span class="size">216 KB</span>
          </a>
          <a class="download-btn" href="renders/grotte_brumeuse_v1/GB1_grotte_brumeuse_calques.png" target="_blank">
            <span>🖼️ Planche Calques Transparents</span>
            <span class="size">426 KB</span>
          </a>
          <a class="download-btn" href="renders/grotte_brumeuse_v1/GB1_grotte_brumeuse_ambiances.webp" target="_blank">
            <span>✨ Animation WebP Jour/Nuit (2s)</span>
            <span class="size">353 KB</span>
          </a>
        </div>
      </div>

      <!-- SPECIFICATIONS TECHNIQUES -->
      <div class="panel">
        <div class="panel-title">Spécifications PMDO</div>
        <table class="specs">
          <tr><td>Dimensions carte</td><td>480 × 336 px (x1)</td></tr>
          <tr><td>Grille tuiles 8px</td><td>60 × 42 tuiles</td></tr>
          <tr><td>Fenêtre caméra</td><td>320 × 240 px (native)</td></tr>
          <tr><td>Point d'arrivée (Spawn Sud)</td><td>[240, 296]</td></tr>
          <tr><td>Portail d'accès (Grotte Nord)</td><td>[240, 95]</td></tr>
          <tr><td>Sol continu 01</td><td>100% opaque (0 trou alpha)</td></tr>
          <tr><td>Zone praticable vérifiée</td><td>43 217 px (érosion 17px)</td></tr>
          <tr><td>Groupes sémantiques</td><td>6 calques indépendants</td></tr>
          <tr><td>Harmonisation roche</td><td>Multiples 8 (5-bit GBA)</td></tr>
          <tr><td>Filtre nocturne</td><td>Matrice canonique Abyss</td></tr>
        </table>
      </div>
    </aside>

    <main class="canvas-container">
      <div class="viewport-meta">
        <div>
          <span>Zoom : </span>
          <button class="btn" style="padding:3px 10px;" onclick="setZoom(1)">1×</button>
          <button class="btn active" id="zoom-2" style="padding:3px 10px;" onclick="setZoom(2)">2×</button>
          <button class="btn" style="padding:3px 10px;" onclick="setZoom(3)">3×</button>
        </div>
        <div id="cam-coords">Caméra : [80, 48] · Viewport 320×240</div>
      </div>

      <div class="canvas-wrapper" id="canvas-wrapper">
        <canvas id="main-canvas" width="480" height="336"></canvas>
      </div>

      <p style="font-size:12px; color:var(--muted); margin-top:14px; text-align:center;">
        💡 <strong>Astuce :</strong> Cliquez ou glissez la souris sur la carte pour déplacer le cadre caméra PMDO 320×240.
      </p>
    </main>
  </div>

  <script>
    const DATA = {json.dumps(data)};
    const W = 480, H = 336;
    const SW = 320, SH = 240;
    
    let currentMode = 'jour';
    let currentBg = 'damier';
    let zoomLevel = 2;
    let camX = 80, camY = 48;
    let isDragging = false;

    const layerVisibility = {{}};
    DATA.order.forEach(id => {{ layerVisibility[id] = true; }});

    // Cache d'images
    const images = {{
      jour: {{}},
      nuit: {{}},
      magenta: {{}}
    }};

    function loadImage(src) {{
      return new Promise((resolve) => {{
        const im = new Image();
        im.onload = () => resolve(im);
        im.src = src;
      }});
    }}

    async function initImages() {{
      for (const id of DATA.order) {{
        images.jour[id] = await loadImage(DATA.jour[id]);
        images.nuit[id] = await loadImage(DATA.nuit[id]);
        images.magenta[id] = await loadImage(DATA.magenta[id]);
      }}
      buildLayerList();
      setZoom(2);
      draw();
    }}

    function buildLayerList() {{
      const container = document.getElementById('layer-list');
      container.innerHTML = '';
      DATA.order.forEach(id => {{
        const row = document.createElement('div');
        row.className = 'layer-row';
        row.innerHTML = `
          <input type="checkbox" id="chk-${{id}}" ${{layerVisibility[id] ? 'checked' : ''}} onchange="toggleLayer('${{id}}')">
          <label for="chk-${{id}}" class="layer-info" style="cursor:pointer;">
            <span class="layer-name">${{DATA.titles[id]}}</span>
            <span class="layer-sub">Calque ${{id}}</span>
          </label>
        `;
        container.appendChild(row);
      }});
    }}

    function toggleLayer(id) {{
      layerVisibility[id] = document.getElementById(`chk-${{id}}`).checked;
      draw();
    }}

    function toggleAllLayers() {{
      const anyOff = DATA.order.some(id => !layerVisibility[id]);
      DATA.order.forEach(id => {{
        layerVisibility[id] = anyOff;
        const chk = document.getElementById(`chk-${{id}}`);
        if (chk) chk.checked = anyOff;
      }});
      draw();
    }}

    function setMode(mode) {{
      currentMode = mode;
      document.getElementById('btn-jour').classList.toggle('active', mode === 'jour');
      document.getElementById('btn-nuit').classList.toggle('active', mode === 'nuit');
      draw();
    }}

    function setBg(bg) {{
      currentBg = bg;
      document.getElementById('btn-bg-check').classList.toggle('active', bg === 'damier');
      document.getElementById('btn-bg-mag').classList.toggle('active', bg === 'magenta');
      const wrapper = document.getElementById('canvas-wrapper');
      wrapper.classList.toggle('magenta-bg', bg === 'magenta');
      draw();
    }}

    function setZoom(z) {{
      zoomLevel = z;
      const canvas = document.getElementById('main-canvas');
      canvas.style.width = (W * z) + 'px';
      canvas.style.height = (H * z) + 'px';
      [1, 2, 3].forEach(i => {{
        const btn = document.getElementById(`zoom-${{i}}`);
        if (btn) btn.classList.toggle('active', i === z);
      }});
    }}

    function focusCamera(x, y) {{
      camX = Math.max(0, Math.min(W - SW, x - SW / 2));
      camY = Math.max(0, Math.min(H - SH, y - SH / 2));
      document.getElementById('cam-coords').textContent = `Caméra : [${{Math.round(camX)}}, ${{Math.round(camY)}}] · Viewport 320×240`;
      draw();
    }}

    function draw() {{
      const canvas = document.getElementById('main-canvas');
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, W, H);

      // Si mode magenta activé, peindre le fond en magenta pur
      if (currentBg === 'magenta') {{
        ctx.fillStyle = '#ff00ff';
        ctx.fillRect(0, 0, W, H);
      }}

      // Rendu des calques dans l'ordre sémantique
      DATA.order.forEach(id => {{
        if (layerVisibility[id]) {{
          const im = (currentBg === 'magenta') ? images.magenta[id] : images[currentMode][id];
          if (im) ctx.drawImage(im, 0, 0);
        }}
      }});

      // Tracé navigabilité et parcours Sud -> Nord si activé
      if (document.getElementById('chk-walkable') && document.getElementById('chk-walkable').checked) {{
        ctx.fillStyle = 'rgba(56, 189, 248, 0.25)';
        ctx.fillRect(170, 75, 140, 240);
        
        ctx.strokeStyle = '#fbbf24';
        ctx.lineWidth = 3;
        ctx.setLineDash([6, 6]);
        ctx.beginPath();
        ctx.moveTo(240, 296);
        ctx.lineTo(240, 95);
        ctx.stroke();
        ctx.setLineDash([]);
      }}

      // Marqueurs Spawn et Grotte
      // Spawn Sud [240, 296]
      ctx.fillStyle = '#22c55e';
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(240, 296, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Portail Grotte Nord [240, 95]
      ctx.fillStyle = '#3b82f6';
      ctx.beginPath();
      ctx.arc(240, 95, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Rectangle Caméra PMDO 320x240
      if (document.getElementById('chk-viewport') && document.getElementById('chk-viewport').checked) {{
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 2;
        ctx.strokeRect(camX, camY, SW, SH);

        // Ombre portée extérieure pour mettre en valeur le cadrage
        ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
        ctx.fillRect(0, 0, W, camY);
        ctx.fillRect(0, camY + SH, W, H - (camY + SH));
        ctx.fillRect(0, camY, camX, SH);
        ctx.fillRect(camX + SW, camY, W - (camX + SW), SH);
      }}
    }}

    // Interaction souris pour déplacer la caméra
    const canvas = document.getElementById('main-canvas');
    function updateCamFromEvent(e) {{
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left) / zoomLevel;
      const y = (e.clientY - rect.top) / zoomLevel;
      focusCamera(x, y);
    }}

    canvas.addEventListener('mousedown', (e) => {{
      isDragging = true;
      updateCamFromEvent(e);
    }});
    window.addEventListener('mousemove', (e) => {{
      if (isDragging) updateCamFromEvent(e);
    }});
    window.addEventListener('mouseup', () => {{
      isDragging = false;
    }});

    // Démarrage
    initImages();
  </script>
</body>
</html>'''

    (R / 'apercu_grotte_brumeuse_v1.html').write_text(html, encoding='utf-8')
    print(f'Generated {R / "apercu_grotte_brumeuse_v1.html"} ({(R / "apercu_grotte_brumeuse_v1.html").stat().st_size} bytes)')

if __name__ == '__main__':
    main()
