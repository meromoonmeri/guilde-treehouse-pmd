"""Jungle aux cascades V1 — 5 calques natifs stricts, sud vers nord.

Sources natives UNIQUEMENT (aucun pixel genere dans les exports) :
  S0 junglewaterfallzonepmdsky.png (744x1032) : herbe, chemin, falaise, chutes, bassins, ecume, buissons, rochers
  S1 Southern_Jungle_exit_2_S.png (600x456) : arbres-park jungle canoniques (troncs + canopees)

Le brut genere source/suite_generee_v1/bruts/jungle_cascades_terrain.png sert de GUIDE
de composition UNIQUEMENT. Son rebord superieur montrant la source des chutes est
explicitement REJETE : les 6 chutes sont coupees au bord haut (source cachee).

5 calques (512x640, grille 8px) :
  01_sol        : herbe + chemin central sud->nord (patchs natifs, coutures sans fondu)
  02_paroi      : mur falaise plein cadre y0-368 (modules natifs entiers, repetition documentee)
  03_cascades   : 6 chutes longues coupees en haut, 26 phases (roulement vertical 16px/phase
                  sur 416px : 26x16=416 -> boucle parfaite exacte, offsets par chute)
  04_bassins    : 2 bassins + ecume + 2 mares (colonnes de chutes masquees au-dessus de l'ecume
                  pour laisser l'animation visible ; pieds des chutes sous l'ecume)
  05_vegetation : 2 arbres jungle canoniques, murs de buissons lateraux, buissons, rochers, galet

Mouvement NOUVEAU sur pixels natifs (repositionnement exact, zero recoloration) :
PAS un cycle officiel recupere. Aucune rotation/miroir/echelle.
"""
from pathlib import Path
import json, hashlib, zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'exports' / 'jungle_cascades_v1'
W, H = 512, 640
PREFIX = 'JungleV1'
PHASES, STEP, PERIOD, FRAME_MS = 26, 16, 96, 80  # boucle exacte : 26 x 16 = 416 = FALL_H

FILES = ['junglewaterfallzonepmdsky.png', 'Southern_Jungle_exit_2_S.png']
A = [np.array(Image.open(R / p).convert('RGBA')) for p in FILES]
SHAS = [hashlib.sha256(open(R / p, 'rb').read()).hexdigest() for p in FILES]


def seam(cost):
    """Coupe verticale min-sum sur la zone de chevauchement (coutures sans fondu)."""
    h, w = cost.shape
    dp = cost.astype(float).copy()
    for y in range(1, h):
        dp[y] += np.minimum(np.roll(dp[y - 1], 1), np.minimum(dp[y - 1], np.roll(dp[y - 1], -1)))
    cut = np.zeros(h, int)
    cut[-1] = int(dp[-1].argmin())
    for y in range(h - 2, -1, -1):
        c = cut[y + 1]
        cut[y] = max(0, min(w - 1, c + int(dp[y, max(0, c - 1):c + 2].argmin()) - (1 if c > 0 else 0)))
    return cut


class Map:
    def __init__(self):
        self.layers = []  # (name, rgba, sxy)
        self.ops = []

    def layer(self, name):
        l = [name, np.zeros((H, W, 4), np.uint8), np.full((H, W, 3), -1, np.int16)]
        self.layers.append(l)
        return l

    def put(self, l, s, box, pos, mask=None):
        x0, y0, x1, y1 = box
        x, y = pos
        p = A[s][y0:y1, x0:x1]
        hh, ww = p.shape[:2]
        assert x >= 0 and y >= 0 and x + ww <= W and y + hh <= H, (box, pos)
        m = p[:, :, 3] > 0 if mask is None else (mask & (p[:, :, 3] > 0))
        sy, sx = np.mgrid[y0:y1, x0:x1]
        q = np.stack([np.full(sx.shape, s), sx, sy], 2)
        l[1][y:y + hh, x:x + ww][m] = p[m]
        l[2][y:y + hh, x:x + ww][m] = q[m]
        self.ops.append(dict(layer=l[0], source=FILES[s], rect=list(box), position=list(pos)))

    def fill(self, l, s, boxes, mask=None, seed=11):
        rng = np.random.default_rng(seed)
        mask = np.ones((H, W), bool) if mask is None else mask
        hh = boxes[0][3] - boxes[0][1]
        ww = boxes[0][2] - boxes[0][0]
        ov = min(8, hh // 2, ww // 2)
        for yy in range(0, H, hh - ov):
            for xx in range(0, W, ww - ov):
                h, w = min(hh, H - yy), min(ww, W - xx)
                want = mask[yy:yy + h, xx:xx + w]
                if not want.any():
                    continue
                old = l[1][yy:yy + h, xx:xx + w]
                occupied = (old[:, :, 3] > 0) & want
                best = None
                for idx in rng.permutation(len(boxes))[:24]:
                    x0, y0, _, _ = boxes[idx]
                    patch = A[s][y0:y0 + h, x0:x0 + w]
                    cost = ((old[:, :, :3].astype(float) - patch[:, :, :3]) ** 2).sum(2)
                    score = cost[occupied].mean() if occupied.any() else rng.random()
                    if best is None or score < best[0]:
                        best = (score, x0, y0, patch, cost)
                _, x0, y0, patch, cost = best
                take = want.copy()
                if xx and w >= ov:
                    take[:, :ov] &= np.arange(ov)[None, :] >= seam(cost[:, :ov])[:, None]
                if yy and h >= ov:
                    take[:ov, :] &= np.arange(ov)[:, None] >= seam(cost[:ov, :].T)[None, :]
                take |= want & (old[:, :, 3] == 0)
                sy, sx = np.mgrid[y0:y0 + h, x0:x0 + w]
                q = np.stack([np.full(sx.shape, s), sx, sy], 2)
                old[take] = patch[take]
                l[2][yy:yy + h, xx:xx + w][take] = q[take]
        self.ops.append(dict(layer=l[0], source=FILES[s], method='native ground patch overlap, no blending',
                             patches=len(boxes), seed=seed))


def path_mask():
    yy, xx = np.mgrid[:H, :W]
    centers = [(256, 500), (244, 555), (268, 600), (256, 640)]
    ys = np.array([p[1] for p in centers])
    xs = np.array([p[0] for p in centers])
    middle = np.interp(np.clip(yy, 500, 640), ys, xs)
    width = np.interp(np.clip(yy, 500, 640), ys, [56, 60, 64, 64])
    jitter = ((yy // 8) % 5 - 2)
    return (yy >= 500) & (np.abs(xx - middle) <= width / 2 + jitter)


FALLS = [
    # (dst_x0, dst_x1, src_x0, src_x1, offset_px) — y0-416, coupe en haut
    (42, 86, 74, 118, 0),
    (121, 135, 153, 167, 32),
    (171, 227, 203, 259, 64),
    (285, 341, 485, 541, 16),
    (377, 391, 577, 591, 80),
    (426, 470, 626, 670, 48),
]
FALL_H = 416


def build():
    O.mkdir(parents=True, exist_ok=True)
    m = Map()

    # ---- 01_sol : herbe sombre plein cadre puis chemin clair ----
    sol = m.layer('01_sol')
    dark = [(x, y, x + 32, y + 32) for x in (40, 72, 104, 136, 560, 592, 624, 656)
            for y in (800, 832, 864, 896)]
    m.fill(sol, 0, dark, seed=21)
    light = [(x, y, x + 32, y + 32) for x in (330, 362, 394, 426) for y in (800, 832, 864, 896)]
    pm = path_mask()
    m.fill(sol, 0, light, pm, seed=22)

    # ---- 02_paroi : mur falaise y0-368, 3 bandes x depuis module central natif ----
    paroi = m.layer('02_paroi')
    bands = [(0, 120, [(260, 8), (260, 150), (360, 100)]),
             (120, 240, [(260, 200), (260, 300), (360, 250)]),
             (240, 368, [(260, 320), (260, 60), (360, 20)])]
    for y0, y1, rows in bands:
        h = y1 - y0
        (ax, ay), (bx, by), (cx, cy) = rows
        m.put(paroi, 0, (ax, ay, ax + 224, ay + h), (0, y0))
        m.put(paroi, 0, (bx, by, bx + 224, by + h), (224, y0))
        m.put(paroi, 0, (cx, cy, cx + 64, cy + h), (448, y0))

    # ---- 03_cascades : 12 phases, roulement vertical, boucle 96px exacte ----
    for sx0, sx1, in [(f[2], f[3]) for f in FALLS]:
        col = A[0][0:FALL_H, sx0:sx1].astype(int)
        assert (col[:FALL_H - PERIOD] == col[PERIOD:]).all(), f'chute {sx0}-{sx1} non 96-periodique'
    base = np.zeros((H, W, 4), np.uint8)
    meta = []
    for dx0, dx1, sx0, sx1, off in FALLS:
        base[0:FALL_H, dx0:dx1] = A[0][0:FALL_H, sx0:sx1]
        meta.append(dict(dst=[dx0, 0, dx1, FALL_H], src=[sx0, 0, sx1, FALL_H], offset=off))
    fall_dir = O / 'cascades_phases'
    fall_dir.mkdir(exist_ok=True)
    for p in range(PHASES):
        rgba = np.zeros((H, W, 4), np.uint8)
        sxy = np.full((H, W, 3), -1, np.int16)
        for dx0, dx1, sx0, sx1, off in FALLS:
            col = A[0][0:FALL_H, sx0:sx1]
            rolled = np.roll(col, off + p * STEP, axis=0)
            rgba[0:FALL_H, dx0:dx1] = rolled
            rows = (np.arange(FALL_H) - (off + p * STEP)) % FALL_H
            sy, sx = np.meshgrid(rows, np.arange(sx0, sx1), indexing='ij')
            sxy[0:FALL_H, dx0:dx1, 0] = 0
            sxy[0:FALL_H, dx0:dx1, 1] = sx
            sxy[0:FALL_H, dx0:dx1, 2] = sy
        Image.fromarray(rgba).save(fall_dir / f'{PREFIX}_03_cascades_phase_{p:02d}.png')
        np.savez_compressed(fall_dir / f'phase_{p:02d}_source.npz', source_sxy=sxy)
    # calque de reference (phase 0) pour la pile fixe + ORA
    casc = m.layer('03_cascades')
    casc[1][:] = np.array(Image.open(fall_dir / f'{PREFIX}_03_cascades_phase_00.png'))
    d = np.load(fall_dir / 'phase_00_source.npz')['source_sxy']
    casc[2][:] = d
    m.ops.append(dict(layer='03_cascades', source=FILES[0], method='native 96-periodic vertical roll, 12 phases x 8px',
                      falls=meta, note='NEW movement on native pixels, not an official cycle'))

    # ---- 04_bassins : 2 bassins + 2 mares, colonnes masquees au-dessus de l'ecume ----
    bas = m.layer('04_bassins')
    lb = (40, 520, 312, 700)
    lpos = (8, 352)
    lmask = np.ones((180, 272), bool)
    for a, b in [(74, 118), (153, 167), (203, 259)]:
        lmask[0:64, a - 40:b - 40] = False  # src y520-584 : animation visible jusqu'en pleine ecume
    m.put(bas, 0, lb, lpos, lmask)
    rb = (432, 520, 704, 700)
    rpos = (232, 352)
    rmask = np.ones((180, 272), bool)
    for a, b in [(485, 541), (577, 591), (626, 670)]:
        rmask[0:64, a - 432:b - 432] = False  # src y520-584 : animation visible jusqu'en pleine ecume
    m.put(bas, 0, rb, rpos, rmask)
    m.put(bas, 0, (190, 710, 270, 790), (140, 560))   # mare gauche
    m.put(bas, 0, (480, 710, 560, 790), (292, 560))   # mare droite

    # ---- 05_vegetation : arbres canoniques + buissons + rochers ----
    veg = m.layer('05_vegetation')
    m.put(veg, 1, (160, 60, 300, 160), (0, 520))      # arbre jungle gauche (tronc+canopee)
    m.put(veg, 1, (340, 60, 480, 160), (372, 520))    # arbre jungle droit (tronc+canopee)
    m.put(veg, 0, (274, 900, 334, 940), (45, 500))    # frange buissons sur couronne gauche
    m.put(veg, 0, (466, 900, 526, 940), (407, 500))   # frange buissons sur couronne droite
    m.put(veg, 0, (272, 760, 320, 970), (0, 430))     # mur buissons gauche
    m.put(veg, 0, (480, 760, 528, 970), (464, 430))   # mur buissons droit
    m.put(veg, 0, (270, 800, 330, 860), (140, 500))   # buisson devant bassin gauche
    m.put(veg, 0, (470, 800, 530, 860), (310, 505))   # buisson devant bassin droit
    m.put(veg, 0, (285, 635, 320, 670), (185, 590))   # rocher mare gauche
    m.put(veg, 0, (425, 635, 460, 670), (300, 595))   # rocher mare droite
    m.put(veg, 0, (384, 752, 400, 768), (248, 590))   # galet sur chemin

    # ---- exports : couches, composites, GIF, ORA, TSX, manifeste ----
    names = []
    stack = []
    for name, rgba, sxy in m.layers:
        fn = f'{PREFIX}_{name}.png'
        Image.fromarray(rgba).save(O / fn)
        np.savez_compressed(O / f'{name}_source.npz', source_sxy=sxy)
        root = ET.Element('tileset', version='1.10', name=Path(fn).stem, tilewidth='8', tileheight='8',
                          columns=str(W // 8), tilecount=str(W // 8 * (H // 8)))
        ET.SubElement(root, 'image', source=fn, width=str(W), height=str(H))
        ET.ElementTree(root).write(O / f'{PREFIX}_{name}.tsx', encoding='utf-8', xml_declaration=True)
        names.append(name)
        stack.append(Image.fromarray(rgba))
    static_bottom = Image.new('RGBA', (W, H))
    for im in stack[:2]:
        static_bottom.alpha_composite(im)
    static_top = Image.new('RGBA', (W, H))
    for im in stack[3:]:
        static_top.alpha_composite(im)
    # Nettoyage d'iterations precedentes a 12 composites (nouveau format : 1 seul composite).
    for old in O.glob(f'{PREFIX}_composite_phase_*.png'):
        old.unlink()
    for old in O.glob(f'{PREFIX}_planche_*_phases.png'):
        old.unlink()
    frames = []
    for p in range(PHASES):
        comp = static_bottom.copy()
        comp.alpha_composite(Image.open(fall_dir / f'{PREFIX}_03_cascades_phase_{p:02d}.png'))
        comp.alpha_composite(static_top)
        if p == 0:
            comp.save(O / f'{PREFIX}_composite_phase_00.png')
        frames.append(comp.convert('RGB'))
    frames[0].save(O / f'{PREFIX}_animation.gif', save_all=True, append_images=frames[1:],
                   duration=FRAME_MS, loop=0)
    tw, th = 128, 160
    sheet = Image.new('RGB', (tw * 13, th * 2), (255, 0, 255))
    for p, fr in enumerate(frames):
        sheet.paste(fr.resize((tw, th), Image.NEAREST), ((p % 13) * tw, (p // 13) * th))
    sheet.save(O / f'{PREFIX}_planche_26_phases.png')
    write_ora([(f'{PREFIX}_{n}.png', n) for n in names], O / f'{PREFIX}_composite_phase_00.png')
    manifest = dict(
        id='jungle_cascades_v1', title='Jungle aux cascades — 5 calques natifs, sud vers nord',
        size=[W, H], orientation='SOUTH_TO_NORTH',
        sources=[dict(file=f, sha256=s) for f, s in zip(FILES, SHAS)],
        layers=[dict(id=n, file=f'{PREFIX}_{n}.png', provenance=f'{name}_source.npz'.replace('name', n))
                for n in names],
        animation=dict(layer='03_cascades', phases=PHASES, step_px=STEP, period_px=PERIOD,
                       frame_ms=FRAME_MS, loop_ms=PHASES * FRAME_MS, offsets=[f[4] for f in FALLS],
                       method='native pixels vertical roll over full 416px height, 26x16 loop exact, NEW movement'),
        operations=m.ops, runtime='NOT TESTED', art_approved=False,
        notes=['Guide genere utilise pour la composition uniquement ; ses pixels ne sont dans aucun export.',
               'Rebord source du guide rejete : chutes coupees au bord haut.',
               'Pieds des chutes en pleine ecume (jonction anime/statique dans la turbulence blanche) ; colonnes masquees dans 04_bassins jusqu\'a dst y416.',
               'Aucune rotation/miroir/echelle/recoloration. Coutures sol sans fondu.'])
    (O / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    return manifest


def write_ora(layers, composite):
    """OpenRaster minimal : mimetype, stack.xml, data/*.png, mergedimage.png."""
    p = O / f'{PREFIX}_5_calques.ora'
    if p.exists():
        p.unlink()
    with zipfile.ZipFile(p, 'w', zipfile.ZIP_STORED) as z:
        z.writestr('mimetype', 'image/openraster')
        img = ET.Element('image', w=str(W), h=str(H))
        st = ET.SubElement(img, 'stack', name='racine')
        for i, (fn, name) in enumerate(layers):
            ET.SubElement(st, 'layer', name=name, src=f'data/{i}.png')
            z.write(O / fn, f'data/{i}.png')
        z.writestr('stack.xml', ET.tostring(img, encoding='utf-8', xml_declaration=True))
        z.write(composite, 'mergedimage.png')
    return p


if __name__ == '__main__':
    man = build()
    print('OK', man['id'], len(man['layers']), 'layers,', man['animation']['phases'], 'phases')
