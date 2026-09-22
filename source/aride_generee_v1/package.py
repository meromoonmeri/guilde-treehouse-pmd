"""Packaging lot aride generee V1 : GIF/WebP, ORA, galerie, ZIP, verification."""
import base64
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
SRC = R / "source/aride_generee_v1"
OUT = R / "renders/aride_generee_v1"
N = 12
FRAME_MS = 100


def composite_with_fx(base, fx):
    f = fx.astype(float)
    b = base.astype(float)
    al = f[:, :, 3:4] / 255
    rgb = (f[:, :, :3] * al + b[:, :, :3] * (1 - al)).astype(np.uint8)
    return np.dstack([rgb, np.full((288, 408, 1), 255, np.uint8)])


def main():
    r = subprocess.run([sys.executable, "-m", "unittest",
                        "source.aride_generee_v1.test_build"], cwd=R)
    assert r.returncode == 0, "tests en echec"

    base = np.array(Image.open(OUT / "composite.png").convert("RGBA"))
    frames = [np.array(Image.open(OUT / f"fx/frame_{i:02d}.png").convert("RGBA"))
              for i in range(N)]
    comp = [Image.fromarray(composite_with_fx(base, f)[:, :, :3], "RGB")
            for f in frames]
    comp[0].save(OUT / "scene_animee.gif", save_all=True, append_images=comp[1:],
                 duration=FRAME_MS, loop=0)
    comp[0].save(OUT / "scene_animee.webp", save_all=True, append_images=comp[1:],
                 duration=FRAME_MS, loop=0, lossless=True)
    print("GIF/WebP OK")

    # ---- ORA multicouche ----
    ora = OUT / "aride_generee_v1.ora"
    layers = [("L00_sol.png", "sol"), ("L01_parois.png", "parois"),
              ("L03_bouche.png", "bouche"), ("L02_props.png", "props"),
              ("fx/frame_00.png", "fx_frame0_sur_12")]
    stack = ('<image h="288" w="408"><stack opacity="1" name="racine" '
             'composite-op="svg:src-over">')
    for i, (_, name) in enumerate(layers):
        stack += (f'<layer opacity="1" name="{name}" composite-op="svg:src-over" '
                  f'src="data/{i}.png" x="0" y="0"/>')
    stack += "</stack></image>"
    with zipfile.ZipFile(ora, "w") as z:
        z.writestr("mimetype", "image/openraster",
                   compress_type=zipfile.ZIP_STORED)
        z.writestr("stack.xml", stack, compress_type=zipfile.ZIP_DEFLATED)
        for i, (f, _) in enumerate(layers):
            z.write(OUT / f, f"data/{i}.png",
                    compress_type=zipfile.ZIP_DEFLATED)
        thumb = Image.open(OUT / "composite.png").convert("RGB")
        thumb.thumbnail((256, 256))
        buf = io.BytesIO()
        thumb.save(buf, "PNG")
        z.writestr("Thumbnails/thumbnail.png", buf.getvalue())
        z.write(OUT / "composite.png", "mergedimage.png")
    print("ORA OK")

    # ---- galerie ----
    def img_b64(path):
        return base64.b64encode(Path(path).read_bytes()).decode()

    layers_js = {}
    for key, f in [("sol", "L00_sol.png"), ("parois", "L01_parois.png"),
                   ("bouche", "L03_bouche.png"), ("props", "L02_props.png")]:
        layers_js[key] = img_b64(OUT / f)
    fx_js = [img_b64(OUT / f"fx/frame_{i:02d}.png") for i in range(N)]
    ref_js = img_b64(R / "entrancearidedungeonpmdsky.png")
    brut = Image.open(SRC / "bruts/terrain_complet.png").convert("RGB")
    brut = brut.resize((408, 288), Image.NEAREST)
    buf = io.BytesIO()
    brut.save(buf, "PNG")
    brut_js = base64.b64encode(buf.getvalue()).decode()

    html = """<!doctype html><html lang="fr"><meta charset="utf-8">
<title>Aride generee V1 — entree de donjon</title>
<style>
body{background:#1a140f;color:#e8dcc8;font:15px system-ui;max-width:1100px;margin:20px auto;padding:0 16px}
h1{font-size:22px}p{line-height:1.5}canvas{image-rendering:pixelated;width:816px;max-width:100%;background:#000}
.row{display:flex;gap:16px;flex-wrap:wrap}label{background:#2c2318;border-radius:8px;padding:6px 10px;margin:2px;display:inline-block}
img.ref{image-rendering:pixelated;width:408px;max-width:100%}button{font-size:15px;padding:6px 12px}
.note{color:#b9a88c;font-size:13px}
</style>
<h1>Entrée aride — map générée V1 (5 bruts → assemblage)</h1>
<p class="note">Textures <b>reproduites au générateur</b> depuis la référence canonique
<code>entrancearidedungeonpmdsky.png</code> (© Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft) :
ce ne sont pas des pixels natifs extraits. Animation poussière <b>proposée</b> (12 frames × 100 ms,
boucle parfaite, translations pures), pas un cycle officiel. Scène 408×288, grille 8 px.</p>
<canvas id="c" width="408" height="288"></canvas>
<div class="row" style="margin:10px 0">
<label><input type="checkbox" id="l_sol" checked> sol</label>
<label><input type="checkbox" id="l_parois" checked> parois</label>
<label><input type="checkbox" id="l_bouche" checked> bouche</label>
<label><input type="checkbox" id="l_props" checked> props</label>
<label><input type="checkbox" id="l_fx" checked> FX poussière</label>
<button id="play">⏸ pause</button>
<input type="range" id="frame" min="0" max="11" value="0" style="width:200px">
<span id="framelabel">frame 0/12</span>
</div>
<h2>Référence canonique vs composition générée de direction</h2>
<div class="row">
<div><h3>Canonique (référence)</h3><img class="ref" id="ref"></div>
<div><h3>Brut terrain_complet (guide, /3)</h3><img class="ref" id="brut"></div>
</div>
<p class="note">La map finale est assemblée depuis les bruts sol/parois/props/FX détourés,
pas une copie du brut terrain_complet. Chemin sud → bouche vérifié par flood-fill
(voir verification.json). ZIP : renders/aride_generee_v1_pack.zip</p>
<script>
const L = __LAYERS__, FX = __FX__;
const store = {};
let playing = true, frame = 0;
function loadImg(b64){ return new Promise(res => { const i = new Image();
  i.onload = () => res(i); i.src = "data:image/png;base64," + b64; }); }
async function init(){
  for (const k of Object.keys(L)) store[k] = await loadImg(L[k]);
  store.fx = [];
  for (const f of FX) store.fx.push(await loadImg(f));
  document.getElementById('ref').src = "data:image/png;base64," + "__REF__";
  document.getElementById('brut').src = "data:image/png;base64," + "__BRUT__";
  for (const k of ['sol','parois','bouche','props','fx'])
    document.getElementById('l_'+k).onchange = draw;
  document.getElementById('play').onclick = e => { playing = !playing;
    e.target.textContent = playing ? "⏸ pause" : "▶ lecture"; };
  document.getElementById('frame').oninput = e => { frame = +e.target.value; draw(); };
  setInterval(() => { if (playing) { frame = (frame+1)%12;
    document.getElementById('frame').value = frame; draw(); } }, 100);
  draw();
}
function draw(){
  const c = document.getElementById('c').getContext('2d');
  c.clearRect(0,0,408,288);
  for (const k of ['sol','parois','bouche','props'])
    if (document.getElementById('l_'+k).checked) c.drawImage(store[k],0,0);
  if (document.getElementById('l_fx').checked) c.drawImage(store.fx[frame],0,0);
  document.getElementById('framelabel').textContent = `frame ${frame}/12`;
}
init();
</script></html>"""
    html = html.replace("__LAYERS__", json.dumps(layers_js))
    html = html.replace("__FX__", json.dumps(fx_js))
    html = html.replace("__REF__", ref_js).replace("__BRUT__", brut_js)
    (R / "apercu_aride_generee_v1.html").write_text(html)
    print("galerie OK", len(html) // 1024, "Ko")

    # ---- verification + ZIP ----
    ver = {"tests": "10 PASS (unittest source.aride_generee_v1.test_build)",
           "frames": N, "frame_ms": FRAME_MS,
           "boucle": "offsets(i+12)==offsets(i) testes",
           "chemin": "flood sud(205,282) -> bouche(205,100) connecte",
           "recomposition": "L00+L01+L03+L02 == composite exact",
           "magenta": "0 pixel opaque rose (seuil dist<120)",
           "honnetete": ("textures generees guidees par la reference, pas des "
                         "pixels natifs ; animation proposee, pas cycle officiel ; "
                         "pas de test PMDO/GPU, pas de collisions moteur")}
    (OUT / "verification.json").write_text(
        json.dumps(ver, ensure_ascii=False, indent=2))
    pack = R / "renders/aride_generee_v1_pack.zip"
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(R))
        z.write(R / "apercu_aride_generee_v1.html",
                "apercu_aride_generee_v1.html")
    print("ZIP OK", pack.stat().st_size // 1024, "Ko")


if __name__ == "__main__":
    main()
