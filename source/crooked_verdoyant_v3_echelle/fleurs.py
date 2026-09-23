"""Fleurs animées Halcyon (Vast Steppe) sur Crooked V3 928×1152 + compositions PNG/WebP.

Même contrat que source/amp_plains_fleurie_v1 : atlas natif 24×24, séquence de poses 0,1,0,2,
trois horloges 8 / 10 / 14 frames de jeu (60 Hz), aucun scale/recolor/miroir des sprites.
Les calques V3 (générés) restent le décor ; les fleurs sont des pixels NATIFS Vast Steppe.

Reproduction : .venv/bin/python source/crooked_verdoyant_v3_echelle/fleurs.py
"""
from __future__ import annotations
import hashlib, io, json, math, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import scipy.ndimage as nd
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/crooked_verdoyant_v3_echelle'
P = O / 'fleurs_halcyon'
D = P / 'sprites'
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night  # noqa: E402

W, H = 928, 1152
PFX = 'CrookedEchelleV3'
LAYERS = ['01_sol_herbe', '02_lisiere_foret', '03_chemin', '04_parois_crooked',
          '05_entree_grotte', '06_rochers', '07_vegetation_basse', '08_troncs_ombres', '09_canopees']
TICKS = [8, 10, 14]
POSES = [0, 1, 0, 2]
ATLAS = R / 'banque_canonique/atlas/Vast_Steppe_Flower_Animations.png'


def load(p):
    return Image.open(p).convert('RGBA')


def png(im):
    b = io.BytesIO(); im.save(b, format='PNG'); return b.getvalue()


def compose(layers):
    c = Image.new('RGBA', (W, H))
    for im in layers:
        c.alpha_composite(im)
    return c


def main():
    P.mkdir(parents=True, exist_ok=True); D.mkdir(exist_ok=True)
    static = [load(O / 'calques' / f'{PFX}_{n}.png') for n in LAYERS]
    static_n = [load(O / 'nuit' / f'{PFX}_{n}_nuit.png') for n in LAYERS]
    base = compose(static)
    assert np.array(base)[:, :, 3].min() == 255

    atlas = load(ATLAS)
    assert atlas.size == (72, 24)
    flower = [atlas.crop((pose * 24, 0, (pose + 1) * 24, 24)) for pose in POSES]
    heads = []
    for i, im in enumerate(flower):
        im.save(D / f'fleur_vast_phase_{i:02}.png')
        fa = np.array(im); fr, fg, fb = fa[:, :, :3].astype(float).transpose(2, 0, 1)
        petals = ((fr >= fg * .98) & (fr > 100) & (fb >= fg * .75)) | ((fr > 220) & (fg > 190) & (fr >= fg))
        petals[14:] = False
        fa[~petals] = 0
        head = Image.fromarray(fa).crop((0, 0, 12, 16))
        head.save(D / f'petales_vast_phase_{i:02}.png')
        heads.append(head)

    path = np.array(static[2])[:, :, 3] > 0
    walls = np.array(static[3])[:, :, 3] > 0
    cave = np.array(static[4])[:, :, 3] > 0
    rocks = np.array(static[5])[:, :, 3] > 0
    trunks = np.array(static[7])[:, :, 3] > 0
    canopy = np.array(static[8])[:, :, 3] > 0
    blocked = nd.binary_dilation(path | walls | cave | rocks | trunks, iterations=4)
    free = ~blocked
    yy, xx = np.mgrid[:H, :W]
    clear = nd.distance_transform_edt(free)
    spots = np.argwhere((clear >= 10) & (yy > 420) & (yy < H - 20) & (xx > 24) & (xx < W - 24))
    rng = np.random.default_rng(716)
    rng.shuffle(spots)
    sites = []
    for y, x in spots:
        if any((x - s['center'][0]) ** 2 + (y - s['center'][1]) ** 2 < 38 ** 2 for s in sites):
            continue
        tx, ty = int(x) - 12, int(y) - 12
        if any(np.any((np.array(im)[:, :, 3] > 0) & ~free[ty:ty + 24, tx:tx + 24]) for im in flower):
            continue
        sites.append({'kind': 'ground', 'center': [int(x), int(y)], 'origin': [tx, ty],
                      'clock': TICKS[len(sites) % 3], 'offset': len(sites) % 4})
        if len(sites) >= 28:
            break
    assert len(sites) >= 12, len(sites)

    leaf = canopy
    inside = nd.distance_transform_edt(leaf)
    cspots = np.argwhere((inside >= 6) & (yy > 8) & (yy < H - 16) & (xx > 8) & (xx < W - 8))
    rng.shuffle(cspots)
    n_canopy = 0
    for y, x in cspots:
        if any(s['kind'] == 'canopy' and (x - s['center'][0]) ** 2 + (y - s['center'][1]) ** 2 < 22 ** 2 for s in sites):
            continue
        tx, ty = int(x) - 6, int(y) - 7
        if ty < 0 or tx < 0 or ty + 16 > H or tx + 12 > W:
            continue
        if any(np.any((np.array(im)[:, :, 3] > 0) & ~leaf[ty:ty + 16, tx:tx + 12]) for im in heads):
            continue
        sites.append({'kind': 'canopy', 'center': [int(x), int(y)], 'origin': [tx, ty],
                      'clock': TICKS[n_canopy % 3], 'offset': n_canopy % 4})
        n_canopy += 1
        if n_canopy >= 16:
            break

    groups = []
    for kind, sprites, prefix in [('ground', flower, '20_fleurs_sol'), ('canopy', heads, '21_floraison_arbres')]:
        for tick in TICKS:
            name = f'{prefix}_{tick}gf'
            ims = []
            for phase in range(4):
                layer = Image.new('RGBA', (W, H))
                for site in sites:
                    if site['kind'] == kind and site['clock'] == tick:
                        layer.alpha_composite(sprites[(phase + site['offset']) % 4], tuple(site['origin']))
                layer.save(P / f'{PFX}_{name}_{phase:03}.png')
                ims.append(layer)
            groups.append({'name': name, 'tick': tick, 'kind': kind, 'images': ims})

    period = math.lcm(*(4 * t for t in TICKS))
    events = sorted(set(t for tick in TICKS for t in range(0, period, tick)))
    base = compose(static)
    base_n = compose(static_n)
    assert np.array(base)[:, :, 3].min() == 255
    base.save(P / 'COMPOSITION_decor.png')
    flower_night = {id(g['images'][i]): night(g['images'][i]) for g in groups for i in range(4)}

    def stack(base_im, extras, night_mode=False):
        im = base_im.copy()
        for x in extras:
            im.alpha_composite(flower_night[id(x)] if night_mode else x)
        return im

    timeline = []; half = []; half_n = []; durations = []; unique = {}
    n_unique = 0
    for ei, t in enumerate(events):
        extra = [g['images'][(t // g['tick']) % 4] for g in groups]
        key = tuple((t // g['tick']) % 4 for g in groups)
        im = stack(base, extra)
        if key not in unique:
            unique[key] = n_unique
            if n_unique < 8:
                im.save(P / f'{PFX}_composition_{n_unique:03}.png')
            n_unique += 1
        stop = events[ei + 1] if ei + 1 < len(events) else period
        duration = round(stop * 1000 / 60) - round(t * 1000 / 60)
        timeline.append({'game_frame': t, 'duration_game_frames': stop - t, 'duration_ms': duration,
                         'phase_tuple': list(key)})
        durations.append(duration)
        half.append(im.resize((W // 2, H // 2), Image.NEAREST))
        nim = stack(base_n, extra, night_mode=True)
        half_n.append(nim.resize((W // 2, H // 2), Image.NEAREST))
        if ei == 0:
            im.save(P / 'COMPOSITION.png')
            nim.save(P / 'COMPOSITION_nuit.png')
        del im, nim

    # 4 poses 1× (horloges synchronisées) — WebP plein cadre
    sync, sync_n = [], []
    for phase in range(4):
        extra = [g['images'][phase] for g in groups]
        s = stack(base, extra); s.save(P / f'COMPOSITION_pose_{phase:02}.png'); sync.append(s)
        sn = stack(base_n, extra, True); sn.save(P / f'COMPOSITION_pose_{phase:02}_nuit.png'); sync_n.append(sn)
    ds4 = [round((i + 1) * 8 * 1000 / 60) - round(i * 8 * 1000 / 60) for i in range(4)]
    sync[0].save(P / 'ANIMATION_1x.webp', save_all=True, append_images=sync[1:], duration=ds4, loop=0, lossless=True, method=4)
    sync_n[0].save(P / 'ANIMATION_1x_nuit.webp', save_all=True, append_images=sync_n[1:], duration=ds4, loop=0, lossless=True, method=4)
    half[0].save(P / 'ANIMATION_COMPLETE.webp', save_all=True, append_images=half[1:],
                 duration=durations, loop=0, lossless=True, method=4)
    half_n[0].save(P / 'ANIMATION_COMPLETE_nuit.webp', save_all=True, append_images=half_n[1:],
                   duration=durations, loop=0, lossless=True, method=4)
    gif = [fr.convert('P', palette=Image.ADAPTIVE, colors=128) for fr in half[::2]]
    gif_d = [sum(durations[i:i + 2]) for i in range(0, len(durations), 2)]
    gif[0].save(P / 'ANIMATION_COMPLETE_0.5x.gif', save_all=True, append_images=gif[1:],
                duration=gif_d, loop=0, optimize=False)

    root = ET.Element('image', w=str(W), h=str(H), name='Crooked V3 fleurs Halcyon')
    stack = ET.SubElement(root, 'stack')
    with zipfile.ZipFile(P / f'{PFX}_fleurs.ora', 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        ordered = list(zip(LAYERS, static)) + [(g['name'], g['images'][0]) for g in groups]
        for k, (n, im) in reversed(list(enumerate(ordered))):
            fn = f'data/{k:02}.png'
            z.writestr(fn, png(im))
            ET.SubElement(stack, 'layer', name=n, src=fn, x='0', y='0', opacity='1.0',
                          visibility='visible', **{'composite-op': 'svg:src-over'})
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))
        z.writestr('mergedimage.png', png(load(P / 'COMPOSITION.png')))

    manifest = {
        'zone': 'Crooked Cavern verdoyante V3 — fleurs Halcyon Vast Steppe animées',
        'size': [W, H],
        'flowers': 'pixels NATIFS atlas Vast_Steppe_Flower_Animations.png 24×24, poses 0,1,0,2, translation seule',
        'decor': 'calques générés V3 (non natifs)',
        'clocks_game_frames': TICKS,
        'sequence': POSES,
        'loop_game_frames': period,
        'loop_ms': sum(durations),
        'unique_phase_tuples': n_unique,
        'frame_events': len(events),
        'flower_sites': sites,
        'animation_groups': [{'name': g['name'], 'tick': g['tick'], 'kind': g['kind'],
                              'files': [f'{PFX}_{g["name"]}_{i:03}.png' for i in range(4)]} for g in groups],
        'timeline': timeline,
        'outputs': ['COMPOSITION.png', 'COMPOSITION_nuit.png', 'COMPOSITION_pose_00..03.png',
                    'ANIMATION_1x.webp', 'ANIMATION_1x_nuit.webp',
                    'ANIMATION_COMPLETE.webp', 'ANIMATION_COMPLETE_nuit.webp', 'ANIMATION_COMPLETE_0.5x.gif'],
        'night': 'filtre Abyss exact sur les calques fleurs, empilés sur la nuit V3',
        'runtime_pmdo_validated': False,
    }
    (P / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    # galerie légère : chemins relatifs, pas de data-uri
    html = f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Crooked V3 — fleurs Halcyon</title>
<style>body{{background:#14201a;color:#e8eee9;font:15px system-ui;max-width:980px;margin:28px auto;padding:0 18px}}
img{{image-rendering:pixelated;max-width:100%;background:#1b2a22}} h1{{margin:0 0 8px}} .warn{{border-left:4px solid #e0a24a;padding:8px 12px;background:#3a2c1a}}</style>
<h1>Crooked V3 — fleurs Vast Steppe (Halcyon)</h1>
<p>Sprites natifs 24×24, séquence 0,1,0,2, horloges 8/10/14 frames de jeu. Décor 928×1152 V3. Boucle {sum(durations)} ms ({period} frames à 60 Hz).</p>
<div class="warn">Fleurs = pixels natifs Vast Steppe. Décor = généré. PMDO non testé. Floraison des canopées = adaptation (pétales natifs posés, pas un arbre fleuri officiel).</div>
<p><b>Jour 1× (4 poses sync)</b></p><img src="renders/crooked_verdoyant_v3_echelle/fleurs_halcyon/ANIMATION_1x.webp" width="464" alt="animation 1x">
<p><b>Jour horloges 8/10/14 (0,5×)</b></p><img src="renders/crooked_verdoyant_v3_echelle/fleurs_halcyon/ANIMATION_COMPLETE.webp" width="464" alt="animation complete">
<p><b>Nuit 1×</b></p><img src="renders/crooked_verdoyant_v3_echelle/fleurs_halcyon/ANIMATION_1x_nuit.webp" width="464" alt="nuit">
<p>PNG : COMPOSITION.png + COMPOSITION_pose_00..03 · GIF 0,5× · ORA {PFX}_fleurs.ora</p>
<p>Sources : <code>banque_canonique/atlas/Vast_Steppe_Flower_Animations.png</code>, même méthode que <code>source/amp_plains_fleurie_v1</code>.</p>
</html>'''
    (R / 'apercu_crooked_v3_fleurs_halcyon.html').write_text(html)
    print('OK fleurs', len(sites), 'sites dont', n_canopy, 'canopée,', n_unique, 'états,',
          len(events), 'events,', sum(durations), 'ms')


if __name__ == '__main__':
    main()
