"""Entrée Southern Jungle — sortie de jungle sud -> nord V1 (ESJ1) — format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Demande : « passe a la suite » (carte suivante de la série, référence choisie par l'agent).
Référence : `Southern_Jungle_exit_S.png` (PMD Explorers), jamais utilisée comme référence principale.
Méthode « textures canoniques » = rendu généré RÉFÉRENCÉ (rip passé au générateur en images=) :
- decor_magenta.png : décor complet (1079 x 976), mare en magenta ; 1er rendu trop saturé, re-teinté une fois
  vers les couleurs du rip (rip + 1er rendu en images=) ;
- sol_complet.png : herbe unie éditée depuis le décor ;
- papillons_poses.png : planche 2 x 4 (papillon jaune et papillon bleu, 4 battements d'ailes) sur magenta.
Normalisation : recadrage 4:3 (1079 x 809, y 30..839) puis réduction x768/1079 par classe (poids BOX, argmax).
Calques : sol complet, sable, herbe, rochers, jungle, grotte (tunnel).
Animations, chacune sur son calque, boucles fermées : mare Métano sans liseré 4 x 10 ; scintillements Métano natifs
4 x 10 ; papillons générés, trajectoires de Lissajous fermées créées par nous, 48 x 5. Scène : 240 ticks.
Lancer : .venv/bin/python source/entree_southern_jungle_sud_nord_v1/build.py
"""
from pathlib import Path
import importlib.util, json, shutil

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
REF = R / 'Southern_Jungle_exit_S.png'
OUT = R / 'renders/entree_southern_jungle_sud_nord_v1'
STAGE = R / '.cache/entree_southern_jungle_sud_nord_v1/entree_southern_jungle_sud_nord'
NAMESPACE = 'entree_southern_jungle_sud_nord'
ASSET = 'esj1_entree_southern_jungle'
PFX = 'ESJ1'
W, H = 768, 576
CROP_Y = 30                                  # recadrage 4:3 du brut : lignes 30..839
WATER_PHASES, WATER_TICKS = 4, 10
BF_PHASES, BF_TICKS = 48, 5
LOOP_TICKS = 240
BF_SIZE = 18                                 # papillon ailes ouvertes ~18 px
GEN = [
    {'file': 'decor_magenta.png', 'images': ['Southern_Jungle_exit_S.png'], 'prompt':
     'Use EXACTLY the same textures, palette and pixel-art style as the reference image (Pokemon Mystery Dungeon Explorers '
     'of Sky, Southern Jungle): pale yellow-beige sandy dirt with pebbles, bright green grass patches with ragged edges, '
     'dense dark jungle foliage, fan palms and ferns, brown trunks, small grey rocks. NEW larger top-down map, WIDE 4:3, '
     'vast. Player arrives at the SOUTH on the sandy path; path goes NORTH through a wide sandy clearing bordered by grass '
     'up to a dark tunnel opening in foliage and big trunks at the top center (dungeon entrance). Dense jungle on sides and '
     'top. Small calm pond on the left, away from the path and not in front of the entrance, filled with flat pure magenta '
     '#FF00FF. No characters, text, UI, border.',
     'note': 'premier rendu trop sature (herbe fluo) : recolore une fois, prompt suivant'},
    {'file': 'decor_magenta.png', 'images': ['source/entree_southern_jungle_sud_nord_v1/bruts/decor_magenta.png',
                                             'Southern_Jungle_exit_S.png'], 'prompt':
     'Recolor and restyle this map to match EXACTLY the colors, textures and shading of the second reference image: muted '
     'olive-khaki sandy ground with darker speckles, medium grass green patches not neon, deep dark teal-green jungle '
     'foliage, fan palms and ferns, dark shadows at the edges, brown trunks. Keep the same layout and the magenta pond.',
     'note': 'brut retenu (1079 x 976) ; le chemin sinueux a fusionne avec la clairiere'},
    {'file': 'sol_complet.png', 'images': ['source/entree_southern_jungle_sud_nord_v1/bruts/decor_magenta.png'], 'prompt':
     'Same image, same size and pixel-art style, but showing only the plain medium-green short jungle grass ground '
     'everywhere (everything else removed and replaced by that same grass texture).'},
    {'file': 'papillons_poses.png', 'images': ['Southern_Jungle_exit_S.png'], 'prompt':
     'Pixel-art sprite sheet on flat pure magenta #FF00FF, PMD Explorers of Sky style. 2 rows of 4 sprites: row 1 = small '
     'yellow-orange jungle butterfly from above in 4 wing-flap poses (open, half, closed, half); row 2 = cyan-blue '
     'butterfly, same 4 poses. Dark outline, wide magenta spacing, no text.'},
]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


FF = loadmod('eff1_build', R / 'source/entree_foggy_forest_sud_nord_v1/build.py')   # utilitaires EFF1
keep_large, close_, open_, quantize_group, rgba = FF.keep_large, FF.close_, FF.open_, FF.quantize_group, FF.rgba
place, cell_grid, sha, is_mag, paste = FF.place, FF.cell_grid, FF.sha, FF.is_mag, FF.paste
PALETTE_GROUPS = {'terrain': (['sol_complet', 'sable', 'herbe'], 64), 'jungle': (['jungle'], 64),
                  'rochers': (['rochers'], 16), 'grotte': (['grotte'], 16)}
STATIC = ['herbe', 'sable', 'rochers', 'jungle', 'grotte']


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(float)


def crop43(a):
    return a[CROP_Y:CROP_Y + round(a.shape[1] * 3 / 4)]


# ---------------------------------------------------------------- fidélité (même classifieur sur rip et brut)
def materials(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]; mag = is_mag(a)
    sand = (r - b > 35) & (np.abs(r - g) < 25) & (lum > 120) & (lum < 215) & ~mag
    grass = (g > r + 35) & (g > b + 40) & (lum > 100) & (lum < 175) & ~mag
    foliage = (g > r + 10) & (lum < 80) & (lum > 20) & ~mag
    return {'sable': sand, 'herbe': grass, 'feuillage': foliage}


def fidelity(decor, ref):
    fr, fd = materials(ref), materials(decor); out = {}
    for k in fr:
        mr, md = ref[fr[k]].mean(0), decor[fd[k]].mean(0)
        out[k] = {'rip_rgb': [round(float(v), 1) for v in mr], 'decor_rgb': [round(float(v), 1) for v in md],
                  'distance': round(float(np.linalg.norm(mr - md)), 1)}
    return out


# ---------------------------------------------------------------- segmentation pleine résolution (brut recadré)
def classify(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    hh, ww = lum.shape; yy, xx = np.mgrid[:hh, :ww]
    L = nd.uniform_filter(lum, 9)
    water = nd.binary_dilation(is_mag(a) | ((r > 180) & (b > 150) & (r - g > 60) & (b - g > 40)), iterations=6)
    # Tunnel (haut-centre) : bouche sombre + arche de pierre grise peu saturée.
    zone = (yy < 190) & (xx > 440) & (xx < 660)
    mouth = nd.binary_fill_holes(keep_large(close_(zone & (lum < 45), 2), 1500))
    stone = zone & (sat < 30) & (lum < 140) & nd.binary_dilation(mouth, iterations=25)
    cave = nd.binary_fill_holes(close_(keep_large(close_(stone | mouth, 3), 1500), 3)) & zone
    # Sable : kaki (r-b > 35, |r-g| < 25), grande composante, trous (cailloux, touffes) comblés.
    sand = (r - b > 30) & (np.abs(r - g) < 28) & (lum > 110) & (lum < 220) & ~water & ~cave
    sand = nd.binary_fill_holes(keep_large(open_(close_(sand, 3), 1), 20000)) & ~water & ~cave
    # Rochers : gris peu saturés, petites composantes, dans ou près de la clairière.
    grey = (sat < 28) & (lum > 95) & (lum < 215) & ~water & ~cave
    gl, n = nd.label(close_(grey, 1)); gs = nd.sum(grey, gl, range(1, n + 1))
    rocks = nd.binary_dilation(np.isin(gl, [i + 1 for i, v in enumerate(gs) if 25 <= v < 3000]), iterations=1) & ~water & ~cave
    # Herbe (moyenne ~ (75,150,65)) : lum lissée > 95 et verte, reliée au sable ou à la mare.
    GR = nd.uniform_filter(g - r, 9)
    grass = (L > 92) & (GR > 35) & ~sand & ~water & ~cave & ~rocks
    grass = open_(close_(grass, 2), 2)
    gl2, _ = nd.label(grass)
    touch = set(np.unique(gl2[nd.binary_dilation(sand | water, iterations=6) & grass])) - {0}
    grass = keep_large(np.isin(gl2, list(touch)), 5000)
    # Touffes et cailloux enclos dans herbe/sable : restent praticables (dessinés sur le calque herbe).
    U = close_(grass | sand, 3); holes = nd.binary_fill_holes(U) & ~U
    hl, _ = nd.label(holes); hs = nd.sum(holes, hl, range(1, hl.max() + 1)) if hl.max() else []
    small = np.isin(hl, [i + 1 for i, v in enumerate(hs) if v < 1500])
    grass = (grass | small | (U & ~sand)) & ~water & ~cave & ~rocks & ~sand
    rocks &= ~sand | rocks
    jungle = ~(water | cave | sand | grass | rocks)
    # Rochers isolés dans la jungle : restent jungle (bloqués de toute façon).
    return dict(water=water, grotte=cave, sable=sand, rochers=rocks, herbe=grass, jungle=jungle, bouche=mouth)


def down_classes(a, masks, order):
    """Réduction par classe : poids BOX, attribution exclusive par poids maximal, couleur = moyenne de la classe."""
    def box(x):
        return np.array(Image.fromarray(x.astype(np.float32)).resize((W, H), Image.Resampling.BOX))
    wts = np.stack([box(masks[k]) for k in order]); win = wts.argmax(0)
    ex, cols = {}, {}
    for i, k in enumerate(order):
        ex[k] = win == i
        s = np.stack([box(a[..., c] * masks[k]) for c in range(3)], -1)
        cols[k] = np.clip(s / np.maximum(wts[i], 1e-6)[..., None], 0, 255)
    return ex, cols


def down_full(a):
    return np.array(Image.fromarray(a.astype('uint8')).resize((W, H), Image.Resampling.BOX)).astype(float)


# ---------------------------------------------------------------- papillons générés
def butterfly_poses(path):
    src = rgb(path); bg = is_mag(src) | ((src[..., 0] - src[..., 1] > 60) & (src[..., 2] - src[..., 1] > 60))
    lab, n = nd.label(nd.binary_dilation(~bg, iterations=6)); items = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = (lab[sl] == i) & ~bg[sl]
        if m.sum() > 3000:
            items.append((sl, m))
    items.sort(key=lambda t: (t[0][0].start // 300, t[0][1].start))
    assert len(items) == 8, len(items)
    k = max(max(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start) for sl, _ in items) / BF_SIZE
    px = np.concatenate([src[sl][m] for sl, m in items])
    q = Image.fromarray(px.reshape(-1, 1, 3).astype('uint8')).quantize(colors=10, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:30], float).reshape(-1, 3)
    out = []
    for sl, m in items:
        s = src[sl] * m[..., None]; hh, ww = m.shape
        nh, nw = max(3, round(hh / k)), max(3, round(ww / k))
        cov = np.array(Image.fromarray(m.astype(np.float32)).resize((nw, nh), Image.Resampling.BOX))
        col = np.stack([np.array(Image.fromarray(s[..., c].astype(np.float32)).resize((nw, nh), Image.Resampling.BOX))
                        for c in range(3)], -1) / np.maximum(cov, 1e-6)[..., None]
        o = np.zeros((nh, nw, 4), 'uint8')
        o[..., :3] = pal[((col[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)]; o[..., 3] = 255
        o[cov < 0.45] = 0
        dark = pal[pal.sum(1).argmin()]                                  # contour sombre de la planche
        ring = nd.binary_dilation(o[..., 3] > 0) & (o[..., 3] == 0)
        big = np.zeros((nh + 2, nw + 2, 4), 'uint8'); big[1:-1, 1:-1] = o
        ring = nd.binary_dilation(big[..., 3] > 0) & (big[..., 3] == 0); big[ring] = (*dark.astype(int), 255)
        out.append(big)
    return out, pal


FLAP = [0, 1, 2, 1]                                  # ouvert, mi, fermé, mi : 1 pose par phase


def butterfly_frames(poses, flights, walk_mask):
    frames = []
    for t in range(BF_PHASES):
        f = np.zeros((H, W, 4), 'uint8')
        for k, (cx, cy, ax, ay, m, ph, fam) in enumerate(flights):
            u = 2 * np.pi * t / BF_PHASES
            x = cx + ax * np.sin(u + ph); y = cy + ay * np.sin(m * u + 2 * ph)
            dx = np.cos(u + ph)
            pi = FLAP[(t + k) % 4]; p = poses[fam * 4 + (3 if pi == 1 and k % 2 else pi)]
            if pi and dx > 0:
                p = p[:, ::-1]
            paste(f, p, x - p.shape[1] / 2, y - p.shape[0] / 2)
        frames.append(f)
    return frames


# ---------------------------------------------------------------- main
def build():
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    ANIMS = ['eau', 'scintillements', 'papillons']
    for d in ['calques', 'animation', 'poses', 'masques', 'review']:
        shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'masques', 'review'] + [f'animation/{x}' for x in ANIMS]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    raw = rgb(RAW / 'decor_magenta.png'); a = crop43(raw); f = crop43(rgb(RAW / 'sol_complet.png')); ref = rgb(REF)
    assert a.shape[:2] == (809, 1079), a.shape
    m = classify(a); mouth = m.pop('bouche')
    order = ['water', 'grotte', 'rochers', 'sable', 'herbe', 'jungle']
    ex, cols = down_classes(a, m, order)
    water = ex['water']
    layers = {'sol_complet': rgba(down_full(f), ~water)}
    for k in STATIC:
        layers[k] = rgba(cols[k], ex[k])
    q = {}
    for keys, n in PALETTE_GROUPS.values():
        q.update(quantize_group({k: layers[k] for k in keys}, n))
    layers = q
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    land = np.zeros((H, W), bool)
    for k in STATIC:
        land |= layers[k][..., 3] == 255
    visible = water & ~land
    FF.V2.H, FF.V2.W = H, W
    wf, dist = FF.V2.water_phases(water, visible)
    fams = FF.BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(visible & (dist > 4), (hh, ww), 1, 71 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    poses, bf_pal = butterfly_poses(RAW / 'papillons_poses.png')
    for i, p in enumerate(poses):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_papillon_{"jaune" if i < 4 else "bleu"}_{i % 4}.png')
    # Vols au-dessus de la clairière et de la mare : (cx, cy, ax, ay, fréquence y, phase, famille).
    flights = [(250, 250, 50, 22, 2, 0.0, 1), (330, 400, 60, 30, 3, 1.1, 0), (470, 330, 70, 26, 2, 2.3, 0),
               (560, 220, 40, 30, 3, 3.6, 1), (420, 470, 55, 20, 2, 4.4, 1), (160, 330, 35, 40, 1, 5.2, 0)]
    pap = butterfly_frames(poses, flights, None)
    anim = {'eau': (wf, WATER_TICKS), 'scintillements': (sf, WATER_TICKS), 'papillons': (pap, BF_TICKS)}
    names = ['eau', 'scintillements', 'sol_complet'] + STATIC + ['papillons']
    stack, layer_list = [], []
    for i, nm in enumerate(names):
        if nm in anim:
            frames, ticks = anim[nm]
            for t, fr in enumerate(frames):
                Image.fromarray(fr).save(OUT / 'animation' / nm / f'{PFX}_{i:02d}_{nm}_f{t:02d}.png')
            layer_list.append({'file': f'animation/{nm}/{PFX}_{i:02d}_{nm}_fNN.png', 'phases': len(frames), 'ticks': ticks})
        else:
            frames, ticks = [layers[nm]], 60
            Image.fromarray(layers[nm]).save(OUT / 'calques' / f'{PFX}_{i:02d}_{nm}.png')
            layer_list.append({'file': f'calques/{PFX}_{i:02d}_{nm}.png', 'phases': 1, 'ticks': 60})
        stack.append((nm, frames, ticks))
    walk_px = (layers['herbe'][..., 3] == 255) | (layers['sable'][..., 3] == 255)
    blocked = cell_grid(~walk_px); gh_, gw_ = blocked.shape
    row = walk_px[H - 8]; pxs = np.nonzero(row)[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    s = W / a.shape[1]; my, mx = np.nonzero(mouth); cx = int(mx.mean() * s)
    cave_bottom = int(np.nonzero(ex['grotte'].any(1))[0].max())
    threshold_px = [cx // 8 * 8 - 8, (cave_bottom + 1 + 7) // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok, 'pas de chemin 16x16'

    def scene(tick):
        im = Image.new('RGBA', (W, H))
        for _, frames, ticks in stack:
            im.alpha_composite(Image.fromarray(frames[(tick // ticks) % len(frames)]))
        return im
    step = 5; scenes = [scene(t) for t in range(0, LOOP_TICKS, step)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(step * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (qx, qy), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([qx, qy, qx + 15, qy + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    sheet = Image.new('RGBA', (8 * 48, 48), (60, 120, 60, 255))
    for i, p in enumerate(poses):
        im = Image.fromarray(p); sheet.alpha_composite(im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST), (i * 48 + 2, 2))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses.png')
    for k, v in dict(STAGE=STAGE, PFX=PFX, ASSET=ASSET, NAMESPACE=NAMESPACE, HERE=HERE).items():
        setattr(FF, k, v)
    FF.write_ora(OUT / f'{PFX}_entree_southern_jungle_calques.ora',
                 {f'{i:02d}_{t}' + ('_f00' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack)})
    counts = FF.ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                                for t, fr, tk in stack], blocked, entry_px, threshold_px, gfx, tools)
    gp = STAGE / f'Data/Ground/{ASSET}.rsground'; doc = json.loads(gp.read_text()); o = doc['Object']
    o['Name']['DefaultText'] = 'Entree Southern Jungle - sortie de jungle, sud vers nord (4:3)'
    o['Comment'] = ('PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Southern Jungle exit ; mare facon Metano sans '
                    'liseré, scintillements Metano natifs, papillons generes (vols crees). Collisions de base a verifier. '
                    'Seuil non raccorde.')
    gp.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')))
    mx_ = (STAGE / 'Mod.xml').read_text()
    mx_ = mx_.replace('Entree Foggy Forest camp sud-nord 4:3', 'Entree Southern Jungle sud-nord 4:3')
    mx_ = mx_.replace('camp de base de foret genere au format 4:3 (ref. rip Foggy Forest Base Camp), mare facon Metano, brume animee.',
                      'sortie de jungle generee au format 4:3 (ref. rip Southern Jungle exit), mare facon Metano, papillons animes.')
    (STAGE / 'Mod.xml').write_text(mx_)
    fid = fidelity(a, ref); final_fid = {}
    for k, nm in (('sable', 'sable'), ('herbe', 'herbe'), ('feuillage', 'jungle')):
        lay = layers[nm]; px = lay[lay[..., 3] == 255][:, :3].astype(float)
        sel = materials(px.reshape(-1, 1, 3))[k][:, 0]; px = px[sel] if sel.sum() > 50 else px
        final_fid[k] = {'calque': nm, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                        'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    manifest = {
        'lot': 'entree_southern_jungle_sud_nord_v1', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8], 'base': 'branche de session (EFF1 pour les utilitaires)',
        'biome': 'Southern Jungle (sortie), reference choisie par l agent (« passe a la suite »)',
        'method': 'textures canoniques = rendu genere REFERENCE : rip passe au generateur ; decor complet sur magenta '
                  '(mare = magenta), herbe complete editee depuis le decor, planche de papillons sur magenta',
        'reference_da': {'file': REF.name, 'sha256': sha(REF), 'titre': 'Sortie de Southern Jungle (PMD Explorers)'},
        'generation': GEN,
        'raw_inputs': [{'file': f'source/entree_southern_jungle_sud_nord_v1/bruts/{n}', 'sha256': sha(RAW / n),
                        'size': list(Image.open(RAW / n).size)} for n in ('decor_magenta.png', 'sol_complet.png', 'papillons_poses.png')],
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur pixel sur le rip et sur le brut ; distance euclidienne',
                         'brut': fid, 'calques_finaux': final_fid},
        'normalization': {'crop_src': [0, CROP_Y, 1079, CROP_Y + 809], 'scale': round(W / 1079, 4),
                          'methode': 'poids BOX par classe, attribution exclusive par poids maximal',
                          'palettes': {g: {'calques': k, 'couleurs': n} for g, (k, n) in PALETTE_GROUPS.items()}},
        'layers': layer_list,
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS,
                  'modele': 'riviere Metano, couleurs Metano EXACTES, sans liseré de rive (water_phases d EWC2)',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'placements': sparkles, 'origine': 'pixels Metano NATIFS inchanges'},
        'papillons': {'poses': len(poses), 'tailles_px': [list(p.shape[:2]) for p in poses],
                      'palette': [[int(c) for c in p] for p in bf_pal], 'vols': [list(v) for v in flights],
                      'battement': 'ouvert, mi, ferme, mi (1 pose par phase)', 'trajectoire': 'Lissajous fermee sur 48 phases',
                      'phases': BF_PHASES, 'frame_length_ticks': BF_TICKS,
                      'origine': 'dessin GENERE ; vols et boucle crees par nous (pas une animation officielle)'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors sable et herbe', 'seuil': 'devant le tunnel, au nord'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'entry': entry_px, 'threshold': threshold_px,
                      'walkable': int((~blocked).sum()), 'fidelite': {k: v['distance'] for k, v in fid.items()},
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'tiles': sum(counts.values())}))


if __name__ == '__main__':
    build()
