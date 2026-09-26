"""Grotte de cristal + VFX « colonnes de flamme » à l'arrivée du légendaire (Groudon) — ECC2, 4:3 (768 x 576 px).

Demande : « rajoute des colonnes de flamme incroyables à l'arrivée du légendaire (créer ce VFX lié à cette map, ce
sera pour Groudon) ». La carte ECC1 est reprise telle quelle (calques PNG et collisions du lot ECC1, relus et
vérifiés octet par octet) ; seul le VFX est ajouté, sur ses PROPRES calques d'événement :
- colonnes_flamme : 8 colonnes en arc autour du point d'arrivée, allumées en cascade du centre vers les bords,
  puis effondrées en gerbes et fumée ; poses GÉNÉRÉES (planche sur magenta, référence Dark_Crater_Pit_TDS.png) ;
- lueur_sol : halo de chaleur tramé en damier (alpha 0/255) sous chaque colonne, aux couleurs de la planche ;
- ecran_chaleur : voile orangé tramé en damier sur toute la carte au plus fort de l'éruption.
Événement joué UNE fois : 48 phases x 4 ticks = 192 ticks (3,2 s). Calques Visible=false dans le Ground ;
init.lua : arrivee_legendaire() (NON TESTÉ dans PMDO). La scène d'ambiance d'ECC1 (240 ticks) est inchangée.
Lancer : .venv/bin/python source/entree_crystal_cave_groudon_v2/build.py
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
BASE = R / 'renders/entree_crystal_cave_sud_nord_v1'
OUT = R / 'renders/entree_crystal_cave_groudon_v2'
STAGE = R / '.cache/entree_crystal_cave_groudon_v2/entree_crystal_cave_groudon'
NAMESPACE = 'entree_crystal_cave_groudon'
ASSET = 'ecc2_grotte_cristal_groudon'
PFX = 'ECC2'
W, H = 768, 576
EVT_PHASES, EVT_TICKS = 48, 4
POSE_K = 3                                     # planche -> carte : x1/3 (colonnes de 120 px de haut)
ARRIVAL = (384, 300)                           # point d'arrivée du légendaire (centre haut du sol de galets)
ARC = (190, 70)                                # demi-axes de l'arc des colonnes
N_COL = 8
# Fenêtres de la planche (cx, y0, y1), choisies à la main : les braises sont des composantes séparées.
WIN = {'fissure': (115, 190, 370), 'jaillissement': (345, 190, 370), 'mi_hauteur': (575, 100, 370),
       'pleine': (808, 10, 370), 'flamme_a': (120, 395, 760), 'flamme_b': (365, 395, 760),
       'flamme_c': (610, 395, 760), 'effondrement': (890, 380, 760)}
HALF_W = 115
GEN = [{'file': 'colonnes_flamme_poses.png', 'images': ['Dark_Crater_Pit_TDS.png'], 'prompt':
        'Pixel-art VFX sprite sheet on a flat pure magenta #FF00FF background, Pokemon Mystery Dungeon Explorers of Sky '
        'style, lava and fire colors of the reference (deep red, orange, yellow, white-hot core). 2 rows of 4 separate '
        'sprites, each a vertical ERUPTING FLAME COLUMN seen from a top-down 3/4 view, bursting up from a small glowing '
        'crack in the ground: row 1 = eruption growing: 1 glowing crack with embers, 2 short fire burst, 3 half-height '
        'roaring column, 4 full tall roaring flame pillar with white-yellow core and swirling edges. Row 2 = 3 different '
        'flicker poses of the full tall pillar, then a collapsing pillar breaking into sparks and smoke. Tall narrow '
        'sprites, all same scale, well separated with wide magenta spacing, no text, no grid lines.',
        'note': 'premier essai, grille 2 x 4 respectee'}]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


EC = loadmod('ecc1_build', R / 'source/entree_crystal_cave_sud_nord_v1/build.py')   # ground_project, write_ora
paste, sha = EC.paste, EC.sha


def is_bg(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r - g > 70) & (b - g > 70)


# ---------------------------------------------------------------- poses générées
def flame_poses(path):
    """Fenêtre -> masque hors magenta -> moyenne de blocs 4 x 4 (couverture >= 0,4) -> palette commune de 16 couleurs.
    Toutes les poses ont la même hauteur de fenêtre alignée sur le pied : le pied reste fixe d'une pose à l'autre."""
    src = np.array(Image.open(path).convert('RGB')).astype(float); bg = is_bg(src)
    crops = {}
    for k, (cx, y0, y1) in WIN.items():
        y0 = y1 - 360                                                   # même hauteur pour toutes : 360 px -> 120 px
        c = src[y0:y1, cx - HALF_W:cx + HALF_W + 1][:, :228]; m = ~bg[y0:y1, cx - HALF_W:cx + HALF_W + 1][:, :228]
        crops[k] = (c, m)
    px = np.concatenate([c[m] for c, m in crops.values()])
    q = Image.fromarray(px.reshape(-1, 1, 3).astype('uint8')).quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:48], float).reshape(-1, 3)
    out = {}
    for k, (c, m) in crops.items():
        hh, ww = c.shape[0] // POSE_K, c.shape[1] // POSE_K
        mb = m[:hh * POSE_K, :ww * POSE_K].reshape(hh, POSE_K, ww, POSE_K); cov = mb.mean((1, 3))
        col = (c[:hh * POSE_K, :ww * POSE_K] * m[:hh * POSE_K, :ww * POSE_K, None]).reshape(hh, POSE_K, ww, POSE_K, 3).sum((1, 3))
        col /= np.maximum(mb.sum((1, 3)), 1)[..., None]
        o = np.zeros((hh, ww, 4), 'uint8'); o[..., :3] = pal[((col[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)]
        o[..., 3] = 255; o[cov < 0.4] = 0
        out[k] = o
    return out, pal


def paste_foot(frame, spr, x, y):
    """Colle le sprite avec son pied (bas-centre) en (x, y)."""
    paste(frame, spr, x, y - spr.shape[0] // 2)


# ---------------------------------------------------------------- chronologie (créée par nous)
FLICKER = ['flamme_a', 'flamme_b', 'flamme_c', 'pleine']
RISE = ['fissure', 'fissure', 'jaillissement', 'jaillissement', 'mi_hauteur', 'mi_hauteur', 'pleine']
COLLAPSE_AT = 36                               # phase où les colonnes s'effondrent (décalées comme à l'allumage)


def column_pose(t, delay):
    u = t - delay
    if u < 0:
        return None
    if u < len(RISE):
        return RISE[u]
    end = COLLAPSE_AT + delay // 2
    if t < end:
        return FLICKER[(u - len(RISE)) % len(FLICKER)]
    v = t - end
    return ['effondrement', 'effondrement', 'effondrement', 'fissure', 'fissure', None][min(v, 5)]


def columns():
    """8 colonnes en arc devant le point d'arrivée ; allumage du centre vers les bords (retard 0, 2, 4, 6)."""
    cols = []
    for i in range(N_COL):
        ang = np.pi * (i + 0.5) / N_COL                                 # demi-ellipse ouverte vers le nord
        x = ARRIVAL[0] - ARC[0] * np.cos(ang); y = ARRIVAL[1] + ARC[1] * np.sin(ang) - 30
        rank = min(i, N_COL - 1 - i)
        cols.append((int(round(x)), int(round(y)), 2 * (N_COL // 2 - 1 - rank)))
    return sorted(cols, key=lambda c: c[1])                             # du fond vers l'avant (recouvrement)


def event_frames(poses, cols, ts=range(EVT_PHASES)):
    yy, xx = np.mgrid[:H, :W]; checker = (xx + yy) % 2 == 0
    glow_pal = poses['_pal']
    hot, warm, deep = (tuple(int(v) for v in glow_pal[i]) for i in poses['_glow'])
    flames, glows, veils = [], [], []
    for t in ts:
        f = np.zeros((H, W, 4), 'uint8'); g = np.zeros((H, W, 4), 'uint8'); v = np.zeros((H, W, 4), 'uint8')
        active = 0
        for x, y, d in cols:
            p = column_pose(t, d)
            if p is None:
                continue
            paste_foot(f, poses[p], x, y)
            size = {'fissure': 12, 'jaillissement': 20, 'mi_hauteur': 26, 'effondrement': 22}.get(p, 32)
            active += size >= 26
            e = ((xx - x) / (size * 1.6)) ** 2 + ((yy - y) / (size * 0.7)) ** 2
            g[(e < 1) & (e > 0.45) & checker & ((xx + yy) % 4 == 0)] = (*deep, 255); g[(e <= 0.45) & checker] = (*warm, 255); g[e < 0.1] = (*hot, 255)
        if active >= 6:                                                 # plus fort de l'éruption : voile de chaleur
            v[((xx + 2 * yy + t) % 7 == 0) & ((xx - yy) % 3 == 0)] = (*deep, 255)      # voile clairsemé (~5 %)
        flames.append(f); glows.append(g); veils.append(v)
    return flames, glows, veils


# ---------------------------------------------------------------- main
def build():
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    for d in ['calques', 'animation', 'poses', 'review']:
        shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'review', 'animation/ecran_chaleur', 'animation/lueur_sol', 'animation/colonnes_flamme']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    BM = json.loads((BASE / 'manifest.json').read_text())
    # Carte ECC1 reprise telle quelle (fichiers copiés, préfixe ECC2 pour des noms uniques à l'import).
    stack, layer_list = [], []
    for L in BM['layers']:
        n = L['phases']; files = [L['file']] if n == 1 else [L['file'].replace('fNN', f'f{t:02d}') for t in range(n)]
        frames = [np.array(Image.open(BASE / f).convert('RGBA')) for f in files]
        name = Path(L['file']).stem.replace('_fNN', '').split('_', 2)[2]
        for f_, a in zip(files, frames):
            dst = OUT / f_.replace('ECC1_', 'ECC2_'); dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(BASE / f_, dst)
        stack.append((name, frames, L['ticks'], True, None))
        layer_list.append({'file': L['file'].replace('ECC1_', 'ECC2_'), 'phases': n, 'ticks': L['ticks'], 'source': 'ECC1'})
    poses, pal = flame_poses(RAW / 'colonnes_flamme_poses.png')
    lum = pal @ [.299, .587, .114]; red = pal[:, 0] - pal[:, 2]
    order = np.argsort(-lum)
    hot = int(order[0])                                                  # blanc-jaune
    warm = int(max(range(len(pal)), key=lambda i: (red[i] > 120) * (lum[i] if lum[i] < 190 else 0)))   # orange
    deep = int(max(range(len(pal)), key=lambda i: red[i] - lum[i] * 0.5))                               # rouge sombre
    for k, p in poses.items():
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_flamme_{k}.png')
    poses['_pal'] = pal; poses['_glow'] = (hot, warm, deep)
    cols = columns()
    flames, glows, veils = event_frames(poses, cols)
    base_n = len(stack)
    for nm, frames in (('lueur_sol', glows), ('colonnes_flamme', flames), ('ecran_chaleur', veils)):
        i = len(stack)
        for t, fr in enumerate(frames):
            Image.fromarray(fr).save(OUT / 'animation' / nm / f'{PFX}_{i:02d}_{nm}_f{t:02d}.png')
        stack.append((nm, frames, EVT_TICKS, False, 'evenement'))
        layer_list.append({'file': f'animation/{nm}/{PFX}_{i:02d}_{nm}_fNN.png', 'phases': EVT_PHASES, 'ticks': EVT_TICKS,
                           'evenement': True, 'visible_au_chargement': False})
    # Collisions et marqueurs d'ECC1, relus dans son projet PMDO.
    with zipfile.ZipFile(BASE / 'ECC1_projet_pmdo_0812.zip') as z:
        doc = json.loads(z.read('entree_crystal_cave_sud_nord/Data/Ground/ecc1_entree_crystal_cave.rsground'))
    obs = doc['Object']['obstacles']
    blocked = np.array([[obs[x][y]['Tags'] for x in range(W // 8)] for y in range(H // 8)], bool)
    entry_px, threshold_px = BM['access']['entry_px'], BM['access']['threshold_px']
    # Revue : scène d'ambiance t000, planche de l'événement, WebP de l'événement sur la carte.
    def scene(tick, evt=None):
        im = Image.new('RGBA', (W, H))
        for _, frames, ticks, vis, _ in stack[:base_n]:
            im.alpha_composite(Image.fromarray(frames[(tick // ticks) % len(frames)]))
        if evt is not None:
            for _, frames, _, _, _ in stack[base_n:]:
                im.alpha_composite(Image.fromarray(frames[evt]))
        return im
    scene(0).save(OUT / 'review' / f'{PFX}_scene_t000.png')
    ev = [scene(t * EVT_TICKS, t) for t in range(EVT_PHASES)] + [scene(EVT_PHASES * EVT_TICKS + 20 * k) for k in range(6)]
    ev[0].save(OUT / 'review' / f'{PFX}_arrivee_groudon.webp', save_all=True, append_images=ev[1:],
               duration=round(EVT_TICKS * 1000 / 60), loop=0, lossless=True)
    ev[20].save(OUT / 'review' / f'{PFX}_arrivee_pic_t20.png')
    sheet = Image.new('RGBA', (8 * 84, 130), (20, 12, 16, 255))
    for i, k in enumerate(WIN):
        sheet.alpha_composite(Image.fromarray(poses[k]), (i * 84 + 4, 4))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses.png')
    strip = Image.new('RGBA', (12 * 192, 144))
    for j, t in enumerate(range(0, EVT_PHASES, 4)):
        strip.alpha_composite(ev[t].crop((192, 150, 576, 438)).resize((192, 144), Image.Resampling.NEAREST), (j * 192, 0))
    strip.save(OUT / 'review' / f'{PFX}_chronologie.png')
    EC.write_ora(OUT / f'{PFX}_grotte_cristal_groudon_calques.ora',
                 {f'{i:02d}_{t}' + (f'_f{20 if e else 0:02d}' if len(fr) > 1 else ''): fr[20 if e else 0]
                  for i, (t, fr, _, _, e) in enumerate(stack)})
    # Ground : ground_project d'ECC1 avec nos identifiants, puis visibilité des calques d'événement et init.lua.
    for k, v in dict(STAGE=STAGE, PFX=PFX, ASSET=ASSET, NAMESPACE=NAMESPACE, HERE=HERE).items():
        setattr(EC, k, v)
    counts = EC.ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                                for t, fr, tk, _, _ in stack], blocked, entry_px, threshold_px, gfx, tools)
    gp = STAGE / f'Data/Ground/{ASSET}.rsground'; doc = json.loads(gp.read_text()); o = doc['Object']
    evt_idx = list(range(base_n, len(stack)))
    for i in evt_idx:
        o['Layers'][i]['Visible'] = False
    o['Name']['DefaultText'] = 'Grotte de cristal - arrivee du legendaire (Groudon), colonnes de flamme'
    o['Comment'] = ('PMDO 0.8.12. Carte ECC1 + VFX colonnes de flamme (poses generees, chronologie creee) sur 3 calques '
                    'd evenement invisibles au chargement ; init.lua arrivee_legendaire() NON TESTE. Aucun warp.')
    gp.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')))
    ticks = EVT_PHASES * EVT_TICKS
    lua = f'''-- {ASSET} : carte ECC1 + VFX d'arrivee du legendaire (Groudon). Aucun warp.
-- Calques d'evenement {evt_idx} (lueur_sol, colonnes_flamme, ecran_chaleur) : invisibles au chargement.
-- {ASSET}.arrivee_legendaire() : les rend visibles pendant {EVT_PHASES} phases x {EVT_TICKS} ticks = {ticks} ticks
-- (3,2 s), puis les recache. A appeler depuis une coroutine de cinematique, juste avant de faire apparaitre Groudon
-- au point ({ARRIVAL[0]}, {ARRIVAL[1]}).
-- NON TESTE DANS PMDO : l'acces Lua a Layers[i].Visible et le calage de la phase 0 des calques d'evenement sur
-- l'horloge d'animation du moteur restent a verifier (sinon l'eruption peut demarrer en cours de cycle).
local {ASSET} = {{}}
local EVENEMENT = {{{', '.join(map(str, evt_idx))}}}
local function montrer(visible)
  local carte = GAME:GetCurrentGround()
  for _, i in ipairs(EVENEMENT) do carte.Layers[i].Visible = visible end
end
function {ASSET}.arrivee_legendaire()
  montrer(true)
  GAME:WaitFrames({ticks})
  montrer(false)
end
return {ASSET}
'''
    gfx.save(STAGE / f'Data/Script/{NAMESPACE}/ground/{ASSET}/init.lua', lua.encode())
    mx = (STAGE / 'Mod.xml').read_text()
    mx = mx.replace('Entree Grotte de cristal sud-nord 4:3 - Atelier 0.8.12', 'Grotte de cristal - arrivee de Groudon 4:3 - Atelier 0.8.12')
    mx = mx.replace('grotte de cristal generee au format 4:3 (ref. rip Waterfall Cave, salle du joyau), bassins facon Metano, eclats de cristaux animes.',
                    'grotte de cristal ECC1 et VFX de colonnes de flamme pour l arrivee de Groudon (calques d evenement, script non teste).')
    (STAGE / 'Mod.xml').write_text(mx)
    manifest = {
        'lot': 'entree_crystal_cave_groudon_v2', 'prefix': PFX, 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'base': {'lot': 'entree_crystal_cave_sud_nord_v1', 'calques': 'copies octet par octet (prefixe ECC2)',
                 'collisions_marqueurs': 'relus dans ECC1_projet_pmdo_0812.zip'},
        'demande': 'colonnes de flamme a l arrivee du legendaire (Groudon), VFX lie a la carte',
        'method': 'VFX genere REFERENCE : planche de colonnes de flamme sur magenta (reference Dark_Crater_Pit_TDS.png, '
                  'couleurs de lave PMD) ; poses reduites x1/3, palette commune de 16 couleurs ; halo et voile tramés en '
                  'damier aux couleurs de la planche ; placement et chronologie crees par nous',
        'generation': GEN,
        'raw_inputs': [{'file': f'source/entree_crystal_cave_groudon_v2/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in GEN],
        'poses': {k: {'fenetre': list(v), 'taille_px': list(poses[k].shape[:2])} for k, v in WIN.items()},
        'palette': [[int(c) for c in p] for p in pal], 'couleurs_halo': {'chaud': hot, 'orange': warm, 'rouge': deep},
        'evenement': {'phases': EVT_PHASES, 'frame_length_ticks': EVT_TICKS, 'duree_ticks': EVT_PHASES * EVT_TICKS,
                      'joue_une_fois': True, 'arrivee': list(ARRIVAL), 'colonnes': [list(c) for c in cols],
                      'montee': RISE, 'crepitement': FLICKER, 'effondrement_phase': COLLAPSE_AT,
                      'calques': evt_idx, 'derniere_phase_vide': True, 'script': 'init.lua arrivee_legendaire(), NON TESTE'},
        'scene_loop_ticks': BM['scene_loop_ticks'], 'layers': layer_list,
        'access': dict(BM['access']), 'fidelite_rip_carte': BM['fidelite_rip'],
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'cols': cols, 'glow': [hot, warm, deep], 'poses': {k: list(v.shape[:2]) for k, v in poses.items() if not k.startswith('_')},
                      'tiles': sum(counts.values())}))


if __name__ == '__main__':
    build()
