"""Generate interactive multi-layer HTML viewer for the Halcyon Palika Guild Path."""
from pathlib import Path
import base64, json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'renders/sentier_guilde_halcyon'

def b64(path):
    return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

base_day = b64(OUT / '00_palika_base.png')
base_night = b64(OUT / '00_palika_base_nuit.png')

obj_day = b64(OUT / '01_palika_objects.png')
obj_night = b64(OUT / '01_palika_objects_nuit.png')

trees_day = b64(OUT / '02_palika_trees.png')
trees_night = b64(OUT / '02_palika_trees_nuit.png')

big_tree_day = b64(OUT / '03_palika_big_tree.png')
big_tree_night = b64(OUT / '03_palika_big_tree_nuit.png')

shadows_day = b64(OUT / '04_palika_shadows.png')
shadows_night = b64(OUT / '04_palika_shadows_nuit.png')

comp_day = b64(OUT / 'composite_palika.png')
comp_night = b64(OUT / 'composite_palika_nuit.png')

# Player sprite (Pachirisu walk frame)
pachi_path = ROOT / 'exports/guild_eat_all_v6/characters/0417/Walk-Anim.png'
from PIL import Image
pachi_crop = Image.open(pachi_path).crop((0, 0, 40, 56))
import io
buf = io.BytesIO()
pachi_crop.save(buf, format='PNG')
player_b64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sentier de la Guilde — Méthode Halcyon Palika (Multi-Calques PMDO)</title>
<style>
  :root {{
    --bg-dark: #0a0f18;
    --panel-bg: #111a28;
    --panel-border: #1e293b;
    --accent-cyan: #38bdf8;
    --accent-gold: #f4d06f;
    --accent-green: #4ade80;
    --accent-purple: #c084fc;
    --text-main: #f1f5f9;
    --text-muted: #94a3b8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg-dark);
    color: var(--text-main);
    padding: 24px;
    line-height: 1.5;
  }}
  header {{
    max-width: 1400px;
    margin: 0 auto 24px auto;
    border-bottom: 1px solid var(--panel-border);
    padding-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 16px;
  }}
  h1 {{ font-size: 1.6rem; color: var(--accent-gold); display: flex; align-items: center; gap: 10px; }}
  .tag {{
    font-size: 0.75rem;
    padding: 3px 8px;
    background: #0369a1;
    color: #e0f2fe;
    border-radius: 4px;
    font-weight: 600;
  }}
  .subtitle {{ color: var(--text-muted); font-size: 0.95rem; margin-top: 4px; }}
  .badge-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }}
  .badge {{
    font-size: 0.8rem;
    padding: 4px 10px;
    border-radius: 6px;
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--panel-border);
    color: var(--accent-cyan);
  }}

  .main-layout {{
    max-width: 1400px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 500px 1fr;
    gap: 28px;
  }}
  @media (max-width: 1100px) {{
    .main-layout {{ grid-template-columns: 1fr; }}
  }}

  /* MAP VIEWPORT */
  .viewport-container {{
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .viewport-toolbar {{
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 10px;
  }}
  .btn {{
    background: #1e293b;
    border: 1px solid #334155;
    color: #e2e8f0;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .btn:hover {{ background: #334155; color: white; }}
  .btn.active {{ background: #0284c7; border-color: #38bdf8; color: white; }}

  /* STACKED STAGE */
  .stage-wrapper {{
    position: relative;
    width: 408px;
    height: 744px;
    background: #05080e;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    border-radius: 4px;
    overflow: hidden;
    perspective: 1200px;
    transition: transform 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
  }}
  .stage-inner {{
    position: absolute;
    width: 100%;
    height: 100%;
    transform-style: preserve-3d;
    transition: transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
  }}
  .stage-wrapper.exploded .stage-inner {{
    transform: rotateX(45deg) rotateZ(-20deg) scale(0.7) translateY(-60px);
  }}

  .map-layer {{
    position: absolute;
    top: 0;
    left: 0;
    width: 408px;
    height: 744px;
    image-rendering: pixelated;
    transition: opacity 0.2s, transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
    pointer-events: none;
  }}

  /* 2.5D Explosion offsets */
  .stage-wrapper.exploded #layer-base {{ transform: translateZ(0px); box-shadow: 0 0 20px rgba(0,0,0,0.8); }}
  .stage-wrapper.exploded #layer-objects {{ transform: translateZ(50px); }}
  .stage-wrapper.exploded #layer-shadows {{ transform: translateZ(90px); }}
  .stage-wrapper.exploded #layer-trees {{ transform: translateZ(140px); }}
  .stage-wrapper.exploded #layer-player {{ transform: translateZ(160px); }}
  .stage-wrapper.exploded #layer-big-tree {{ transform: translateZ(220px); }}

  /* Player sprite demo */
  #layer-player {{
    position: absolute;
    width: 40px;
    height: 56px;
    top: 360px;
    left: 184px;
    image-rendering: pixelated;
    z-index: 10;
    transition: transform 0.6s;
    animation: pachi-walk 6s infinite alternate ease-in-out;
  }}
  @keyframes pachi-walk {{
    0% {{ transform: translate(0, 0); }}
    25% {{ transform: translate(-30px, -80px); }}
    50% {{ transform: translate(30px, -180px); }}
    75% {{ transform: translate(10px, -280px); }}
    100% {{ transform: translate(0px, -350px); }}
  }}

  /* CONTROLS & SIDEBAR */
  .controls-container {{
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}
  .card {{
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 12px;
    padding: 20px;
  }}
  .card-title {{
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--accent-gold);
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  
  .layer-item {{
    background: #162235;
    border: 1px solid #23334d;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    transition: border-color 0.2s;
  }}
  .layer-item:hover {{ border-color: #38bdf8; }}
  .layer-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .layer-label {{
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.92rem;
  }}
  .layer-badge {{
    font-size: 0.72rem;
    padding: 2px 6px;
    border-radius: 4px;
    background: #1e293b;
    color: #94a3b8;
  }}
  .layer-slider {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.8rem;
    color: var(--text-muted);
  }}
  input[type=range] {{
    flex: 1;
    accent-color: var(--accent-cyan);
  }}
  .layer-desc {{
    font-size: 0.78rem;
    color: #94a3b8;
    line-height: 1.4;
  }}

  .stat-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-top: 10px;
  }}
  .stat-item {{
    background: #162235;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid #23334d;
  }}
  .stat-val {{ font-size: 1.2rem; font-weight: 700; color: var(--accent-cyan); }}
  .stat-lbl {{ font-size: 0.75rem; color: var(--text-muted); }}

  .links-list {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 10px;
  }}
  .link-btn {{
    display: block;
    background: #162235;
    border: 1px solid #23334d;
    padding: 10px 14px;
    border-radius: 8px;
    color: #38bdf8;
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s;
  }}
  .link-btn:hover {{
    background: #1e293b;
    border-color: #38bdf8;
    color: white;
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>Sentier de la Guilde <span class="tag">MÉTHODE HALCYON PALIKA</span></h1>
    <p class="subtitle">Architecture multicalques native PMDO avec arbres d'Apricorn Glade et textures de sol d'Apricorn Grove (Palika / Halcyon)</p>
    <div class="badge-row">
      <span class="badge">Résolution native : 408 × 744 px</span>
      <span class="badge">Grille : 17 × 31 cases de 24 px</span>
      <span class="badge">Palette Halcyon : 395 couleurs (0 hors-palette)</span>
      <span class="badge">Format moteur : .rsground + .tile + .tmj</span>
    </div>
  </div>
  <div style="display:flex; gap:10px;">
    <button id="theme-btn" class="btn" onclick="toggleTheme()">🌙 Mode Nuit (Abyss)</button>
    <button id="explode-btn" class="btn" onclick="toggleExploded()">🧊 Vue Éclatée 2.5D</button>
  </div>
</header>

<main class="main-layout">
  <!-- VIEWPORT -->
  <div class="viewport-container">
    <div class="viewport-toolbar">
      <span style="font-size:0.85rem; color:var(--text-muted);">Viewport PMDO interactif (Z-Order en temps réel)</span>
      <button class="btn" onclick="resetLayers()">Réinitialiser Calques</button>
    </div>

    <div class="stage-wrapper" id="stage">
      <div class="stage-inner">
        <!-- Layer 0: Base (Ground) -->
        <img id="layer-base" class="map-layer" src="{base_day}" alt="Base Ground">
        <!-- Layer 1: Objects (Meadow & details) -->
        <img id="layer-objects" class="map-layer" src="{obj_day}" alt="Objects">
        <!-- Layer 4: Shadows -->
        <img id="layer-shadows" class="map-layer" src="{shadows_day}" alt="Shadows">
        <!-- Layer 2: Trees (Collision & trunks) -->
        <img id="layer-trees" class="map-layer" src="{trees_day}" alt="Trees">
        <!-- Animated player between Trees and Overhead Canopy -->
        <img id="layer-player" src="{player_b64}" alt="Player Sprite" title="Explorateur sous la canopée">
        <!-- Layer 3: Big Tree (Overhead Canopy) -->
        <img id="layer-big-tree" class="map-layer" src="{big_tree_day}" alt="Big Tree Overhead">
      </div>
    </div>
    <div style="font-size:0.8rem; color:var(--text-muted); margin-top:14px; text-align:center;">
      Observez le joueur (Pachirisu) : il marche <strong>SUR</strong> le sol, <strong>DERRIÈRE</strong> les troncs, et <strong>SOUS</strong> la canopée haute !
    </div>
  </div>

  <!-- CONTROLS -->
  <div class="controls-container">
    <!-- LAYER MANAGER -->
    <div class="card">
      <div class="card-title">🥞 Gestionnaire des Calques (Méthode Halcyon Palika)</div>
      
      <!-- Layer 3: Big Tree Overhead -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-big-tree" checked onchange="updateLayer('big-tree')">
            <span>3. Big Tree (Canopée Haute)</span>
          </label>
          <span class="layer-badge">199 cases · Z: Overhead</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-big-tree" min="0" max="100" value="100" oninput="updateOpacity('big-tree')">
          <span id="txt-big-tree">100%</span>
        </div>
        <div class="layer-desc">Frondaisons et couronnes de feuilles d'Apricorn Glade passant au-dessus du joueur (Fringe / Objects Over).</div>
      </div>

      <!-- Player Simulation -->
      <div class="layer-item" style="border-left: 3px solid #38bdf8;">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-player" checked onchange="togglePlayer()">
            <span style="color:#38bdf8;">🎮 Sprite Joueur (Pachirisu)</span>
          </label>
          <span class="layer-badge">Niveau de tri Y</span>
        </div>
        <div class="layer-desc">Marche le long du sentier entre les troncs et sous la grande canopée pour tester l'occlusion.</div>
      </div>

      <!-- Layer 2: Trees -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-trees" checked onchange="updateLayer('trees')">
            <span>2. Trees (Arbres & Troncs)</span>
          </label>
          <span class="layer-badge">378 cases · Z: Collision</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-trees" min="0" max="100" value="100" oninput="updateOpacity('trees')">
          <span id="txt-trees">100%</span>
        </div>
        <div class="layer-desc">Troncs d'Apricorn Glade, racines au sol, souches et bordures d'obstacles bloquants (niveau collision PMDO).</div>
      </div>

      <!-- Layer 4: Shadows -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-shadows" checked onchange="updateLayer('shadows')">
            <span>4. Shadows (Ombres Portées)</span>
          </label>
          <span class="layer-badge">435 cases · Z: Décor</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-shadows" min="0" max="100" value="100" oninput="updateOpacity('shadows')">
          <span id="txt-shadows">100%</span>
        </div>
        <div class="layer-desc">Ombres volumétriques douces projetées sous la canopée sur le sentier et la végétation (palette d'ardoise Halcyon).</div>
      </div>

      <!-- Layer 1: Objects -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-objects" checked onchange="updateLayer('objects')">
            <span>1. Objects (Sous-bois & Fleurs)</span>
          </label>
          <span class="layer-badge">407 cases · Z: Sol supérieur</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-objects" min="0" max="100" value="100" oninput="updateOpacity('objects')">
          <span id="txt-objects">100%</span>
        </div>
        <div class="layer-desc">Bordures herbeuses d'Apricorn Grove, touffes d'herbe, fleurs sauvages et parterres naturels.</div>
      </div>

      <!-- Layer 0: Base -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-base" checked onchange="updateLayer('base')">
            <span>0. Base (Sol & Sentier)</span>
          </label>
          <span class="layer-badge">527 cases · 100% plein</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-base" min="0" max="100" value="100" oninput="updateOpacity('base')">
          <span id="txt-base">100%</span>
        </div>
        <div class="layer-desc">Fondation continue en terre battue d'Apricorn Grove et pelouse de sous-bois. Aucun trou noir sous les arbres.</div>
      </div>
    </div>

    <!-- SPECS & ENGINE COMPLIANCE -->
    <div class="card">
      <div class="card-title">📊 Fiche Technique PMDO (Méthode Palika)</div>
      <div class="stat-grid">
        <div class="stat-item">
          <div class="stat-val">5 Calques</div>
          <div class="stat-lbl">Conforme apricorn_glade.rsground</div>
        </div>
        <div class="stat-item">
          <div class="stat-val">395 Coul.</div>
          <div class="stat-lbl">Palette authentique Halcyon (0 erreur)</div>
        </div>
        <div class="stat-item">
          <div class="stat-val">24 px</div>
          <div class="stat-lbl">Taille native de cellule (TexSize: 24)</div>
        </div>
        <div class="stat-item">
          <div class="stat-val">17 × 31</div>
          <div class="stat-lbl">527 cases par calque (408×744 px)</div>
        </div>
      </div>

      <div style="margin-top:16px;">
        <div class="card-title" style="font-size:0.95rem;">📁 Fichiers Moteur et Planches</div>
        <div class="links-list">
          <a class="link-btn" href="renders/sentier_guilde_halcyon/PLANCHE_HALCYON_PALIKA_CALQUES.png" target="_blank">🖼️ Ouvrir la Planche Contact Multi-Calques (2100×1300)</a>
          <a class="link-btn" href="sprites/sentier_guilde_halcyon_pmdo/guild_path_halcyon_palika.rsground" download>💾 Télécharger guild_path_halcyon_palika.rsground</a>
          <a class="link-btn" href="sprites/sentier_guilde_halcyon_pmdo/guild_path_halcyon_palika.tmj" download>🗺️ Télécharger la carte Tiled (guild_path_halcyon_palika.tmj)</a>
        </div>
      </div>
    </div>
  </div>
</main>

<script>
  let isNight = false;
  let isExploded = false;

  const assets = {{
    day: {{
      base: "{base_day}",
      objects: "{obj_day}",
      trees: "{trees_day}",
      big_tree: "{big_tree_day}",
      shadows: "{shadows_day}"
    }},
    night: {{
      base: "{base_night}",
      objects: "{obj_night}",
      trees: "{trees_night}",
      big_tree: "{big_tree_night}",
      shadows: "{shadows_night}"
    }}
  }};

  function toggleTheme() {{
    isNight = !isNight;
    const btn = document.getElementById('theme-btn');
    const set = isNight ? assets.night : assets.day;
    btn.innerHTML = isNight ? '☀️ Mode Jour' : '🌙 Mode Nuit (Abyss)';
    btn.classList.toggle('active', isNight);

    document.getElementById('layer-base').src = set.base;
    document.getElementById('layer-objects').src = set.objects;
    document.getElementById('layer-trees').src = set.trees;
    document.getElementById('layer-big-tree').src = set.big_tree;
    document.getElementById('layer-shadows').src = set.shadows;
  }}

  function toggleExploded() {{
    isExploded = !isExploded;
    const stage = document.getElementById('stage');
    const btn = document.getElementById('explode-btn');
    stage.classList.toggle('exploded', isExploded);
    btn.classList.toggle('active', isExploded);
  }}

  function updateLayer(id) {{
    const chk = document.getElementById('chk-' + id);
    const layer = document.getElementById('layer-' + id);
    layer.style.display = chk.checked ? 'block' : 'none';
  }}

  function updateOpacity(id) {{
    const op = document.getElementById('op-' + id).value;
    const layer = document.getElementById('layer-' + id);
    const txt = document.getElementById('txt-' + id);
    layer.style.opacity = op / 100;
    txt.innerText = op + '%';
  }}

  function togglePlayer() {{
    const chk = document.getElementById('chk-player');
    const p = document.getElementById('layer-player');
    p.style.display = chk.checked ? 'block' : 'none';
  }}

  function resetLayers() {{
    ['base', 'objects', 'trees', 'big-tree', 'shadows'].forEach(id => {{
      document.getElementById('chk-' + id).checked = true;
      document.getElementById('op-' + id).value = 100;
      updateLayer(id);
      updateOpacity(id);
    }});
    document.getElementById('chk-player').checked = true;
    togglePlayer();
  }}
</script>

</body>
</html>
"""
(ROOT / 'apercu_sentier_guilde_halcyon.html').write_text(html_content, encoding='utf-8')
print("Generated apercu_sentier_guilde_halcyon.html successfully.")
