#!/usr/bin/env python3
"""Entrée de forêt — sol Vast Steppe, rochers Amp Plains, arbres Halcyon sur calque propre.

Méthode validée :
- SOL et ROCHERS : pixels 100 % canoniques (Vast_Steppe_Base 8 px ; Amp Plains Entrance 24 px).
- ARBRES : layer de placement passé au générateur dans le style canonique Halcyon
  (référence `arbres_halcyon.png`), détouré du magenta, posé sur son propre calque.
Pas d'import PMDO réel ; collisions/warps non configurés.
"""
from __future__ import annotations

import base64
import importlib.util
import io
import json
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

R = Path(__file__).resolve().parents[2]
S = Path(__file__).resolve().parent
REF = S / 'references'
GEN = S / 'generation'
O = R / 'exports' / 'entree_foret_halcyon_v1'
CELL = 8
W, H = 512, 384

_spec = importlib.util.spec_from_file_location('nat', R / 'source' / 'structures_metano_treasure_v1' / 'native.py')
nat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nat)


def flood_remove(rgba, tol=28):
    h, w = rgba.shape[:2]
    rgb = rgba.astype(int)[:, :, :3]
    seeds = [rgba[y, x, :3].astype(int) for (y, x) in
             [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1), (0, w // 2), (h - 1, w // 2), (h // 2, 0), (h // 2, w - 1)]]
    g = np.zeros((h, w), bool)
    for s in seeds:
        g |= np.abs(rgb - np.array(s)).sum(2) <= tol
    b = np.zeros((h, w), bool)
    b[0, :] = b[-1, :] = True
    b[:, 0] = b[:, -1] = True
    r = nd.binary_propagation(b & g, structure=np.ones((3, 3)), mask=g)
    out = rgba.copy()
    out[r, 3] = 0
    return out


def largest(rgba):
    m = rgba[:, :, 3] > 0
    lab, n = nd.label(m, np.ones((3, 3)))
    if n == 0:
        return rgba
    cnt = np.bincount(lab.ravel())
    cnt[0] = 0
    out = rgba.copy()
    out[lab != np.argmax(cnt), 3] = 0
    return out


def trim(rgba):
    ys, xs = np.where(rgba[:, :, 3] > 0)
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def remove_magenta(rgba):
    r = rgba[:, :, 0].astype(int)
    g = rgba[:, :, 1].astype(int)
    b = rgba[:, :, 2].astype(int)
    matte = (r > 150) & (b > 150) & (g < 120)
    out = rgba.copy()
    out[matte, 3] = 0
    return out


def stamp(canvas, spr, ox, oy):
    h, w = spr.shape[:2]
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(canvas.shape[1], ox + w), min(canvas.shape[0], oy + h)
    if x1 <= x0 or y1 <= y0:
        return
    sx, sy = x0 - ox, y0 - oy
    reg = canvas[y0:y1, x0:x1]
    sub = spr[sy:sy + (y1 - y0), sx:sx + (x1 - x0)]
    a = sub[:, :, 3:4] / 255.0
    reg[:, :, :3] = (sub[:, :, :3] * a + reg[:, :, :3] * (1 - a)).astype(np.uint8)
    reg[:, :, 3] = np.maximum(reg[:, :, 3], sub[:, :, 3])


def build():
    O.mkdir(parents=True, exist_ok=True)

    # --- SOL canonique Vast Steppe (8 px) ---
    vast = nat.read_ground(REF / 'vast_steppe_entrance.rsground')
    vsheets = nat.sheets_from_tiles([REF / f'Vast_Steppe_{n}.tile' for n in ['Base', 'Objects', 'Objects_Under', 'Fringe', 'Cliifs']])
    # Tuiles de sol prises DIRECTEMENT dans la feuille canonique Vast_Steppe_Base.
    btiles = nat.read_tile(REF / 'Vast_Steppe_Base.tile')
    opaque = [(k, t) for k, t in btiles.items() if t[:, :, 3].min() > 0]
    greens = [(k, t) for k, t in opaque if t[:, :, 1].astype(int).mean() >= t[:, :, 0].astype(int).mean() and t[:, :, 1].astype(int).mean() > t[:, :, 2].astype(int).mean()]
    grass = greens[0][1]
    grass2 = next(t for k, t in greens[1:] if t.tobytes() != grass.tobytes())
    lights = [(k, t) for k, t in opaque if t[:, :, :3].astype(int).mean() > 150]
    path = lights[0][1] if lights else grass
    sol = np.zeros((H, W, 4), np.uint8)
    for y in range(0, H, 8):
        for x in range(0, W, 8):
            if 232 <= x < 280:
                sol[y:y + 8, x:x + 8] = path
            else:
                sol[y:y + 8, x:x + 8] = grass if ((x // 8) + (y // 8)) % 2 else grass2

    # --- ROCHERS canoniques Amp Plains (24 px) ---
    amp = nat.read_ground(REF / 'amp_plains_entrance.rsground')
    acache = {'Amp Plains Entrance Layer 1': nat.read_tile(REF / 'AmpPlains_Entrance_L1.tile'),
              'Amp Plains Entrance Layer 2': nat.read_tile(REF / 'AmpPlains_Entrance_L2.tile')}
    arender, _ = nat.render_ground(amp, acache)
    aa = np.array(arender.convert('RGBA'))
    rock_boxes = [(120, 330, 185, 400), (265, 335, 330, 400), (150, 170, 210, 220)]
    rocks = [trim(largest(flood_remove(aa[y0:y1, x0:x1]))) for (x0, y0, x1, y1) in rock_boxes]
    (O / 'rochers').mkdir(exist_ok=True)
    for i, rk in enumerate(rocks):
        Image.fromarray(rk).save(O / 'rochers' / f'AmpRocher_{i+1}.png')

    rochers = np.zeros((H, W, 4), np.uint8)
    rock_pos = [(150, 208), (320, 208), (40, 320), (430, 320)]
    for (px, py), rk in zip(rock_pos, [rocks[0], rocks[1], rocks[2], rocks[1]]):
        h, w = rk.shape[:2]
        reg = rochers[py:py + h, px:px + w]
        a = rk[:, :, 3:4] / 255.0
        reg[:, :, :3] = (rk[:, :, :3] * a + reg[:, :, :3] * (1 - a)).astype(np.uint8)
        reg[:, :, 3] = np.maximum(reg[:, :, 3], rk[:, :, 3])

    # --- ARBRES : sprites CANONIQUES Halcyon (mêmes arbres), placement issu du générateur ---
    obj_render, _ = nat.render_ground(vast, vsheets, layer_filter={2, 3, 4})
    oa = np.array(obj_render.convert('RGBA'))
    m = oa[:, :, 3] > 0
    lab, n = nd.label(m, np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    order = np.argsort(sizes)[::-1]
    trees = []
    for idx in order[1:]:
        ys, xs = np.where(lab == idx)
        h, w = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
        if h < 30 or w < 30:
            continue
        trees.append(trim(oa[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()))
        if len(trees) >= 5:
            break
    (O / 'trees_canoniques').mkdir(exist_ok=True)
    for i, t in enumerate(trees):
        Image.fromarray(t).save(O / 'trees_canoniques' / f'HalArbre_{i+1}.png')

    # Le générateur fournit uniquement le PLACEMENT (masque) ; les arbres posés sont canoniques.
    pm = remove_magenta(np.array(Image.open(GEN / 'placement_arbres.png').convert('RGBA')))[:, :, 3] > 0
    pma = np.array(Image.fromarray((pm * 255).astype(np.uint8)).resize((W, H), Image.Resampling.NEAREST)) > 0
    arbres = np.zeros((H, W, 4), np.uint8)
    cell = 40
    import random
    random.seed(7)
    for cy in range(0, H, cell):
        for cx in range(0, W, cell):
            block = pma[cy:cy + cell, cx:cx + cell]
            if block.size == 0 or block.mean() < 0.45:
                continue
            t = random.choice(trees)
            th, tw = t.shape[:2]
            stamp(arbres, t, cx + cell // 2 - tw // 2, cy + cell - th + 8)

    # --- composite ---
    comp = sol.copy().astype(np.float64)
    for layer in (rochers, arbres):
        a = layer[:, :, 3:4].astype(np.float64) / 255.0
        comp[:, :, :3] = layer[:, :, :3] * a + comp[:, :, :3] * (1 - a)
        comp[:, :, 3] = 255
    comp = np.clip(comp, 0, 255).astype(np.uint8)

    Image.fromarray(sol).save(O / 'entree_00_sol.png')
    Image.fromarray(rochers).save(O / 'entree_01_rochers.png')
    Image.fromarray(arbres).save(O / 'entree_02_arbres.png')
    Image.fromarray(comp).save(O / 'entree_composite.png')

    # --- Tiled 8 px ---
    gids = []
    for y in range(H // 8):
        row = [2 if 232 <= x * 8 < 280 else 1 for x in range(W // 8)]
        gids.append(row)
    csv = ',\n'.join(','.join(map(str, r)) for r in gids)
    Image.fromarray(np.concatenate([grass, path], axis=1)).save(O / 'entree_sol_2tiles.png')
    (O / 'entree_sol.tsx').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<tileset version="1.10" name="entree_sol" tilewidth="8" tileheight="8" tilecount="2" columns="2">\n <image source="entree_sol_2tiles.png" width="16" height="8"/>\n</tileset>\n')
    objs = [f'  <object id="1" name="rochers_amp" x="0" y="0" width="{W}" height="{H}">\n   <image source="entree_01_rochers.png" width="{W}" height="{H}"/>\n  </object>',
            f'  <object id="2" name="arbres_halcyon" x="0" y="0" width="{W}" height="{H}">\n   <image source="entree_02_arbres.png" width="{W}" height="{H}"/>\n  </object>']
    (O / 'entree_foret.tmx').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<map version="1.10" orientation="orthogonal" width="{W//8}" height="{H//8}" tilewidth="8" tileheight="8">\n <tileset firstgid="1" source="entree_sol.tsx"/>\n'
        f' <layer id="1" name="sol" width="{W//8}" height="{H//8}">\n  <data encoding="csv">\n{csv}\n  </data>\n </layer>\n <objectgroup id="2" name="calques">\n' + '\n'.join(objs) + '\n </objectgroup>\n</map>\n')

    # --- provenance + manifeste ---
    prov = {}
    for p in sorted(REF.iterdir()):
        if p.is_file():
            repo = 'Halcyon' if p.stem.startswith(('Vast', 'vast')) else 'ExplorersOfSkyOrigins'
            prov[p.name] = {'repository': {'Halcyon': 'https://github.com/Palikadude/Halcyon', 'ExplorersOfSkyOrigins': 'https://github.com/Minemaker0430/ExplorersOfSkyOrigins'}[repo],
                            'sha256': nat.sha256(p), 'bytes': p.stat().st_size}
    (O / 'provenance.json').write_text(json.dumps(prov, ensure_ascii=False, indent=2) + '\n')
    manifest = {
        'size_px': [W, H], 'grid_px': CELL,
        'layers': ['entree_00_sol.png', 'entree_01_rochers.png', 'entree_02_arbres.png'],
        'composite': 'entree_composite.png',
        'sources': {'sol': 'Vast_Steppe_Base (Halcyon, canonique 8 px)', 'rochers': 'Amp Plains Entrance (ExplorersOfSkyOrigins, canonique 24 px)',
                    'arbres': 'sprites canoniques Halcyon (Vast_Steppe_Objects/Fringe), placement (masque) issu du générateur, calque propre'},
        'not_validated': ['Import PMDO réel', 'Collisions / warps'],
    }
    (O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    _viewer(sol, rochers, arbres, comp)
    with zipfile.ZipFile(R / 'exports' / 'entree_foret_halcyon_v1_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
    print(f'entrée de forêt {W}x{H}px ; rochers {len(rocks)} ; arbres calque alpha {(arbres[:,:,3]>0).sum()} px.')


def _imguri(a):
    buf = io.BytesIO()
    Image.fromarray(a).save(buf, 'png')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def _viewer(sol, rochers, arbres, comp):
    layers = [('sol', sol), ('rochers', rochers), ('arbres', arbres), ('composite', comp)]
    data = [{'id': i, 'uri': _imguri(a)} for i, a in layers]
    html = f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Entrée de forêt — Halcyon</title>
<style>body{{background:#14231e;color:#ecdfba;font:16px system-ui;max-width:1100px;margin:32px auto;padding:16px}}h1{{font-size:30px}}p{{line-height:1.6;color:#c3cfbc}}canvas{{image-rendering:pixelated;background:repeating-conic-gradient(#2a4035 0% 25%,#30493c 0% 50%) 0/16px 16px;display:block;margin:8px 0}}label{{display:block;margin:6px}}a{{color:#e1c97a}}</style>
<h1>Entrée de forêt · sol Vast Steppe + rochers Amp Plains + arbres Halcyon</h1>
<p>Sol et rochers canoniques ; layer de placement des arbres passé au générateur dans le style Halcyon, sur son propre calque. Cochez/masquez les calques.</p>
<div id="c"></div><script>const D={json.dumps(data)};const c=document.getElementById('c');const imgs=[];const checks=[];
const cv=document.createElement('canvas');cv.width={W};cv.height={H};cv.style.width={W*2}+'px';cv.style.height={H*2}+'px';c.append(cv);const x=cv.getContext('2d');
D.forEach((l,i)=>{{const lab=document.createElement('label');const ch=document.createElement('input');ch.type='checkbox';ch.checked=true;ch.dataset.i=i;ch.onchange=draw;checks.push(ch);lab.append(ch,document.createTextNode(l.id));c.append(lab);const im=new Image();imgs.push(im);im.onload=draw;im.src=l.uri}});
function draw(){{x.clearRect(0,0,{W},{H});checks.forEach((ch,i)=>{{if(ch.checked&&imgs[i].complete)x.drawImage(imgs[i],0,0)}})}}</script></html>'''
    (R / 'apercu_entree_foret_halcyon_v1.html').write_text(html)


if __name__ == '__main__':
    build()
