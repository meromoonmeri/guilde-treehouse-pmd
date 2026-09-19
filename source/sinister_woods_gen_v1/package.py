#!/usr/bin/env python3
"""Package sinister_woods_gen_v1: ORA + gallery + ZIP."""
import json, os, zipfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REN = os.path.join(ROOT, "renders", "sinister_woods_gen_v1")
LAY = os.path.join(REN, "calques")
ANIM = os.path.join(REN, "anim")
man = json.load(open(os.path.join(REN, "manifest.json")))
order = man["layers_order"]
W, H = 512, 640

# ---- ORA ----
ora_path = os.path.join(REN, "sinister_woods_gen_v1.ora")
stack = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<image w="%d" h="%d" version="0.0.5">' % (W, H), "<stack>"]
for nm in reversed(order):
    stack.append('  <layer name="%s" src="data/%s.png" opacity="1" visibility="visible" composite-op="svg:src-over" />' % (nm, nm))
stack += ["</stack>", "</image>"]
with zipfile.ZipFile(ora_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
    z.writestr("stack.xml", "\n".join(stack))
    for nm in order:
        z.write(os.path.join(LAY, nm + ".png"), "data/%s.png" % nm)
    z.write(os.path.join(REN, "scene_composite.png"), "mergedimage.png")
    thumb = Image.open(os.path.join(REN, "scene_composite.png")).resize((128, 160))
    tmp = "/tmp/sin_thumb.png"
    thumb.save(tmp)
    z.write(tmp, "Thumbnails/thumbnail.png")
print("ORA:", ora_path, os.path.getsize(ora_path))

# ---- gallery ----
names = {"00_base_terrain": "00 — Terrain de base (opaque)",
         "01_arbre_B_devant_gauche": "01 — Grand arbre devant gauche",
         "02_arbre_C_devant_droit": "02 — Grand arbre devant droit",
         "03_arbre_A_milieu_gauche": "03 — Arbre milieu gauche",
         "04_buisson_A_milieu": "04 — Buisson milieu",
         "05_buisson_B_milieu": "05 — Buisson milieu",
         "06_frise_gauche": "06 — Frise sombre gauche",
         "07_frise_droite": "07 — Frise sombre droite",
         "08_arche_grove": "08 — Arche de lianes (bosquet)",
         "09_herbe_bas_gauche": "09 — Herbes avant-plan gauche",
         "10_herbe_bas_droite": "10 — Herbes avant-plan droit"}
boxes = "".join(
    '<label><input type="checkbox" data-l="%s" checked> %s</label>' % (nm, names[nm])
    for nm in order)
imgs = "".join(
    '<img id="l-%s" src="renders/sinister_woods_gen_v1/calques/%s.png">' % (nm, nm)
    for nm in order)
pulses = "".join(
    '<img class="fx" id="p-%d" src="renders/sinister_woods_gen_v1/anim/pulse_%d.png" style="display:none">' % (i, i)
    for i in range(4))
flies = "".join(
    '<img class="fx" id="f-%d" src="renders/sinister_woods_gen_v1/anim/firefly_%d.png" style="display:none">' % (i, i)
    for i in range(8))
html = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>Entrée Sinister Woods — générée, 11 calques + anim</title>
<style>
body{background:#0d1410;color:#d7e5d7;font-family:sans-serif;margin:0;padding:16px}
h1{font-size:20px} .wrap{display:flex;gap:16px;flex-wrap:wrap}
#stage{position:relative;width:512px;height:640px;background:#000}
#stage img{position:absolute;left:0;top:0;width:512px;height:640px;image-rendering:pixelated}
#grid{position:absolute;left:0;top:0;width:512px;height:640px;display:none;pointer-events:none;
background-image:linear-gradient(#0f03 1px,transparent 1px),linear-gradient(90deg,#0f03 1px,transparent 1px);
background-size:8px 8px}
.panel{max-width:380px} label{display:block;margin:3px 0;font-size:14px}
button{margin:4px 4px 4px 0} .note{font-size:13px;color:#9db89d} code{color:#cfe6cf}
img.preview{max-width:100%;image-rendering:pixelated;border:1px solid #334}
</style></head><body>
<h1>Entrée de forêt style Sinister Woods — lot généré v1</h1>
<p class="note">Pixels <b>générés</b> (détourage magenta), PAS des tuiles natives. Références :
<code>Mystifying_Forest_entrance_TDS.png</code>, <code>Southern_Jungle_entrance_S.png</code>.
Scène 512×640. Arrivée sud, bosquet sombre au nord. Animation : pulsation du bosquet (4 phases)
+ lucioles procédurales (8 phases, 150 ms).</p>
<div class="wrap">
<div id="stage">@@IMGS@@@@PULSES@@@@FLIES@@<div id="grid"></div></div>
<div class="panel">
<button id="play">Lecture anim</button>
<button id="stop">Stop</button>
<button id="toggleGrid">Grille 8px</button>
<button id="all">Tous</button>
<button id="none">Aucun</button>
<div id="boxes">@@BOXES@@</div>
<p class="note">Phases : <span id="ph">–</span></p>
<h3>Aperçu animé (GIF)</h3>
<img class="preview" src="renders/sinister_woods_gen_v1/scene_animee.gif">
<h3>Calques sources</h3>
<p class="note">PNG dans <code>renders/sinister_woods_gen_v1/calques/</code>,
bruts dans <code>bruts/</code>, ORA multicouche + ZIP à côté.</p>
</div></div>
<script>
const order=@@ORDER@@;
document.querySelectorAll('#boxes input').forEach(cb=>{
  cb.addEventListener('change',()=>{
    document.getElementById('l-'+cb.dataset.l).style.display=cb.checked?'block':'none';
  });
});
document.getElementById('all').onclick=()=>{document.querySelectorAll('#boxes input').forEach(cb=>{cb.checked=true;document.getElementById('l-'+cb.dataset.l).style.display='block';});};
document.getElementById('none').onclick=()=>{document.querySelectorAll('#boxes input').forEach(cb=>{cb.checked=false;document.getElementById('l-'+cb.dataset.l).style.display='none';});};
document.getElementById('toggleGrid').onclick=()=>{const g=document.getElementById('grid');g.style.display=g.style.display==='block'?'none':'block';};
let timer=null,fr=0;
function show(f){
  for(let i=0;i<4;i++)document.getElementById('p-'+i).style.display=(i===f%%4)?'block':'none';
  for(let i=0;i<8;i++)document.getElementById('f-'+i).style.display=(i===f)?'block':'none';
  document.getElementById('ph').textContent='pulse '+(f%%4+1)+'/4 — lucioles '+(f+1)+'/8';
}
document.getElementById('play').onclick=()=>{if(timer)return;timer=setInterval(()=>{fr=(fr+1)%%8;show(fr);},150);show(fr);};
document.getElementById('stop').onclick=()=>{clearInterval(timer);timer=null;for(let i=0;i<4;i++)document.getElementById('p-'+i).style.display='none';for(let i=0;i<8;i++)document.getElementById('f-'+i).style.display='none';document.getElementById('ph').textContent='–';};
</script></body></html>"""
html = html.replace("@@IMGS@@", imgs).replace("@@PULSES@@", pulses).replace("@@FLIES@@", flies).replace("@@BOXES@@", boxes).replace("@@ORDER@@", json.dumps(order))
open(os.path.join(ROOT, "apercu_sinister_woods_gen_v1.html"), "w").write(html)
print("gallery OK")

# ---- ZIP ----
zpath = os.path.join(REN, "sinister_woods_gen_v1_pack.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fns in os.walk(REN):
        for fn in sorted(fns):
            if fn.endswith(".zip"):
                continue
            fp = os.path.join(dp, fn)
            z.write(fp, os.path.relpath(fp, REN))
print("ZIP:", zpath, os.path.getsize(zpath))
