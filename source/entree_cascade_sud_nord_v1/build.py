"""Entrée Cascade — sud vers nord, V1 (4:3 vaste, 768×576) — PIXELS NATIFS EXACTS.

Méthode « pixels natifs exacts » (comme zones_south_north_v3) : chaque pixel opaque des calques
est copié tel quel (aucune rotation, aucun miroir, aucun redimensionnement, aucune recoloration)
depuis une source canonique, avec sa provenance (source, x, y) enregistrée dans provenance.npz.

Sources canoniques :
  * Waterfall_Cave_ledge_TDS.png  (L) : plafond/stalactites, fond sombre, parois de rochers,
    sol de galets du couloir, source turquoise, petites pierres.
  * Waterfall_Cave_gem_TDS.png    (G) : eau profonde (mailles), paires de rochers, cristaux.
  * sprites/eau_metano/cascade_frame_1..4.png : cascade Métano native (4 phases).
  * source/eau_metano/natifs/Metano_Town_River_Sparkles.tile : scintillements Métano natifs.
Le rendu généré bruts/decor_magenta.png n'a servi que de guide de composition : aucun de ses
pixels n'entre dans les exports (test_build le vérifie via la provenance).

.venv/bin/python source/entree_cascade_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
OUT = R / 'renders/entree_cascade_sud_nord_v1'
STAGE = R / '.cache/entree_cascade_sud_nord_v1/entree_cascade_sud_nord'
NAMESPACE = 'entree_cascade_sud_nord'
ASSET = 'ecn1_entree_cascade'
PFX = 'ECN1'
W, H = 768, 576
PHASES, TICKS = 4, 10          # cascade et scintillements : 4 phases × 10 ticks (cadence proposée, cf. sprites/eau_metano/README.md)
LOOP_TICKS = PHASES * TICKS

SRC_FILES = {1: 'Waterfall_Cave_ledge_TDS.png', 2: 'Waterfall_Cave_gem_TDS.png',
             3: 'sprites/eau_metano/cascade_frame_1.png', 4: 'sprites/eau_metano/cascade_frame_2.png',
             5: 'sprites/eau_metano/cascade_frame_3.png', 6: 'sprites/eau_metano/cascade_frame_4.png'}
SPARK_ID = 7                   # scintillements : tuiles natives décodées (famille, phase, décalage dans la grappe)

# Géométrie de la composition (coordonnées map). Ledge = plateforme au pied de la cascade = seuil du donjon.
FALLS = (336, 190, 432, 286)         # deux bandes natives de 48×96 (corps propre de la cascade, lignes 24..119, colonnes 8..55)
LEDGE = (336, 272, 432, 312)         # plateforme au pied de la cascade = seuil
CAUSEWAY = (364, 304, 404, 448)
ENTRY_PX = [376, H - 16]
THRESHOLD_PX = [376, 292]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


BM = loadmod('ebn1_utils', R / 'source/entree_bristle_sud_nord_v1/build.py')
BM.W, BM.H = W, H
place, cell_grid, write_ora = BM.place, BM.cell_grid, BM.write_ora


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_sources():
    src = {}
    for i, f in SRC_FILES.items():
        im = Image.open(R / f).convert('RGBA'); a = np.array(im)
        if i <= 2:
            a[..., 3] = 255
        src[i] = a
    return src


# ---------------------------------------------------------------- toile avec provenance
class Canvas:
    """Un calque RGBA + provenance par pixel (id source, x source, y source)."""

    def __init__(self):
        self.rgba = np.zeros((H, W, 4), 'uint8')
        self.pid = np.zeros((H, W), 'uint8')
        self.sx = np.zeros((H, W), 'int16')
        self.sy = np.zeros((H, W), 'int16')

    def opaque(self):
        return self.rgba[..., 3] == 255

    def write(self, sid, src, box, pos, take):
        """Copie src[box] en pos là où take (bool, taille du box) ; retourne le nombre de pixels écrits."""
        x0, y0, x1, y1 = box; px, py = pos
        cx0, cy0 = max(px, 0), max(py, 0); cx1, cy1 = min(px + (x1 - x0), W), min(py + (y1 - y0), H)
        if cx1 <= cx0 or cy1 <= cy0:
            return 0
        bx0, by0 = cx0 - px, cy0 - py; bx1, by1 = bx0 + (cx1 - cx0), by0 + (cy1 - cy0)
        t = take[by0:by1, bx0:bx1]
        patch = src[y0 + by0:y0 + by1, x0 + bx0:x0 + bx1]
        view = self.rgba[cy0:cy1, cx0:cx1]; view[t] = patch[t]; view[t, 3] = 255
        self.pid[cy0:cy1, cx0:cx1][t] = sid
        gy, gx = np.mgrid[y0 + by0:y0 + by1, x0 + bx0:x0 + bx1]
        self.sx[cy0:cy1, cx0:cx1][t] = gx[t]; self.sy[cy0:cy1, cx0:cx1][t] = gy[t]
        return int(t.sum())

    def put(self, sid, src, box, pos, mask=None, seam=None):
        """Pose un rectangle natif. mask : bool (h, w) facultatif. seam='v' : couture verticale à
        coût minimal dans la zone déjà opaque (le nouveau bloc arrive par la droite)."""
        x0, y0, x1, y1 = box
        take = np.ones((y1 - y0, x1 - x0), bool) if mask is None else mask.copy()
        take &= src[y0:y1, x0:x1, 3] == 255
        if seam == 'v':
            take &= self.seam_v(src[y0:y1, x0:x1, :3], pos, take)
        return self.write(sid, src, box, pos, take)

    def seam_v(self, patch, pos, take):
        """Couture verticale : garde l'existant à gauche du chemin, le nouveau à droite."""
        h, w = take.shape; px, py = pos
        cy0, cy1 = max(py, 0), min(py + h, H); cx0, cx1 = max(px, 0), min(px + w, W)
        ex = self.opaque()[cy0:cy1, cx0:cx1]
        sub = take[cy0 - py:cy1 - py, cx0 - px:cx1 - px] & ex
        keep = np.ones_like(take)
        if not sub.any():
            return keep
        cols = np.nonzero(sub.any(0))[0]; ox0, ox1 = cols[0], cols[-1] + 1
        cost = np.where(sub[:, ox0:ox1], ((self.rgba[cy0:cy1, cx0 + ox0:cx0 + ox1, :3].astype(int) -
                                            patch[cy0 - py:cy1 - py, cx0 - px + ox0:cx0 - px + ox1].astype(int)) ** 2).sum(2), 0)
        path = min_path(cost)
        cut = np.zeros((cy1 - cy0, ox1 - ox0), bool)
        xs = np.arange(ox1 - ox0)
        for r in range(cy1 - cy0):
            cut[r] = (xs >= path[r]) | ~ex[r, ox0:ox1]
        keep[cy0 - py:cy1 - py, cx0 - px + ox0:cx0 - px + ox1] = cut
        return keep


def min_path(cost):
    """Chemin vertical (une colonne par ligne, |dx|<=1) de coût cumulé minimal ; retourne x par ligne."""
    h, w = cost.shape
    acc = cost.astype(float).copy(); back = np.zeros((h, w), int)
    for r in range(1, h):
        prev = acc[r - 1]
        left = np.concatenate(([np.inf], prev[:-1])); right = np.concatenate((prev[1:], [np.inf]))
        stack = np.stack([left, prev, right]); k = stack.argmin(0)
        back[r] = np.arange(w) + k - 1; acc[r] += stack[k, np.arange(w)]
    path = np.zeros(h, int); path[-1] = int(acc[-1].argmin())
    for r in range(h - 1, 0, -1):
        path[r - 1] = back[r, path[r]]
    return path


def dark_cut(patch_rgb, y_lo, y_hi):
    """Masque qui coupe le bas d'un bloc le long d'un chemin horizontal de pixels sombres
    (contours/ombres natifs) entre les lignes y_lo..y_hi : le bloc garde les lignes au-dessus du chemin."""
    lum = patch_rgb.astype(float) @ [.299, .587, .114]
    band = lum[y_lo:y_hi].T                    # chemin horizontal = chemin vertical sur la transposée
    path = min_path(band)                      # pour chaque colonne : ligne (relative) du pixel sombre suivi
    h, w = lum.shape; m = np.zeros((h, w), bool)
    rows = np.arange(h)[:, None]
    m[:] = rows <= (y_lo + path)[None, :]
    return m


# ---------------------------------------------------------------- quilting par chevauchement (sol, eau)
def quilt(cv, sid, src, region, rects, block, overlap, seed, phase=None, phase_base=0):
    """Remplit `region` par blocs natifs `block`×`block` pris dans les rectangles sources `rects`,
    chevauchement `overlap` avec coutures à coût minimal (Efros–Freeman simplifié). Avec `phase`,
    seule une source de même phase verticale (y0 ≡ y_bloc mod phase) est admise : le sol de L a une
    période verticale de 24 px, ce qui rend les coutures horizontales quasi invisibles."""
    rng = np.random.default_rng(seed)
    cands = []
    for (x0, y0, x1, y1) in rects:
        for y in range(y0, y1 - block + 1):
            for x in range(x0, x1 - block + 1, 2):
                cands.append((x, y))
    cands = np.array(cands)
    patches = np.stack([src[y:y + block, x:x + block, :3] for x, y in cands]).astype(np.int32)
    by = np.nonzero(region.any(1))[0]; bx = np.nonzero(region.any(0))[0]
    ry0, ry1, rx0, rx1 = by[0], by[-1] + 1, bx[0], bx[-1] + 1
    step = block - overlap
    filled = np.zeros((H, W), bool)
    ys = list(range(ry0 - (ry0 - phase_base) % (phase or 1), ry1, step))
    for y in ys:
        for x in range(rx0 - overlap, rx1, step):
            yy0, yy1, xx0, xx1 = max(y, 0), min(y + block, H), max(x, 0), min(x + block, W)
            if yy1 <= yy0 or xx1 <= xx0 or not region[yy0:yy1, xx0:xx1].any():
                continue
            sel = np.arange(len(cands)) if phase is None else np.nonzero((cands[:, 1] - y) % phase == 0)[0]
            f = filled[yy0:yy1, xx0:xx1]
            tgt = cv.rgba[yy0:yy1, xx0:xx1, :3].astype(np.int32)
            P = patches[sel][:, yy0 - y:yy1 - y, xx0 - x:xx1 - x]
            if f.any():
                cost = ((P - tgt) ** 2).sum(3)[:, f].sum(1)
                best = sel[np.argsort(cost)[:3]]
            else:
                best = sel
            sx, sy = cands[rng.choice(best)]
            patch = src[sy:sy + block, sx:sx + block]
            take = np.zeros((block, block), bool)
            sub = np.ones((yy1 - yy0, xx1 - xx0), bool)
            pr = patch[yy0 - y:yy1 - y, xx0 - x:xx1 - x, :3].astype(np.int32)
            d = ((pr - tgt) ** 2).sum(2)
            # couture verticale dans la bande gauche déjà remplie
            lc = f[:, :overlap]
            if lc.any():
                path = min_path(np.where(lc, d[:, :overlap], 0))
                xs = np.arange(overlap)[None, :]
                sub[:, :overlap] &= (xs >= path[:, None]) | ~lc
            tc = f[:overlap, :]
            if tc.any():
                path = min_path(np.where(tc, d[:overlap, :], 0).T)
                ys_ = np.arange(overlap)[:, None]
                sub[:overlap, :] &= (ys_ >= path[None, :]) | ~tc
            sub &= region[yy0:yy1, xx0:xx1]
            take[yy0 - y:yy1 - y, xx0 - x:xx1 - x] = sub
            cv.write(sid, src, (sx, sy, sx + block, sy + block), (x, y), take)
            filled[yy0:yy1, xx0:xx1] |= sub
    assert (filled | ~region).all(), 'région incomplète'


# ---------------------------------------------------------------- extraction d'objets natifs (masques)
def teal_pool(L, box):
    x0, y0, x1, y1 = box; a = L[y0:y1, x0:x1, :3].astype(int); r, g, b = a.transpose(2, 0, 1)
    lum = a @ [.299, .587, .114]
    m = ((g - r >= 60) & (b - r >= 60) & (lum > 70)) | ((r > 150) & (g > 190) & (b > 190))
    m = nd.binary_fill_holes(nd.binary_closing(m, iterations=2))
    lab, n = nd.label(m); sizes = nd.sum(m, lab, range(1, n + 1))
    return lab == (int(np.argmax(sizes)) + 1)


def dark_blob(L, box):
    x0, y0, x1, y1 = box; lum = L[y0:y1, x0:x1, :3].astype(float) @ [.299, .587, .114]
    m = nd.binary_fill_holes(nd.binary_closing(lum < 100, iterations=1))
    lab, n = nd.label(m); sizes = nd.sum(m, lab, range(1, n + 1))
    return nd.binary_dilation(lab == (int(np.argmax(sizes)) + 1), iterations=1)


def gem_mask(G, box):
    """Cristal : pixels saturés ou très clairs (facettes), petits socles gris clairs ; le sol de galets de G est exclu."""
    x0, y0, x1, y1 = box; a = G[y0:y1, x0:x1, :3].astype(int)
    sat = a.max(2) - a.min(2); lum = a @ [.299, .587, .114]
    m = (sat > 120) | (lum > 150) | ((sat < 45) & (lum > 95))
    m = nd.binary_fill_holes(nd.binary_closing(m, iterations=1))
    m = nd.binary_opening(m, iterations=1)
    lab, n = nd.label(m); sizes = nd.sum(m, lab, range(1, n + 1))
    return lab == (int(np.argmax(sizes)) + 1)


def g_boulders(G, box):
    """Paire de rochers de G : tout sauf le vide pourpre, l'eau et le noir."""
    x0, y0, x1, y1 = box; a = G[y0:y1, x0:x1, :3].astype(int); r, g, b = a.transpose(2, 0, 1)
    lum = a @ [.299, .587, .114]
    void = (r >= g); water = (b - r >= 100); dark = lum < 45      # pourpre (racines/vide), eau, noir
    m = nd.binary_opening(~void & ~water & ~dark, iterations=1)
    m = nd.binary_fill_holes(m)
    lab, n = nd.label(m); sizes = nd.sum(m, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i in range(n) if sizes[i] >= 200])
    return keep


# ---------------------------------------------------------------- formes
def ellipse_mask(cx, cy, rx, ry):
    yy, xx = np.mgrid[0:H, 0:W]
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1


def rect_mask(box):
    m = np.zeros((H, W), bool); x0, y0, x1, y1 = box; m[y0:y1, x0:x1] = True; return m


def pool_mask():
    west = ellipse_mask(272, 302, 80, 40) | ellipse_mask(262, 352, 72, 62) | ellipse_mask(300, 400, 60, 32) | ellipse_mask(230, 318, 40, 40)
    east = ellipse_mask(496, 302, 80, 40) | ellipse_mask(506, 352, 72, 62) | ellipse_mask(468, 400, 60, 32) | ellipse_mask(538, 318, 40, 40)
    m = west | east
    m = nd.binary_closing(m, iterations=6); m = nd.binary_opening(m, iterations=3)
    # bord irrégulier déterministe (bruit à 4 px)
    rng = np.random.default_rng(7)
    noise = rng.random((H // 4 + 1, W // 4 + 1)) > 0.5
    noise = np.kron(noise, np.ones((4, 4), bool))[:H, :W]
    edge = m & ~nd.binary_erosion(m, iterations=3)
    m = m & ~(edge & noise)
    m = nd.binary_opening(m, iterations=1)
    m &= ~rect_mask(LEDGE) & ~rect_mask(CAUSEWAY)
    m &= ~nd.binary_dilation(rect_mask(LEDGE) | rect_mask(CAUSEWAY), iterations=2)
    m[:264] = False
    lab, n = nd.label(m); sizes = nd.sum(m, lab, range(1, n + 1))
    return np.isin(lab, [i + 1 for i in range(n) if sizes[i] > 2000])


def shore_points(pool, spacing, seed):
    """Points espacés (≥ spacing) sur le bord des bassins, décalés de 3 px vers l'eau."""
    rng = np.random.default_rng(seed)
    edge = pool & ~nd.binary_erosion(pool, iterations=4)
    inner = nd.binary_erosion(pool, iterations=1)
    ys, xs = np.nonzero(edge); idx = rng.permutation(len(ys)); pts = []
    for i in idx:
        y, x = int(ys[i]), int(xs[i])
        if all((x - qx) ** 2 + (y - qy) ** 2 >= spacing ** 2 for qx, qy in pts):
            pts.append((x, y))
    return pts


# ---------------------------------------------------------------- Ground PMDO
def ground_project(stack, blocked, gfx, tools):
    if STAGE.exists():
        shutil.rmtree(STAGE)
    with zipfile.ZipFile(R / 'mod_metano_expeditions_pmdo_0812.zip') as z:
        tpl = json.loads(z.read('metano_expeditions/Data/Ground/v50812_01_crete_sillage_jour.rsground'))
    o = tpl['Object']; gw, gh = W // 8, H // 8; layers, banks = [], []
    for i, (title, frames, ticks) in enumerate(stack):
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
        layers.append(gfx.layer(f'{i:02d} {title}', gw, gh, cell, ticks)); banks.append(bank)
    layers.append(gfx.layer(f'{len(layers):02d} Vos elements avant-plan (Top)', gw, gh, draw=4))
    for bank in banks:
        bank.write(STAGE / f'Content/Tile/{bank.name}.tile')
    o.update(Name={'DefaultText': 'Entree Cascade - sud vers nord (4:3, natif)', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Pixels natifs exacts : Waterfall Cave (ledge + gem) + cascade et scintillements Metano. '
                     'Cascade 4 phases x 10 ticks (cadence proposee). Collisions de base a verifier. Seuil non raccorde.')
    o['obstacles'] = [[{'Bounds': {'X': x*8, 'Y': y*8, 'Width': 8, 'Height': 8}, 'Tags': int(blocked[y, x])}
                       for y in range(gh)] for x in range(gw)]
    mk = lambda n, p: {'EntName': n, 'Direction': 4, 'EntEnabled': True, 'triggerType': 0,
                       'Collider': {'X': p[0], 'Y': p[1], 'Width': 16, 'Height': 16}}
    o['Entities'] = [{'Name': 'Entrees et vos acteurs', 'Visible': True, 'MapChars': [], 'GroundObjects': [], 'Spawners': [],
                      'Markers': [mk('entrance', ENTRY_PX), mk('donjon_seuil', THRESHOLD_PX)]}]
    o['Decorations'] = [{'Name': 'Vos decorations', 'Layer': 2, 'Visible': True, 'Anims': []}]
    tpl['Version'] = '0.8.12.0'
    gfx.save(STAGE / f'Data/Ground/{ASSET}.rsground', json.dumps(tpl, ensure_ascii=False, separators=(',', ':')).encode())
    gfx.save(STAGE / f'Data/Script/{NAMESPACE}/ground/{ASSET}/init.lua',
             f'-- {ASSET} : base d edition, aucun warp.\nlocal {ASSET} = {{}}\nreturn {ASSET}\n'.encode())
    nodes = {}
    for p in sorted((STAGE / 'Content/Tile').glob('*.tile')):
        with p.open('rb') as f:
            nodes[p.stem] = tools.read_node(f)
    (STAGE / 'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    ident = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/meromoonmeri/guilde-treehouse-pmd/' + NAMESPACE)
    (STAGE / 'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Entree Cascade sud-nord 4:3 natif - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de grotte a cascade au format 4:3, composee uniquement de pixels natifs (Waterfall Cave, cascade et scintillements Metano). Pas une aventure jouable.</Description>
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
    return {b.name: len(b.data) for b in banks}


# ---------------------------------------------------------------- composition
def compose(src):
    L, G = src[1], src[2]
    cv = {k: Canvas() for k in ['fond', 'plafond', 'sol', 'eau', 'parois', 'rochers']}
    ops = []

    # 00 fond : aplat natif du vide de L (pixel (4,4)) sur toute la map.
    cv['fond'].write(1, L, (4, 4, 5, 5), (0, 0), np.ones((1, 1), bool))
    cv['fond'].rgba[:] = cv['fond'].rgba[0, 0]; cv['fond'].pid[:] = 1; cv['fond'].sx[:] = 4; cv['fond'].sy[:] = 4
    ops.append({'calque': 'fond', 'source': 'L', 'op': 'aplat du pixel natif (4,4) = vide (31,47,47)'})

    # 01 plafond + parois nord : pièces hautes de L (colonnes hors couloir), bas coupé le long des contours sombres.
    A = (0, 0, 156, 262); B = (252, 0, 408, 262)
    pieces = [(B, 132), (A, 264), (B, 396), (A, 528)]
    for box, px in pieces:
        x0, y0, x1, y1 = box
        m = dark_cut(L[y0:y1, x0:x1, :3], 214, 262)
        n = cv['plafond'].put(1, L, box, (px, 0), mask=m, seam='v')
        ops.append({'calque': 'plafond', 'source': 'L', 'box': list(box), 'pos': [px, 0], 'op': 'bloc natif, couture verticale, bas coupé sur contours sombres', 'px': n})
    # murs latéraux : mêmes colonnes de L prolongées jusqu'au pied natif des parois (y=470), identité (gauche) / +360 (droite).
    for box, px in [((0, 0, 156, 470), 0), ((252, 0, 408, 470), 612)]:
        x0, y0, x1, y1 = box
        m = dark_cut(L[y0:y1, x0:x1, :3], 430, 470)
        n = cv['parois'].put(1, L, box, (px, 0), mask=m)
        ops.append({'calque': 'parois', 'source': 'L', 'box': list(box), 'pos': [px, 0], 'op': 'paroi native entière, pied coupé sur contours sombres', 'px': n})

    # 02 sol : galets du couloir de L (période verticale 24 px) — blocs exacts en identité près des parois,
    # quilting à phase alignée partout ailleurs.
    region = np.zeros((H, W), bool); region[168:] = True
    exact = [((156, 190, 252, 456), (156, 190)), ((156, 190, 252, 456), (516, 190))]
    for box, pos in exact:
        cv['sol'].put(1, L, box, pos)
        region[pos[1]:pos[1] + box[3] - box[1], pos[0]:pos[0] + box[2] - box[0]] = False
        ops.append({'calque': 'sol', 'source': 'L', 'box': list(box), 'pos': list(pos), 'op': 'couloir natif exact (raccord sans couture avec la paroi voisine)'})
    quilt(cv['sol'], 1, L, region, [(156, 190, 252, 456)], block=48, overlap=16, seed=11, phase=24, phase_base=190)
    ops.append({'calque': 'sol', 'source': 'L', 'rect_source': [156, 190, 252, 456], 'op': 'quilting blocs 48 px, chevauchement 16, phase verticale 24 px'})

    # 03 eau : mailles profondes de G (deux bassins autour de la plateforme et de la chaussée).
    pool = pool_mask()
    quilt(cv['eau'], 2, G, pool, [(0, 162, 150, 256), (354, 162, 504, 256)], block=48, overlap=12, seed=5)
    ops.append({'calque': 'eau', 'source': 'G', 'rects_source': [[0, 162, 150, 256], [354, 162, 504, 256]], 'op': 'quilting blocs 48 px, chevauchement 12 (eau statique)'})

    # 05 rochers, source turquoise, pierres, cristaux : objets natifs masqués.
    rocks = cv['rochers']
    pairs = {'g1': (42, 257, 102, 294), 'g2': (402, 257, 462, 294), 'g3': (0, 264, 53, 295), 'g4': (451, 264, 504, 295)}
    pair_masks = {k: g_boulders(G, b) for k, b in pairs.items()}
    rock_places = [('g1', 184, 262), ('g3', 552, 262), ('g1', 292, 176), ('g2', 416, 176), ('g3', 296, 270), ('g4', 420, 270),
                   ('g4', 236, 226), ('g3', 500, 226),                                    # pied de la rangée nord
                   ('g2', 168, 390), ('g1', 238, 414), ('g3', 306, 428), ('g4', 304, 456),
                   ('g1', 470, 428), ('g2', 526, 414), ('g4', 596, 392), ('g3', 470, 458),
                   ('g2', 30, 446), ('g1', 96, 456), ('g4', 660, 446), ('g3', 720, 456),   # pied des murs latéraux
                   ('g1', 6, 500), ('g2', 60, 520), ('g4', 700, 500), ('g3', 660, 528),
                   ('g2', 588, 436), ('g1', 648, 470)]
    for k, x, y in rock_places:
        n = rocks.put(2, G, pairs[k], (x, y), mask=pair_masks[k])
        ops.append({'calque': 'rochers', 'source': 'G', 'objet': k, 'box': list(pairs[k]), 'pos': [x, y], 'op': 'paire de rochers native (masque vide/eau/noir)', 'px': n})
    stones = {'s1': (166, 283, 184, 296), 's2': (224, 306, 249, 323)}
    stone_masks = {k: dark_blob(L, b) for k, b in stones.items()}
    # liseré de pierres natives le long des bassins (côté eau : ne bloque pas la chaussée)
    ring = shore_points(pool, spacing=15, seed=3)
    for j, (x, y) in enumerate(ring):
        k = 's1' if j % 3 else 's2'; bx0, by0, bx1, by1 = stones[k]
        n = rocks.put(1, L, stones[k], (x - (bx1 - bx0) // 2, y - (by1 - by0) // 2), mask=stone_masks[k])
    ops.append({'calque': 'rochers', 'source': 'L', 'objets': ['s1', 's2'], 'op': f'liseré de {len(ring)} pierres natives sur le bord des bassins (pas 15 px)', 'points': ring})
    for k, x, y in [('s1', 210, 470), ('s2', 448, 500), ('s1', 560, 300), ('s2', 176, 330), ('s1', 630, 540), ('s2', 120, 560), ('s1', 340, 536)]:
        n = rocks.put(1, L, stones[k], (x, y), mask=stone_masks[k])
        ops.append({'calque': 'rochers', 'source': 'L', 'objet': k, 'box': list(stones[k]), 'pos': [x, y], 'op': 'pierre native', 'px': n})
    gems = {'c1': (160, 248, 176, 272), 'c2': (304, 225, 328, 248), 'c4': (168, 224, 184, 240), 'c5': (216, 184, 232, 200),
            'c8': (184, 190, 224, 224), 'c9': (272, 218, 316, 254)}
    gem_masks = {k: gem_mask(G, b) for k, b in gems.items()}
    for k, x, y in [('c1', 170, 452), ('c2', 588, 468), ('c8', 226, 492), ('c4', 640, 350), ('c5', 150, 400), ('c2', 700, 548),
                    ('c9', 540, 536), ('c1', 60, 486), ('c4', 300, 246), ('c5', 470, 250), ('c8', 606, 236), ('c9', 176, 236)]:
        n = rocks.put(2, G, gems[k], (x, y), mask=gem_masks[k])
        ops.append({'calque': 'rochers', 'source': 'G', 'objet': k, 'box': list(gems[k]), 'pos': [x, y], 'op': 'cristal natif (masque = hors palette du sol de G)', 'px': n})

    # 06 cascade : corps natif Métano (lignes 24..119, colonnes 8..55) posé deux fois côte à côte, 4 phases.
    falls = []
    for k in range(PHASES):
        c = Canvas(); fr = src[3 + k]
        for i in range(2):
            c.put(3 + k, fr, (8, 24, 56, 120), (FALLS[0] + 48 * i, FALLS[1]))
        falls.append(c)
    ops.append({'calque': 'cascade', 'source': 'cascade_frame_1..4', 'box': [8, 24, 56, 120], 'pos': [[FALLS[0], FALLS[1]], [FALLS[0] + 48, FALLS[1]]],
                'op': 'translation pure, 4 phases natives, 10 ticks par phase (cadence proposée)'})
    return cv, falls, pool, ops


def sparkles(visible, near):
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    frames = [np.zeros((H, W, 4), 'uint8') for _ in range(PHASES)]
    prov = [np.zeros((H, W, 3), 'int16') for _ in range(PHASES)]      # (id famille, dx, dy) dans la grappe
    out = []
    for fi, (name, fr) in enumerate(fams.items()):
        hh, ww = fr[0].shape[:2]
        for zone, count, seed in [(near, 2, 101 + fi), (visible, 4, 41 + fi)]:
            for (y, x) in place(zone, (hh, ww), count, seed, taken, core=8):
                out.append({'famille': name, 'xy': [x, y]})
                for t in range(PHASES):
                    mm = fr[t][..., 3] > 0
                    frames[t][y:y+hh, x:x+ww][mm] = fr[t][mm]
                    gy, gx = np.nonzero(mm)
                    prov[t][y + gy, x + gx] = np.stack([np.full(len(gy), fi + 1), gx, gy], 1)
    for t in range(PHASES):
        frames[t][~visible] = 0; prov[t][~visible] = 0
    return frames, prov, out, {k: [f.copy() for f in v] for k, v in fams.items()}


def build():
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    for d in ['calques', 'animation/cascade', 'animation/scintillements', 'masques', 'review', 'provenance']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    src = load_sources()
    cv, falls, pool, ops = compose(src)

    order = ['fond', 'sol', 'eau', 'plafond', 'parois', 'rochers']
    names = {'fond': 'fond_vide', 'sol': 'sol_galets', 'eau': 'eau_profonde', 'plafond': 'plafond_parois_nord',
             'parois': 'murs_lateraux', 'rochers': 'rochers_pierres_cristaux'}
    # visibilité : indice du calque opaque le plus haut par pixel (cascade = 6)
    top = np.full((H, W), -1, int)             # cascade (6) sous les rochers (5) : rochers de cadrage devant la chute
    for i, k in enumerate(order):
        top[cv[k].opaque()] = i
        if k == 'parois':
            top[falls[0].opaque()] = 6
    visible_water = top == order.index('eau')
    dist = nd.distance_transform_cdt(visible_water, metric='taxicab')
    fx0, fy0, fx1, fy1 = FALLS
    near = np.zeros((H, W), bool); near[fy1 - 8:fy1 + 40, fx0 - 40:fx1 + 40] = True
    sf, sprov, spark_list, fams = sparkles(visible_water & (dist > 4), visible_water & (dist > 3) & near)

    # Exports calques / animations / masques / provenance
    files = {}
    idx = {'fond': 0, 'sol': 1, 'eau': 2, 'plafond': 3, 'parois': 4, 'rochers': 6}
    for k in order:
        fn = f'{PFX}_{idx[k]:02d}_{names[k]}.png'; Image.fromarray(cv[k].rgba).save(OUT / 'calques' / fn); files[k] = fn
    for t in range(PHASES):
        Image.fromarray(falls[t].rgba).save(OUT / 'animation/cascade' / f'{PFX}_05_cascade_f{t}.png')
        Image.fromarray(sf[t]).save(OUT / 'animation/scintillements' / f'{PFX}_07_scintillements_f{t}.png')
    Image.fromarray((pool * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_eau.png')
    prov = {}
    for k in order:
        prov[f'{k}_pid'] = cv[k].pid; prov[f'{k}_sx'] = cv[k].sx; prov[f'{k}_sy'] = cv[k].sy
    for t in range(PHASES):
        prov[f'cascade_f{t}_pid'] = falls[t].pid; prov[f'cascade_f{t}_sx'] = falls[t].sx; prov[f'cascade_f{t}_sy'] = falls[t].sy
        prov[f'scintillements_f{t}'] = sprov[t]
    np.savez_compressed(OUT / 'provenance' / f'{PFX}_provenance.npz', **prov)

    stack_named = [(names[k], [cv[k].rgba], 60) for k in order[:-1]] + \
                  [('cascade', [f.rgba for f in falls], TICKS), (names['rochers'], [cv['rochers'].rgba], 60), ('scintillements', sf, TICKS)]
    # Collisions : praticable = sol visible (aucun calque opaque au-dessus).
    walk = top == order.index('sol')
    blocked = cell_grid(~walk)
    ok, explored = v1.reachable(blocked, (ENTRY_PX[1] // 8, ENTRY_PX[0] // 8), (THRESHOLD_PX[1] // 8, THRESHOLD_PX[0] // 8))
    assert ok, 'pas de chemin 16x16'

    def scene(tick):
        p = (tick // TICKS) % PHASES
        im = Image.new('RGBA', (W, H))
        for title, frames, _ in stack_named:
            im.alpha_composite(Image.fromarray(frames[p if len(frames) > 1 else 0]))
        return im
    scenes = [scene(t * TICKS) for t in range(PHASES)]          # 4 phases de 10 ticks (167 ms), boucle 40 ticks
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(TICKS * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (qx, qy), c in ((ENTRY_PX, (255, 230, 40, 255)), (THRESHOLD_PX, (60, 220, 255, 255))):
        dr.rectangle([qx, qy, qx + 15, qy + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    # Planche des sources : cadres des rectangles natifs utilisés sur L et G.
    sheet = Image.new('RGB', (408 + 504 + 24, 552), (20, 20, 24)); d = ImageDraw.Draw(sheet)
    sheet.paste(Image.fromarray(src[1][..., :3]), (0, 0)); sheet.paste(Image.fromarray(src[2][..., :3]), (432, 0))
    for op in ops:
        if 'box' in op and op['source'] in ('L', 'G'):
            x0, y0, x1, y1 = op['box']; dx = 0 if op['source'] == 'L' else 432
            d.rectangle([x0 + dx, y0, x1 + dx - 1, y1 - 1], outline=(255, 220, 60) if op['source'] == 'L' else (120, 255, 160))
    for r_ in [(156, 190, 252, 456)]:
        d.rectangle([r_[0], r_[1], r_[2] - 1, r_[3] - 1], outline=(255, 120, 200))
    for r_ in [(0, 162, 150, 256), (354, 162, 504, 256)]:
        d.rectangle([r_[0] + 432, r_[1], r_[2] + 432 - 1, r_[3] - 1], outline=(120, 200, 255))
    sheet.save(OUT / 'review' / f'{PFX}_sources_cadres.png')
    write_ora(OUT / f'{PFX}_entree_cascade_calques.ora',
              {f'{i:02d}_{t}' + ('_f0' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, gfx, tools)
    order_files = [f'calques/{files[k]}' for k in order[:-1]] + \
                  [f'animation/cascade/{PFX}_05_cascade_fX.png', f'calques/{files["rochers"]}',
                   f'animation/scintillements/{PFX}_07_scintillements_fX.png']
    manifest = {
        'lot': 'entree_cascade_sud_nord_v1', 'format': '4:3 vaste', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'pixels natifs exacts : rectangles et objets masques copies tels quels (aucune rotation, miroir, echelle ou recoloration) ; '
                  'sol et eau par quilting de blocs natifs avec coutures a cout minimal ; provenance par pixel dans provenance/',
        'sources': {str(i): {'file': f, 'sha256': sha(R / f), 'size': list(Image.open(R / f).size)} for i, f in SRC_FILES.items()},
        'sparkles_source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile (pixels natifs, aplat de surface retire)',
        'guide_composition': {'file': 'source/entree_cascade_sud_nord_v1/bruts/decor_magenta.png',
                              'role': 'rendu genere utilise UNIQUEMENT comme guide de composition ; aucun pixel dans les exports'},
        'operations': ops,
        'layer_order_bottom_to_top': order_files,
        'cascade': {'phases': PHASES, 'frame_length_ticks': TICKS, 'rect': list(FALLS),
                    'origine': 'cascade_frame_1..4 Metano natives, corps lignes 24..119 colonnes 8..55, deux bandes cote a cote (translation pure)',
                    'cadence': 'proposee (10 ticks), non prouvee par la map Metano'},
        'water': {'origine': 'mailles de Waterfall_Cave_gem_TDS.png, statiques (aucun cycle natif recupere)', 'phases': 1},
        'sparkles': {'phases': PHASES, 'frame_length_ticks': TICKS, 'placements': spark_list, 'origine': 'pixels Metano NATIFS inchanges'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': ENTRY_PX, 'threshold_px': THRESHOLD_PX, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % de pixels non sol visible'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(spark_list), 'blocked': int(blocked.sum()), 'cells': int(blocked.size), 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
