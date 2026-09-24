"""Entree Crooked v2 : les 8 calques generes (maquette = composite v1).

Bruts 1:1 (translation seule, jamais de resampling) : sol/chemin/paroi 848x1264
sur place ; rochers/fleurs/arbres recentres (tailles brutes differentes).
Detourage : inondation magenta depuis les bords + frange b>g.
"""
from pathlib import Path
import hashlib
import io
import json
import sys
import zipfile

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from night import night

SRC = R / 'source/entree_crooked_v2'
OUT = R / 'renders/entree_crooked_v2'
W, H = 848, 1264
PFX = 'EntreeCrookedV2'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def detour(name, fringe=3, pink=False):
    a = np.array(Image.open(SRC / 'bruts' / name).convert('RGBA')).astype(int)
    h, w = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (r > 150) & (b > 150) & (g < 100)
    # purge GLOBALE du magenta cuit : aucune couleur legitime Crooked ne matche
    # r>150&b>150&g<100 (rose fleurs : g>100) -> les trous interieurs partent aussi
    alpha = ~mag
    if fringe:
        edge = alpha & ~ndi.binary_erosion(alpha, iterations=fringe)
        if pink:
            flesh = (r > 180) & (g > 90) & (b > 90) & (r > b + 20)
            kill = edge & (b > g + 10) & ~flesh
        else:
            kill = edge & (b > g + 10)
        alpha[kill] = False
    out = np.zeros((h, w, 4), np.uint8)
    out[alpha] = np.concatenate([a[..., :3], np.full((h, w, 1), 255)], 2)[alpha]
    return Image.fromarray(out), alpha


def place(im, dx, dy):
    cv = Image.new('RGBA', (W, H))
    cv.alpha_composite(im, (dx, dy))
    return cv


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    layers, info = {}, {}
    # 01 sol : brut opaque plein cadre
    sol = Image.open(SRC / 'bruts/G_sol.png').convert('RGBA')
    assert sol.size == (W, H)
    a = np.array(sol).astype(int)
    assert not (((a[..., 0] > 150) & (a[..., 2] > 150) & (a[..., 1] < 100)).any()), 'magenta dans G_sol'
    layers['01_sol_herbe'] = sol
    info['01_sol_herbe'] = dict(brut='G_sol.png', translation=[0, 0])
    # 03/04 paroi+bouche (reference d'alignement : la bouche)
    paroi_d, _ = detour('G_paroi.png')
    P = np.array(paroi_d)
    lum = P[..., :3].mean(2)
    dark = (lum < 80) & (P[..., 3] > 0)
    lab, _ = ndi.label(dark)
    sizes = [[(lab == i).sum(), i] for i in range(1, lab.max() + 1)]
    mouth = lab == max(sizes)[1]
    ys, xs = np.nonzero(mouth)
    mcx, mcy = int(xs.mean()), int(ys.mean())
    info['bouche_ref'] = dict(centroid=[mcx, mcy], bbox=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1])
    rect = np.zeros((H, W), bool)
    rect[max(0, mcy - 150):mcy + 150, max(0, mcx - 110):mcx + 110] = True
    lab2, _ = ndi.label((lum < 110) & (P[..., 3] > 0) & rect)
    sizes2 = [[(lab2 == i).sum(), i] for i in range(1, lab2.max() + 1)]
    bouche_m = lab2 == max(sizes2)[1]
    bys, bxs = np.nonzero(bouche_m)
    info['bouche_ref']['bbox_rectifie'] = [int(bxs.min()), int(bys.min()), int(bxs.max()) + 1, int(bys.max()) + 1]
    info['bouche_ref']['entree'] = [mcx, int(bys.max()) + 12]
    paroi_m = (P[..., 3] > 0) & ~bouche_m
    la = np.zeros((H, W, 4), np.uint8)
    la[bouche_m] = P[bouche_m]
    layers['04_bouche'] = Image.fromarray(la)
    la = np.zeros((H, W, 4), np.uint8)
    la[paroi_m] = P[paroi_m]
    layers['03_paroi'] = Image.fromarray(la)
    info['03_paroi'] = dict(brut='G_paroi.png', translation=[0, 0], regle='detoure moins bouche')
    info['04_bouche'] = dict(brut='G_paroi.png', translation=[0, 0], regle='lum<110, plus grande composante du rect bouche')
    # 02 chemin : recentre sur la bouche (translation 8px)
    ch_d, _ = detour('G_chemin.png')
    C = np.array(ch_d)
    col = (C[H * 2 // 3:, :, 3] > 0)
    pcx = int(np.nonzero(col.any(0))[0].mean() + 0) if col.any() else W // 2
    xs_all = np.flatnonzero(col.any(0))
    pcx = int((xs_all.min() + xs_all.max()) / 2)
    dx = int(round((mcx - pcx) / 8) * 8)
    layers['02_chemin_sable'] = place(ch_d, dx, 0)
    info['02_chemin_sable'] = dict(brut='G_chemin.png', translation=[dx, 0], bouche_x=mcx, couloir_x_avant=pcx)
    # 05 rochers : placement par composante (translations 1:1, snap 8).
    # recentrage seul (-24,+32) : C1/C2 caches derriere la paroi -> descendus au pied ;
    # galets C3/C4 deja au seuil de la bouche -> sur place (le point d'entree passe entre eux) ;
    # eclat C5 suit C1 (meme delta, disposition relative preservee).
    ro_d, _ = detour('G_rochers.png')
    RA = np.array(ro_d)
    ropa = RA[..., 3] > 0
    rlab, rn = ndi.label(ropa)
    assert rn == 5, f'composantes rochers: {rn}'
    rcs = []
    for i in range(1, rn + 1):
        ys, xs = np.nonzero(rlab == i)
        rcs.append(dict(px=int((rlab == i).sum()), x=int(xs.min()), y=int(ys.min()), m=rlab == i))
    big = sorted([c for c in rcs if c['px'] > 10000], key=lambda c: c['x'])
    small = [c for c in rcs if c['px'] < 5000]
    assert len(big) == 2 and len(small) == 3, 'ventilation rochers inattendue'
    c1, c2 = big  # gros gauche, gros droit (triés par x)
    chip = [c for c in small if c['x'] < c1['x']]
    gals = [c for c in small if c['x'] >= c1['x']]
    assert len(chip) == 1 and len(gals) == 2, 'tri rochers inattendu'
    base = [(W - ro_d.width) // 2, (H - ro_d.height) // 2]
    plan = [(c1, (-72, 432)), (c2, (40, 392))] + [(c, (0, 0)) for c in gals] + [(chip[0], (-72, 432))]
    rock = np.zeros((H, W, 4), np.uint8)
    placed = []
    for c, (ex, ey) in plan:
        assert ex % 8 == 0 and ey % 8 == 0
        tx, ty = c['x'] + base[0] + ex, c['y'] + base[1] + ey
        sub = RA.copy()
        sub[~c['m']] = (0, 0, 0, 0)
        ys, xs = np.nonzero(c['m'])
        h0, w0 = ys.min(), xs.min()
        crop = sub[h0:ys.max() + 1, w0:xs.max() + 1]
        hh, ww = crop.shape[:2]
        assert tx >= 0 and ty >= 0 and tx + ww <= W and ty + hh <= H, 'rocher hors cadre'
        zone = rock[ty:ty + hh, tx:tx + ww]
        cm = crop[..., 3] > 0
        zone[cm] = crop[cm]
        placed.append([tx, ty])
    layers['05_rochers'] = Image.fromarray(rock)
    info['05_rochers'] = dict(brut='G_rochers.png', recentrage=base,
                             placements=[[c['px'], [c['x'] + base[0], c['y'] + base[1]], p]
                                         for c, p in [(c1, placed[0]), (c2, placed[1]),
                                                      (gals[0], placed[2]), (gals[1], placed[3]),
                                                      (chip[0], placed[4])]])
    # 06 fleurs : recentrage + suppression des touffes hors prairie
    fl_d, _ = detour('G_fleurs.png', fringe=1, pink=True)
    dxf, dyf = (W - fl_d.width) // 2, (H - fl_d.height) // 2
    fl = place(fl_d, dxf, dyf)
    F = np.array(fl)
    non_prairie = (np.array(layers['02_chemin_sable'])[:, :, 3] > 0) | \
        (np.array(layers['03_paroi'])[:, :, 3] > 0) | (np.array(layers['04_bouche'])[:, :, 3] > 0)
    lab3, n3 = ndi.label(F[:, :, 3] > 0)
    dropped, tiny, off = 0, 0, 0
    for i in range(1, n3 + 1):
        m = lab3 == i
        if m.sum() < 12:
            tiny += 1
            F[m] = (0, 0, 0, 0)
            dropped += 1
        elif (m & non_prairie).sum() / m.sum() > 0.15:
            off += 1
            F[m] = (0, 0, 0, 0)
            dropped += 1
    layers['06_fleurs'] = Image.fromarray(F)
    info['06_fleurs'] = dict(brut='G_fleurs.png', translation=[dxf, dyf],
                             touffes_total=n3, touffes_supprimees=dropped,
                             dont_minuscules=tiny, dont_hors_prairie=off)
    # 07/08 arbres : recentrage + split tronc/canopee par couleur
    ar_d, _ = detour('G_arbres.png')
    dxa, dya = (W - ar_d.width) // 2, (H - ar_d.height) // 2
    ar = place(ar_d, dxa, dya)
    A = np.array(ar).astype(int)
    opa = A[..., 3] > 0
    r, g, b = A[..., 0], A[..., 1], A[..., 2]
    can = opa & (g >= r) & (g >= b - 10)
    can = ndi.binary_dilation(can, iterations=4) & opa
    tr = opa & ~can
    la = np.zeros((H, W, 4), np.uint8)
    la[can] = np.concatenate([A[..., :3], np.full((H, W, 1), 255)], 2)[can]
    layers['08_canopees'] = Image.fromarray(la)
    la = np.zeros((H, W, 4), np.uint8)
    la[tr] = np.concatenate([A[..., :3], np.full((H, W, 1), 255)], 2)[tr]
    layers['07_troncs'] = Image.fromarray(la)
    info['07_troncs'] = dict(brut='G_arbres.png', translation=[dxa, dya], regle='non-vert')
    info['08_canopees'] = dict(brut='G_arbres.png', translation=[dxa, dya], regle='vert + contour 4px')
    order = ['01_sol_herbe', '02_chemin_sable', '05_rochers', '06_fleurs',
             '03_paroi', '04_bouche', '07_troncs', '08_canopees']
    for n, im in layers.items():
        im.save(OUT / f'{PFX}_{n}_jour.png')
        night(im).save(OUT / f'{PFX}_{n}_nuit.png')
    comp = Image.new('RGBA', (W, H))
    for n in order:
        comp.alpha_composite(layers[n])
    comp.save(OUT / 'composite_jour.png')
    compn = Image.new('RGBA', (W, H))
    for n in order:
        compn.alpha_composite(night(layers[n]))
    compn.save(OUT / 'composite_nuit.png')
    ora = io.BytesIO()
    with zipfile.ZipFile(ora, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', zipfile.ZIP_STORED)
        xml = ['<image w="%d" h="%d"><stack>' % (W, H)]
        for n, im in layers.items():
            buf = io.BytesIO()
            im.save(buf, format='PNG')
            z.writestr(f'data/{n}.png', buf.getvalue())
            xml.append(f'<layer name="{n}" src="data/{n}.png" visible="1"/>')
        xml.append('</stack></image>')
        z.writestr('stack.xml', ''.join(xml))
    (OUT / f'{PFX.lower()}.ora').write_bytes(ora.getvalue())
    # IoU informatifs vs v1 (le generateur deplace les objets : pas d'assert)
    V1 = R / 'renders/entree_crooked_v1'
    iou = {}
    for n in order:
        a1 = np.array(Image.open(V1 / f'EntreeCrookedV1_{n}_jour.png').convert('RGBA'))[:, :, 3] > 0
        a2 = np.array(layers[n])[:, :, 3] > 0
        iou[n] = round(float((a1 & a2).sum() / max(1, (a1 | a2).sum())), 3)
    man = dict(canevas=[W, H], orientation='SOUTH_TO_NORTH', maquette='renders/entree_crooked_v1/composite_jour.png',
               style='refs canoniques Crooked/Halcyon/Sky Peak (renvoi visuel, pixels regeneres)',
               bruts={f: sha(SRC / 'bruts' / f) for f in
                      ['G_sol.png', 'G_chemin.png', 'G_paroi.png', 'G_rochers.png', 'G_fleurs.png', 'G_arbres.png']},
               couches={n: 'GENERE (traduit, jamais resample)' for n in order},
               details=info, ordre=order, iou_vs_v1_informatif=iou,
               entree=info['bouche_ref']['entree'], fleurs='statiques en v2 (v1 native animee conservee)',
               nuit='Abyss exact, une fois par calque', runtime='NOT TESTED', art_approved=False)
    (OUT / 'manifest.json').write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print('translations:', {n: info[n].get('translation', info[n].get('recentrage')) for n in order})
    print('IoU vs v1:', iou)


if __name__ == '__main__':
    main()
