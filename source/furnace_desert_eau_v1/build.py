"""Furnace Desert (PMD Rescue Team) en biome EAU — calques PNG séparés et animations.

Demande : remplacer tout le sable par de l'eau sur son propre calque, animée, ainsi que le siphon.
Sources :
  - scène : references/furnace_desert_rt_original_456x336.png (voir provenance dans le README) ;
  - eau : mer native animée de large.D25P11A.gif (30 phases x 130 ms, racine du dépôt) ;
    tuile de haute mer doublement périodique extraite par consensus (réseau (48,48) & (144,72)) ;
  - rythme de siphon : cycle de palette natif de large.D14P11A.gif (6 phases, fonction couleur->couleur).
Transformations assumées (biome swap demandé) : les teintes de sable du siphon et des cascades sont
remplacées par des bleus pris dans la palette native de la mer D25 (aucune couleur inventée pour l'eau) ;
les roches, le ciel et le premier plan gardent leurs pixels source exacts.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from segment import REFERENCE, segment  # noqa: E402

OUT = ROOT / 'renders/furnace_desert_eau_v1'
PREFIX = 'FDE_V1'
D25 = ROOT / 'large.D25P11A.gif.1859d89ca99571b9d779dbb182a1b681.gif'
D14 = ROOT / 'large.D14P11A.gif.de6fb5fd180b164fe8a67715f1d7ee5c.gif'
FRAMES, TICK_MS = 30, 130          # cadence native de la mer D25
SEA_REGION = (0, 330, 200, 504)    # haute mer propre de D25 (x0, y0, x1, y1)
LATTICE_X, LATTICE_Y = 48, 72      # domaine fondamental : (x mod 48, (y - 48*(x//48)) mod 72)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def gif_frames(path):
    im = Image.open(path)
    out = []
    for i in range(im.n_frames):
        im.seek(i)
        out.append(np.array(im.convert('RGB')))
    return np.stack(out), im.info.get('duration')


def lattice_index(x, y):
    return x % LATTICE_X, (y - LATTICE_X * (x // LATTICE_X)) % LATTICE_Y


def sea_tile():
    """Tuile 48x72 x 30 phases : couleur majoritaire de chaque classe du réseau (pixels natifs)."""
    F, dur = gif_frames(D25)
    assert F.shape[0] == FRAMES and dur == TICK_MS
    x0, y0, x1, y1 = SEA_REGION
    reg = F[:, y0:y1, x0:x1].astype(np.int64)
    blue = (reg[0, ..., 2] > reg[0, ..., 0] + 40) & (reg[0, ..., 2] > reg[0, ..., 1])
    yy, xx = np.nonzero(blue)
    ix, iy = lattice_index(xx + x0, yy + y0)
    cls = iy * LATTICE_X + ix
    tile = np.zeros((FRAMES, LATTICE_Y, LATTICE_X, 3), np.uint8)
    agree = []
    for t in range(FRAMES):
        key = reg[t, yy, xx, 0] * 65536 + reg[t, yy, xx, 1] * 256 + reg[t, yy, xx, 2]
        best = np.zeros(LATTICE_X * LATTICE_Y, np.int64)
        order = np.lexsort((key, cls))
        c_s, k_s = cls[order], key[order]
        cut = np.flatnonzero(np.diff(c_s * (1 << 25) + k_s)) + 1
        starts = np.r_[0, cut]
        counts = np.diff(np.r_[starts, len(c_s)])
        g_cls, g_key = c_s[starts], k_s[starts]
        bestn = np.zeros(LATTICE_X * LATTICE_Y, np.int64)
        for c, k, n in zip(g_cls, g_key, counts):
            if n > bestn[c]:
                bestn[c], best[c] = n, k
        assert (bestn > 0).all(), 'classe du réseau non couverte'
        tile[t] = np.stack([(best >> 16) & 255, (best >> 8) & 255, best & 255], -1).reshape(LATTICE_Y, LATTICE_X, 3)
        agree.append(float((key == best[cls]).mean()))
    return tile, {'consensus_agreement_min': min(agree), 'consensus_agreement_mean': float(np.mean(agree)),
                  'samples': int(len(cls))}


def sea_palette(tile):
    u = np.unique(tile.reshape(-1, 3), axis=0)
    lum = 0.299 * u[:, 0] + 0.587 * u[:, 1] + 0.114 * u[:, 2]
    return u[np.argsort(lum)]


def d14_cycle():
    """Cycle natif du siphon D14 : ordre des couleurs parcourues par un pixel sur les 6 phases."""
    F, dur = gif_frames(D14)
    x, y, w, h = 370, 168, 60, 48
    reg = F[:, y:y + h, x:x + w].reshape(F.shape[0], -1, 3).astype(np.int64)
    keys = reg[..., 0] * 65536 + reg[..., 1] * 256 + reg[..., 2]
    for t in range(1, F.shape[0]):     # vérifie : animation = pure fonction couleur -> couleur
        m = {}
        assert all(m.setdefault(a, b) == b for a, b in zip(keys[0], keys[t]))
    # pixel le plus fréquent du centre de l'anneau : sa séquence de couleurs = le cycle
    cyc_counts = {}
    for i in range(keys.shape[1]):
        seq = tuple(keys[:, i])
        if len(set(seq)) == F.shape[0]:
            cyc_counts[seq] = cyc_counts.get(seq, 0) + 1
    seq = max(cyc_counts, key=cyc_counts.get)
    rgb = [((k >> 16) & 255, (k >> 8) & 255, k & 255) for k in seq]
    return rgb, dur


def build():
    seg = segment()
    src = seg['rgba']
    H, W = src.shape[:2]
    assert W % 8 == 0 and H % 8 == 0
    tile, tile_stats = sea_tile()
    pal = sea_palette(tile)                          # bleus natifs D25, du plus sombre au plus clair
    cycle, d14_ms = d14_cycle()

    floor = seg['sand'] | seg['halo'] | seg['pit']
    ys, xs = np.nonzero(floor)
    ix, iy = lattice_index(xs, ys)

    layers = {}

    def empty():
        return np.zeros((H, W, 4), np.uint8)

    # 01 ciel (pixels source exacts)
    ciel = empty(); ciel[seg['sky']] = src[seg['sky']]
    # les pixels non classés (bords) rejoignent les roches
    rock = seg['rock'] | seg['unclassified']
    roches = empty(); roches[rock] = src[rock]
    avant = empty(); avant[seg['foreground']] = src[seg['foreground']]
    # Nettoyage minimal : les pixels à couleur rare (< 4 occurrences) du calque roches sont les bords
    # fondus des rayons de soleil incrustés dans cette version source ; chacun prend la couleur
    # fréquente la plus proche présente dans son voisinage 5x5 (sinon la plus proche du calque).
    r64 = roches.astype(np.int64)
    rk = r64[..., 0] * 65536 + r64[..., 1] * 256 + r64[..., 2]
    u, cnt = np.unique(rk[rock], return_counts=True)
    freq = dict(zip(u.tolist(), cnt.tolist()))
    rare_y, rare_x = np.nonzero(rock & np.isin(rk, u[cnt < 4]))
    fu = u[cnt >= 4]
    frgb = np.stack([(fu >> 16) & 255, (fu >> 8) & 255, fu & 255], -1)
    snapped = roches.copy()
    for y, x in zip(rare_y, rare_x):
        y0, y1, x0, x1 = max(0, y - 2), min(H, y + 3), max(0, x - 2), min(W, x + 3)
        cand = rk[y0:y1, x0:x1][rock[y0:y1, x0:x1]]
        cand = np.array([k for k in set(cand.tolist()) if freq.get(k, 0) >= 4])
        pool = np.stack([(cand >> 16) & 255, (cand >> 8) & 255, cand & 255], -1) if len(cand) else frgb
        o = roches[y, x, :3].astype(int)
        snapped[y, x, :3] = pool[np.abs(pool - o).sum(1).argmin()]
    ray_cleanup = int(len(rare_y))
    roches = snapped

    # 02 eau : 30 phases natives
    eau = []
    for t in range(FRAMES):
        e = empty()
        e[ys, xs, :3] = tile[t, iy, ix]
        e[ys, xs, 3] = 255
        eau.append(e)

    # 03 ombres de contact : noir semi-transparent proportionnel à l'assombrissement du sable source
    h_, s_, v_ = seg['hsv']
    om = empty()
    sm = seg['shadow']
    alpha = np.clip((0.97 - v_) / 0.30, 0, 1) * 150
    om[sm, 3] = alpha[sm].astype(np.uint8)
    om[om[..., 3] < 24] = 0

    # 04 siphon : bandes concentriques qui suivent le contour de la cuvette, cycle natif D14 (6 phases)
    pit = seg['pit']
    halo = seg['halo'] & nd.binary_dilation(pit, iterations=12)   # halo borné autour de la cuvette
    d = nd.distance_transform_edt(pit)
    band = np.floor(d / 1.5).astype(int)
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in cycle]
    rank = np.argsort(np.argsort(lum))            # rang de luminance de chaque étape du cycle D14
    n = len(cycle)
    # bleus natifs D25 choisis par rang (du bleu moyen à l'écume), liseré d'écume fixe au bord
    ramp_idx = np.linspace(2, len(pal) - 1, n).round().astype(int)
    ramp = pal[ramp_idx]
    rim = pal[-1]
    siphon = []
    py, px = np.nonzero(pit)
    hy, hx = np.nonzero(halo)
    for t in range(n):
        s_img = empty()
        step = (band[py, px] + t) % n               # t croissant : les anneaux avancent vers le centre
        s_img[py, px, :3] = ramp[rank[step]]
        edge = d[py, px] <= 1.0
        s_img[py[edge], px[edge], :3] = rim
        s_img[py, px, 3] = 255
        s_img[hy, hx, :3] = pal[-3]                 # halo d'eau claire (ancien halo de sable clair)
        s_img[hy, hx, 3] = 255
        siphon.append(s_img)

    # 05 cascades : texture de chevrons native de la chute gauche (propre, hors rayon), teintes -> bleus
    # natifs D25 par rang, défilement vertical vers le bas : boucle 96 px, 16 px par phase = 6 phases.
    falls = seg['falls']
    lab, nf = nd.label(falls)
    clean = np.zeros_like(falls)
    for i, sl in enumerate(nd.find_objects(lab)):
        comp = lab == i + 1
        occ = comp[0:90].mean(0)
        cols = np.flatnonzero(occ >= 0.8)
        x0, x1 = cols.min(), cols.max()
        keep = np.zeros_like(comp)
        keep[:, x0:x1 + 1] = True
        keep[96:, max(0, x0 - 6):x1 + 7] = True       # évasement du pied de chute
        clean |= comp & keep
    falls = clean
    fl_mask_left = falls.copy(); fl_mask_left[:, W // 2:] = False
    lcols = np.flatnonzero(fl_mask_left[0:90].mean(0) >= 0.8)
    lx0 = lcols.min()
    tex_rgb = src[0:96, lx0:lx0 + (lcols.max() - lx0 + 1), :3].astype(int)
    tex_lum = 0.299 * tex_rgb[..., 0] + 0.587 * tex_rgb[..., 1] + 0.114 * tex_rgb[..., 2]
    main = np.array([[0xff, 0xd7, 0x5f], [0xff, 0xe7, 0x5f], [0xff, 0xf7, 0x5f]])
    main_lum = 0.299 * main[:, 0] + 0.587 * main[:, 1] + 0.114 * main[:, 2]
    tex_cls = np.abs(tex_lum[..., None] - main_lum).argmin(-1)
    fall_ramp = pal[[len(pal) - 5, len(pal) - 3, len(pal) - 1]]
    TW = tex_cls.shape[1]
    cascades = []
    fy, fx = np.nonzero(falls)
    for t in range(6):
        c = empty()
        right = fx >= W // 2
        rx0 = np.flatnonzero(falls[0:90, W // 2:].mean(0) >= 0.8).min() + W // 2
        col = np.where(right, fx - rx0, fx - lx0)
        col = np.clip(col, 0, TW - 1)
        row = (fy - 16 * t) % 96
        c[fy, fx, :3] = fall_ramp[tex_cls[row, col]]
        c[fy, fx, 3] = 255
        cascades.append(c)
    # pixels retirés du masque des chutes (fragments de roche) : ils restent roche
    rest = seg['falls'] & ~falls
    roches[rest] = src[rest]

    return {
        'size': (W, H), 'seg': seg, 'ciel': ciel, 'eau': eau, 'ombres': om, 'siphon': siphon,
        'cascades': cascades, 'roches': roches, 'avant': avant, 'tile': tile, 'tile_stats': tile_stats,
        'palette': pal, 'ray_cleanup_px': ray_cleanup, 'cycle_d14': cycle, 'd14_ms': d14_ms, 'ramp': ramp, 'fall_ramp': fall_ramp,
    }


def stack(parts):
    im = Image.new('RGBA', parts[0].shape[1::-1])
    for p in parts:
        im.alpha_composite(Image.fromarray(p))
    return im


def frame(res, t):
    return stack([res['ciel'], res['eau'][t % FRAMES], res['ombres'], res['siphon'][t % len(res['siphon'])],
                  res['cascades'][t % len(res['cascades'])], res['roches'], res['avant']])


if __name__ == '__main__':
    res = build()
    print('tuile mer', res['tile'].shape, res['tile_stats'])
    print('cycle D14', res['cycle_d14'], res['d14_ms'], 'ms')
    frame(res, 0).save('/tmp/fde_f0.png')
    frames = [frame(res, t) for t in range(FRAMES)]
    frames[0].save('/tmp/fde_anim.webp', save_all=True, append_images=frames[1:], duration=TICK_MS, loop=0,
                   lossless=True)
    print('ok')
