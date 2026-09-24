"""Decomposition de la map FINALE generee en calques (partition exacte).

FINALE_map.png (generateur, guide V1 + refs canoniques) -> 8 calques + sol complet
reconstitue sous les objets (echantillons du meme brut, declare). Nuit Abyss.
"""
from pathlib import Path
import hashlib
import io
import json
import sys
import zipfile
import random

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from night import night

SRC = R / 'source/entree_crooked_finale'
OUT = R / 'renders/entree_crooked_finale'
PFX = 'EntreeCrookedFinale'

F = np.array(Image.open(SRC / 'bruts/FINALE_map.png').convert('RGBA')).astype(int)
H, W = F.shape[:2]
r, g, b = F[..., 0], F[..., 1], F[..., 2]
lum = F[..., :3].mean(2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    grass = (g > r + 10) & (g > b + 5) & (g > 80)
    # --- bouche : plus grande composante sombre de la moitie haute
    top = np.zeros((H, W), bool)
    top[:int(H * 0.55)] = True
    lab, _ = ndi.label((lum < 70) & top)
    bouche = lab == (max([[(lab == i).sum(), i] for i in range(1, lab.max() + 1)])[1])
    ys, xs = np.nonzero(bouche)
    mb = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    print('bouche bbox:', mb, 'n=', bouche.sum())
    # --- arbres : coeurs vert sombre -> ROI -> canopee (dilatation geodesique
    # dans prairie) + tronc (brun, bas du ROI)
    # --- fleurs : petites composantes claires/roses sur prairie (bas 60%)
    low = np.zeros((H, W), bool)
    low[int(H * 0.4):] = True
    sat = F[..., :3].max(2) - F[..., :3].min(2)
    near_grass = ndi.binary_dilation(grass, iterations=1)
    strongsand = (lum > 175) & (r - b > 45) & (g - b > 30)
    white = (lum > 195) & (sat < 50) & low & near_grass & ~strongsand
    cream = (r > 225) & (g > 195) & (b > 165) & (b < 225) & low & near_grass & ~strongsand
    seedfl = white | cream
    ylab, _ = ndi.label((r > 215) & (g > 165) & (b < 165) & low)
    dilf = ndi.binary_dilation(seedfl, iterations=1)
    yadd = np.zeros((H, W), bool)
    for i in range(1, ylab.max() + 1):
        m = ylab == i
        if m.sum() < 80 and (m & dilf).any():
            yadd |= m
    lab3, _ = ndi.label(seedfl | yadd)
    fleurM = np.zeros((H, W), bool)
    nf = 0
    for i in range(1, lab3.max() + 1):
        s = (lab3 == i).sum()
        if 6 < s < 600:
            fleurM |= lab3 == i
            nf += 1
    print('fleurs:', nf)
    low2 = np.zeros((H, W), bool)
    low2[int(H * 0.55):] = True
    lab2, _ = ndi.label((lum < 95) & (g > r + 15) & low2)
    cores = []
    for i in range(1, lab2.max() + 1):
        if (lab2 == i).sum() > 800:
            yy, xx = np.nonzero(lab2 == i)
            cores.append((xx.min(), yy.min(), xx.max() + 1, yy.max() + 1))
    cores.sort(key=lambda b: (b[1], b[0]))
    print('coeurs arbres:', cores)
    assert len(cores) == 4, cores
    trees, trunkM, canM = [], np.zeros((H, W), bool), np.zeros((H, W), bool)
    taken = np.zeros((H, W), bool)
    YY = np.mgrid[:H, :W][0]
    for (x0, y0, x1, y1) in cores:
        roi = np.zeros((H, W), bool)
        roi[max(0, y0 - 60):min(H, y1 + 60), max(0, x0 - 60):min(W, x1 + 60)] = True
        roi &= ~taken
        taken |= roi
        ys3, xs3 = np.nonzero(roi)
        trees.append((int(xs3.min()), int(ys3.min()), int(xs3.max() + 1), int(ys3.max() + 1)))
        core = (lab2 == 0) | False
        seed = ((lum < 95) & (g > r + 15) & roi)
        can = ndi.binary_dilation(seed, iterations=5, mask=grass & roi & (lum < 160) & ~fleurM)
        can |= ndi.binary_fill_holes(can) & grass
        canM |= can
        brown = (r > g + 5) & (g > b) & (lum > 60) & (lum < 150) & roi
        brown &= YY > ys3.min() + (ys3.max() - ys3.min()) * 0.45
        blab, _ = ndi.label(brown)
        for i in range(1, blab.max() + 1):
            if (blab == i).sum() > 80:
                trunkM |= ndi.binary_dilation(blab == i, iterations=1) & roi & ~grass & ~fleurM
    canM &= ~trunkM
    # fleurs hors ROIs arbres (les points clairs dans les frondaisons = trous de feuillage)
    anyroi = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in trees:
        anyroi[y0:y1, x0:x1] = True
    corebox = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in cores:
        corebox[y0:y1, x0:x1] = True
    flab, _ = ndi.label(fleurM)
    keep = np.zeros((H, W), bool)
    nf = 0
    for i in range(1, flab.max() + 1):
        ys4, xs4 = np.nonzero(flab == i)
        if not corebox[int(ys4.mean()), int(xs4.mean())]:
            keep[ys4, xs4] = True
            nf += 1
    fleurM = keep
    flab2, _ = ndi.label(fleurM)
    keep2 = np.zeros((H, W), bool)
    nf = 0
    for i in range(1, flab2.max() + 1):
        ys5, xs5 = np.nonzero(flab2 == i)
        if ys5.mean() >= 620:
            keep2[ys5, xs5] = True
            nf += 1
    fleurM = keep2
    canM &= ~fleurM
    canlab, _ = ndi.label(canM)
    cankeep = np.zeros((H, W), bool)
    for i in range(1, canlab.max() + 1):
        if (canlab == i).sum() > 5000:
            cankeep |= canlab == i
    canM = cankeep
    _, ncan = ndi.label(canM)
    print('canopees gardees:', ncan)
    assert ncan == 4
    # --- sable : chemin + parvis + sol de bouche
    sandcol = (lum > 170) & (r > b + 20) & ~grass & ~fleurM
    lowsand = np.zeros((H, W), bool)
    lowsand[int(H * 0.35):] = True
    lab4, _ = ndi.label(sandcol & lowsand)
    chemin = np.zeros((H, W), bool)
    for i in range(1, lab4.max() + 1):
        if (lab4 == i).sum() > 200:
            chemin |= lab4 == i
    inmouth = np.zeros((H, W), bool)
    inmouth[max(0, mb[1] - 10):mb[3] + 30, max(0, mb[0] - 10):mb[2] + 10] = True
    chemin |= (lum > 140) & inmouth & ~bouche & ~fleurM & ~grass
    # chemin restreint au corridor eventail + parvis bouche, hors ROIs arbres
    YYc, XXc = np.mgrid[0:H, 0:W]
    t2 = np.clip((YYc - mb[3] + 40) / max(1, (H - mb[3] + 39)), 0, 1)
    corridor = (np.abs(XXc - 424) <= (64 + t2 * 240 + 80 + t2 * 140)) & (YYc >= mb[3] - 40)
    corridor |= (np.abs(XXc - 424) < 190) & (YYc > mb[1] - 60) & (YYc < mb[3] + 40)
    chemin &= corridor & ~corebox
    # --- paroi = masse chaude haut ; rochers = autres composantes chaudes du parvis
    warm = (r >= g) & ~bouche & ~chemin & ~fleurM
    band = np.zeros((H, W), bool)
    band[:int(H * 0.68)] = True
    lab5, _ = ndi.label(warm & band)
    sizes5 = [[(lab5 == i).sum(), i] for i in range(1, lab5.max() + 1)]
    paroi = lab5 == max(sizes5)[1]
    rochM = np.zeros((H, W), bool)
    for s, i in sizes5:
        if 150 < s < 60000 and i != max(sizes5)[1]:
            ysr, xsr = np.nonzero(lab5 == i)
            if abs(xsr.mean() - 424) < 260 and ysr.mean() < mb[3] + 120:
                rochM |= lab5 == i
    # --- sol = prairie restante ; restes par zone/couleur
    sol = grass & ~canM & ~fleurM
    assigned = sol | chemin | paroi | bouche | rochM | fleurM | trunkM | canM
    rest = ~assigned
    print('restes: %.3f%%' % (100 * rest.mean()))
    sol |= rest & (g >= r)
    lower = np.mgrid[:H, :W][0] >= H * 0.62
    chemin |= rest & (g < r) & lower & corridor & ~anyroi & (lum > 120) & (r > b)
    paroi |= rest & (g < r) & ~(lower & corridor & ~anyroi & (lum > 120) & (r > b))
    masks = {'01_sol_herbe': sol, '02_chemin_sable': chemin, '03_paroi': paroi,
             '04_bouche': bouche, '05_rochers': rochM, '06_fleurs': fleurM,
             '07_troncs': trunkM, '08_canopees': canM}
    order = list(masks)
    # verif partition avant ecriture
    names = list(masks)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ov = (masks[names[i]] & masks[names[j]]).sum()
            if ov:
                print('OVERLAP', names[i], names[j], ov)
    acc = np.zeros((H, W), int)
    for m in masks.values():
        acc += m
    assert (acc == 1).all(), f'partition inexacte : min={acc.min()} max={acc.max()}'
    layers = {}
    for n, m in masks.items():
        a = np.array(Image.open(SRC / 'bruts/FINALE_map.png').convert('RGBA'))
        a[~m] = (0, 0, 0, 0)
        layers[n] = Image.fromarray(a)
        layers[n].save(OUT / f'{PFX}_{n}_jour.png')
        night(layers[n]).save(OUT / f'{PFX}_{n}_nuit.png')
    comp = Image.new('RGBA', (W, H))
    for n in order:
        comp.alpha_composite(layers[n])
    comp.save(OUT / 'composite_jour.png')
    compn = Image.new('RGBA', (W, H))
    for n in order:
        compn.alpha_composite(night(layers[n]))
    compn.save(OUT / 'composite_nuit.png')
    # sol complet : echantillons de prairie sous objets (declare, meme brut)
    rng = random.Random(5)
    cells = []
    for _ in range(4000):
        x, y = rng.randrange(W - 16), rng.randrange(int(H * 0.55), H - 16)
        if sol[y:y + 16, x:x + 16].all():
            cells.append((x, y))
        if len(cells) >= 200:
            break
    under = np.array(layers['01_sol_herbe'])
    need = canM | trunkM | fleurM
    ys2, xs2 = np.nonzero(need)
    src = np.array(Image.open(SRC / 'bruts/FINALE_map.png').convert('RGBA'))
    for y, x in zip(ys2[::1], xs2[::1]):
        cx, cy = rng.choice(cells)
        under[y, x] = src[cy + (y % 16), cx + (x % 16)]
    Image.fromarray(under).save(OUT / f'{PFX}_00_sol_complet_jour.png')
    night(Image.fromarray(under)).save(OUT / f'{PFX}_00_sol_complet_nuit.png')
    # debug couleurs
    dbg = np.zeros((H, W, 3), np.uint8)
    cols = {'01_sol_herbe': (0, 200, 0), '02_chemin_sable': (255, 220, 130), '03_paroi': (150, 110, 70),
            '04_bouche': (0, 0, 255), '05_rochers': (255, 140, 0), '06_fleurs': (255, 150, 220),
            '07_troncs': (120, 70, 30), '08_canopees': (0, 120, 0)}
    for n, m in masks.items():
        dbg[m] = cols[n]
    Image.fromarray(dbg).save('/tmp/finale_debug.png')
    man = dict(canevas=[W, H], brut='FINALE_map.png',
               sha256=hashlib.sha256((SRC / 'bruts/FINALE_map.png').read_bytes()).hexdigest(),
               bouche_bbox=[int(v) for v in mb], arbres=[[int(v) for v in b] for b in trees], nb_fleurs=int(nf), ordre=order,
               sol_complet='prairie echantillonnee 16px du meme brut sous objets (declare)',
               nuit='Abyss exact', runtime='NOT TESTED', art_approved=False)
    (OUT / 'manifest.json').write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print('OK', W, 'x', H, {n: int(m.sum()) for n, m in masks.items()})


if __name__ == '__main__':
    main()
