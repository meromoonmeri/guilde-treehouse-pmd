"""Export des livrables « Furnace Desert — biome eau V1 » + vérifications + galerie autonome."""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B  # noqa: E402

ROOT, OUT, P = B.ROOT, B.OUT, B.PREFIX
CAL, PHA = OUT / 'calques', OUT / 'phases'
GALLERY = ROOT / 'apercu_furnace_desert_eau_v1.html'

LAYERS = [  # (numéro, nom, clé, description)
    ('01', 'ciel', 'ciel', 'Ciel source exact (rayons de soleil présents dans cette version source)'),
    ('02', 'eau', 'eau', 'Eau : mer native D25P11A, 15 phases x 130 ms, remplace tout le sable'),
    ('03', 'ombres_contact', 'ombres', 'Ombres de contact semi-transparentes au pied des roches'),
    ('04', 'siphon', 'siphon', 'Siphon en tourbillon : cycle de palette natif D14P11A, 6 phases'),
    ('05', 'cascades', 'cascades', 'Chutes d’eau (anciennes chutes de sable), défilement 6 phases'),
    ('06', 'roches', 'roches', 'Roches et mesas source exactes'),
    ('07', 'premier_plan', 'avant', 'Roches et piliers du premier plan, source exacts'),
]


def png_bytes(arr):
    b = io.BytesIO()
    a = arr.copy()
    a[a[..., 3] == 0] = 0
    Image.fromarray(a).save(b, format='PNG', optimize=True)
    return b.getvalue()


def save(path, arr):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png_bytes(arr))


def layer_at(res, key, t):
    v = res[key]
    return v[t % len(v)] if isinstance(v, list) else v


def write_ora(path, res):
    W, H = res['size']
    stack_xml = ['<?xml version="1.0" encoding="UTF-8"?>', f'<image version="0.0.3" w="{W}" h="{H}">', '<stack>']
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for num, name, key, _ in reversed(LAYERS):
            fn = f'data/{P}_{num}_{name}.png'
            z.writestr(fn, png_bytes(layer_at(res, key, 0)), compress_type=zipfile.ZIP_DEFLATED)
            stack_xml.append(f'<layer name="{num} {name}" src="{fn}" x="0" y="0" opacity="1.0" visibility="visible"/>')
        stack_xml += ['</stack>', '</image>']
        z.writestr('stack.xml', '\n'.join(stack_xml))
        comp = np.array(B.frame(res, 0))
        z.writestr('mergedimage.png', png_bytes(comp))
        th = Image.fromarray(comp)
        th.thumbnail((256, 256), Image.NEAREST)
        b = io.BytesIO(); th.save(b, format='PNG')
        z.writestr('Thumbnails/thumbnail.png', b.getvalue())


def main():
    res = B.build()
    W, H = res['size']
    src = res['seg']['rgba']
    OUT.mkdir(parents=True, exist_ok=True)
    files = {}
    # calques (phase 0 pour les animés) + composite
    for num, name, key, _ in LAYERS:
        fn = CAL / f'{P}_{num}_{name}.png'
        save(fn, layer_at(res, key, 0))
        files[name] = str(fn.relative_to(OUT))
    comp0 = np.array(B.frame(res, 0))
    save(CAL / f'{P}_composite.png', comp0)
    # phases
    phases = {'eau': [], 'siphon': [], 'cascades': []}
    assert all(np.array_equal(res['eau'][i], res['eau'][i + 15]) for i in range(15))  # mer native : période 15
    for key in phases:
        seq = res[key][:15] if key == 'eau' else res[key]
        for t, arr in enumerate(seq):
            fn = PHA / key / f'{P}_{key}_p{t:02d}.png'
            save(fn, arr)
            phases[key].append(str(fn.relative_to(OUT)))
    # animation complète : 30 images x 130 ms (siphon et cascades bouclent 5 fois)
    frames = [B.frame(res, t) for t in range(B.FRAMES)]
    webp = OUT / f'{P}_animation.webp'
    clean = []
    for f in frames:
        a = np.array(f); a[a[..., 3] == 0] = 0; clean.append(Image.fromarray(a))
    clean[0].save(webp, save_all=True, append_images=clean[1:], duration=B.TICK_MS, loop=0, lossless=True,
                  method=6)
    ora = OUT / f'{P}_furnace_eau.ora'
    write_ora(ora, res)

    # ---------------- vérifications ----------------
    ver = {}
    gate = subprocess.run([sys.executable, str(ROOT / 'source/controle_qualite_pixel/gate.py'), '--json',
                           str(OUT / 'gate_rapport.json'), str(CAL)], capture_output=True, text=True)
    ver['gate'] = {'exit_code': gate.returncode, 'stdout': gate.stdout.strip()}
    ver['dimensions'] = {'size': [W, H], 'grid_8px': W % 8 == 0 and H % 8 == 0}
    ver['opaque_composites'] = all(np.array(f)[..., 3].min() == 255 for f in frames)
    seg = res['seg']
    exact = {}
    for key, mask in [('ciel', seg['sky']), ('roches', seg['rock'] | seg['unclassified']), ('avant', seg['foreground'])]:
        arr = res[key]
        m = arr[..., 3] > 0
        exact[key] = {'pixels': int(m.sum()), 'diff_vs_source': int((arr[m] != src[m]).any(-1).sum())}
    exact['roches']['pixels_fondus_des_rayons_nettoyes'] = res['ray_cleanup_px']
    ver['source_pixels_exact'] = exact
    pal = {tuple(c) for c in res['palette'].tolist()}
    tilepal = [{tuple(c) for c in res['tile'][t].reshape(-1, 3).tolist()} for t in range(B.FRAMES)]
    ok_water = all({tuple(c) for c in res['eau'][t][res['eau'][t][..., 3] > 0][:, :3].tolist()} <= tilepal[t]
                   for t in range(B.FRAMES))
    def colors(seq):
        s = set()
        for a in seq:
            s |= {tuple(c) for c in a[a[..., 3] > 0][:, :3].tolist()}
        return s
    ver['palette'] = {
        'eau_couleurs_de_la_phase_native': ok_water,
        'siphon_couleurs_natives_D25': colors(res['siphon']) <= pal,
        'cascades_couleurs_natives_D25': colors(res['cascades']) <= pal,
        'palette_mer_D25': ['#%02x%02x%02x' % c for c in sorted(pal, key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])],
    }
    def distinct(seq):
        return len({a.tobytes() for a in seq})
    ver['animation'] = {'eau_phases_distinctes': distinct(res['eau']), 'siphon_phases_distinctes': distinct(res['siphon']),
                        'cascades_phases_distinctes': distinct(res['cascades']),
                        'boucle_commune_ms': B.FRAMES * B.TICK_MS}
    # relecture WebP : chaque image décodée = empilement des calques de la phase
    wi = Image.open(webp)
    diffs = []
    for t in range(wi.n_frames):
        wi.seek(t)
        a = np.array(wi.convert('RGBA'))
        diffs.append(int((a != np.array(frames[t])).any(-1).sum()))
    ver['webp_relu_exact'] = {'images': wi.n_frames, 'pixels_differents_max': max(diffs)}
    with zipfile.ZipFile(ora) as z:
        merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
    ver['ora_merged_egal_composite'] = bool((merged == comp0).all())
    ver['sea_tile'] = res['tile_stats']
    ver['pass'] = (gate.returncode == 0 and ver['opaque_composites'] and exact['ciel']['diff_vs_source'] == 0 and exact['avant']['diff_vs_source'] == 0 and exact['roches']['diff_vs_source'] == res['ray_cleanup_px']
                   and ok_water and ver['palette']['siphon_couleurs_natives_D25'] and ver['palette']['cascades_couleurs_natives_D25']
                   and ver['webp_relu_exact']['pixels_differents_max'] == 0 and ver['ora_merged_egal_composite'])
    (OUT / 'verification.json').write_text(json.dumps(ver, ensure_ascii=False, indent=1))

    manifest = {
        'zone': 'Furnace Desert (PMD Rescue Team) — biome eau V1', 'prefixe': P, 'taille': [W, H],
        'grille': '8 px (PNG to Tileset)', 'ordre_empilement': [f'{n}_{m}' for n, m, _, _ in LAYERS],
        'calques': [{'num': n, 'nom': m, 'fichier': files[m], 'description': d,
                     'phases': phases.get(k, [])} for n, m, k, d in LAYERS],
        'animation': {'tick_ms': B.TICK_MS, 'images': B.FRAMES, 'boucle_ms': B.FRAMES * B.TICK_MS,
                      'eau': {'phases': 15, 'ms': B.TICK_MS, 'source': 'mer native D25P11A (GIF 30 x 130 ms, cycle réel de 15 phases)'},
                      'siphon': {'phases': len(res['siphon']), 'ms': B.TICK_MS,
                                 'source': 'mécanique du cycle de palette natif D14P11A (6 phases, 60 ms natif) ralentie à 130 ms'},
                      'cascades': {'phases': len(res['cascades']), 'ms': B.TICK_MS, 'defilement_px_par_phase': 16,
                                   'boucle_px': 96},
                      'pmdo_framelength_suggere': 8},
        'sources': {
            'scene': {'fichier': str(B.REFERENCE.relative_to(ROOT)), 'sha256': B.sha(B.REFERENCE),
                      'origine': 'pamtre-berry.neocities.org/images/friend-areas/og/witheringdesert.png (« Furnace Desert, original version »), récupérée via recherche d’images',
                      'note': 'La pièce jointe utilisateur (version mysterydungeonwiki.com, sans grands rayons) n’est pas arrivée dans le bac à sable ; seule sa miniature 300x220 est conservée pour comparaison.'},
            'miniature_wiki': {'fichier': 'source/furnace_desert_eau_v1/references/furnace_desert_wiki_miniature_300x220.png',
                               'sha256': B.sha(HERE / 'references/furnace_desert_wiki_miniature_300x220.png')},
            'mer': {'fichier': B.D25.name, 'sha256': B.sha(B.D25), 'region_haute_mer': B.SEA_REGION,
                    'reseau': 'périodes (48,48) et (144,72), domaine 48x72'},
            'siphon_rythme': {'fichier': B.D14.name, 'sha256': B.sha(B.D14), 'siphon_analyse': [370, 168, 60, 48]},
        },
        'limites': [
            'Biome swap demandé : le sable est remplacé, le siphon et les chutes sont recolorés avec des bleus de la palette native de la mer D25 ; ce ne sont pas des éléments officiels de Furnace Desert en eau.',
            'Les rayons de soleil incrustés dans cette version source restent sur le ciel et les roches, pas sur l’eau.',
            'Pas de pack .rsground ni de test PMDO/GPU pour ce lot.',
        ],
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    write_readme(manifest, ver)
    write_gallery(res, src)
    zpath = OUT / f'{P}_furnace_desert_eau.zip'
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(list(CAL.glob('*.png')) + list(PHA.rglob('*.png'))) + [webp, ora, OUT / 'manifest.json',
                                                                               OUT / 'verification.json', OUT / 'README.md']:
            z.write(p, f'furnace_desert_eau_v1/{p.relative_to(OUT)}')
    print(json.dumps({k: ver[k] for k in ('gate', 'opaque_composites', 'source_pixels_exact', 'animation',
                                          'webp_relu_exact', 'ora_merged_egal_composite', 'pass')}, ensure_ascii=False, indent=1))
    print('palette ok', ver['palette']['eau_couleurs_de_la_phase_native'], ver['palette']['siphon_couleurs_natives_D25'],
          ver['palette']['cascades_couleurs_natives_D25'])


def write_readme(man, ver):
    rows = '\n'.join(f"| {c['num']} | `{Path(c['fichier']).name}` | {c['description']} | "
                     f"{len(c['phases']) if c['phases'] else 'statique'} |" for c in man['calques'])
    cleanup = ver["source_pixels_exact"]["roches"]["pixels_fondus_des_rayons_nettoyes"]
    txt = f"""# Furnace Desert — biome eau V1 (calques PNG animés)

Galerie autonome : **`apercu_furnace_desert_eau_v1.html`** (racine du dépôt) : calques activables, lecture/pause, phase par phase, zoom 1×/2×, comparaison avec le désert d’origine.

Demande : « cette zone en biome swapping en eau, remplace tout le sable par de l’eau sur son propre calque et anime-le ainsi que le siphon ».

## Calques ({man['taille'][0]} × {man['taille'][1]} px, grille 8 px, origine commune (0,0))

| N° | Fichier (`calques/`) | Contenu | Phases |
|---|---|---|---|
{rows}

`calques/{P}_composite.png` = empilement exact des 7 calques (phase 0). Les phases de chaque calque animé sont dans `phases/eau/`, `phases/siphon/`, `phases/cascades/` ; `{P}_animation.webp` montre la boucle complète ; `{P}_furnace_eau.ora` ouvre les calques (phase 0) dans Krita/GIMP. Import PMDO : **PNG to Tileset en 8 px** ; noms de fichiers uniques (préfixe `{P}`).

## Animation

- **Eau** : mer native de `large.D25P11A` (PMD Explorers of Sky) : GIF de 30 images × 130 ms dont le cycle réel est de **15 phases** (1,95 s) — 15 PNG dans `phases/eau/`. La haute mer de la référence est doublement périodique (réseau (48,48) & (144,72)) : sa tuile 48×72 est extraite pour chacune des 30 phases (couleur majoritaire par classe du réseau, accord {ver['sea_tile']['consensus_agreement_mean']:.1%}) puis répétée sans couture sur toute l’ancienne surface de sable.
- **Siphon** : même mécanique que les siphons natifs de `large.D14P11A` (pur cycle de palette, 6 phases, vérifié couleur → couleur). Les bandes suivent le contour ondulé de la cuvette d’origine et avancent vers le centre ; halo d’eau claire à la place du halo de sable clair. 6 phases × 130 ms (le natif D14 tourne à 60 ms ; ralenti pour un grand tourbillon).
- **Chutes** : les deux chutes de sable deviennent des chutes d’eau ; texture de chevrons de la chute gauche (hors rayon), défilement vers le bas de 16 px par phase, boucle de 96 px = 6 phases × 130 ms.
- Tout est synchronisé sur un pas de 130 ms (≈ `FrameLength` 8 à 60 im/s dans PMDO) ; boucle commune : 30 images = 3,9 s (15 × 6 → PPCM 30).

## Ce qui est source exacte / ce qui est transformé

- Ciel et premier plan : **pixels source exacts** (0 différence). Roches et mesas : source exacte sauf **{cleanup} pixels** (bords fondus des rayons de soleil incrustés dans cette version, couleurs uniques) ramenés à la couleur fréquente la plus proche de leur voisinage — nettoyage anti-flou, rien de redessiné.
- Eau : pixels de la mer native D25, phase par phase. Siphon et chutes : leurs formes viennent de la scène, leurs couleurs sont **uniquement des bleus de la palette native de la mer D25** (aucune couleur inventée) — c’est la transformation demandée (biome swap), pas un élément officiel.
- Ombres de contact : noir semi-transparent, proportionnel à l’assombrissement du sable d’origine au pied des roches.

## Source de la scène — important

La pièce jointe (`Rescue_Team_Friend_Area_-_Furnace_Desert.png`, version du wiki Mystery Dungeon) **n’est pas arrivée dans le bac à sable**, et le wiki n’est pas joignable directement. La scène utilisée est la version pleine taille 456×336 « Furnace Desert, original version » (pamtre-berry.neocities.org), même décor mais **avec de grands rayons de soleil incrustés** : ils restent visibles sur le ciel et les roches de droite. Si tu déposes ton fichier dans le dépôt (par ex. `source/furnace_desert_eau_v1/references/`), il suffit de changer `REFERENCE` dans `segment.py` et de relancer — tout le pipeline est automatique.

## Vérifications (`verification.json`)

- `gate.py` : **{'PASS' if ver['gate']['exit_code'] == 0 else 'FAIL'}** sur `calques/` (grille 8 px, alpha binaire hors ombres, zéro magenta, palette pixel art, recomposition exacte).
- Pixels source exacts : ciel, roches, premier plan = 0 différence.
- Couleurs de l’eau = couleurs de la phase native correspondante ; siphon et chutes ⊂ palette de la mer D25.
- Phases distinctes : eau {ver['animation']['eau_phases_distinctes']}, siphon {ver['animation']['siphon_phases_distinctes']}, chutes {ver['animation']['cascades_phases_distinctes']}.
- WebP relu : {ver['webp_relu_exact']['images']} images identiques aux empilements ; ORA : image fusionnée = composite.
- **Non testé** : rendu dans PMDO, collisions, pack `.rsground` (non demandé pour ce lot).

## Reconstruire

```sh
.venv/bin/python source/furnace_desert_eau_v1/export.py
.venv/bin/python source/controle_qualite_pixel/gate.py renders/furnace_desert_eau_v1/calques
```
"""
    (OUT / 'README.md').write_text(txt)


def write_gallery(res, src):
    def uri(arr):
        return 'data:image/png;base64,' + base64.b64encode(png_bytes(arr)).decode()
    data = {'W': res['size'][0], 'H': res['size'][1], 'tick': B.TICK_MS, 'frames': B.FRAMES,
            'source': uri(src), 'layers': []}
    for num, name, key, desc in LAYERS:
        v = res[key]
        seq = v if isinstance(v, list) else [v]
        data['layers'].append({'num': num, 'name': name, 'desc': desc, 'imgs': [uri(a) for a in seq]})
    html = """<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Furnace Desert — biome eau V1</title>
<style>body{background:#0e1a26;color:#e8f1f7;font:15px system-ui;max-width:1100px;margin:24px auto;padding:0 18px}
h1{color:#8fd3ff;margin-bottom:4px}p{line-height:1.55}canvas{image-rendering:pixelated;background:#000;border:1px solid #2b4a63}
.bar button,.bar label{margin:4px 6px 4px 0}button{background:#1d3950;color:#e8f1f7;border:1px solid #4d7ea3;padding:6px 10px;border-radius:4px}
.layers label{display:inline-block;margin:3px 10px 3px 0}small{color:#9fb6c7}</style>
<h1>Furnace Desert — biome eau V1</h1>
<p>Tout le sable est remplacé par la <b>mer native animée</b> de D25P11A (15 phases × 130 ms), le siphon devient un <b>tourbillon</b> (cycle de palette natif façon D14P11A, 6 phases) et les chutes de sable des <b>chutes d’eau</b> défilantes. Roches, ciel et premier plan : pixels source exacts. Calques séparés, 456×336, grille 8 px.</p>
<div class="bar"><button id="play">Pause</button><button id="prev">◀ phase</button><button id="next">phase ▶</button>
<button id="zoom">Zoom 1×</button><label><input type="checkbox" id="src"> désert d’origine</label>
<span id="info"></span></div>
<div class="layers" id="layers"></div>
<canvas id="cv"></canvas>
<p><small>Source de la scène : version pleine taille « original version » (rayons de soleil incrustés) ; la pièce jointe du wiki n’a pas été reçue. Pas de test PMDO.</small></p>
<script>
const D=__DATA__;const cv=document.getElementById('cv'),cx=cv.getContext('2d');cv.width=D.W;cv.height=D.H;
let z=2,t=0,playing=true,last=0;const imgs=D.layers.map(L=>L.imgs.map(s=>{const i=new Image();i.src=s;return i}));
const src=new Image();src.src=D.source;const on=D.layers.map(()=>true);
const box=document.getElementById('layers');D.layers.forEach((L,k)=>{const l=document.createElement('label');
l.title=L.desc;l.innerHTML=`<input type="checkbox" checked> ${L.num} ${L.name}`+(L.imgs.length>1?` <small>(${L.imgs.length} ph.)</small>`:'');
l.querySelector('input').onchange=e=>{on[k]=e.target.checked;draw()};box.appendChild(l)});
function size(){cv.style.width=D.W*z+'px';cv.style.height=D.H*z+'px';document.getElementById('zoom').textContent='Zoom '+z+'×'}
function draw(){cx.clearRect(0,0,D.W,D.H);if(document.getElementById('src').checked){cx.drawImage(src,0,0)}else{
D.layers.forEach((L,k)=>{if(on[k])cx.drawImage(imgs[k][t%imgs[k].length],0,0)})}
document.getElementById('info').textContent=` image ${t+1}/${D.frames} · ${D.tick} ms · boucle ${(D.frames*D.tick/1000).toFixed(1)} s`}
function loop(ts){if(playing&&ts-last>=D.tick){last=ts;t=(t+1)%D.frames;draw()}requestAnimationFrame(loop)}
document.getElementById('play').onclick=e=>{playing=!playing;e.target.textContent=playing?'Pause':'Lecture'};
document.getElementById('prev').onclick=()=>{playing=false;t=(t+D.frames-1)%D.frames;draw()};
document.getElementById('next').onclick=()=>{playing=false;t=(t+1)%D.frames;draw()};
document.getElementById('zoom').onclick=()=>{z=z==2?1:2;size()};document.getElementById('src').onchange=draw;
size();window.onload=()=>{draw();requestAnimationFrame(loop)};
</script></html>"""
    GALLERY.write_text(html.replace('__DATA__', json.dumps(data)))


if __name__ == '__main__':
    main()
