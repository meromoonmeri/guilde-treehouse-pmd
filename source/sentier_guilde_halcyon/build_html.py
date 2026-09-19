"""Generate interactive multi-layer HTML viewer for the Halcyon Guild Path."""
from pathlib import Path
import base64

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'renders/sentier_guilde_halcyon'

def b64(path):
    return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

sol_day = b64(OUT / '00_sol.png')
sol_night = b64(OUT / '00_sol_nuit.png')

chemin_day = b64(OUT / '01_chemin.png')
chemin_night = b64(OUT / '01_chemin_nuit.png')

veg_day = b64(OUT / '02_vegetation.png')
veg_night = b64(OUT / '02_vegetation_nuit.png')

arbres_day = b64(OUT / '03_arbres.png')
arbres_night = b64(OUT / '03_arbres_nuit.png')

premier_plan_day = b64(OUT / '04_premier_plan.png')
premier_plan_night = b64(OUT / '04_premier_plan_nuit.png')

comp_day = b64(OUT / 'composition.png')
comp_night = b64(OUT / 'composition_nuit.png')

html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sentier de la Guilde — Calques et Composition Finale (Halcyon)</title>
<style>
  :root {{
    --bg-dark: #0a0f18;
    --panel-bg: #111a28;
    --panel-border: #1e293b;
    --accent-cyan: #38bdf8;
    --accent-gold: #f4d06f;
    --accent-green: #4ade80;
    --accent-orange: #fb923c;
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

  .stage-wrapper {{
    position: relative;
    width: 408px;
    height: 744px;
    background: #05080e;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    border-radius: 4px;
    overflow: hidden;
    perspective: 1200px;
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

  .stage-wrapper.exploded #layer-sol {{ transform: translateZ(0px); box-shadow: 0 0 20px rgba(0,0,0,0.8); }}
  .stage-wrapper.exploded #layer-chemin {{ transform: translateZ(50px); }}
  .stage-wrapper.exploded #layer-vegetation {{ transform: translateZ(100px); }}
  .stage-wrapper.exploded #layer-arbres {{ transform: translateZ(160px); }}
  .stage-wrapper.exploded #layer-premier-plan {{ transform: translateZ(230px); }}

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
    <h1>Sentier de la Guilde <span class="tag">CALQUES SÉPARÉS & COMPOSITION</span></h1>
    <p class="subtitle">Génération des calques indépendants (Sol / Chemin / Végétation / Arbres / 1er Plan) avec textures et arbres de Halcyon</p>
    <div class="badge-row">
      <span class="badge">Résolution native : 408 × 744 px</span>
      <span class="badge">Grille : 17 × 31 cases de 24 px</span>
      <span class="badge">Palette Halcyon : 395 couleurs (0 erreur)</span>
      <span class="badge">Projet : OpenRaster .ora + .rsground + .tmj</span>
    </div>
  </div>
  <div style="display:flex; gap:10px;">
    <button id="theme-btn" class="btn" onclick="toggleTheme()">🌙 Mode Nuit (Abyss)</button>
    <button id="explode-btn" class="btn" onclick="toggleExploded()">🧊 Vue Éclatée 2.5D</button>
  </div>
</header>

<main class="main-layout">
  <div class="viewport-container">
    <div class="viewport-toolbar">
      <span style="font-size:0.85rem; color:var(--text-muted);">Composition dynamique en temps réel</span>
      <button class="btn" onclick="resetLayers()">Réinitialiser Calques</button>
    </div>

    <div class="stage-wrapper" id="stage">
      <div class="stage-inner">
        <!-- Layer 0: Sol -->
        <img id="layer-sol" class="map-layer" src="{sol_day}" alt="Calque Sol">
        <!-- Layer 1: Chemin -->
        <img id="layer-chemin" class="map-layer" src="{chemin_day}" alt="Calque Chemin">
        <!-- Layer 2: Végétation -->
        <img id="layer-vegetation" class="map-layer" src="{veg_day}" alt="Calque Végétation">
        <!-- Layer 3: Arbres -->
        <img id="layer-arbres" class="map-layer" src="{arbres_day}" alt="Calque Arbres">
        <!-- Layer 4: Premier Plan -->
        <img id="layer-premier-plan" class="map-layer" src="{premier_plan_day}" alt="Calque Premier Plan">
      </div>
    </div>
    <div style="font-size:0.8rem; color:var(--text-muted); margin-top:14px; text-align:center;">
      Activez ou désactivez les calques ci-contre pour voir la composition se reconstruire.
    </div>
  </div>

  <div class="controls-container">
    <div class="card">
      <div class="card-title">🥞 Calques Générés Séparément</div>

      <!-- Layer 4: Premier Plan -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-premier-plan" checked onchange="updateLayer('premier-plan')">
            <span style="color:var(--accent-purple);">04_premier_plan.png</span>
          </label>
          <span class="layer-badge">169 cases · Canopée haute</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-premier-plan" min="0" max="100" value="100" oninput="updateOpacity('premier-plan')">
          <span id="txt-premier-plan">100%</span>
        </div>
        <div class="layer-desc">Frondaisons hautes et branches d'Apricorn Glade Big Tree passant au-dessus du joueur.</div>
      </div>

      <!-- Layer 3: Arbres -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-arbres" checked onchange="updateLayer('arbres')">
            <span style="color:var(--accent-green);">03_arbres.png</span>
          </label>
          <span class="layer-badge">391 cases · Troncs & canopée</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-arbres" min="0" max="100" value="100" oninput="updateOpacity('arbres')">
          <span id="txt-arbres">100%</span>
        </div>
        <div class="layer-desc">Arbres complets d'Apricorn Glade : troncs en bois brun, racines au sol et parois forestières.</div>
      </div>

      <!-- Layer 2: Végétation -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-vegetation" checked onchange="updateLayer('vegetation')">
            <span style="color:#a3e635;">02_vegetation.png</span>
          </label>
          <span class="layer-badge">407 cases · Sous-bois & fleurs</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-vegetation" min="0" max="100" value="100" oninput="updateOpacity('vegetation')">
          <span id="txt-vegetation">100%</span>
        </div>
        <div class="layer-desc">Touffes d'herbes denses, parterres de fleurs sauvages et buissons bas bordant le sentier.</div>
      </div>

      <!-- Layer 1: Chemin -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-chemin" checked onchange="updateLayer('chemin')">
            <span style="color:var(--accent-orange);">01_chemin.png</span>
          </label>
          <span class="layer-badge">240 cases · Sentier sinueux</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-chemin" min="0" max="100" value="100" oninput="updateOpacity('chemin')">
          <span id="txt-chemin">100%</span>
        </div>
        <div class="layer-desc">Sentier sinueux en terre battue et graviers dorés d'Apricorn Grove de Halcyon.</div>
      </div>

      <!-- Layer 0: Sol -->
      <div class="layer-item">
        <div class="layer-header">
          <label class="layer-label">
            <input type="checkbox" id="chk-sol" checked onchange="updateLayer('sol')">
            <span style="color:var(--accent-gold);">00_sol.png</span>
          </label>
          <span class="layer-badge">527 cases · 100% plein</span>
        </div>
        <div class="layer-slider">
          <span>Opacité</span>
          <input type="range" id="op-sol" min="0" max="100" value="100" oninput="updateOpacity('sol')">
          <span id="txt-sol">100%</span>
        </div>
        <div class="layer-desc">Sol de base continu d'Apricorn Grove. Texture de terre et pelouse sans aucun vide sous les arbres.</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">📁 Fichiers Composés et Téléchargements</div>
      <div class="links-list">
        <a class="link-btn" href="renders/sentier_guilde_halcyon/PLANCHE_CALQUES_HALCYON.png" target="_blank">🖼️ Ouvrir la Planche Contact Multi-Calques (2100×1300)</a>
        <a class="link-btn" href="renders/sentier_guilde_halcyon/sentier_guilde_halcyon.ora" download>🎨 Télécharger le projet OpenRaster (sentier_guilde_halcyon.ora)</a>
        <a class="link-btn" href="sprites/sentier_guilde_halcyon_pmdo/guild_path_halcyon_layers.rsground" download>💾 Télécharger la carte PMDO (guild_path_halcyon_layers.rsground)</a>
        <a class="link-btn" href="sprites/sentier_guilde_halcyon_pmdo/guild_path_halcyon_layers.tmj" download>🗺️ Télécharger la carte Tiled (guild_path_halcyon_layers.tmj)</a>
      </div>
    </div>
  </div>
</main>

<script>
  let isNight = false;
  let isExploded = false;

  const assets = {{
    day: {{
      sol: "{sol_day}",
      chemin: "{chemin_day}",
      vegetation: "{veg_day}",
      arbres: "{arbres_day}",
      premier_plan: "{premier_plan_day}"
    }},
    night: {{
      sol: "{sol_night}",
      chemin: "{chemin_night}",
      vegetation: "{veg_night}",
      arbres: "{arbres_night}",
      premier_plan: "{premier_plan_night}"
    }}
  }};

  function toggleTheme() {{
    isNight = !isNight;
    const btn = document.getElementById('theme-btn');
    const set = isNight ? assets.night : assets.day;
    btn.innerHTML = isNight ? '☀️ Mode Jour' : '🌙 Mode Nuit (Abyss)';
    btn.classList.toggle('active', isNight);

    document.getElementById('layer-sol').src = set.sol;
    document.getElementById('layer-chemin').src = set.chemin;
    document.getElementById('layer-vegetation').src = set.vegetation;
    document.getElementById('layer-arbres').src = set.arbres;
    document.getElementById('layer-premier-plan').src = set.premier_plan;
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

  function resetLayers() {{
    ['sol', 'chemin', 'vegetation', 'arbres', 'premier-plan'].forEach(id => {{
      document.getElementById('chk-' + id).checked = true;
      document.getElementById('op-' + id).value = 100;
      updateLayer(id);
      updateOpacity(id);
    }});
  }}
</script>

</body>
</html>
"""
(ROOT / 'apercu_sentier_guilde_halcyon.html').write_text(html_content, encoding='utf-8')
print("Generated apercu_sentier_guilde_halcyon.html successfully.")
