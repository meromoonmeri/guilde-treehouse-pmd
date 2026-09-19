#!/usr/bin/env python3
"""Package V1 : ORA multicouche + galerie HTML + README + ZIP."""
import json, os, zipfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REN = os.path.join(ROOT, "renders", "foret_sinister_generee_v1")
ORDER = ["01_sol", "02_chemin", "03_sous_bois", "04_rochers", "05_troncs", "06_canpees", "07_profondeur", "08_fringe"]
W, H = 848, 1264

# ---------- ORA ----------
ora_path = os.path.join(REN, "SinisterGenV1.ora")
if os.path.exists(ora_path):
    os.remove(ora_path)
z = zipfile.ZipFile(ora_path, "w", zipfile.ZIP_DEFLATED)
z.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
stack = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<image w="%d" h="%d" version="0.0.5">' % (W, H), ' <stack opacity="1" name="root" composite-op="svg:src-over">']
for nm in ORDER:
    stack.append('  <layer name="%s" src="data/%s.png" opacity="1" visibility="visible" composite-op="svg:src-over" x="0" y="0"/>' % (nm, nm))
stack += [' </stack>', '</image>']
z.writestr("stack.xml", "\n".join(stack))
for nm in ORDER:
    z.write(os.path.join(REN, "calques", "SinisterGenV1_%s.png" % nm), "data/%s.png" % nm)
z.write(os.path.join(REN, "SinisterGenV1_composite.png"), "mergedimage.png")
thumb = Image.open(os.path.join(REN, "SinisterGenV1_composite.png")).resize((212, 316), Image.BILINEAR)
tmp = os.path.join(REN, "review", "_thumb.png")
thumb.save(tmp)
z.write(tmp, "Thumbnails/thumbnail.png")
os.remove(tmp)
z.close()
print("ORA", os.path.getsize(ora_path))

# ---------- README ----------
man = json.load(open(os.path.join(REN, "calques", "manifest.json")))
readme = """# Forêt Sinister générée V1 — entrée de donjon (rendu généré)

Entrée de forêt style Sinister Woods : chemin sud → grotte sombre nord,
gros arbres à racines, rochers, lisière noire. **Dessin 100 % généré**
(d'après références Mystifying Forest + guide V3), PAS des pixels natifs,
PAS des bouts de map. 848 x 1264 (grille 8 px), aucun resampling.

## Contenu
- `bruts/foret_sinister_complete.png` : scène complète générée (2e essai conservé : `brume_magenta.png` remplacé par `brume_noir.png` pour la brume).
- `bruts/foret_sinister_sol.png` : variante sol nu non recalée (bonus, même courbe approximative).
- `calques/SinisterGenV1_*.png` : 8 calques (sol reconstitué sous les éléments, chemin, sous-bois, rochers, troncs, canopées, profondeur, frange). Recomposition = brut exact (0 px d'écart).
- `SinisterGenV1.ora` : projet multicouche éditable (GIMP/Krita/MyPaint).
- `SinisterGenV1_composite.png` : composition de contrôle (= brut).
- `anim/overlay_00..47.png` + `anim_overlay.webp` : 48 frames x 100 ms (4,8 s, boucle exacte), brume dérivante + 54 lucioles.
- `preview_scene.gif` / `preview_scene.webp` : aperçu animé x0.5.
- Galerie : `apercu_foret_sinister_v1.html` à la racine du dépôt.

## Limites
- Les calques sont des partitions de surfaces visibles : les faces cachées (sous canopées) sont reconstituées, pas dessinées.
- Le sol caché est un remplissage plausible (voronoï d'herbe), visible uniquement si on masque les calques supérieurs.
- Aucun test PMDO/GPU, aucune collision/warp. Prochaine version prévue : méthode canonique (guide générateur + tuiles natives multicouches style Halcyon).

## Reproduction
```
.venv/bin/python source/foret_sinister_generee_v1/build.py
.venv/bin/python source/foret_sinister_generee_v1/animate.py
.venv/bin/python source/foret_sinister_generee_v1/package.py
.venv/bin/python source/foret_sinister_generee_v1/test_v1.py
```
"""
open(os.path.join(REN, "README.md"), "w").write(readme)

# ---------- galerie ----------
items = "\n".join(
    '    <label><input type="checkbox" data-layer="%s" checked> %s</label>' % (nm, nm) for nm in ORDER)
counts = " / ".join("%s %s px" % (k, v) for k, v in man["counts"].items())
html = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>Forêt Sinister V1 — entrée générée + animation</title>
<style>
body{background:#0b120d;color:#dfe;margin:0;font-family:sans-serif}
.wrap{max-width:1000px;margin:auto;padding:16px}
.view{position:relative;width:424px;height:632px;margin:8px auto;border:1px solid #456}
.view img.layer{position:absolute;left:0;top:0;width:424px;height:632px;image-rendering:auto}
.panel{background:#142014;padding:10px;margin:10px 0;border-radius:8px}
label{display:inline-block;margin:3px 8px}
.grid8{position:absolute;left:0;top:0;width:424px;height:632px;display:none;pointer-events:none;
background-image:linear-gradient(#f0f 1px,transparent 1px),linear-gradient(90deg,#f0f 1px,transparent 1px);
background-size:4px 4px;opacity:.35}
.row{display:flex;gap:12px;flex-wrap:wrap;justify-content:center}
.row img{max-width:424px;border:1px solid #456}
small{color:#9b9}
</style></head><body><div class="wrap">
<h1>Forêt Sinister V1 <small>rendu généré 848×1264 + brume/lucioles 4,8 s</small></h1>
<div class="panel"><b>Calques</b> (recomposition exacte du brut) :<br>%s<br>
<label><input type="checkbox" id="grid"> grille 8 px</label>
<label><input type="checkbox" id="anim" checked> animation overlay</label></div>
<div class="view" id="view">
%s
<div class="grid8" id="grid8"></div>
</div>
<div class="panel"><b>Animation</b> — 48 frames × 100 ms, boucle exacte.<br>
<img src="renders/foret_sinister_generee_v1/preview_scene.webp" width="424" alt="preview anime">
<br><small>Fichiers : anim_overlay.webp (overlay seul) · preview_scene.gif · anim/overlay_*.png</small></div>
<div class="panel"><b>Composition</b> (PNG = brut généré, 0 px d'écart) :<br>
<div class="row"><img src="renders/foret_sinister_generee_v1/SinisterGenV1_composite.png" style="max-width:424px"></div></div>
<div class="panel"><b>Bruts &amp; contrôles</b><div class="row">
<img src="renders/foret_sinister_generee_v1/bruts/foret_sinister_complete.png" width="300">
<img src="renders/foret_sinister_generee_v1/review/planche_masques.png" width="300">
<img src="renders/foret_sinister_generee_v1/review/sol_reconstitue.png" width="300">
</div><small>Comptes : %s</small></div>
<div class="panel"><small>Dessin généré (réfs Mystifying Forest + guide V3), pas des pixels natifs.
Calques = partitions de surfaces visibles. Sol caché reconstitué. Aucun test PMDO/GPU/collision.
ORA éditable + ZIP dans renders/foret_sinister_generee_v1*. Reproduction : voir README du lot.</small></div>
</div>
<script>
const view=document.getElementById('view');
const layers=[...view.querySelectorAll('img.layer')];
document.querySelectorAll('input[data-layer]').forEach(cb=>cb.onchange=()=>{
const img=layers.find(i=>i.dataset.layer===cb.dataset.layer);img.style.display=cb.checked?'block':'none';});
document.getElementById('grid').onchange=e=>{document.getElementById('grid8').style.display=e.target.checked?'block':'none';};
const ov=document.createElement('img');ov.src='renders/foret_sinister_generee_v1/anim/overlay_00.png';
ov.style.cssText='position:absolute;left:0;top:0;width:424px;height:632px';view.appendChild(ov);
let f=0;setInterval(()=>{if(!document.getElementById('anim').checked){ov.style.display='none';return;}
ov.style.display='block';f=(f+1)%%48;ov.src='renders/foret_sinister_generee_v1/anim/overlay_'+String(f).padStart(2,'0')+'.png';},100);
</script></body></html>
""" % (items, "\n".join(
    '<img class="layer" data-layer="%s" src="renders/foret_sinister_generee_v1/calques/SinisterGenV1_%s.png">' % (nm, nm) for nm in ORDER), counts)
open(os.path.join(ROOT, "apercu_foret_sinister_v1.html"), "w").write(html)
print("gallery ok")

# ---------- ZIP ----------
zp = os.path.join(ROOT, "renders", "foret_sinister_generee_v1_pack.zip")
if os.path.exists(zp):
    os.remove(zp)
z = zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED)
base = os.path.join(ROOT, "renders", "foret_sinister_generee_v1")
for dp, dn, fn in os.walk(base):
    if "/review" in dp.replace(base, ""):
        continue
    for f in sorted(fn):
        if f.startswith("_"):
            continue
        full = os.path.join(dp, f)
        z.write(full, os.path.relpath(full, os.path.join(ROOT, "renders")))
z.write(os.path.join(ROOT, "apercu_foret_sinister_v1.html"), "apercu_foret_sinister_v1.html")
z.close()
print("ZIP", os.path.getsize(zp))
