"""Package V3 : ORA + galerie autonome + ZIP + verification."""
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
SRC = Path(__file__).resolve().parent
OUT = R / 'renders' / 'aride_finale_magenta_v3'
LAYERS = ['L00_sol', 'L01_chemin', 'L02_cliff', 'L03_roches', 'L04_arbres', 'L05_ombres']
NOMS = {'L00_sol': 'Sol sableux', 'L01_chemin': 'Sentier en S', 'L02_cliff': 'Cliff + bouche',
        'L03_roches': 'Blocs + cailloux', 'L04_arbres': 'Arbres morts', 'L05_ombres': 'Ombres'}


def make_ora():
    ora = OUT / 'aride_finale_magenta_v3.ora'
    stack = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<image w="408" h="288" version="0.0.1"><stack name="racine" opacity="1" visibility="visible" isolation="isolate" composite-op="svg:src-over">']
    for i, k in enumerate(reversed(LAYERS)):
        stack.append(f'<layer name="{NOMS[k]}" src="data/layer{i}.png" opacity="1" visibility="visible" composite-op="svg:src-over"/>')
    stack.append('</stack></image>')
    if ora.exists():
        ora.unlink()
    with zipfile.ZipFile(ora, 'w') as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        z.writestr('stack.xml', '\n'.join(stack))
        for i, k in enumerate(reversed(LAYERS)):
            z.write(OUT / f'{k}.png', f'data/layer{i}.png')
        comp = Image.open(OUT / 'composite.png').convert('RGB').resize((204, 144))
        buf = io.BytesIO()
        comp.save(buf, 'PNG')
        z.writestr('Thumbnails/thumbnail.png', buf.getvalue())
    print('ORA', ora.stat().st_size)


def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


def make_gallery():
    man = json.loads((OUT / 'manifest.json').read_text())
    imgs = {k: b64(OUT / f'{k}.png') for k in LAYERS}
    imgs['composite'] = b64(OUT / 'composite.png')
    imgs['access'] = b64(OUT / 'access_review.png')
    imgs['ref'] = b64(R / 'entrancearidedungeonpmdsky.png')
    order = man['ordre']
    checks = '\n'.join(
        f'<label><input type="checkbox" data-k="{k}" checked> {NOMS[k]}</label>' for k in order)
    page = f"""<!doctype html><html lang="fr"><meta charset="utf-8"><title>Aride finale V3 — magenta → natif</title>
<style>body{{background:#1d150c;color:#f0e2c8;font:16px system-ui;max-width:1100px;margin:20px auto;padding:16px}}
canvas{{image-rendering:pixelated;border:1px solid #6b543a;background:#808080}}label{{margin-right:12px;white-space:nowrap}}
.row{{display:flex;gap:16px;flex-wrap:wrap}}img{{image-rendering:pixelated;max-width:100%}}code{{color:#c8a878}}</style>
<h1>Entrée aride — version finale V3</h1>
<p>Méthode <b>générateur sur fond magenta</b> : 5 bruts 1224×864 → inondation + pelage → /3 NEAREST → <b>remap palette 100% native</b> (99 couleurs de la référence) → 6 calques → assemblage sud→nord. Motifs générés, pixels 1× nets, palette native.</p>
<div><b>Calques :</b><br>{checks}<br><br>
<label>Zoom <select id="z"><option value="1">1×</option><option value="2" selected>2×</option><option value="3">3×</option></select></label>
<label><input type="checkbox" id="grid"> grille 8px</label>
<label><input type="checkbox" id="acc"> review accès</label></div><br>
<canvas id="cv" width="408" height="288"></canvas>
<h2>Rendu final + accès</h2><div class="row"><div><img src="data:image/png;base64,{imgs['composite']}" width="408"><p>composite</p></div>
<div><img src="data:image/png;base64,{imgs['access']}" width="408"><p>accès sud→bouche (rouge = bloqué)</p></div>
<div><img src="data:image/png;base64,{imgs['ref']}" width="408"><p>référence canonique (comparatif)</p></div></div>
<h2>Limites honnêtes</h2><p>Textures reproduites au générateur, pas des pixels extraits du jeu. Bouche {man['bouche_bbox']}, accès vérifié par flood-fill (pas de collisions/warps moteur). Pas de test PMDO/GPU.</p>
<script>const IM={{}};const SRC={{{','.join(f"{k}:'data:image/png;base64,{v}'" for k,v in imgs.items() if k in set(order))}}};
const ORDER={json.dumps(order)};const cv=document.getElementById('cv'),cx=cv.getContext('2d');cx.imageSmoothingEnabled=false;
let loaded=0;const total=ORDER.length;
ORDER.forEach(k=>{{const i=new Image();i.onload=()=>{{IM[k]=i;if(++loaded===total)draw();}};i.src=SRC[k];}});
function draw(){{const z=+document.getElementById('z').value;cv.width=408;cv.height=288;cx.clearRect(0,0,408,288);
ORDER.forEach(k=>{{const c=document.querySelector(`input[data-k="${{k}}"]`);if(c&&c.checked)cx.drawImage(IM[k],0,0);}});
if(document.getElementById('acc').checked){{const a=new Image();a.onload=()=>cx.drawImage(a,0,0);a.src='data:image/png;base64,{imgs['access']}';}}
cv.style.width=408*z+'px';cv.style.height=288*z+'px';
if(document.getElementById('grid').checked){{cx.strokeStyle='rgba(255,255,255,.25)';for(let x=0;x<=408;x+=8){{cx.beginPath();cx.moveTo(x+.5,0);cx.lineTo(x+.5,288);cx.stroke();}}for(let y=0;y<=288;y+=8){{cx.beginPath();cx.moveTo(0,y+.5);cx.lineTo(408,y+.5);cx.stroke();}}}}}}
document.querySelectorAll('input,select').forEach(e=>e.addEventListener('change',draw));</script></html>"""
    (R / 'apercu_aride_finale_magenta_v3.html').write_text(page)
    print('galerie OK')


def make_zip():
    zp = R / 'renders' / 'aride_finale_magenta_v3_pack.zip'
    if zp.exists():
        zp.unlink()
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():
                z.write(p, f'aride_finale_magenta_v3/{p.relative_to(OUT)}')
    print('ZIP', zp.stat().st_size)


def main():
    make_ora()
    make_gallery()
    make_zip()
    r = subprocess.run([sys.executable, 'test_build.py'], cwd=SRC, capture_output=True, text=True)
    print(r.stderr[-1500:] if r.stderr else r.stdout[-1500:])
    ver = {'tests': 'PASS' if r.returncode == 0 else 'FAIL', 'detail': (r.stderr or r.stdout)[-2000:]}
    (OUT / 'verification.json').write_text(json.dumps(ver, indent=2) + '\n')
    if r.returncode != 0:
        raise SystemExit('TESTS FAIL')
    print('PACKAGE OK')


if __name__ == '__main__':
    main()
