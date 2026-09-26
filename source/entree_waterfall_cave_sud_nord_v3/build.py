"""Entrée Waterfall Cave sud -> nord V3 (EWC3) — format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Même demande qu'EWC2 (retours sur EWC1, 26 septembre) : « il y a des petits traits blancs au bord des rives, fais une
version sans ça, et faut pas d'eau devant l'entrée de la grotte, et faut que la cascade soit en deux temps : la cascade
qui prend tout et après une animation où la cascade se fend pour ouvrir la grotte que tu as créée ».
EWC2 garde les points 1 et 2 (eau sans liseré, couloir de sable) ; sa fente est un trou en forme de grotte découpé dans
le rideau. V3 = autre lecture du point 3, « la cascade se fend » :
- la cascade se fend EN DEUX sur toute sa hauteur, sous la lèvre de la falaise : une fissure part de la lèvre et descend
  jusqu'à la grotte (fermeture éclair), puis s'élargit ;
- les deux moitiés du rideau S'ÉCARTENT : l'eau est repoussée vers les bords et s'y tasse (champ de déplacement
  horizontal), au lieu d'être découpée ; bords d'eau clairs qui ondulent et défilent avec le rideau, gerbes le long de
  la fissure ;
- derrière : la paroi rocheuse sèche, GÉNÉRÉE (nouveau brut : le décor EWC1 édité par le générateur, cascade retirée,
  cadrage conservé au pixel près), et la grotte d'EWC1 ;
- ouverte : deux chutes de part et d'autre de la grotte, paroi et grotte dégagées, plus rien devant la bouche.
Base : EWC2 (même branche) importé tel quel pour l'eau, le couloir, la texture du rideau, l'écume et les états.
Lancer : .venv/bin/python source/entree_waterfall_cave_sud_nord_v3/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


V2 = loadmod('ewc2_build', R / 'source/entree_waterfall_cave_sud_nord_v2/build.py')   # eau, couloir, rideau, écume
V1 = V2.V1
BM, JM = V1.BM, V1.JM
RAW1, REF = V1.RAW, V1.REF
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_waterfall_cave_sud_nord_v3'
STAGE = R / '.cache/entree_waterfall_cave_sud_nord_v3/entree_waterfall_cave_v3'
NAMESPACE = 'entree_waterfall_cave_v3'
ASSET = 'ewc3_entree_waterfall_cave'
PFX = 'EWC3'
W, H = V1.W, V1.H
PAL = BM.PAL
WATER_TICKS = V2.WATER_TICKS
FALL_PHASES, FALL_TICKS, FALL_PERIOD = V1.FALL_PHASES, V1.FALL_TICKS, V1.FALL_PERIOD
FALL_Y0, FALL_STEP = V1.FALL_Y0, V1.FALL_STEP
FOAM_PHASES, FOAM_TICKS = V1.FOAM_PHASES, V1.FOAM_TICKS
OPEN_PHASES = 24                      # ouverture : 24 x 4 = 96 ticks (1,6 s) ; multiple de 12 -> défilement continu
OPEN_TICKS = OPEN_PHASES * FALL_TICKS
LOOP_TICKS = 240                      # PPCM(4 x 10, 12 x 4)
SPLIT_TOP = 34                        # pointe de la fente, sous la lèvre de la falaise (lèvre y~26 dans le brut roche)
ARCH = 22                             # hauteur de l'arrondi de la pointe (quart d'ellipse)
MARGIN = 4                            # marge de la fente autour de la porte (bouche + éclats de rebord) ; >= 2 px de roche avec l'ondulation
ZIP = 0.4                             # part de la durée pendant laquelle la fissure descend
PUSH_Q = 1.4                          # tassement de l'eau repoussée : déplacement = largeur x u^1.4 (u = 0 au bord, 1 au centre)
WIG_AMP, WIG_LAMBDA = 1, 36           # ondulation des bords de la fente (px, période) ; 36 divise 72 -> boucle fermée
LIP_BAND = 12                         # bord d'eau de 2 px sur la moitié de chaque bande de 12 px, défile avec le rideau
GEN3 = [{'file': 'falaise_sans_cascade.png',
         'images': ['source/entree_waterfall_cave_sud_nord_v1/bruts/decor_magenta.png'],
         'prompt': "Edit this image: keep the exact same framing, size, pixel-art style and everything else identical "
                   "(trees, cliffs, sand, magenta areas), but remove the waterfall and its white foam. Where the falling "
                   "water was, show the dry tan layered rock cliff face that was behind it, with the same rock texture and "
                   "colors as the cliffs beside it. Keep the dark cave entrance at the base of that cliff, in the same place."}]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- paroi derrière la cascade (brut généré)
def register(a0, g, m0):
    """Décalage entier du brut roche sur le décor, mesuré sur les falaises et arbres loin du rideau (pleine rés.)."""
    busy = m0['cascade'] | m0['ecume_pied'] | m0['entree_sombre'] | m0['water']
    sel = (m0['falaises'] | m0['arbres']) & ~nd.binary_dilation(busy, iterations=40)
    sel[:, :8] = sel[:, -8:] = False; sel[:8] = sel[-8:] = False
    ys, xs = np.nonzero(sel); ys, xs = ys[::3], xs[::3]; hh, ww = g.shape[:2]
    err = {(dx, dy): float(np.abs(g[np.clip(ys - dy, 0, hh - 1), np.clip(xs - dx, 0, ww - 1)] - a0[ys, xs]).mean())
           for dy in range(-6, 7) for dx in range(-6, 7)}
    (dx, dy), e = min(err.items(), key=lambda kv: kv[1])
    return (dx, dy), e, sorted(err.values())[1]


def rock_layer(g, shift, region, terrain_pal):
    """Pixels du brut roche (recalés, réduits comme le sol complet) dans la zone de la fente, ramenés à la palette
    terrain (celle des falaises, du sable... : aucune couleur nouvelle)."""
    dx, dy = shift
    gs = np.roll(np.roll(g, dy, 0), dx, 1)
    small = JM.down_full(gs).astype(float)
    idx = ((small[region][:, None, :] - terrain_pal[None].astype(float)) ** 2).sum(-1).argmin(-1)
    out = np.zeros((H, W, 4), 'uint8'); out[region, :3] = terrain_pal[idx]; out[region, 3] = 255
    return out, small


# ---------------------------------------------------------------- la cascade se fend en deux et s'écarte
class Split:
    def __init__(self, cave, door, tex):
        ys, xs = np.nonzero(cave); dys, dxs = np.nonzero(door)
        self.xc = int(round((xs.min() + xs.max()) / 2))
        self.gl, self.gr = self.xc - int(dxs.min()) + MARGIN, int(dxs.max()) - self.xc + MARGIN
        self.yb = int(dys.max())
        y = np.arange(H); u = np.clip((y - SPLIT_TOP) / ARCH, 0, 1)
        self.shape = np.where((y >= SPLIT_TOP) & (y <= self.yb), np.sqrt(1 - (1 - u) ** 2), 0.0)   # arrondi de la pointe
        self.rows = (y >= SPLIT_TOP) & (y <= self.yb)
        self.t0 = ZIP * np.clip((y - SPLIT_TOP) / (self.yb - SPLIT_TOP), 0, 1)                   # la fissure descend
        self.tex = tex

    def wiggle(self, t):
        ph = 2 * np.pi * (np.arange(H) - FALL_Y0 - t * FALL_STEP) / WIG_LAMBDA
        return WIG_AMP * np.sin(ph), WIG_AMP * np.sin(ph + 2.1)

    def widths(self, t, k=None):
        """Demi-largeurs entières de la fente par rangée : k=None -> ouverte ; sinon phase k de l'ouverture.
        Renvoie (gauche, droite) sans ondulation (champ de déplacement, fixe dans l'état ouvert), (gauche, droite)
        avec ondulation (bord de la fente seulement) et la progression p par rangée."""
        if k is None:
            p, started = np.where(self.rows, 1.0, 0.0), self.rows
        else:
            tau = k / (OPEN_PHASES - 1)
            v = np.clip((tau - self.t0) / (1 - ZIP), 0, 1); p = v * v * (3 - 2 * v)
            started = self.rows & (tau > self.t0)
            p = np.where(started, p, 0.0)
        el, er = self.wiggle(t)
        bl = np.where(started, np.maximum(np.ceil(p * self.gl * self.shape - 1e-9), 1), 0).astype(int)
        br = np.where(started, np.maximum(np.ceil(p * self.gr * self.shape - 1e-9), 1), 0).astype(int)
        wl = np.where(started, np.maximum(bl + np.round(p * el), 1), 0).astype(int)
        wr = np.where(started, np.maximum(br + np.round(p * er), 1), 0).astype(int)
        return (bl, br), (wl, wr), p

    def row_source(self, gl, gr, wl, wr):
        """Colonne source de chaque colonne de la boîte du rideau : l'eau repoussée se tasse vers les bords (champ
        de déplacement monotone, largeurs sans ondulation), rien n'est découpé ; + masque de la fente (avec ondulation)."""
        _, x0, x1, _ = self.tex; xc = self.xc; xs = np.arange(x0, x1); src = xs.astype(float)
        gap = (xs >= xc - wl) & (xs < xc + wr)
        if gl:
            s = np.linspace(x0, xc, 8 * (xc - x0) + 1); D = s - gl * ((s - x0) / (xc - x0)) ** PUSH_Q
            left = xs < xc - gl; src[left] = np.interp(xs[left], D, s)
        if gr:
            s = np.linspace(xc, x1 - 1, 8 * (x1 - 1 - xc) + 1); D = s + gr * ((x1 - 1 - s) / (x1 - 1 - xc)) ** PUSH_Q
            right = xs >= xc + gr; src[right] = np.interp(xs[right], D, s)
        return np.clip(np.round(src).astype(int), x0, x1 - 1), gap

    def frame(self, t, closed, base, wig):
        Tq, x0, x1, pal = self.tex; (gl, gr), (wl, wr) = base, wig
        f = np.zeros((H, W, 4), 'uint8'); gap = np.zeros((H, W), bool)
        ty = (np.arange(H) - FALL_Y0 - t * FALL_STEP) % FALL_PERIOD
        for y in range(H):
            if gl[y] or gr[y]:
                src, g_ = self.row_source(int(gl[y]), int(gr[y]), int(wl[y]), int(wr[y])); gap[y, x0:x1] = g_
            else:
                src = np.arange(x0, x1)
            f[y, x0:x1, :3] = Tq[ty[y], src - x0]
        f[..., 3] = 255
        water = closed & ~gap; f[~water] = 0
        if gap.any():                                                   # bords d'eau clairs qui défilent
            lum = pal @ [.299, .587, .114]; white = pal[lum.argmax()].astype('uint8')
            d1 = water & nd.binary_dilation(gap)
            band = ((np.arange(H) - FALL_Y0 - t * FALL_STEP) % LIP_BAND < LIP_BAND // 2)[:, None]
            d2 = water & nd.binary_dilation(gap, iterations=2) & ~d1 & band
            f[d1, :3] = white
            if d2.any():
                c = (f[d2, :3].astype(float) + 255) / 2
                f[d2, :3] = pal[((c[:, None] - pal[None]) ** 2).sum(-1).argmin(-1)].astype('uint8')
        return f, gap & closed

    def states(self, cas, door):
        closed = cas | door
        fermee = [V2.fall_frame(self.tex, t, closed) for t in range(FALL_PHASES)]
        ouverte, gaps_open = [], []
        for t in range(FALL_PHASES):
            base, wig, _ = self.widths(t); f, g_ = self.frame(t, closed, base, wig); ouverte.append(f); gaps_open.append(g_)
        ouverture, opens, prog = [], [], []
        for k in range(OPEN_PHASES):
            t = k % FALL_PHASES; base, wig, p = self.widths(t, k)
            f, g_ = self.frame(t, closed, base, wig); ouverture.append(f); opens.append(g_)
            prog.append(p)
        return fermee, ouverture, ouverte, opens, gaps_open, prog


def door_foam_split(puffs, sprays, door, closed, walk, opens, split):
    """Écume de la porte d'EWC2 (bouillons qui s'éteignent quand la fente atteint le pied, gerbes aux lèvres basses)
    + une gerbe qui court avec la pointe de la fissure pendant qu'elle descend."""
    fermee, ouverture, info = V2.door_foam(puffs, sprays, door, closed, walk, opens)
    yy, xx = np.mgrid[:H, :W]; zips = []
    for k, op in enumerate(opens):
        col = np.flatnonzero(op[:, split.xc - 1:split.xc + 1].any(1))
        if not len(col) or k / (OPEN_PHASES - 1) > ZIP + 0.05 or col.max() >= split.yb - 6:
            continue
        yf = int(min(max(col.max(), 16), H - 17)); spr = sprays[k % len(sprays)]
        hh, ww = spr.shape[:2]; y0, x0 = yf - hh // 2, split.xc - ww // 2; m = spr[..., 3] > 0
        f = ouverture[k]; sub = f[y0:y0 + hh, x0:x0 + ww]; keep = m & closed[y0:y0 + hh, x0:x0 + ww]
        sub[keep] = spr[keep]; zips.append([k, split.xc, yf])
    info['gerbes_fissure'] = zips
    return fermee, ouverture, info


# ---------------------------------------------------------------- ORA (visibilité par calque)
def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Waterfall Cave sud-nord V3 (EWC3), cascade fermee')
    stack = ET.SubElement(root, 'stack'); comp = Image.new('RGBA', (W, H))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for i, (name, a, vis) in reversed(list(enumerate(layers))):
            fn = f'data/layer{i:02d}.png'
            ET.SubElement(stack, 'layer', name=name, src=fn, x='0', y='0', opacity='1.0',
                          visibility='visible' if vis else 'hidden', **{'composite-op': 'svg:src-over'})
            b = io.BytesIO(); Image.fromarray(a).save(b, format='PNG'); z.writestr(fn, b.getvalue())
        for _, a, vis in layers:
            if vis:
                comp.alpha_composite(Image.fromarray(a))
        b = io.BytesIO(); comp.save(b, format='PNG'); z.writestr('mergedimage.png', b.getvalue())
        th = comp.copy(); th.thumbnail((256, 256)); b = io.BytesIO(); th.save(b, format='PNG')
        z.writestr('Thumbnails/thumbnail.png', b.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))


# ---------------------------------------------------------------- Ground PMDO 0.8.12
def ground_project(stack, blocked, entry_px, threshold_px, gfx, tools):
    """stack : (titre, frames, ticks, etat) du bas vers le haut ; visibles au chargement : etat None ou fermee."""
    if STAGE.exists():
        shutil.rmtree(STAGE)
    with zipfile.ZipFile(R / 'mod_metano_expeditions_pmdo_0812.zip') as z:
        tpl = json.loads(z.read('metano_expeditions/Data/Ground/v50812_01_crete_sillage_jour.rsground'))
    o = tpl['Object']; gw, gh = W // 8, H // 8; layers, banks = [], []
    for i, (title, frames, ticks, etat) in enumerate(stack):
        vis = etat in (None, 'fermee')
        bank = gfx.TileBank(f'{PFX}_{i:02d}_{title.split()[0].upper()}')
        bank.ids[bytes(256)] = (0, 0); bank.data[(0, 0)] = bytes(256)

        def cell(x, y, frames=frames, bank=bank):
            fs = []
            for a in frames:
                f = bank.add(Image.fromarray(a[y*8:y*8+8, x*8:x*8+8]), x, y)
                fs.append(f if f else {'Sheet': bank.name, 'TexLoc': {'X': 0, 'Y': 0}})
            if all(f['TexLoc'] == {'X': 0, 'Y': 0} for f in fs):
                return []
            return [fs[0]] if all(f == fs[0] for f in fs) else fs
        lay = gfx.layer(f'{i:02d} {title}', gw, gh, cell, ticks); lay['Visible'] = bool(vis)
        layers.append(lay); banks.append(bank)
    layers.append(gfx.layer(f'{len(layers):02d} Vos elements avant-plan (Top)', gw, gh, draw=4))
    for bank in banks:
        bank.write(STAGE / f'Content/Tile/{bank.name}.tile')
    o.update(Name={'DefaultText': 'Entree Waterfall Cave V3 - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Waterfall Cave (entrancecascade.png), V3 : '
                     'eau facon Metano sans lisere de rive, couloir de sable jusqu a la bouche, cascade qui se fend en deux '
                     'et s ecarte devant une paroi generee (calques d etat fermee / ouverture / ouverte, script init.lua '
                     'NON TESTE). Collisions a verifier.')
    o['obstacles'] = [[{'Bounds': {'X': x*8, 'Y': y*8, 'Width': 8, 'Height': 8}, 'Tags': int(blocked[y, x])}
                       for y in range(gh)] for x in range(gw)]
    mk = lambda n, p: {'EntName': n, 'Direction': 4, 'EntEnabled': True, 'triggerType': 0,
                       'Collider': {'X': p[0], 'Y': p[1], 'Width': 16, 'Height': 16}}
    o['Entities'] = [{'Name': 'Entrees et vos acteurs', 'Visible': True, 'MapChars': [], 'GroundObjects': [], 'Spawners': [],
                      'Markers': [mk('entrance', entry_px), mk('donjon_seuil', threshold_px)]}]
    o['Decorations'] = [{'Name': 'Vos decorations', 'Layer': 2, 'Visible': True, 'Anims': []}]
    tpl['Version'] = '0.8.12.0'
    gfx.save(STAGE / f'Data/Ground/{ASSET}.rsground', json.dumps(tpl, ensure_ascii=False, separators=(',', ':')).encode())
    etats = {e: [i for i, st in enumerate(stack) if st[3] == e] for e in ('fermee', 'ouverture', 'ouverte')}
    lua = f'''-- {ASSET} : base d edition, aucun warp.
-- Cascade en deux temps. Au chargement, le rideau est ferme (calques {etats['fermee']} visibles).
-- {ASSET}.ouvrir_cascade() : la cascade se fend en deux et s ecarte (calques {etats['ouverture']}, {OPEN_PHASES} phases x
-- {FALL_TICKS} ticks = {OPEN_TICKS} ticks), puis reste ouverte (calques {etats['ouverte']}). A appeler depuis une coroutine
-- (cinematique). NON TESTE DANS PMDO : l acces Lua a Layers[i].Visible et le calage de la phase 0 du calque
-- d ouverture sur l horloge d animation du moteur restent a verifier.
local {ASSET} = {{}}
local ETATS = {{ fermee = {{{', '.join(map(str, etats['fermee']))}}}, ouverture = {{{', '.join(map(str, etats['ouverture']))}}}, ouverte = {{{', '.join(map(str, etats['ouverte']))}}} }}
local function montrer(etat, visible)
  local carte = GAME:GetCurrentGround()
  for _, i in ipairs(ETATS[etat]) do carte.Layers[i].Visible = visible end
end
function {ASSET}.ouvrir_cascade()
  montrer('fermee', false); montrer('ouverture', true)
  GAME:WaitFrames({OPEN_TICKS})
  montrer('ouverture', false); montrer('ouverte', true)
end
return {ASSET}
'''
    gfx.save(STAGE / f'Data/Script/{NAMESPACE}/ground/{ASSET}/init.lua', lua.encode())
    nodes = {}
    for p in sorted((STAGE / 'Content/Tile').glob('*.tile')):
        with p.open('rb') as f:
            nodes[p.stem] = tools.read_node(f)
    (STAGE / 'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    ident = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/meromoonmeri/guilde-treehouse-pmd/' + NAMESPACE)
    (STAGE / 'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Entree Waterfall Cave V3 sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de Waterfall Cave V3 au format 4:3 (ref. rip entrancecascade), couloir de sable jusqu'a la grotte, cascade qui se fend en deux et s'ecarte devant la paroi. Pas une aventure jouable.</Description>
  <Namespace>{NAMESPACE}</Namespace>
  <UUID>{ident}</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>0.8.12.0</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
''')
    script = (R / 'source/pmdo_cote/INSTALLER.py').read_text()
    needle = '            relative = src.relative_to(source)\n'
    assert needle in script
    script = script.replace(needle, needle + "            if relative.as_posix() == 'Content/Tile/index.idx':\n                continue\n")
    (STAGE / 'INSTALLER.py').write_text(script)
    shutil.copyfile(HERE / 'README_PACK.md', STAGE / 'README.md')
    return {b.name: len(b.data) for b in banks}, etats


# ---------------------------------------------------------------- main
def build():
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    ANIMS = ['eau', 'scintillements', 'cascade_fermee', 'cascade_ouverture', 'cascade_ouverte', 'ecume',
             'ecume_porte_fermee', 'ecume_porte_ouverture', 'embruns']
    if OUT.exists():
        for d in ['calques', 'animation', 'poses', 'masques', 'review']:
            shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'masques', 'review'] + [f'animation/{a}' for a in ANIMS]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    # --- identique à EWC2 : décor, couloir, classes, calques fixes, eau sans liseré, scintillements
    a0 = V1.rgb(RAW1 / 'decor_magenta.png'); f = V1.rgb(RAW1 / 'sol_complet.png'); ref = V1.rgb(REF)
    m0 = V1.classify(a0)
    a, m, corr_full, corr_info = V2.reshape_front(a0, f, m0)
    order = ['water', 'cascade', 'ecume_pied', 'entree_sombre', 'sable', 'cailloux', 'touffes', 'plateaux', 'berge',
             'falaises', 'arbres']
    ex, cols = V1.down_class(a, m, order)
    water = ex['water']
    static = ['sable', 'cailloux', 'touffes', 'plateaux', 'berge', 'falaises', 'arbres', 'entree_sombre']
    layers = {'sol_complet': V1.rgba(V1.down_full(f), ~water)}
    for k in static + ['cascade', 'ecume_pied']:
        layers[k] = V1.rgba(cols[k], ex[k])
    q = {}
    for keys, n in V1.PALETTE_GROUPS.values():
        q.update(V1.quantize_group({k: layers[k] for k in keys}, n))
    layers = q
    corr = V1.resize_plane(corr_full.astype(np.float32)) > 0.5
    land = np.zeros((H, W), bool)
    for k in static + ['cascade', 'ecume_pied']:
        land |= layers[k][..., 3] == 255
    visible = water & ~land
    wf, dist = V2.water_phases(water, visible)
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(V2.WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in V1.place(visible & (dist > 4), (hh, ww), 4, 41 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(V2.WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    cave, cas = ex['entree_sombre'], ex['cascade']
    tex, fall_info = V2.fall_texture(layers['cascade'], cas, cave)
    walk_px = layers['sable'][..., 3] == 255
    door = V2.door_region(cas, cave, ex['arbres'] | ex['water'] | ex['ecume_pied'] | walk_px | nd.binary_dilation(corr))
    # --- V3 : la cascade se fend en deux, paroi générée derrière
    split = Split(cave, door, tex)
    c_fermee, c_ouverture, c_ouverte, opens, gaps_open, prog = split.states(cas, door)
    reveal = np.zeros((H, W), bool)
    for g_ in opens + gaps_open:
        reveal |= g_
    region = cas & nd.binary_dilation(reveal, iterations=2) & ~door        # tout ce que la fente peut montrer du rideau
    g = V1.rgb(RAW / 'falaise_sans_cascade.png')
    assert g.shape == a0.shape, 'brut roche : taille différente du décor'
    shift, reg_err, reg_next = register(a0, g, m0)
    terrain_pal = np.unique(np.concatenate([layers[k][layers[k][..., 3] == 255][:, :3]
                                            for k in V1.PALETTE_GROUPS['terrain'][0]]), axis=0)
    roche, rock_small = rock_layer(g, shift, region, terrain_pal)
    layers['roche_derriere'] = roche
    for k, v in list(ex.items()) + [('couloir', corr), ('porte', door), ('fente_max', reveal), ('roche_derriere', region)]:
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    foam_pal = np.unique(layers['ecume_pied'][ex['ecume_pied']][:, :3], axis=0).astype(float)
    grid = (4, 4)
    puffs = V1.sheet_poses(RAW1 / 'ecume_poses.png', grid, [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)], foam_pal)
    sprays = V1.sheet_poses(RAW1 / 'ecume_poses.png', grid, [(3, 3), (3, 0), (3, 1), (3, 2)], foam_pal)
    for i, p in enumerate(puffs):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_bouillon_{i}.png')
    for i, p in enumerate(sprays):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_embrun_{i}.png')
    cy_, cx_ = np.nonzero(cave); cave_x = (int(cx_.min()), int(cx_.max()))
    fy, fx = np.nonzero(ex['ecume_pied']); foot_y = int(np.median(fy))
    xs_c = np.nonzero(cas.any(0))[0]
    puff_em = [(x, foot_y, (i * 5) % FOAM_PHASES) for i, x in enumerate(range(int(xs_c.min()) + 12, int(xs_c.max()) - 11, 13))
               if not (cave_x[0] - 8 <= x <= cave_x[1] + 8)]
    pool_y = foot_y + 18
    basin = np.flatnonzero(visible[pool_y] & (np.arange(W) >= xs_c.min() - 20) & (np.arange(W) <= xs_c.max() + 20))
    left, right = basin[basin < cave_x[0]], basin[basin > cave_x[1]]
    spray_em = [(int(np.percentile(s_, p_)), pool_y, off) for s_, p_, off in
                ((left, 30, 0), (left, 75, 3), (right, 25, 6), (right, 70, 9))]
    clip = (ex['water'] | ex['ecume_pied'] | cas) & ~cave
    ecume = V1.sprite_frames(puffs, puff_em, V1.PUFF_SEQ, clip)
    embruns = V1.sprite_frames(sprays, spray_em, V1.SPRAY_SEQ, clip & ~cas)
    d_fermee, d_ouverture, door_info = door_foam_split(puffs, sprays, door, cas | door, walk_px, opens, split)
    door_info['porte_px'] = int(door.sum()); door_info['eclats_rebord_px'] = int((door & ~cave).sum())
    # --- exports
    anim = {'eau': (wf, WATER_TICKS), 'scintillements': (sf, WATER_TICKS), 'cascade_fermee': (c_fermee, FALL_TICKS),
            'cascade_ouverture': (c_ouverture, FALL_TICKS), 'cascade_ouverte': (c_ouverte, FALL_TICKS),
            'ecume': (ecume, FOAM_TICKS), 'ecume_porte_fermee': (d_fermee, FOAM_TICKS),
            'ecume_porte_ouverture': (d_ouverture, FOAM_TICKS), 'embruns': (embruns, FOAM_TICKS)}
    state_of = {'cascade_fermee': 'fermee', 'ecume_porte_fermee': 'fermee', 'cascade_ouverture': 'ouverture',
                'ecume_porte_ouverture': 'ouverture', 'cascade_ouverte': 'ouverte'}
    order_names = (['eau', 'scintillements', 'sol_complet', 'sable', 'cailloux', 'touffes', 'plateaux', 'berge', 'falaises',
                    'roche_derriere', 'arbres', 'entree_sombre', 'cascade_fermee', 'cascade_ouverture', 'cascade_ouverte',
                    'ecume_pied', 'ecume', 'ecume_porte_fermee', 'ecume_porte_ouverture', 'embruns'])
    stack_named, layer_list = [], []
    for i, nm in enumerate(order_names):
        etat = state_of.get(nm)
        if nm in anim:
            frames, ticks = anim[nm]
            for t, fr in enumerate(frames):
                Image.fromarray(fr).save(OUT / 'animation' / nm / f'{PFX}_{i:02d}_{nm}_f{t:02d}.png')
            layer_list.append({'file': f'animation/{nm}/{PFX}_{i:02d}_{nm}_fNN.png', 'phases': len(frames), 'ticks': ticks,
                               'etat': etat, 'boucle': etat != 'ouverture'})
        else:
            frames, ticks = [layers[nm]], 60
            Image.fromarray(layers[nm]).save(OUT / 'calques' / f'{PFX}_{i:02d}_{nm}.png')
            layer_list.append({'file': f'calques/{PFX}_{i:02d}_{nm}.png', 'phases': 1, 'ticks': 60, 'etat': None, 'boucle': True})
        stack_named.append((nm, frames, ticks, etat))
    # --- collisions (identiques à EWC2) : sable relié au sud (couloir compris), cailloux, touffes enclavées
    ground = (layers['sable'][..., 3] == 255) | (layers['cailloux'][..., 3] == 255)
    walk = ground | ((layers['touffes'][..., 3] == 255) & nd.binary_fill_holes(ground))
    blocked = V1.cell_grid(~walk); gh_, gw_ = blocked.shape
    pxs = np.nonzero(walk[H - 8])[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    ccx = (cave_x[0] + cave_x[1]) // 2
    north = int(np.nonzero(walk[:, ccx])[0].min())
    threshold_px = [ccx // 8 * 8 - 8, north // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok, 'pas de chemin 16x16'

    def scene(tick, state, since=0):
        im = Image.new('RGBA', (W, H))
        for nm, frames, ticks, etat in stack_named:
            if etat is not None and etat != state:
                continue
            idx = min((tick - since) // ticks, len(frames) - 1) if etat == 'ouverture' else (tick // ticks) % len(frames)
            im.alpha_composite(Image.fromarray(frames[idx]))
        return im
    closed0, open0 = scene(0, 'fermee'), scene(0, 'ouverte')
    closed0.save(OUT / 'review' / f'{PFX}_scene_fermee_t000.png'); open0.save(OUT / 'review' / f'{PFX}_scene_ouverte_t000.png')
    step, seq = 4, []
    for t in range(0, 96, step):
        seq.append(scene(t, 'fermee'))
    for t in range(96, 96 + OPEN_TICKS, step):
        seq.append(scene(t, 'ouverture', since=96))
    for t in range(96 + OPEN_TICKS, 96 + OPEN_TICKS + 144, step):
        seq.append(scene(t, 'ouverte'))
    seq[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=seq[1:],
                duration=round(step * 1000 / 60), loop=0, lossless=True)
    bx0, bx1, by0, by1 = int(xs_c.min()) - 14, int(xs_c.max()) + 15, 0, int(cy_.max()) + 26
    picks = [0, 3, 6, 9, 12, 15, 18, 23]; bw, bh = (bx1 - bx0) * 2, (by1 - by0) * 2
    planche = Image.new('RGBA', (4 * (bw + 8) + 8, 2 * (bh + 8) + 8), (13, 26, 34, 255))
    for j, k in enumerate(picks):
        im = scene(96 + k * FALL_TICKS, 'ouverture', since=96).crop((bx0, by0, bx1, by1)).resize((bw, bh), Image.Resampling.NEAREST)
        planche.alpha_composite(im, (8 + (j % 4) * (bw + 8), 8 + (j // 4) * (bh + 8)))
    planche.save(OUT / 'review' / f'{PFX}_ouverture_planche_x2.png')
    v2o = R / 'renders/entree_waterfall_cave_sud_nord_v2/review/EWC2_scene_ouverte_t000.png'
    if v2o.exists():                                                   # ouverte : EWC2 (gauche) / EWC3 (droite)
        A = Image.open(v2o).convert('RGBA').crop((bx0, by0, bx1, by1)); B = open0.crop((bx0, by0, bx1, by1))
        cmp_ = Image.new('RGBA', (bw * 2 + 12, bh), (13, 26, 34, 255))
        cmp_.alpha_composite(A.resize((bw, bh), Image.Resampling.NEAREST), (0, 0))
        cmp_.alpha_composite(B.resize((bw, bh), Image.Resampling.NEAREST), (bw + 12, 0))
        cmp_.save(OUT / 'review' / f'{PFX}_ouverte_v2_v3_x2.png')
    col = open0.copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (qx, qy), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([qx, qy, qx + 15, qy + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    write_ora(OUT / f'{PFX}_entree_waterfall_cave_calques.ora',
              [(f'{i:02d}_{nm}' + ('_f00' if len(fr) > 1 else ''), fr[0], etat in (None, 'fermee'))
               for i, (nm, fr, _, etat) in enumerate(stack_named)])
    counts, etats = ground_project([(nm.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk, etat)
                                    for nm, fr, tk, etat in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    fid = V1.fidelity(a0, ref, m0['cascade'])
    final_fid = {}
    lay_of = dict(layers, cascade_fermee=c_fermee[0], cascade_ouverte=c_ouverte[0])
    for k, nm in (('sable', 'sable'), ('roche', 'falaises'), ('roche_derriere', 'roche_derriere'), ('feuillage', 'arbres'),
                  ('rideau', 'cascade_fermee'), ('rideau_ouvert', 'cascade_ouverte')):
        lay = lay_of[nm]
        px = lay[lay[..., 3] == 255][:, :3].astype(float)
        if nm == 'arbres':
            px = px[(px[:, 1] > px[:, 0] + 8) & (px[:, 1] > px[:, 2] + 20)]
        rip = fid[{'roche_derriere': 'roche', 'rideau_ouvert': 'rideau'}.get(k, k)]['rip_rgb']
        final_fid[k] = {'calque': nm, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                        'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(rip))), 1)}
    fal = layers['falaises'][layers['falaises'][..., 3] == 255][:, :3].astype(float).mean(0)
    final_fid['roche_derriere']['distance_falaises'] = round(float(np.linalg.norm(roche[region][:, :3].astype(float).mean(0) - fal)), 1)
    gv1 = json.loads((R / 'renders/entree_waterfall_cave_sud_nord_v1/manifest.json').read_text())['generation']
    raw = [{'file': f'source/entree_waterfall_cave_sud_nord_v1/bruts/{g_["file"]}', 'sha256': sha(RAW1 / g_['file']),
            'size': list(Image.open(RAW1 / g_['file']).size)} for g_ in gv1]
    raw += [{'file': f'source/entree_waterfall_cave_sud_nord_v3/bruts/{g_["file"]}', 'sha256': sha(RAW / g_['file']),
             'size': list(Image.open(RAW / g_['file']).size)} for g_ in GEN3]
    open_rows = [y for y in range(SPLIT_TOP + ARCH, int(np.nonzero(cas)[0].max()) + 1)]
    split_info = {'centre_x': split.xc, 'demi_largeurs': [split.gl, split.gr], 'pointe_y': SPLIT_TOP, 'arrondi_px': ARCH,
                  'bas_y': split.yb, 'marge_porte_px': MARGIN, 'fissure_part_duree': ZIP, 'tassement_exposant': PUSH_Q,
                  'ondulation': {'amplitude_px': WIG_AMP, 'periode_px': WIG_LAMBDA},
                  'bord_clair': {'px1': 'blanc du rideau', 'px2': f'eclairci, une moitie de bande de {LIP_BAND} px sur deux, defile'},
                  'rangees_fendues_ouverte': len(open_rows),
                  'progression': 'rangee y : debut t0 = ZIP x (y - pointe) / (bas - pointe), puis smoothstep sur (1 - ZIP)',
                  'deplacement': 'colonne source s -> s -/+ largeur x u^PUSH_Q (u = 0 au bord du rideau, 1 au centre) : '
                                 'l eau est repoussee et se tasse, rien n est decoupe',
                  'paroi': {'brut': 'bruts/falaise_sans_cascade.png', 'recalage_px': list(shift),
                            'ecart_moyen_recale': round(reg_err, 2), 'ecart_decale_1px': round(reg_next, 2),
                            'pixels': int(region.sum()), 'palette': f'palette terrain ({len(terrain_pal)} couleurs), aucune couleur nouvelle'}}
    manifest = {
        'lot': 'entree_waterfall_cave_sud_nord_v3', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8],
        'base': 'EWC2 (meme branche) importe tel quel : eau sans lisere, couloir de sable, texture du rideau, ecume, etats ; '
                'bruts EWC1 + 1 brut genere (paroi derriere la cascade)',
        'demande': 'petits traits blancs au bord des rives -> version sans ; pas d eau devant l entree de la grotte ; '
                   'cascade en deux temps : la cascade qui prend tout puis une animation ou elle se fend pour ouvrir la grotte',
        'lecture_v3': 'la cascade se fend EN DEUX sur toute sa hauteur sous la levre et ses deux moities s ecartent ; '
                      'EWC2 = fente en forme de grotte decoupee dans le rideau',
        'method': 'textures canoniques = rendu genere REFERENCE (bruts EWC1 references sur le rip ; paroi = decor EWC1 edite '
                  'par le generateur)',
        'reference_da': {'file': 'entrancecascade.png', 'sha256': sha(REF), 'titre': 'Entree cascade (Waterfall Cave, PMD Explorers)'},
        'generation': gv1 + GEN3,
        'raw_inputs': raw,
        'fente': split_info,
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur sur le rip et sur le brut (rideau : boite '
                                    'x 150-355, y 0-180 du rip contre rideau segmente) ; distance euclidienne ; '
                                    'paroi derriere = comparee a la roche du rip',
                         'brut': fid, 'calques_finaux': final_fid},
        'normalization': {'scale': JM.SCALE, 'scaled': [JM.SCALED_W, H], 'crop_x': [JM.CROP_X, JM.SCALED_W - W - JM.CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal',
                          'palettes': dict({g_: {'calques': k, 'couleurs': n} for g_, (k, n) in V1.PALETTE_GROUPS.items()},
                                           terrain={'calques': V1.PALETTE_GROUPS['terrain'][0] + ['roche_derriere'], 'couleurs': 96})},
        'layers': layer_list,
        'etats': {'defaut': 'fermee', 'sequence': ['fermee', 'ouverture', 'ouverte'], 'ouverture_ticks': OPEN_TICKS,
                  'calage': f'lancer l ouverture sur un tick multiple de {FALL_PHASES * FALL_TICKS} (phase 0 du rideau) '
                            'pour un defilement continu', 'pmdo_calques': etats},
        'water': {'phases': V2.WATER_PHASES, 'frame_length_ticks': WATER_TICKS,
                  'couleurs': {k: list(v) for k, v in PAL.items() if k != V2.REMOVED}, 'retire': V2.REMOVED,
                  'rgb_retire': list(PAL[V2.REMOVED]),
                  'modele': 'structure et cadence riviere Metano, couleurs Metano EXACTES, sans lisere de rive (EWC2)',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels et couleurs Metano NATIFS inchanges (aplat de surface retire)'},
        'couloir': dict(corr_info, bords_pleine_res=V2.CORR_KNOTS, origine='EWC2 (reshape_front)'),
        'cascade': dict(fall_info, phases=FALL_PHASES, frame_length_ticks=FALL_TICKS, period_px=FALL_PERIOD,
                        blend_px=V1.FALL_BLEND, step_px=FALL_STEP, ouverture_phases=OPEN_PHASES,
                        origine='pixels GENERES du rideau du decor, rendus periodiques par fondu puis ramenes a la palette '
                                'du rideau ; defilement, fente et ecartement crees par nous, pas une animation officielle'),
        'foam': {'brut': 'source/entree_waterfall_cave_sud_nord_v1/bruts/ecume_poses.png', 'grille_rendue': list(grid),
                 'bouillon': {'cases': [[0, c] for c in range(4)] + [[1, c] for c in range(4)], 'sequence': V1.PUFF_SEQ,
                              'emetteurs': [list(e) for e in puff_em]},
                 'embruns': {'cases': [[3, 3], [3, 0], [3, 1], [3, 2]], 'sequence': V1.SPRAY_SEQ, 'emetteurs': [list(e) for e in spray_em]},
                 'porte': door_info,
                 'reduction': f'fenetre {V1.FCELL * V1.FK} px -> {V1.FCELL} px (x1/{V1.FK}) centree, palette = couleurs de l ecume du pied',
                 'phases': FOAM_PHASES, 'frame_length_ticks': FOAM_TICKS,
                 'origine': 'dessin GENERE, emetteurs et chronologie crees ; pas une animation officielle'},
        'shadows': 'aucun calque d ombres : le rendu genere ne contient pas d ombre portee separable',
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors sable praticable/cailloux/touffes enclavees',
                   'seuil': 'haut du couloir de sable, au pied de la bouche (visible une fois la cascade ouverte)'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun', 'script': 'init.lua : ouvrir_cascade(), NON TESTE'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()),
                      'cells': int(blocked.size), 'fente': {k: v for k, v in split_info.items() if k != 'paroi'},
                      'paroi': split_info['paroi'], 'door': door_info,
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'etats': etats,
                      'tiles': sum(counts.values())}, indent=1, default=str))


if __name__ == '__main__':
    build()
