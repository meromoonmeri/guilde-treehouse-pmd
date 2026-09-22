"""Packaging aride generee V2 : ORA, GIF/WebP, galerie, ZIP. Lance les tests d'abord."""
import base64
import io
import json
import subprocess
import zipfile
from pathlib import Path
from PIL import Image

R = Path(__file__).resolve().parents[2]
SRC = R / 'source/aride_generee_v2'
OUT = R / 'renders/aride_generee_v2'
PROPS = ['grandA', 'grandB', 'moyenA', 'moyenB', 'arbusteA', 'arbusteB', 'blocA', 'blocB']


def run_tests():
    r = subprocess.run(['.venv/bin/python', '-m', 'unittest', 'source.aride_generee_v2.test_build', '-v'],
                       cwd=R, capture_output=True, text=True)
    print(r.stdout[-1500:])
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit('tests FAIL')


def make_ora():
    ora = OUT / 'aride_generee_v2.ora'
    layers = [('00_plafond', 'couches/00_plafond.png'), ('00_sol', 'couches/00_sol.png'),
              ('01_parois', 'couches/01_parois.png')] + \
             [(f'02_prop_{n}', f'couches/02_prop_{n}.png') for n in PROPS] + \
             [('03_fx_frame0', 'fx/fx_00.png')]
    xml = ['<image w="400" h="360" version="0.0.1"><stack name="racine" opacity="1">']
    for name, _ in layers:
        xml.append(f'<layer name="{name}" src="data/{name}.png" x="0" y="0" opacity="1" visibility="visible" composite-op="svg:src-over"/>')
    xml.append('</stack></image>')
    if ora.exists():
        ora.unlink()
    with zipfile.ZipFile(ora, 'w') as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        z.writestr('stack.xml', ''.join(xml), compress_type=zipfile.ZIP_DEFLATED)
        for name, rel in layers:
            z.write(OUT / rel, f'data/{name}.png', compress_type=zipfile.ZIP_DEFLATED)
    print('ora', ora.stat().st_size)


def make_anim():
    frames = [Image.open(OUT / f'compos_anim/c_{f:02d}.png') for f in range(12)]
    frames[0].save(OUT / 'scene_animee.gif', save_all=True, append_images=frames[1:],
                   duration=100, loop=0, disposal=1)
    frames[0].save(OUT / 'scene_animee.webp', save_all=True, append_images=frames[1:],
                   duration=100, loop=0, lossless=True, method=6)
    print('gif/webp ok')


def b64(p):
    return base64.b64encode((OUT / p).read_bytes()).decode()


def make_gallery():
    m = json.loads((OUT / 'manifest.json').read_text())
    layers = [('Plafond', 'couches/00_plafond.png'), ('Sol', 'couches/00_sol.png'),
              ('Parois + bouche', 'couches/01_parois.png')] + \
             [(f'Prop {n}', f'couches/02_prop_{n}.png') for n in PROPS] + \
             [('FX poussiere (frame 0)', 'fx/fx_00.png')]
    anim = [b64(f'compos_anim/c_{f:02d}.png') for f in range(12)]
    imgs = '\n'.join(
        f'<div class="L" id="L{i}"><label><input type="checkbox" checked data-i="{i}"> {n}</label>'
        f'<img src="data:image/png;base64,{b64(p)}"></div>' for i, (n, p) in enumerate(layers))
    frames_js = json.dumps(anim)
    html = f"""<!doctype html><html lang="fr"><meta charset="utf-8">
<title>Aride generee V2 — entree de donjon desertique</title>
<style>body{{background:#1c130c;color:#efe3cc;font:15px system-ui;margin:0 auto;max-width:1180px;padding:22px}}
h1{{font-size:22px}}p{{line-height:1.55;max-width:75ch}}.warn{{background:#3a2a12;border:1px solid #8a6a2a;
border-radius:10px;padding:12px 16px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}
.L{{background:#2a1d10;border-radius:10px;padding:10px}}img{{width:100%;image-rendering:pixelated;background:#000}}
.stage{{background:#000;border-radius:12px;padding:12px;text-align:center}}#scene{{width:400px;max-width:100%}}
button{{font-size:15px;margin:4px;padding:6px 12px}}input[type=range]{{width:280px}}</style>
<h1>Entree aride — map finale generee (V1)</h1>
<p class="warn"><b>Methode :</b> textures et layers repris au <b>generateur</b> guides par la reference
canonique <code>entrancearidedungeonpmdsky.png</code> (downscale /3, detourage magenta, assemblage
400&times;360, grille 8&nbsp;px). <b>Ce ne sont PAS des pixels natifs.</b>
L'animation de poussiere (12 frames, boucle parfaite, derive + scintillement) est une
<b>proposition originale</b>, pas un cycle officiel. Aucun test PMDO/GPU, collisions a dessiner.</p>
<div class="stage"><img id="scene" alt="scene animee"><br>
<button id="play">⏸ pause</button>
<button id="prev">◀ frame</button><button id="next">frame ▶</button>
<input id="slider" type="range" min="0" max="11" value="0">
<button id="zoom">zoom 2x</button>
<button id="access">voir acces</button></div>
<p><b>Bouche :</b> x{m['mouth']['x0']}-{m['mouth']['x1']}, y{m['mouth']['y0']}-{m['mouth']['y1']} ·
<b>Arrivee sud → seuil :</b> {m['path'][-1]} → {m['path'][0]} ·
<b>12 frames × 100&nbsp;ms</b> · ZIP : <code>renders/aride_generee_v2_pack.zip</code> ·
ORA editable inclus.</p>
<h2>Calques (cocher pour afficher/masquer)</h2><div class="grid">{imgs}</div>
<script>const F={frames_js};let f=0,play=true,z=1,timer;
const el=document.getElementById('scene');
function show(){{el.src='data:image/png;base64,'+F[f];document.getElementById('slider').value=f;}}
timer=setInterval(()=>{{if(play){{f=(f+1)%12;show();}}}},100);
document.getElementById('play').onclick=e=>{{play=!play;e.target.textContent=play?'⏸ pause':'▶ lecture';}};
document.getElementById('prev').onclick=()=>{{f=(f+11)%12;show();}};
document.getElementById('next').onclick=()=>{{f=(f+1)%12;show();}};
document.getElementById('slider').oninput=e=>{{f=+e.target.value;show();}};
document.getElementById('zoom').onclick=e=>{{z=z==1?2:z==2?3:1;el.style.width=(400*z)+'px';e.target.textContent='zoom '+z+'x';}};
document.getElementById('access').onclick=e=>{{
el.src=el.src.includes('access')?'data:image/png;base64,'+F[f]:'{b64('access_review.png')}'?'x':'x';}};
document.querySelectorAll('.L input').forEach(c=>c.onchange=()=>{{
document.getElementById('L'+c.dataset.i).querySelector('img').style.opacity=c.checked?1:0.08;}});
show();</script></html>"""
    # bouton acces : bascule simple entre frame courante et overlay (data-url directe)
    acc = b64('access_review.png')
    html = html.replace(
        "el.src=el.src.includes('access')?'data:image/png;base64,'+F[f]:'{b64('access_review.png')}'?'x':'x';",
        f"if(el.dataset.acc){{el.dataset.acc='';show();}}else{{el.dataset.acc='1';"
        f"el.src='data:image/png;base64,{acc}';}}")
    (R / 'apercu_aride_generee_v2.html').write_text(html)
    print('galerie ok', len(html) // 1024, 'Ko')


def make_zip():
    zp = R / 'renders/aride_generee_v2_pack.zip'
    if zp.exists():
        zp.unlink()
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(R / 'renders'))
    print('zip', zp.stat().st_size)


def make_readme():
    m = json.loads((OUT / 'manifest.json').read_text())
    (OUT / 'README.md').write_text(f"""# Entree aride generee V2

Map finale 400x360 (grille 8 px) : parois canyon + bouche de grotte a l'ouest,
sol sableux avec sentier, 8 props (4 arbres morts, 2 arbustes, 2 blocs),
poussiere animee en 3 bandes (12 frames x 100 ms, boucle parfaite).

## Methode (rendus generes, PAS natif)
4 bruts generateur guides par `entrancearidedungeonpmdsky.png` :
parois/bouche, sol, planche de props, planche de poussiere.
Downscale /3 (BOX), detourage magenta (seuil global d<170 + pelage 2 anneaux),
quantification 128 couleurs, assemblage par calques, raccord dithere (Bayer 8)
entre le seuil de la paroi et le sol.

## Contenu
- `couches/` : plafond, sol, parois, 8 props separes (pieds sur grille 8 px)
- `fx/fx_00..11.png` : derive horizontale wrap (48/72/36 px par cycle) + scintillement alpha
- `compos_anim/` : 12 composites, `scene_animee.gif` / `.webp`
- `aride_generee_v2.ora` : calques editables
- `composite.png`, `access_review.png` (arrivee sud {m['path'][-1]} -> seuil {m['path'][0]})
- `manifest.json` : bouche {m['mouth']}, sentier, pieds, parametres

## Limites honnetes
Textures generees dans la DA PMD, pas des tuiles natives ; bouche/x et cadence
choisies ; animation proposee, pas cycle officiel ; pas de test PMDO/GPU ;
collisions et warp grotte a configurer moteur.

Reproduction : `.venv/bin/python source/aride_generee_v2/build.py` puis
`.venv/bin/python source/aride_generee_v2/package.py` (les tests tournent avant le ZIP).
""")
    print('readme ok')


if __name__ == '__main__':
    run_tests()
    make_ora()
    make_anim()
    make_readme()
    make_gallery()
    make_zip()
    print('PACKAGE OK')
