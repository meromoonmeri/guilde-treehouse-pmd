#!/usr/bin/env python3
"""Package sinister_woods_gen_v1: manifest, gallery, ZIP."""
import os, json, hashlib, shutil, zipfile
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXP = os.path.join(ROOT, "renders", "sinister_woods_gen_v1")
PLANES = [("01_sol", "Sol du couloir central"),
          ("02_chemin", "Chemin (arrivee sud -> grotte nord)"),
          ("03_rochers", "Rochers"),
          ("04_buissons", "Buissons"),
          ("05_vegetation", "Masses vegetales laterales/hautes"),
          ("06_ombres", "Ombres et creux profonds"),
          ("07_grotte", "Grotte / ouverture nord")]

# bonus bare ground
shutil.copyfile(os.path.join(EXP, "bruts", "sol_nu_magenta.png"),
                os.path.join(EXP, "SinisterGen_00_sol_nu.png"))

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

files = {}
for pid, _ in PLANES:
    f = "SinisterGen_%s.png" % pid
    a = np.asarray(Image.open(os.path.join(EXP, f)))
    files[f] = {"sha256": sha(os.path.join(EXP, f)), "opaque_px": int((a[:, :, 3] > 0).sum())}
for f in ["SinisterGen_composite.png", "SinisterGen_00_sol_nu.png",
          "bruts/foret_entree_magenta.png", "bruts/sol_nu_magenta.png"]:
    files[f] = {"sha256": sha(os.path.join(EXP, f))}
man = {"lot": "sinister_woods_partition_v1", "scene": {"width": 1408, "height": 768, "grid": 8},
       "method": "generated render (PMD-style invented textures), magenta cutout, color/spatial partition",
       "planes": [{"id": pid, "label": lb} for pid, lb in PLANES],
       "files": files,
       "limits": ["Generated art, NOT native certified tiles; no PMDO import tested.",
                  "Visible-surface partition; hidden parts under masses not reconstructed.",
                  "Blue parasites removed by local ring-median inpaint (documented).",
                  "Bonus bare ground is a separate generation (path course differs), texture donor only."]}
json.dump(man, open(os.path.join(EXP, "manifest_partition_7calques.json"), "w"), indent=2)

# gallery
checks = "\n".join(
    '    <label><input type="checkbox" data-plane="%s" checked> %s %s</label>' % (pid, pid, lb)
    for pid, lb in PLANES)
html = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>Sinister Woods — entree de foret generee (multicouches)</title>
<style>
body{background:#14161a;color:#e8e8e8;font-family:sans-serif;margin:0;padding:16px}
h1{font-size:20px}p{max-width:1100px;line-height:1.45}
#panel{display:flex;gap:16px;flex-wrap:wrap}
#ctrl{background:#1e2229;padding:12px;border-radius:8px;min-width:260px}
#ctrl label{display:block;margin:4px 0;cursor:pointer}
#stage{position:relative;border:1px solid #444;
 background:repeating-conic-gradient(#2a2d33 0 25%,#22252b 0 50%) 0 0/32px 32px;}
#stage canvas{display:block;image-rendering:pixelated}
button{margin:4px 4px 0 0;padding:6px 10px;cursor:pointer}
.warn{background:#3a2b12;border:1px solid #a97c2e;padding:8px 12px;border-radius:8px;max-width:1100px}
code{color:#ffd98a}
</style></head><body>
<h1>Entree de foret style Sinister Woods — rendu genere multicouches</h1>
<div class="warn"><b>Rendu genere</b> (textures inventees dans la DA PMD, demandees via generateur),
decoupe magenta + partition des surfaces visibles. <b>Pas des tuiles natives certifiees</b>,
aucun import/test PMDO. Scene 1408x768 (176x96 cases de 8 px), arrivee sud, grotte au nord.</div>
<p>6 pixels bleus parasites retires par inpaint median local (documente dans le lot).
Le sol nu bonus est une generation separee (trace du chemin different) : donneur de texture uniquement.</p>
<div id="panel"><div id="ctrl">
<b>Calques</b>
__CHECKS__
<p><b>Zoom</b> <button id="zout">-</button> <span id="zv">50%</span> <button id="zin">+</button></p>
<p><label><input type="checkbox" id="grid"> Grille 8 px</label></p>
<p><button id="all">Tout afficher</button><button id="none">Tout masquer</button></p>
</div><div id="stage"><canvas id="cv" width="1408" height="768"></canvas></div></div>
<script>
const PLANES=[__PLANES__];
const imgs={};let zoom=0.5;
const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
ctx.imageSmoothingEnabled=false;
function draw(){
 cv.width=1408*zoom;cv.height=768*zoom;
 ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,cv.width,cv.height);
 document.querySelectorAll('#ctrl input[data-plane]').forEach(cb=>{
   if(!cb.checked)return;const im=imgs[cb.dataset.plane];
   if(im&&im.complete&&im.naturalWidth)ctx.drawImage(im,0,0,cv.width,cv.height);});
 if(document.getElementById('grid').checked){
  ctx.strokeStyle='rgba(255,255,0,.35)';ctx.lineWidth=1;ctx.beginPath();
  for(let x=0;x<=1408;x+=8){ctx.moveTo(x*zoom+.5,0);ctx.lineTo(x*zoom+.5,cv.height);}
  for(let y=0;y<=768;y+=8){ctx.moveTo(0,y*zoom+.5);ctx.lineTo(cv.width,y*zoom+.5);}
  ctx.stroke();}
 document.getElementById('zv').textContent=Math.round(zoom*100)+'%';}
let loaded=0;
PLANES.forEach(p=>{const im=new Image();
 im.onload=()=>{if(++loaded===PLANES.length)draw();};im.src='renders/sinister_woods_gen_v1/SinisterGen_'+p+'.png';imgs[p]=im;});
document.querySelectorAll('#ctrl input').forEach(el=>el.addEventListener('change',draw));
document.getElementById('zin').onclick=()=>{zoom=Math.min(2,zoom*1.25);draw();};
document.getElementById('zout').onclick=()=>{zoom=Math.max(.25,zoom/1.25);draw();};
document.getElementById('all').onclick=()=>{document.querySelectorAll('#ctrl input[data-plane]').forEach(c=>c.checked=true);draw();};
document.getElementById('none').onclick=()=>{document.querySelectorAll('#ctrl input[data-plane]').forEach(c=>c.checked=false);draw();};
</script></body></html>
""".replace("__CHECKS__", checks).replace("__PLANES__", ",".join("'%s'" % p for p, _ in PLANES))
open(os.path.join(ROOT, "apercu_sinister_woods_partition_v1.html"), "w").write(html)

# ZIP
zpath = os.path.join(ROOT, "renders", "sinister_woods_gen_v1_pack.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _, fs in os.walk(EXP):
        for f in sorted(fs):
            if f.startswith("_review") or f.startswith("_grid"):
                continue
            p = os.path.join(base, f)
            z.write(p, os.path.relpath(p, ROOT))
print("OK manifest+gallery+zip:", zpath)
