"""Thunder Meadow — falaise à terrasses et arène au-dessus de l'orage V1 (TMA1) — 4:3 (768 x 576, 96 x 72 cases).

Demande : « fait une falaise magnifique en plusieurs calque de tiny meadow une arene etc au dessus des nuage electrique
et en bg des nuage en spiral avec de la foudre etc avec les texture color canonique ». « Tiny meadow » = Thunder Meadow
(Friend Area de PMD Rescue Team), rip trouvé dans la branche arena/01a0d8a8 : `Rescue_Team_Friend_Area_-_Thunder_Meadow.png`
et la planche Toastypk `5394.png` (carte + « Cloud flash colors » 8 x 6 + éclairs natifs), copiée dans bruts/ref_5394.png.
Méthode « textures canoniques » = rendu généré RÉFÉRENCÉ (rip en images=) + COULEURS CANONIQUES :
- falaise_magenta.png : falaise à 3 terrasses, arène de pierres au sommet, îlots flottants ; vide = magenta ;
- fond_spirale.png : spirale d'orage + mer de nuages vue d'en haut ;
- foudre_poses.png : 8 éclairs sur magenta (référence 5394.png).
Couleurs canoniques : le fond est ré-indexé EXACTEMENT sur les 8 couleurs du niveau 0 de la palette de flash du rip
(rang de luminance), et le flash rejoue les 6 niveaux natifs (Dark -> Light) ; étincelles = pixels d'éclairs NATIFS.
Calques : fond nuages (flash), foudre, étincelles, îlots, falaises, prairie, chemin, arène, pierres, arbre.
Boucle : 48 phases x 5 ticks = 240 ticks. Brut 1200 x 896 -> x0.64 exact (pas de recadrage).
Lancer : .venv/bin/python source/thunder_meadow_arene_v1/build.py
"""
from pathlib import Path
import importlib.util, json, shutil

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
REF = R / 'Rescue_Team_Friend_Area_-_Thunder_Meadow.png'
SHEET = RAW / 'ref_5394.png'
OUT = R / 'renders/thunder_meadow_arene_v1'
STAGE = R / '.cache/thunder_meadow_arene_v1/thunder_meadow_arene'
NAMESPACE = 'thunder_meadow_arene'
ASSET = 'tma1_thunder_meadow_arene'
PFX = 'TMA1'
W, H = 768, 576
PH, TK = 48, 5
LOOP = PH * TK
FLASH = [[tuple(0 for _ in range(3))] * 8] * 6          # rempli depuis la planche
# Niveau de flash par phase : calme, puis 2 coups de tonnerre (montée brève, retombée lente).
LEVELS = [0] * 8 + [5, 5, 4, 3, 2, 1, 1, 0] + [0] * 10 + [4, 5, 5, 3, 2, 2, 1, 1, 0] + [0] * 7 + [3, 2, 1, 0, 0, 0]
assert len(LEVELS) == PH
# Éclairs : (pose, x centre, y haut, phase de départ) ; visibles 3 phases pendant les flashs.
BOLTS = [(0, 110, 20, 8), (5, 650, 10, 9), (3, 380, -10, 26), (7, 700, 40, 27), (1, 60, 60, 28), (6, 250, 0, 42)]
GEN = [
    {'file': 'falaise_magenta.png', 'images': ['Rescue_Team_Friend_Area_-_Thunder_Meadow.png'], 'prompt':
     'Use EXACTLY the same textures, palette and pixel-art style as the reference image (Pokemon Mystery Dungeon Rescue '
     'Team, Thunder Meadow): bright yellow-green meadow grass with olive tufts, brown-pink layered cliff faces under grassy '
     'overhangs, blue-grey boulders, dead twisted tree. NEW MAGNIFICENT top-down 3/4 map, WIDE 4:3: tall cliff mountain top '
     'in several stacked tiers of grassy plateaus with cliff walls; on the highest plateau a round ARENA (pale worn grass '
     'ring bordered by standing blue-grey stones); a path climbs from the south with steps up to the arena; floating grassy '
     'rock pillars left and right. Sky and void = flat pure magenta #FF00FF. No clouds, characters, text.'},
    {'file': 'fond_spirale.png', 'images': ['Rescue_Team_Friend_Area_-_Thunder_Meadow.png'], 'prompt':
     'Same cloud textures, palette and pixel-art style as the reference storm clouds. Full-frame WIDE 4:3 background seen '
     'from high above: upper half a huge dark SPIRAL storm vortex of scalloped clouds around a dark eye; lower half an '
     'endless sea of layered storm clouds far below. Only clouds, 8 teal-grey greens, no lightning, no land.'},
    {'file': 'foudre_poses.png', 'images': ['source/thunder_meadow_arene_v1/bruts/ref_5394.png'], 'prompt':
     'Pixel-art sprite sheet on flat pure magenta #FF00FF, exact pale yellow and white colors of the reference lightning. '
     '2 rows of 4 tall jagged forked LIGHTNING BOLTS striking downward, white-yellow core, pale yellow edges, no halo.'},
]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


ESJ = loadmod('esj1_build', R / 'source/entree_southern_jungle_sud_nord_v1/build.py')
FF = ESJ.FF
keep_large, close_, open_, quantize_group, rgba = FF.keep_large, FF.close_, FF.open_, FF.quantize_group, FF.rgba
cell_grid, sha, paste = FF.cell_grid, FF.sha, FF.paste
PALETTE_GROUPS = {'terrain': (['prairie', 'chemin', 'arene'], 48), 'falaises': (['falaises', 'ilots'], 32),
                  'pierres': (['pierres'], 16), 'arbre': (['arbre'], 12)}
CANON = {'prairie': 'herbe', 'falaises': 'falaise', 'ilots': 'herbe (dessus) + falaise (parois)', 'pierres': 'pierre'}
STATIC = ['ilots', 'falaises', 'prairie', 'chemin', 'arene', 'pierres', 'arbre']


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(float)


def load_flash():
    s = np.array(Image.open(SHEET).convert('RGB'))
    return [[tuple(int(v) for v in s[57 + 9 * r + 3, 519 + 9 * c + 3]) for c in range(8)] for r in range(6)]


def bgmask(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return nd.binary_dilation((r > 150) & (b > 150) & (g < 130) & (r - g > 60), iterations=2)


# ---------------------------------------------------------------- fidélité (même classifieur rip / brut)
def materials(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]
    grass = (g - b > 90) & (g > r - 10) & (lum > 150)
    cliff = (r > g + 20) & (r > b + 5) & (lum > 80) & (lum < 190)
    stone = (b > r + 15) & (b > g - 5) & (lum > 90)
    return {'herbe': grass, 'falaise': cliff, 'pierre': stone}


def fidelity(decor, ref):
    fr, fd = materials(ref), materials(decor); out = {}
    for k in fr:
        mr, md = ref[fr[k]].mean(0), decor[fd[k]].mean(0)
        out[k] = {'rip_rgb': [round(float(v), 1) for v in mr], 'decor_rgb': [round(float(v), 1) for v in md],
                  'distance': round(float(np.linalg.norm(mr - md)), 1)}
    return out


# ---------------------------------------------------------------- segmentation de la falaise (pleine résolution)
def classify(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    hh, ww = lum.shape; yy, xx = np.mgrid[:hh, :ww]
    void = bgmask(a); land = ~void
    lab, n = nd.label(land); sizes = nd.sum(land, lab, range(1, n + 1)); main = lab == (int(np.argmax(sizes)) + 1)
    islands = land & ~main
    stone = (b > r + 12) & (b > g - 8) & land
    stone = nd.binary_fill_holes(keep_large(close_(stone, 2), 150)) & land
    tree_box = (xx > 690) & (xx < 850) & (yy > 410) & (yy < 570)
    tree = tree_box & (r > g + 5) & (lum < 150) & (b < g - 22) & main
    tree = nd.binary_fill_holes(keep_large(close_(tree, 3), 800)) & tree_box
    cliff = (r > g + 18) & (r > b + 5) & (b > g - 22) & ~stone & ~tree & main
    cliff = keep_large(open_(close_(cliff, 2), 1), 400) & main
    khaki = (r >= g - 12) & (r - b > 25) & (r - b < 110) & (sat < 115) & (lum > 110) & ~(g - b > 100) & main & ~stone & ~tree & ~cliff
    khaki = open_(close_(khaki, 3), 2)
    kl, kn = nd.label(khaki); ks = nd.sum(khaki, kl, range(1, kn + 1))
    arena = np.zeros_like(khaki); path = np.zeros_like(khaki)
    for i, sl in enumerate(nd.find_objects(kl), 1):
        if ks[i - 1] < 1500:
            continue
        c = kl == i
        (arena if sl[0].stop < 330 else path)[c] = True
    arena = nd.binary_fill_holes(arena) & ~stone
    # Marches : bandes olive entre les lignes kaki dans le corridor du chemin -> rattachées au chemin.
    corridor = nd.binary_dilation(path, iterations=10) & (np.abs(xx - 580) < 120) & (yy > 320) & (yy < 760)
    stairs = close_(path | (corridor & ~cliff & ~stone & ~tree & main & (lum < 200) & (sat > 60) & (r > g - 25)), 4) & corridor
    path = (path | stairs) & ~cliff & ~stone & ~tree & ~arena
    grass = main & ~stone & ~tree & ~cliff & ~arena & ~path
    return dict(void=void, ilots=islands, falaises=cliff, prairie=grass, chemin=path, arene=arena, pierres=stone, arbre=tree)


# ---------------------------------------------------------------- fond : couleurs canoniques du flash
def canon_materials(a):
    """Matières LARGES du rip pour les couleurs canoniques (toute la gamme d'ombrage, nuages exclus)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]
    cloud = np.abs(b - g) < 18
    return {'herbe': (g - b > 45) & (r > g - 60) & ~cloud,
            'falaise': (r > g + 10) & (b > g - 35) & (lum > 35) & ~cloud,
            'pierre': (b > r + 8) & (b > g - 8) & ~cloud & (lum > 40)}


def canon_map(layer, ref, mat, sel=None):
    """Couleurs CANONIQUES : chaque pixel prend la couleur du rip (matière `mat`) de même rang de luminance."""
    rp = ref[canon_materials(ref)[mat]]; rl = rp @ [.299, .587, .114]; rp = rp[np.argsort(rl)]
    m = layer[..., 3] == 255
    if sel is not None:
        m &= sel
    px = layer[m][:, :3].astype(float); lum = px @ [.299, .587, .114]
    rank = np.argsort(np.argsort(lum, kind='stable'), kind='stable') / max(len(lum) - 1, 1)
    out = layer.copy(); out[m, :3] = rp[(rank * (len(rp) - 1)).astype(int)].astype('uint8')
    return out


def cloud_layers(bg, flash):
    lum = bg @ [.299, .587, .114]
    edges = np.quantile(lum, np.linspace(0, 1, 9)[1:-1])
    rank = np.digitize(lum, edges)                                        # 0 (sombre) .. 7 (clair)
    order = np.argsort([sum(c) for c in flash[0]])                         # colonnes de la planche par luminance
    idx = order[rank]
    frames = []
    for lv in LEVELS:
        pal = np.array(flash[lv], 'uint8'); f = np.zeros((H, W, 4), 'uint8'); f[..., :3] = pal[idx]; f[..., 3] = 255
        frames.append(f)
    return frames, idx


def bolt_poses(path, k):
    src = rgb(path); r, g, b = src[..., 0], src[..., 1], src[..., 2]
    bg = (r > 150) & (b > 150) & (g < 140)
    hh, ww = bg.shape; out = []
    px = src[~bg]
    q = Image.fromarray(px.reshape(-1, 1, 3).astype('uint8')).quantize(colors=3, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:9], float).reshape(-1, 3)
    for row in range(2):
        for col in range(4):
            sl = (slice(row * hh // 2, (row + 1) * hh // 2), slice(col * ww // 4, (col + 1) * ww // 4))
            m = ~bg[sl]; ys, xs = np.nonzero(m)
            sl2 = (slice(sl[0].start + ys.min(), sl[0].start + ys.max() + 1), slice(sl[1].start + xs.min(), sl[1].start + xs.max() + 1))
            m = ~bg[sl2]; s = src[sl2] * m[..., None]
            nh, nw = max(3, round(m.shape[0] / k)), max(3, round(m.shape[1] / k))
            cov = np.array(Image.fromarray(m.astype(np.float32)).resize((nw, nh), Image.Resampling.BOX))
            colr = np.stack([np.array(Image.fromarray(s[..., c].astype(np.float32)).resize((nw, nh), Image.Resampling.BOX))
                             for c in range(3)], -1) / np.maximum(cov, 1e-6)[..., None]
            o = np.zeros((nh, nw, 4), 'uint8')
            o[..., :3] = pal[((colr[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)]; o[..., 3] = 255
            o[cov < 0.3] = 0; out.append(o)
    return out, pal


def native_sparks():
    """Petits éclairs NATIFS de la planche (zone noire x 470..710, y 125..400) : composantes, pixels inchangés."""
    s = np.array(Image.open(SHEET).convert('RGB'))[125:400, 470:710]
    m = s.sum(2) > 60
    lab, n = nd.label(nd.binary_dilation(m, iterations=1)); out = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        c = (lab[sl] == i) & m[sl]
        if 12 <= c.sum() and sl[1].stop - sl[1].start <= 40:
            o = np.zeros((*c.shape, 4), 'uint8'); o[..., :3] = s[sl]; o[..., 3] = c * 255; out.append(o)
    return out


# ---------------------------------------------------------------- main
def build():
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    ANIMS = ['fond_nuages', 'foudre', 'etincelles']
    for d in ['calques', 'animation', 'poses', 'masques', 'review']:
        shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'masques', 'review'] + [f'animation/{x}' for x in ANIMS]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    flash = load_flash()
    a = rgb(RAW / 'falaise_magenta.png'); ref = rgb(REF)
    assert a.shape[:2] == (896, 1200)
    m = classify(a)
    order = ['void', 'ilots', 'falaises', 'pierres', 'arbre', 'arene', 'chemin', 'prairie']
    ex, cols = ESJ.down_classes(a, m, order)
    layers = {k: rgba(cols[k], ex[k]) for k in STATIC}
    q = {}
    for keys, n in PALETTE_GROUPS.values():
        q.update(quantize_group({k: layers[k] for k in keys}, n))
    layers = q
    il = layers['ilots'].astype(int); il_grass = il[..., 1] > il[..., 0] - 10      # dessus d'herbe des îlots
    for nm, mat in CANON.items():
        if nm == 'ilots':
            layers[nm] = canon_map(canon_map(layers[nm], ref, 'herbe', il_grass), ref, 'falaise', ~il_grass)
        else:
            layers[nm] = canon_map(layers[nm], ref, mat)
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    void = ex['void']
    # Fond : spirale + mer de nuages, ré-indexés sur la palette canonique.
    bg = ESJ.down_full(rgb(RAW / 'fond_spirale.png'))
    clouds, idx = cloud_layers(bg, flash)
    # Foudre : éclairs générés (~150 px de haut), visibles 3 phases pendant les flashs ; masqués sous la falaise.
    bolts, bolt_pal = bolt_poses(RAW / 'foudre_poses.png', 2.7)
    for i, p in enumerate(bolts):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_foudre_{i}.png')
    foudre = []
    for t in range(PH):
        f = np.zeros((H, W, 4), 'uint8')
        for (pi, x, y, t0) in BOLTS:
            if 0 <= t - t0 < 3:
                p = bolts[pi]; paste(f, p, x - p.shape[1] / 2, y)
        f[~void] = 0; foudre.append(f)
    # Étincelles : petits éclairs natifs dans la mer de nuages, 2 phases chacun, aux flashs et en calme.
    sparks = native_sparks()
    for i, p in enumerate(sparks):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_etincelle_native_{i:02d}.png')
    rng = np.random.default_rng(7); cand = np.argwhere(void[:H - 40:8, :W - 40:8]) * 8
    spark_pl = [(int(rng.integers(len(sparks))), *map(int, cand[rng.integers(len(cand))]), int(rng.integers(PH)))
                for _ in range(22)]
    etinc = []
    for t in range(PH):
        f = np.zeros((H, W, 4), 'uint8')
        for (si, y, x, t0) in spark_pl:
            if (t - t0) % PH < 2:
                p = sparks[si]; mm = p[..., 3] > 0; hh, ww = p.shape[:2]
                f[y:y + hh, x:x + ww][mm] = p[mm]
        f[~void] = 0; etinc.append(f)
    anim = {'fond_nuages': clouds, 'foudre': foudre, 'etincelles': etinc}
    names = ANIMS + STATIC
    stack, layer_list = [], []
    for i, nm in enumerate(names):
        if nm in anim:
            frames = anim[nm]
            for t, fr in enumerate(frames):
                Image.fromarray(fr).save(OUT / 'animation' / nm / f'{PFX}_{i:02d}_{nm}_f{t:02d}.png')
            layer_list.append({'file': f'animation/{nm}/{PFX}_{i:02d}_{nm}_fNN.png', 'phases': PH, 'ticks': TK})
            stack.append((nm, frames, TK))
        else:
            Image.fromarray(layers[nm]).save(OUT / 'calques' / f'{PFX}_{i:02d}_{nm}.png')
            layer_list.append({'file': f'calques/{PFX}_{i:02d}_{nm}.png', 'phases': 1, 'ticks': 60})
            stack.append((nm, [layers[nm]], 60))
    walk_px = sum((layers[k][..., 3] == 255) for k in ('prairie', 'chemin', 'arene')).astype(bool)
    blocked = cell_grid(~walk_px); gh_, gw_ = blocked.shape
    pth = layers['chemin'][..., 3] == 255
    pxs = np.nonzero(pth[H - 8])[0]; med = int(np.median(pxs)) // 8 if len(pxs) else gw_ // 2
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    ay, ax = np.nonzero(layers['arene'][..., 3] == 255)
    centre = [int(ax.mean()) // 8 * 8 - 8, int(ay.mean()) // 8 * 8 - 8]
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (centre[1] // 8, centre[0] // 8))

    def scene(tick):
        im = Image.new('RGBA', (W, H))
        for _, frames, ticks in stack:
            im.alpha_composite(Image.fromarray(frames[(tick // ticks) % len(frames)]))
        return im
    scenes = [scene(t) for t in range(0, LOOP, TK)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[9].save(OUT / 'review' / f'{PFX}_scene_eclair.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(TK * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (qx, qy), c in ((entry_px, (255, 230, 40, 255)), (centre, (60, 220, 255, 255))):
        dr.rectangle([qx, qy, qx + 15, qy + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    for k, v in dict(STAGE=STAGE, PFX=PFX, ASSET=ASSET, NAMESPACE=NAMESPACE, HERE=HERE).items():
        setattr(FF, k, v)
    FF.write_ora(OUT / f'{PFX}_thunder_meadow_arene_calques.ora',
                 {f'{i:02d}_{t}' + ('_f09' if len(fr) > 1 else ''): fr[9 if len(fr) > 1 else 0] for i, (t, fr, _) in enumerate(stack)})
    counts = FF.ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                                for t, fr, tk in stack], blocked, entry_px, centre, gfx, tools)
    gp = STAGE / f'Data/Ground/{ASSET}.rsground'; doc = json.loads(gp.read_text()); o = doc['Object']
    o['Name']['DefaultText'] = 'Thunder Meadow - falaise a terrasses et arene au-dessus de l orage (4:3)'
    o['Comment'] = ('PMDO 0.8.12. Rendu genere reference sur le rip Thunder Meadow ; fond re-indexe sur la palette de flash '
                    'canonique (6 niveaux natifs), foudre generee, etincelles natives. Marqueur donjon_seuil = centre de l arene.')
    gp.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')))
    mx_ = (STAGE / 'Mod.xml').read_text()
    mx_ = mx_.replace('Entree Foggy Forest camp sud-nord 4:3', 'Thunder Meadow arene 4:3')
    mx_ = mx_.replace('camp de base de foret genere au format 4:3 (ref. rip Foggy Forest Base Camp), mare facon Metano, brume animee.',
                      'falaise a terrasses et arene au-dessus d un orage en spirale (ref. rip Thunder Meadow), flash canonique et foudre.')
    (STAGE / 'Mod.xml').write_text(mx_)
    fid = fidelity(a, ref); final = {}
    for k, nm in (('herbe', 'prairie'), ('falaise', 'falaises'), ('pierre', 'pierres')):
        lay = layers[nm]; px = lay[lay[..., 3] == 255][:, :3].astype(float)
        sel = materials(px.reshape(-1, 1, 3))[k][:, 0]; px = px[sel] if sel.sum() > 50 else px
        final[k] = {'calque': nm, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                    'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    manifest = {
        'lot': 'thunder_meadow_arene_v1', 'prefix': PFX, 'format': '4:3', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'demande': 'falaise magnifique en plusieurs calques de Thunder Meadow (« tiny meadow »), arene, au-dessus de nuages '
                   'electriques, fond de nuages en spirale avec foudre, textures et couleurs canoniques',
        'references': {'rip': {'file': REF.name, 'sha256': sha(REF), 'origine': 'branche arena/01a0d8a8-guilde-treehouse-pmd'},
                       'planche': {'file': 'source/thunder_meadow_arene_v1/bruts/ref_5394.png', 'sha256': sha(SHEET),
                                   'origine': 'Toastypk (spriters-resource 5394), branche arena/01a0d8a8'}},
        'method': 'rendu genere REFERENCE (rip en images=) pour la falaise, le fond et la foudre ; couleurs du fond = palette '
                  'de flash CANONIQUE exacte (8 couleurs x 6 niveaux de la planche) ; etincelles = pixels natifs',
        'generation': GEN,
        'raw_inputs': [{'file': f'source/thunder_meadow_arene_v1/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in GEN],
        'fidelite_rip': {'brut': fid, 'calques_finaux': final, 'couleurs_canoniques': {k: f'couleurs EXACTES du rip ({v}), rang de luminance' for k, v in CANON.items()}, 'non_canonique': 'chemin, arene, arbre : couleurs du rendu (matieres absentes du rip ou sans equivalent)'},
        'flash': {'palette_niveaux': [[list(c) for c in row] for row in flash], 'sequence': LEVELS,
                  'indexation': 'rang de luminance du fond (8 quantiles) -> colonne de la planche triee par luminance'},
        'foudre': {'poses': len(bolts), 'palette': [[int(c) for c in p] for p in bolt_pal], 'placements': BOLTS,
                   'duree_phases': 3, 'masque': 'visible seulement sur le vide (derriere la falaise)'},
        'etincelles': {'poses_natives': len(sparks), 'placements': spark_pl, 'origine': 'pixels NATIFS de la planche, inchanges'},
        'layers': layer_list, 'scene_loop_ticks': LOOP,
        'access': {'entry_px': entry_px, 'arene_centre_px': centre, 'path_found_16x16': bool(ok), 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors prairie, chemin et arene ; falaises, pierres, arbre, ilots et vide bloques'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'ok': bool(ok), 'entry': entry_px, 'centre': centre, 'walk': int((~blocked).sum()), 'sparks': len(sparks),
                      'fid': {k: v['distance'] for k, v in fid.items()}, 'final': {k: v['distance_rip'] for k, v in final.items()},
                      'tiles': sum(counts.values())}))


if __name__ == '__main__':
    build()
