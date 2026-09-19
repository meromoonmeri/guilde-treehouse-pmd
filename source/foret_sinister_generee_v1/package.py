#!/usr/bin/env python3
"""Package V1 — galerie HTML autonome (images embarquees) + ZIP."""
import base64, json, os, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REN = os.path.join(ROOT, "renders", "foret_sinister_generee_v1")
CAL = os.path.join(REN, "calques")
ORDER = ["01_sol", "02_chemin", "03_sous_bois", "04_rochers", "05_troncs", "06_canpees", "07_profondeur", "08_fringe"]
NAMES = {"01_sol": "01 Sol reconstitue (opaque)", "02_chemin": "02 Chemin", "03_sous_bois": "03 Sous-bois / ombres",
         "04_rochers": "04 Rochers", "05_troncs": "05 Troncs / racines", "06_canpees": "06 Canopees (anime)",
         "07_profondeur": "07 Profondeur (grotte)", "08_fringe": "08 Frange (vignette)"}

def b64(path, mime):
    with open(path, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

layers_js = []
for n in ORDER:
    layers_js.append('"%s": "%s"' % (n, b64(os.path.join(CAL, "SinisterGenV1_%s.png" % n), "image/png")))
webp = b64(os.path.join(REN, "SinisterGenV1_animation.webp"), "image/webp")

html = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>Foret Sinister generee V1 — 8 calques + animation</title>
<style>
body{background:#0b0f0c;color:#d8e4d8;font-family:sans-serif;max-width:1100px;margin:auto;padding:16px}
h1{font-size:22px}h2{font-size:17px;margin-top:26px;color:#9fd09f}
.wrap{display:flex;gap:16px;flex-wrap:wrap}
#stage{position:relative;width:424px;height:632px;border:1px solid #355;flex:none}
#stage img{position:absolute;left:0;top:0;width:424px;height:632px;image-rendering:pixelated}
#grid{position:absolute;left:0;top:0;width:424px;height:632px;display:none;pointer-events:none;
background-image:repeating-linear-gradient(0deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px),
repeating-linear-gradient(90deg,rgba(255,255,255,.14) 0 1px,transparent 1px 4px)}
.panel{flex:1;min-width:240px}
label{display:block;margin:5px 0;cursor:pointer}
.chk{width:16px;height:16px;vertical-align:middle}
button{margin:4px 6px 4px 0;padding:6px 10px;cursor:pointer}
.note{background:#141b14;border:1px solid #355;padding:10px;margin-top:14px;font-size:13px;line-height:1.5}
#anim{max-width:424px;width:100%;image-rendering:pixelated;border:1px solid #355}
code{color:#ffd98a}
</style></head><body>
<h1>Foret Sinister generee V1 — entree de foret (848 x 1264, grille 8 px)</h1>
<div class="wrap">
<div id="stage"><div id="grid"></div></div>
<div class="panel">
<h2>Calques</h2>
<div id="toggles"></div>
<button onclick="allLayers(true)">Tous</button><button onclick="allLayers(false)">Aucun</button>
<button onclick="solo('06_canpees')">Canopees seules</button>
<h2>Options</h2>
<label><input type="checkbox" class="chk" id="cgrid" onchange="document.getElementById('grid').style.display=this.checked?'block':'none'"> Grille 8 px</label>
<label>Zoom <select id="zoom" onchange="setZoom(this.value)">
<option value="0.5">0.5x (424px)</option><option value="1">1x natif (848px)</option></select></label>
</div></div>
<h2>Animation — fremissement des canopees (8 frames x 150 ms, boucle 1,2 s)</h2>
<img id="anim" alt="animation">
<div class="note"><b>Limites annoncees.</b> Dessin <b>genere</b> integre, PAS des tuiles natives, PAS un demontage de map.
Le sol sous les elements est <b>reconstitue</b> depuis l'herbe et le chemin visibles de la meme image.
L'animation est un fremissement <b>propose</b> (frame0 = brut exact, boucle fermee), pas un cycle officiel.
Recomposition des 8 calques = brut au pixel pres (28 tests PASS). Aucun test PMDO/GPU.
Fichiers : <code>renders/foret_sinister_generee_v1/</code> (bruts, calques PNG, frames, WebP, GIF) + <code>renders/foret_sinister_generee_v1_pack.zip</code>.
Scripts : <code>source/foret_sinister_generee_v1/</code> (build.py, animate.py, test_build.py, package.py).</div>
<script>
var LAYERS={__LAYERS__};
var WEBP="__WEBP__";
var stage=document.getElementById('stage'), tg=document.getElementById('toggles');
var ORDER=__ORDER__, NAMES=__NAMES__, imgs={};
ORDER.forEach(function(n){
  var im=document.createElement('img'); im.src=LAYERS[n]; stage.insertBefore(im,document.getElementById('grid')); imgs[n]=im;
  var lb=document.createElement('label'); var cb=document.createElement('input');
  cb.type='checkbox'; cb.className='chk'; cb.checked=true;
  cb.onchange=(function(nn,cc){return function(){imgs[nn].style.display=cc.checked?'block':'none';};})(n,cb);
  lb.appendChild(cb); lb.appendChild(document.createTextNode(' '+NAMES[n])); tg.appendChild(lb);
});
document.getElementById('anim').src=WEBP;
function allLayers(v){ORDER.forEach(function(n){imgs[n].style.display=v?'block':'none';});
  tg.querySelectorAll('input').forEach(function(c){c.checked=v;});}
function solo(n){ORDER.forEach(function(k){imgs[k].style.display=(k===n)?'block':'none';});
  var cbs=tg.querySelectorAll('input'); ORDER.forEach(function(k,i){cbs[i].checked=(k===n);});}
function setZoom(z){var w=z==1?848:424,h=z==1?1264:632;stage.style.width=w+'px';stage.style.height=h+'px';
  ORDER.forEach(function(n){imgs[n].style.width=w+'px';imgs[n].style.height=h+'px';});
  var g=document.getElementById('grid');g.style.width=w+'px';g.style.height=h+'px';}
</script></body></html>
"""
html = html.replace("__LAYERS__", ",\n".join(layers_js)).replace("__WEBP__", webp)
html = html.replace("__ORDER__", str(ORDER).replace("'", '"')).replace("__NAMES__", json.dumps(NAMES, ensure_ascii=False))

out = os.path.join(ROOT, "apercu_foret_sinister_v1.html")
open(out, "w").write(html)
print("galerie:", out, os.path.getsize(out), "octets")

zp = os.path.join(REN + "_pack.zip")
if os.path.exists(zp):
    os.remove(zp)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _, files in os.walk(REN):
        for f in sorted(files):
            if f == "grid.png":
                continue
            p = os.path.join(base, f)
            z.write(p, os.path.relpath(p, ROOT))
print("zip:", zp, os.path.getsize(zp), "octets")
