"""
Plage entre falaises rouges — V1
Methode hybride choisie par l'utilisateur : generation guidee par la reference
canonique arenapmdskybeach.png, puis AUDIT colorimetrique vers la palette native
de la reference (147 couleurs exactes, appariement CIEDE2000), a la maniere de
l'audit caps_terrasses_v4. NE PAS presenter ca comme une preuve de motif : la
conformite de palette ne prouve ni raccords, ni qualite de tuile, ni validation
artistique (lecon documentee dans AGENTS.md).

Calques livres : fond void (option viewer), mer (8 frames animees, silhouette
maitre commune), sable, parois falaises, bordures d'herbe, ombres objets
(calculees, signalees), objets (sprites extraits de la planche, normalises).
Versions seche (sans eau) et animee. Critere Halcyon : canvas multiple de 8,
placements sur grille 8 px, frames a taille/duree uniformes, pas de wrap.
"""
from pathlib import Path
import json, hashlib, io, base64, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage

R = Path(__file__).resolve().parents[2]          # racine du depot
O = R / 'renders/plage_rouge_v1'
B = O / 'bruts'
C = O / 'couches'
REF_PATH = R / 'arenapmdskybeach.png'

MS = 120                                          # duree uniforme par frame
VOID = np.array([39, 39, 55], float)             # fond void de la reference
TARGET_H = 512

# tailles visibles ciblees pour le decor (style PMD), en px sur le canvas
TAILLES_CIBLES = {'galet_roux': 16, 'bloc_stratifie': 34, 'amas_cailloux': 34, 'rocher_mousse': 34,
                  'galet_roux_b': 16, 'bloc_lisse': 26, 'rocher_plat': 30, 'touffe_herbe': 24,
                  'plante_littorale': 28, 'succulente': 24, 'arbrisseau_roux': 30}

# ---------------------------------------------------------------- palette --
def srgb_to_lab(rgb):
    x = rgb.astype(float) / 255.0
    mask = x <= 0.04045
    x = np.where(mask, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    X = x[..., 0] * 0.4124564 + x[..., 1] * 0.3575761 + x[..., 2] * 0.1804375
    Y = x[..., 0] * 0.2126729 + x[..., 1] * 0.7151522 + x[..., 2] * 0.0721750
    Z = x[..., 0] * 0.0193339 + x[..., 1] * 0.1191920 + x[..., 2] * 0.9503041
    Xn, Yn, Zn = 0.95047, 1.0, 1.08883
    def f(t):
        d = 6.0 / 29.0
        return np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4.0 / 29.0)
    fx, fy, fz = f(X / Xn), f(Y / Yn), f(Z / Zn)
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=-1)

def delta_e_00(lab1, lab2):
    """CIEDE2000 entre lab1 (...,3) et lab2 (N,3) -> (...,N). kL=kC=kH=1."""
    L1, a1, b1 = lab1[..., 0:1], lab1[..., 1:2], lab1[..., 2:3]
    L2, a2, b2 = lab2.T[0], lab2.T[1], lab2.T[2]
    C1 = np.hypot(a1, b1); C2 = np.hypot(a2, b2)
    Cb = (C1 + C2) / 2.0
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25.0 ** 7)))
    ap1, ap2 = a1 * (1 + G), a2 * (1 + G)
    Cp1 = np.hypot(ap1, b1); Cp2 = np.hypot(ap2, b2)
    hp1 = np.arctan2(b1, ap1) % (2 * np.pi)
    hp2 = np.arctan2(b2, ap2) % (2 * np.pi)
    dLp = L2 - L1
    dCp = Cp2 - Cp1
    dhp = hp2 - hp1
    dhp = np.where(dhp > np.pi, dhp - 2 * np.pi, dhp)
    dhp = np.where(dhp < -np.pi, dhp + 2 * np.pi, dhp)
    dhp = np.where((Cp1 * Cp2) == 0, 0.0, dhp)
    dHp = 2 * np.sqrt(np.clip(Cp1 * Cp2, 0, None)) * np.sin(dhp / 2.0)
    Lbp = (L1 + L2) / 2.0
    Cbp = (Cp1 + Cp2) / 2.0
    hsum = hp1 + hp2
    hmean = np.where((Cp1 * Cp2) == 0, hsum,
                     np.where(np.abs(hp1 - hp2) <= np.pi, hsum / 2,
                              np.where(hsum < 2 * np.pi, (hsum / 2) + np.pi, (hsum / 2) - np.pi)))
    T = (1 - 0.17 * np.cos(hmean - np.deg2rad(30)) + 0.24 * np.cos(2 * hmean)
         + 0.32 * np.cos(3 * hmean + np.deg2rad(6)) - 0.20 * np.cos(4 * hmean - np.deg2rad(63)))
    dth = np.deg2rad(30) * np.exp(-(((hmean - np.deg2rad(275)) / np.deg2rad(25)) ** 2))
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25.0 ** 7))
    Sl = 1 + (0.015 * ((Lbp - 50) ** 2)) / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -np.sin(2 * dth) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))

def charger_palette():
    ref = Image.open(REF_PATH).convert('RGB')
    rgb = np.array(ref).reshape(-1, 3)
    cols = np.unique(rgb, axis=0)
    return cols, srgb_to_lab(cols)

def quantifier(rgba, pal_rgb, pal_lab):
    """Remplace chaque pixel opaque par la couleur native la plus proche (dE00).
    Les pixels semi-transparents (ombres calculees) ne sont pas touches."""
    out = rgba.copy()
    op = rgba[:, :, 3] == 255
    pix = rgba[op][:, :3]
    if len(pix) == 0:
        return out, {'n': 0}
    lab = srgb_to_lab(pix)
    dmin = np.full(len(pix), 1e9); idx = np.zeros(len(pix), np.int64)
    CH = 4096
    for i in range(0, len(pix), CH):
        d = delta_e_00(lab[i:i + CH], pal_lab)
        idx[i:i + CH] = d.argmin(1); dmin[i:i + CH] = d[np.arange(len(d)), d.argmin(1)]
    out[op, 0:3] = pal_rgb[idx]
    return out, {'n': int(len(pix)), 'dE_moy': float(dmin.mean()), 'dE_p95': float(np.percentile(dmin, 95)), 'dE_max': float(dmin.max())}

# ------------------------------------------------------------- extraction --
def flood_magenta(rgb, seuil_large=140.0, seuil_serre=40.0):
    """Zone magenta : inondation depuis les bords + seuil serre global (lecon V16).
    AUCUN fill_holes (lecon V9)."""
    d = np.linalg.norm(rgb.astype(float) - np.array([255.0, 0.0, 255.0]), axis=2)
    cand = d < seuil_large
    bord = np.zeros_like(cand); bord[0, :] = bord[-1, :] = bord[:, 0] = bord[:, -1] = True
    inonde = ndimage.binary_propagation(bord & cand, mask=cand)
    return inonde | (d < seuil_serre)

def normaliser(im, tw, th):
    return np.array(im.resize((tw, th), Image.Resampling.NEAREST))

def couche_transparente(h, w):
    return np.zeros((h, w, 4), np.uint8)

# ------------------------------------------------------------------ build --
def construire():
    for d in ['couches/mer_frames', 'review', 'scene', 'ora', 'sprites_pack', 'exports']:
        (O / d).mkdir(parents=True, exist_ok=True)

    pal_rgb, pal_lab = charger_palette()
    np.save(O / 'review' / 'palette_native.npy', pal_rgb)
    sw = Image.new('RGB', (8 * 8, 19 * 8))
    for i, c in enumerate(pal_rgb):
        x0, y0 = (i % 8) * 8, (i // 8) * 8
        for yy in range(8):
            for xx in range(8):
                sw.putpixel((x0 + xx, y0 + yy), tuple(c))
    sw.save(O / 'review' / 'palette_native.png')

    brut_t = Image.open(B / 'terrain_magenta.png').convert('RGB')
    Wb, Hb = brut_t.size
    TW = int(round(TARGET_H * Wb / Hb / 8.0)) * 8
    TH = TARGET_H
    t = normaliser(brut_t, TW, TH)
    mask_mer = flood_magenta(t)
    mask_terrain = ~mask_mer

    r, g, b = t[:, :, 0].astype(int), t[:, :, 1].astype(int), t[:, :, 2].astype(int)
    herbe = mask_terrain & (g > r + 8) & (g > b + 8) & (g > 60)
    sable = mask_terrain & (~herbe) & (r > 165) & (g > 135) & ((g - b) > 40) & ((r - g) < 75)
    falaise = mask_terrain & (~herbe) & (~sable)

    def pose_mask(mask):
        a = couche_transparente(TH, TW)
        a[:, :, :3] = t
        a[:, :, 3] = np.where(mask, 255, 0)
        return a

    lay_sable = pose_mask(sable)
    lay_falaise = pose_mask(falaise)
    lay_herbe = pose_mask(herbe)

    # ----- mer : silhouette maitre = zone magenta du terrain
    ys, xs = np.where(mask_mer)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    patch_w, patch_h = x1 - x0, y1 - y0

    # la pose peinte mer_f0 est reservee a l'export statique (verif d'alignement)
    brut_f0 = Image.open(B / 'mer_f0.png').convert('RGB')
    f0n = normaliser(brut_f0, TW, TH)
    diff = np.abs(f0n.astype(int) - t.astype(int)).max(2) > 40
    ratio = float(diff[mask_terrain].mean())
    aligne = ratio <= 0.03

    # extraction des 8 cellules de la planche 2x4
    pl = Image.open(B / 'vagues_8frames.png').convert('RGB')
    pw, ph = pl.size
    pa = np.array(pl)
    poses = []
    for k in range(8):
        col, lig = k % 2, k // 2
        cell = pa[lig * ph // 4:(lig + 1) * ph // 4, col * pw // 2:(col + 1) * pw // 2]
        d = np.linalg.norm(cell.astype(float) - np.array([255., 0., 255.]), axis=2)
        ink = d > 110
        lab, n = ndimage.label(ndimage.binary_dilation(ink, iterations=4))
        if n == 0:
            continue
        tailles = ndimage.sum(ink, lab, range(1, n + 1))
        big = 1 + int(np.argmax(tailles))
        comp = ndimage.binary_erosion(lab == big, iterations=4)
        yy, xx = np.where(comp)
        if len(yy) == 0:
            en = cell
        else:
            cy0, cy1, cx0, cx1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
            en = cell[cy0:cy1, cx0:cx1]
        poses.append(normaliser(Image.fromarray(en), patch_w, patch_h).astype(float))
    nb_cellules = len(poses)

    # reordonnancement optimal : cycle Hamiltonien qui minimise le plus grand
    # saut entre frames consecutives (meme methode d'esprit que les fondus V11)
    import itertools
    N = len(poses)
    D = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            D[i, j] = np.abs(poses[i] - poses[j]).mean() if i != j else 0.0
    best, best_score = None, 1e18
    for perm in itertools.permutations(range(N)):
        seg = [D[perm[k], perm[(k + 1) % N]] for k in range(N)]
        score = max(seg) * 1000 + sum(seg)
        if score < best_score:
            best_score, best = score, perm
    poses = [poses[i] for i in best]
    sauts = [float(D[best[k], best[(k + 1) % N]]) for k in range(N)]

    # poses + fondus premultiplies 50 % -> 2N frames uniformes
    frames = []
    for k in range(N):
        a = poses[k]
        bb = poses[(k + 1) % N]
        frames.append(np.clip(a, 0, 255).astype(np.uint8))
        frames.append(np.clip(a * 0.5 + bb * 0.5, 0, 255).astype(np.uint8))
    NF = len(frames)

    lay_mer = []
    for f in frames:
        a = couche_transparente(TH, TW)
        a[y0:y1, x0:x1, :3] = f
        a[:, :, 3] = np.where(mask_mer, 255, 0)
        lay_mer.append(a)

    lay_mer_peinte = None
    if aligne:
        lay_mer_peinte = couche_transparente(TH, TW)
        lay_mer_peinte[:, :, :3] = f0n
        lay_mer_peinte[:, :, 3] = np.where(mask_mer, 255, 0)

    # ----- sprites deco : extraction + normalisation vers tailles cibles
    sp = np.array(Image.open(B / 'sprites_deco.png').convert('RGB'))
    dd = np.linalg.norm(sp.astype(float) - np.array([255., 0., 255.]), axis=2)
    ink = dd > 110
    lab, n = ndimage.label(ndimage.binary_dilation(ink, iterations=6))
    bruts_items = []
    for i in range(1, n + 1):
        comp = ndimage.binary_erosion(lab == i, iterations=6)
        yy, xx = np.where(comp)
        if len(yy) < 250:
            continue
        cy0, cy1, cx0, cx1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
        sub = sp[cy0:cy1, cx0:cx1]
        subd = np.linalg.norm(sub.astype(float) - np.array([255., 0., 255.]), axis=2)
        alpha = np.where(subd > 100, 255, 0).astype(np.uint8)
        alpha = ndimage.binary_opening(alpha > 0, iterations=1).astype(np.uint8) * 255
        bruts_items.append({'bbox': (int(cx0), int(cy0), int(cx1), int(cy1)),
                            'rgba': np.dstack([sub, alpha])})
    bruts_items.sort(key=lambda it: (it['bbox'][1] // 200, it['bbox'][0]))
    noms = ['galet_roux', 'bloc_stratifie', 'amas_cailloux', 'rocher_mousse',
            'galet_roux_b', 'bloc_lisse', 'rocher_plat', 'touffe_herbe',
            'plante_littorale', 'succulente', 'arbrisseau_roux']
    items = []
    for i, it in enumerate(bruts_items):
        nom = noms[i] if i < len(noms) else f'objet_{i:02d}'
        aim = TAILLES_CIBLES.get(nom, 24)
        h0, w0 = it['rgba'].shape[:2]
        tw = aim
        th = max(8, int(round(h0 * aim / w0)))
        resized = np.array(Image.fromarray(it['rgba'], 'RGBA').resize((tw, th), Image.Resampling.NEAREST))
        items.append({'nom': nom, 'rgba': resized})
        Image.fromarray(resized, 'RGBA').save(O / 'sprites_pack' / f"{i:02d}_{nom}.png")

    # ----- placements (grille 8 px), valides dans le bon domaine
    def round8(v): return int(round(v / 8.0)) * 8
    def libre(mask, x, y, w, h):
        if x < 0 or y < 0 or x + w > mask.shape[1] or y + h > mask.shape[0]:
            return False
        return bool(mask[y:y + h, x:x + w].all())

    def placer(nom, xr, yr, domaine, prefer=None):
        it = next((e for e in items if e['nom'] == nom), None)
        if it is None:
            return None
        h, w = it['rgba'].shape[:2]
        essais = []
        base_x, base_y = round8(TW * xr), round8(TH * yr)
        essais.append((base_x, base_y))
        for dy in range(0, 120, 16):
            for dx in range(-64, 65, 16):
                essais.append((round8(base_x + dx), round8(base_y + dy)))
        for (x, y) in essais:
            if libre(domaine, x, y, w, h):
                return {'nom': nom, 'x': x, 'y': y, 'w': w, 'h': h,
                        'sur_eau': bool(domaine is mask_mer), 'grille8': (x % 8 == 0 and y % 8 == 0)}
        return None

    placements = [p for p in [
        placer('rocher_mousse', 0.56, 0.10, mask_mer),
        placer('bloc_lisse', 0.33, 0.17, mask_mer),
        placer('amas_cailloux', 0.10, 0.42, sable),
        placer('galet_roux', 0.70, 0.40, sable),
        placer('rocher_plat', 0.44, 0.68, sable),
        placer('touffe_herbe', 0.13, 0.30, sable),
        placer('plante_littorale', 0.88, 0.29, sable),
        placer('arbrisseau_roux', 0.90, 0.55, sable),
    ] if p is not None]

    lay_objets = couche_transparente(TH, TW)
    lay_ombres = couche_transparente(TH, TW)
    for p in placements:
        it = next(e for e in items if e['nom'] == p['nom'])
        x, y, w, h = p['x'], p['y'], p['w'], p['h']
        tile = lay_objets[y:y + h, x:x + w]
        op = it['rgba'][:, :, 3] == 255
        tile[op] = it['rgba'][op]
        lay_objets[y:y + h, x:x + w] = tile
        if not p['sur_eau']:                                # ombre de contact CALCULEE (signalee)
            yyg, xxg = np.mgrid[0:TH, 0:TW]
            rx, ry = max(6, w // 2), max(3, h // 6)
            cx, cy = x + w // 2, y + h - 2
            el = ((xxg - cx) / float(rx)) ** 2 + ((yyg - cy) / float(ry)) ** 2 <= 1.0
            m = el & sable
            lay_ombres[m, :3] = 0
            lay_ombres[m, 3] = np.maximum(lay_ombres[m, 3], 72)

    # ----- quantification palette canonique
    audit = {}
    lay_sable, audit['sable'] = quantifier(lay_sable, pal_rgb, pal_lab)
    lay_falaise, audit['falaises'] = quantifier(lay_falaise, pal_rgb, pal_lab)
    lay_herbe, audit['bordures_herbe'] = quantifier(lay_herbe, pal_rgb, pal_lab)
    lay_objets, audit['objets'] = quantifier(lay_objets, pal_rgb, pal_lab)
    lay_mer_q = []
    for i, a in enumerate(lay_mer):
        q, st = quantifier(a, pal_rgb, pal_lab)
        lay_mer_q.append(q); audit[f'mer_f{i:02d}'] = st
    if lay_mer_peinte is not None:
        lay_mer_peinte, audit['mer_pose_peinte'] = quantifier(lay_mer_peinte, pal_rgb, pal_lab)
    audit['_note'] = 'conformite palette != preuve de motif/art ; ombres non quantifiees (alpha calcule)'

    # ----- sortie calques
    fond = np.zeros((TH, TW, 4), np.uint8)
    fond[:, :, :3] = VOID.astype(np.uint8); fond[:, :, 3] = 255
    Image.fromarray(fond, 'RGBA').save(C / '00_fond_void.png')

    for i, a in enumerate(lay_mer_q):
        Image.fromarray(a, 'RGBA').save(C / 'mer_frames' / f'MerV1_{i:02d}.png')
    ordre = [('02_sable', lay_sable), ('03_parois_falaises', lay_falaise),
             ('04_bordures_herbe', lay_herbe), ('05_ombres_objets', lay_ombres), ('06_objets', lay_objets)]
    for n, a in ordre:
        Image.fromarray(a, 'RGBA').save(C / f'{n}.png')

    def compose(avec_mer=True, f=0, avec_fond=True, mer=None):
        base = Image.fromarray(fond if avec_fond else couche_transparente(TH, TW), 'RGBA')
        if avec_mer:
            base.alpha_composite(Image.fromarray(mer if mer is not None else lay_mer_q[f % NF], 'RGBA'))
        for _, a in ordre:
            base.alpha_composite(Image.fromarray(a, 'RGBA'))
        return base

    for f in range(NF):
        compose(True, f).save(O / 'scene' / f'scene_anim_{f:02d}.png')
    compose(False).save(O / 'scene' / 'scene_seche.png')
    if lay_mer_peinte is not None:
        compose(True, 0, mer=lay_mer_peinte).save(O / 'exports' / 'scene_pose_peinte.png')
        Image.fromarray(lay_mer_peinte, 'RGBA').save(C / '01_mer_pose_peinte.png')

    sc = [compose(True, f) for f in range(NF)]
    sc[0].save(O / 'scene_anim16f.webp', save_all=True, append_images=sc[1:], duration=MS, loop=0, lossless=True, method=4)
    pal_img = Image.new('RGB', (TW, TH * NF))
    for i, s in enumerate(sc):
        pal_img.paste(s.convert('RGB'), (0, TH * i))
    q = pal_img.quantize(colors=256)
    gs = [s.convert('RGB').quantize(palette=q, dither=Image.Dither.NONE) for s in sc]
    gs[0].save(O / 'review' / 'scene_anim.gif', save_all=True, append_images=gs[1:], duration=MS, loop=0, disposal=1, optimize=False)
    sheet = Image.new('RGBA', (TW // 2 * 4, TH // 2 * 4), (24, 24, 40, 255))
    for i, s in enumerate(sc):
        sheet.alpha_composite(s.resize((TW // 2, TH // 2), Image.Resampling.NEAREST), ((i % 4) * TW // 2, (i // 4) * TH // 2))
    sheet.save(O / 'review' / 'planche_16frames.png')
    dbg = np.zeros((TH, TW, 3), np.uint8)
    dbg[sable] = (255, 220, 120); dbg[falaise] = (200, 60, 60); dbg[herbe] = (60, 220, 80); dbg[mask_mer] = (60, 120, 255)
    Image.fromarray(dbg).save(O / 'review' / 'masques_debug.png')
    imgs = [fond] + lay_mer_q + [a for _, a in ordre]
    lq = Image.new('RGBA', (TW // 2 * 4, TH // 2 * 4), (40, 40, 60, 255))
    for i, a in enumerate(imgs[:16]):
        lq.alpha_composite(Image.fromarray(a).resize((TW // 2, TH // 2), Image.Resampling.NEAREST),
                           ((i % 4) * TW // 2, (i // 4) * TH // 2))
    lq.convert('RGB').save(O / 'review' / 'planche_calques.png')

    # ----- ORA (stack.xml conforme : image w/h, layer x/y)
    def ordpng(a):
        b_ = io.BytesIO(); Image.fromarray(a, 'RGBA').save(b_, format='PNG'); return b_.getvalue()
    ora_layers = (ordre[::-1] + [(f'01_mer_f{i:02d}', lay_mer_q[i]) for i in range(NF)]
                  + [('00_fond_void', fond)])
    stack = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<image w="{TW}" h="{TH}" name="plage_rouge_v1"><stack>']
    with zipfile.ZipFile(O / 'ora' / 'plage_rouge_v1.ora', 'w') as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for nom, _a in ora_layers:
            vis = 'hidden' if (nom.startswith('01_mer') and nom != '01_mer_f00') else 'visible'
            stack.append(f'  <layer name="{nom}" src="data/{nom}.png" x="0" y="0" visibility="{vis}" composite-op="svg:src-over" opacity="1.0" />')
            z.writestr(f'data/{nom}.png', ordpng(_a))
        stack.append('</stack></image>')
        z.writestr('stack.xml', '\n'.join(stack))
        th = np.array(compose(True, 0).resize((64, round(64 * TH / TW)), Image.Resampling.NEAREST))
        z.writestr('Thumbnails/thumbnail.png', ordpng(th))

    # ----- viewer
    def uri(im):
        b_ = io.BytesIO()
        if isinstance(im, np.ndarray):
            Image.fromarray(im, 'RGBA').save(b_, format='PNG')
        else:
            im.save(b_, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(b_.getvalue()).decode()
    donnees = {'W': TW, 'H': TH, 'ms': MS, 'fond': uri(fond),
               'mer': [uri(a) for a in lay_mer_q],
               'calques': [{'nom': n, 'png': uri(a)} for n, a in ordre],
               'palette': uri(sw)}
    tpl = (R / 'source/plage_rouge_v1/viewer_template.html').read_text()
    (R / 'apercu_plage_rouge_v1.html').write_text(tpl.replace('__DATA__', json.dumps(donnees)))

    manifest = {
        'lot': 'plage_rouge_v1',
        'choix_utilisateur': {'map': 'plage falaises rouges (arenapmdskybeach)',
                              'methode': 'hybride : generation + quantification palette canonique 147 couleurs (CIEDE2000)',
                              'animations': 'seche + animee (8 phases d eau)', 'format': 'standard'},
        'canvas': [TW, TH], 'grille_px': 8,
        'normalisation': f'brut {Wb}x{Hb} -> {TW}x{TH} NEAREST (ratio natif, arrondi 8)',
        'palette_native': {'source': 'arenapmdskybeach.png', 'couleurs': int(len(pal_rgb))},
        'mer_f0_aligne_sur_terrain': aligne, 'mer_f0_terrain_diff_ratio': ratio,
        'frames_mer': {'n': NF, 'poses_planche': nb_cellules, 'fondus_50pct': int(NF - nb_cellules),
                       'ordre_optimise': list(map(int, best)), 'sauts_moyens_rgb': sauts,
                       'duree_ms': MS, 'silhouette': 'masque maitre commun',
                       'boucle': 'cycle propose (poses reordonnees + fondus), pas le cycle officiel PMD'},
        'ombres': 'calculees (ellipses alpha 72, sable uniquement), PAS textures natives',
        'placements': placements,
        'audit_palette': audit,
        'bruts_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(B.glob('*.png'))},
        'reference_sha256': hashlib.sha256(REF_PATH.read_bytes()).hexdigest(),
        'limites': ['pixels generes quantifies, pas tuiles natives Metano', 'art non approuve',
                    'cycle eau propose, pas natif', 'runtime/PMDO/collisions NON TESTES'],
    }
    (O / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print('canvas', TW, TH, '| sprites', len(items), '| placements', len(placements),
          '| f0 aligné', aligne, f'(diff {ratio:.4f})', '| cellules', nb_cellules)
    print('audit sable', audit['sable'], '| mer_f0', audit['mer_f00'])

if __name__ == '__main__':
    construire()
