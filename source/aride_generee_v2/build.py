"""Aride generee V2 — terrain d'entree aride recompose au generateur.

Reference canonique : entrancearidedungeonpmdsky.png (408x288).
Methode rendus generes : 4 bruts generateur -> downscale /3 BOX -> detourage
magenta (seuil global + pelage) -> couches separees -> assemblage 400x360
+ FX poussiere 12 frames.
Les textures sont GENEREES guidees par la reference, PAS des pixels natifs.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import label, binary_opening

R = Path(__file__).resolve().parents[2]
SRC = R / 'source/aride_generee_v2/bruts'
OUT = R / 'renders/aride_generee_v2'
CW, CH = 400, 360  # 50x45 cellules de 8 px
NFRAMES, FRAMEMS = 12, 100
NOCOLORS = 128  # quantification douce du grain genere (0 = off)
MAG = np.array([255, 0, 255])
BAYER8 = (np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) + 0.5) / 64.0


def down3(im):
    w, h = im.size
    return im.resize((w // 3, h // 3), Image.BOX)


def magdist(rgb):
    return np.abs(rgb.astype(int) - MAG).sum(axis=2)


def cut_magenta(rgb):
    """Fond magenta -> alpha. Seuil global d<170 (aucun rose interieur :
    roche/sable/arbres/poussiere tous a d>300), puis pelage de 2 anneaux
    de frange rose (d<230) au contact du transparent, puis 1 passe de
    recopie voisin pour le dernier anneau."""
    h, w, _ = rgb.shape
    alpha = np.where(magdist(rgb) < 170, 0, 255).astype(np.uint8)
    for _ in range(2):
        op = alpha > 0
        edge = op & ((np.roll(~op, 1, 0)) | (np.roll(~op, -1, 0))
                     | (np.roll(~op, 1, 1)) | (np.roll(~op, -1, 1)))
        peel = edge & (magdist(rgb) < 230)
        if not peel.any():
            break
        alpha[peel] = 0
    # dernier anneau : recopie du voisin opaque non-rose le plus proche
    op = alpha > 0
    edge = op & ((np.roll(~op, 1, 0)) | (np.roll(~op, -1, 0))
                 | (np.roll(~op, 1, 1)) | (np.roll(~op, -1, 1)))
    ys, xs = np.where(edge & (magdist(rgb) < 230))
    fixed = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        for rr in range(1, 7):
            done = False
            for dy in range(-rr, rr + 1):
                for dx in range(-rr, rr + 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and alpha[yy, xx] and magdist(rgb)[yy, xx] >= 230:
                        rgb[y, x] = rgb[yy, xx]
                        fixed += 1
                        done = True
                        break
                if done:
                    break
            if done:
                break
    return alpha, fixed


def quantize_rgb(im, colors):
    if not colors:
        return im
    return im.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB')


def prep(brut_path, crop=None):
    im = Image.open(brut_path).convert('RGB')
    if crop:
        im = im.crop(crop)
    im = quantize_rgb(down3(im), NOCOLORS)
    rgb = np.array(im).astype(int)
    alpha, fixed = cut_magenta(rgb)
    im = quantize_rgb(Image.fromarray(rgb.astype(np.uint8)), NOCOLORS)
    im.putalpha(Image.fromarray(alpha))
    return im, alpha, fixed


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'couches').mkdir(exist_ok=True)
    (OUT / 'fx').mkdir(exist_ok=True)
    (OUT / 'compos_anim').mkdir(exist_ok=True)
    log = {}
    # --- SOL ---
    sand = quantize_rgb(down3(Image.open(SRC / 'sol_sable.png').convert('RGB')), NOCOLORS)
    assert sand.size == (408, 288), sand.size
    # --- PAROIS ---
    wall_small, w_alpha, w_fix = prep(SRC / 'parois_grotte.png', crop=(0, 0, 1200, 894))
    assert wall_small.size == (400, 298), wall_small.size
    log['wall_defringe_px'] = w_fix
    # bouche = plus grande masse sombre APRES ouverture 5x5
    dark = (np.array(wall_small.convert('RGB')).astype(int).sum(axis=2) < 220) & (w_alpha > 0)
    opened = binary_opening(dark, structure=np.ones((5, 5)))
    lab, n = label(opened)
    sizes = [(np.count_nonzero(lab == i), i) for i in range(1, n + 1)]
    sizes.sort(reverse=True)
    my, mx = np.where(lab == sizes[0][1])
    mouth = dict(x0=int(mx.min()), x1=int(mx.max()), y0=int(my.min()), y1=int(my.max()))
    log['mouth'] = mouth
    # --- ASSEMBLAGE ---
    ground = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    ground.paste(sand.crop((4, 0, 404, 288)), (0, 72))  # couvre y72-360
    mouth_dark = np.array(wall_small.convert('RGB'))[opened]
    ceil = tuple(int(v) for v in np.median(mouth_dark, axis=0)) if len(mouth_dark) else (20, 14, 18)
    back = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    ba = np.array(back)
    ba[:40, :, :3] = ceil
    ba[:40, :, 3] = 255
    back = Image.fromarray(ba)
    back.save(OUT / 'couches/00_plafond.png')
    log['ceiling_color'] = ceil
    wall_layer = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    wall_layer.paste(wall_small, (0, 0))
    wl = np.array(wall_layer)
    gl = np.array(ground)
    H0, H1 = 220, 236
    for y in range(H0, H1):
        t = (y - H0 + 0.5) / (H1 - H0)
        row = np.tile(BAYER8[y % 8], CW // 8 + 1)[:CW]
        m = (row < t) & (wl[y, :, 3] > 0)
        wl[y, m] = gl[y, m]
    wl[H1:, :, 3] = 0
    wall_layer = Image.fromarray(wl)
    ground.save(OUT / 'couches/00_sol.png')
    wall_layer.save(OUT / 'couches/01_parois.png')
    log['blend_band'] = [H0, H1]
    # --- PROPS ---
    pbrut, palpha, p_fix = prep(SRC / 'props_arbres_blocs.png')
    log['props_defringe_px'] = p_fix
    plab, pn = label(palpha > 0)
    boxes = []
    for i in range(1, pn + 1):
        ys, xs = np.where(plab == i)
        if len(xs) > 300:
            boxes.append(dict(x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max())))
    assert len(boxes) == 8, f'{len(boxes)} props: {boxes}'
    boxes.sort(key=lambda b: (b['y0'] // 140, b['x0']))
    names = ['grandA', 'moyenA', 'arbusteA', 'blocA', 'grandB', 'moyenB', 'arbusteB', 'blocB']
    order = list(range(8))  # tri (rangee,x) = grand, moyen, arbuste, bloc
    ordered = [boxes[i] for i in order]
    props = {}
    for nm, b in zip(names, ordered):
        props[nm] = dict(bbox=b, sprite=pbrut.crop((b['x0'], b['y0'], b['x1'] + 1, b['y1'] + 1)))
    log['props_boxes'] = {k: v['bbox'] for k, v in props.items()}
    feet = dict(grandA=(56, 320), grandB=(336, 312), moyenA=(40, 224), moyenB=(360, 248),
                arbusteA=(80, 208), arbusteB=(248, 208), blocA=(56, 240), blocB=(304, 224))
    for nm, (fx, fy) in feet.items():
        assert fx % 8 == 0 and fy % 8 == 0, nm
    prop_layers = {}
    for nm in names:
        sp = props[nm]['sprite']
        fx, fy = feet[nm]
        lay = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        lay.paste(sp, (fx - sp.width // 2, fy - sp.height), sp)
        lay.save(OUT / f'couches/02_prop_{nm}.png')
        prop_layers[nm] = lay
    log['props_feet'] = feet
    sheet = Image.new('RGBA', (408, 288), (0, 0, 0, 0))
    sheet.paste(pbrut, (0, 0), pbrut)
    sheet.save(OUT / 'planche_props.png')
    # --- FX POUSSIERE ---
    dbrut, dalpha, d_fix = prep(SRC / 'fx_poussiere.png')
    log['fx_defringe_px'] = d_fix
    bands = [dict(y0=0, y1=100, speed=48, yy=250), dict(y0=100, y1=190, speed=72, yy=290),
             dict(y0=190, y1=288, speed=36, yy=212)]
    fx_frames = []
    for f in range(NFRAMES):
        lay = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        shimmer = (150 + 25 * np.sin(2 * np.pi * f / NFRAMES)) / 255.0
        for b in bands:
            band = dbrut.crop((4, b['y0'], 404, b['y1']))
            off = (b['speed'] * f) // NFRAMES
            for x in (off, off - CW):
                lay.paste(band, (x, b['yy'] - band.height // 2), band)
        la = np.array(lay)
        la[:, :, 3] = (la[:, :, 3].astype(float) * shimmer).astype(np.uint8)
        lay = Image.fromarray(la)
        lay.save(OUT / f'fx/fx_{f:02d}.png')
        fx_frames.append(lay)
    log['fx'] = dict(frames=NFRAMES, ms=FRAMEMS, bands=bands)
    # --- COMPOSITE ---
    comp = back.copy()
    comp = Image.alpha_composite(comp, ground)
    comp = Image.alpha_composite(comp, wall_layer)
    for nm in sorted(names, key=lambda n: feet[n][1]):
        comp = Image.alpha_composite(comp, prop_layers[nm])
    comp0 = Image.alpha_composite(comp, fx_frames[0])
    comp0.save(OUT / 'composite.png')
    for f, fx in enumerate(fx_frames):
        Image.alpha_composite(comp, fx).save(OUT / f'compos_anim/c_{f:02d}.png')
    # --- SENTIER ---
    ga = np.array(ground.convert('RGB')).astype(int)
    path = []
    for y in range(220, CH, 4):
        row = ga[y, 110:270, :].sum(axis=1)
        path.append([110 + int(np.argmax(row)), y])
    xs = np.array([p[0] for p in path])
    xs = np.array([np.median(xs[max(0, i - 2):i + 3]) for i in range(len(xs))]).astype(int)
    path = [[int(x), y] for x, y in zip(xs, range(220, CH, 4))]
    mcx = (mouth['x0'] + mouth['x1']) // 2
    path = [[mcx, mouth['y1'] + 6], [mcx + 25, mouth['y1'] + 14]] + path
    ov = comp0.copy()
    from PIL import ImageDraw
    dr = ImageDraw.Draw(ov)
    dr.line([tuple(p) for p in path], fill=(255, 140, 0), width=2)
    dr.ellipse([path[0][0] - 5, path[0][1] - 5, path[0][0] + 5, path[0][1] + 5], outline=(255, 60, 60), width=2)
    dr.ellipse([path[-1][0] - 6, path[-1][1] - 6, path[-1][0] + 6, path[-1][1] + 6], outline=(80, 255, 80), width=2)
    ov.save(OUT / 'access_review.png')
    manifest = dict(canvas=[CW, CH], grid=8, frames=NFRAMES, frame_ms=FRAMEMS,
                    reference='entrancearidedungeonpmdsky.png',
                    method='generateur guide par reference canonique, PAS pixels natifs',
                    ceiling_color=ceil, mouth=mouth, path=path, feet=feet, log=log)
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('mouth', mouth, 'defringe', w_fix, p_fix, d_fix)
    print('path top/bottom', path[0], path[-1])


if __name__ == '__main__':
    main()
