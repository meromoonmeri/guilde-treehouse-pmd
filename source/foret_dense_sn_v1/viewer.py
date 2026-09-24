"""Galerie autonome de FDENSE_V1 : apercu_foret_dense_sn_v1.html (racine du dépôt).

Lit renders/foret_dense_sn_v1/ (calques, manifest, provenance) — n'écrit rien à l'import.
Usage : .venv/bin/python source/foret_dense_sn_v1/viewer.py
"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "renders" / "foret_dense_sn_v1"
HTML = ROOT / "apercu_foret_dense_sn_v1.html"
PREFIX = "FDENSE_V1_"


def _b64png(arr_or_path) -> str:
    if isinstance(arr_or_path, (str, Path)):
        data = Path(arr_or_path).read_bytes()
    else:
        b = io.BytesIO()
        Image.fromarray(arr_or_path).save(b, "PNG", optimize=True)
        data = b.getvalue()
    return "data:image/png;base64," + base64.b64encode(data).decode()


def provenance_overlay(manifest) -> np.ndarray:
    """Couleur par pixel selon la source du pixel visible au sommet de l'empilement."""
    prov = np.load(OUT / f"{PREFIX}provenance.npz")
    names = [c["fichier"][len(PREFIX):-4] for c in manifest["calques"]]
    H, W = prov[names[0]].shape[:2]
    top = np.full((H, W), -1, np.int32)
    for n in names:
        a = prov[f"{n}_alpha"]
        top[a] = prov[n][..., 0][a]
    img = np.zeros((H, W, 4), np.uint8)
    img[top == 0] = (60, 140, 255, 150)   # D24P11A exact
    img[top == 1] = (60, 230, 120, 150)   # D24P31A exact
    img[top >= 100] = (255, 140, 30, 170)  # généré puis retouché
    return img


def write():
    man = json.loads((OUT / "manifest.json").read_text())
    layers = man["calques"]
    imgs = {c["fichier"]: _b64png(OUT / c["fichier"]) for c in layers}
    over = _b64png(provenance_overlay(man))
    W, H = man["taille"]
    rows = []
    for i, c in enumerate(layers):
        tot = max(1, c["pixels_visibles"])
        can = 100.0 * (c["px_D24P11A"] + c["px_D24P31A"]) / tot
        gen = 100.0 * c["px_generes_retouches"] / tot
        rows.append(f"<tr><td><label><input type=checkbox data-i={i} checked> {c['fichier']}</label></td>"
                    f"<td><button data-solo={i}>solo</button></td><td>{c['pixels_visibles']}</td>"
                    f"<td>{c['couleurs']}</td><td>{can:.0f} %</td><td>{gen:.0f} %</td><td>{c['role']}</td></tr>")
    layer_js = json.dumps([imgs[c["fichier"]] for c in layers])
    html = f"""<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>FDENSE V1 · entrée de forêt dense sud → nord</title>
<style>body{{background:#18241b;color:#e9eed8;font:15px system-ui;max-width:1200px;margin:24px auto;padding:0 20px}}
h1{{color:#f0d69a;font-size:24px}}p,li{{line-height:1.6}}table{{border-collapse:collapse;font-size:13px}}td,th{{border-bottom:1px solid #34463a;padding:4px 8px;text-align:left}}
button,select{{padding:6px 10px;margin:4px;background:#2f4533;border:1px solid #7f906b;color:#f4ecd1;cursor:pointer}}
#wrap{{overflow:auto;max-height:80vh;border:1px solid #34463a;background:#101810}}canvas{{image-rendering:pixelated;display:block}}
.k{{display:inline-block;width:12px;height:12px;margin:0 4px -1px 10px}}</style>
<h1>FDENSE V1 · entrée de forêt dense, arrivée sud → entrée de donjon au nord</h1>
<p>Carte {W} × {H} px ({W // 8} × {H // 8} cases de 8 px), 9 calques + composite. Méthode hybride :
<b>sol, ombre, chemin et parois = pixels exacts</b> de D24P11A / D24P31A (provenance au pixel) ;
fleurs et buissons = sprites canoniques exacts ; <b>arbres géants, entrée et rochers = générés sur magenta
puis retouchés 1:1</b> dans les sous-palettes exactes des références (ce ne sont pas des pixels natifs).
Gate technique PASS ≠ validation artistique ; <b>pas de test PMDO, collisions/warps non définis</b>.</p>
<div><button id=z1>1×</button><button id=z2>2×</button><button id=z3>3×</button><button id=z4>4×</button>
<label><input type=checkbox id=grid> grille 8 px</label>
<label><input type=checkbox id=prov> provenance</label>
<span class=k style="background:#3c8cff"></span>D24P11A exact<span class=k style="background:#3ce678"></span>D24P31A exact<span class=k style="background:#ff8c1e"></span>généré retouché
<button id=all>tout afficher</button></div>
<div id=wrap><canvas id=cv width={W} height={H}></canvas></div>
<table><tr><th>calque</th><th></th><th>px</th><th>couleurs</th><th>canonique</th><th>généré</th><th>rôle</th></tr>{''.join(rows)}</table>
<p>Composite : {man['couleurs_composite']} couleurs, {man['couleurs_hors_palette_references']} hors de la palette des deux références.
Parois : bande périodique exacte de 192 lignes de D24P31A (raccord = continuation canonique). Chemin : {len(man['chemin_segments'])} segments rigides de D24P11A.</p>
<script>
const SRC={layer_js};const OVER="{over}";const W={W},H={H};
const cv=document.getElementById('cv'),ctx=cv.getContext('2d');let zoom=2;
const imgs=SRC.map(s=>{{const i=new Image();i.src=s;return i}});const ov=new Image();ov.src=OVER;
const boxes=[...document.querySelectorAll('input[data-i]')];
function draw(){{cv.width=W*zoom;cv.height=H*zoom;ctx.imageSmoothingEnabled=false;
ctx.fillStyle='#000';ctx.fillRect(0,0,cv.width,cv.height);
boxes.forEach((b,i)=>{{if(b.checked&&imgs[i].complete)ctx.drawImage(imgs[i],0,0,W*zoom,H*zoom)}});
if(document.getElementById('prov').checked&&ov.complete)ctx.drawImage(ov,0,0,W*zoom,H*zoom);
if(document.getElementById('grid').checked){{ctx.strokeStyle='rgba(255,255,255,.18)';ctx.lineWidth=1;ctx.beginPath();
for(let x=0;x<=W;x+=8){{ctx.moveTo(x*zoom+.5,0);ctx.lineTo(x*zoom+.5,H*zoom)}}for(let y=0;y<=H;y+=8){{ctx.moveTo(0,y*zoom+.5);ctx.lineTo(W*zoom,y*zoom+.5)}}ctx.stroke()}}}}
imgs.forEach(i=>i.onload=draw);ov.onload=draw;boxes.forEach(b=>b.onchange=draw);
document.getElementById('grid').onchange=draw;document.getElementById('prov').onchange=draw;
[1,2,3,4].forEach(z=>document.getElementById('z'+z).onclick=()=>{{zoom=z;draw()}});
document.querySelectorAll('button[data-solo]').forEach(b=>b.onclick=()=>{{const k=+b.dataset.solo;boxes.forEach((x,i)=>x.checked=i===k);draw()}});
document.getElementById('all').onclick=()=>{{boxes.forEach(x=>x.checked=true);draw()}};draw();
</script></html>"""
    HTML.write_text(html)
    return HTML


if __name__ == "__main__":
    print(write())
