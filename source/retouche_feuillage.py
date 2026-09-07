# -*- coding: utf-8 -*-
"""
Cadre d'immersion « feuilles » autour des bordures de bois.

Ajoute un 12e calque, 11_feuillage_immersion, pose AU-DESSUS de la bordure
avant : une guirlande continue de feuillage découpée en festons qui suit
l'extrémité des parois de bois et de la bordure de premier plan, s'épaissit
près des extrémités des segments de bordure, dans les épaules de la pièce et
autour du tronc, puis se dissout dans le fond noir par un dégradé vers le
presque-noir et quelques masses d'arrière-plan fondues. Effet PMD : la pièce
est observée à travers la canopée.

Règles respectées :
- les passages (N/S/E/O) restent entièrement dégagés, le sol traverse ;
- fenêtres, tableaux et porte ne sont jamais recouverts (débordement
  intérieur limité à 6 px sur le bois) ;
- images fixes, aucune animation ;
- la nuit est recalculée avec la formule du pipeline (rgb*[.36,.34,.43]
  +[9,10,19]) ; les pixels « doux » (franges fondues, masses lointaines)
  restent noirs pour se marier au fond dans les deux palettes.

Le script part des calques courants, n'en modifie aucun et n'ajoute qu'un
fichier par salle et par palette ; il est rejouable à l'identique (RNG
semé par salle). Il régénère ensuite composites, Aseprite, cartes Tiled,
kit.json et les deux planches — comme retouche_hall_02.py.

Chaîne complète après un rebuild_kit.py :
    python source/rebuild_kit.py
    python source/retouche_hall_02.py
    python source/retouche_feuillage.py
    python source/build_preview.py
    python source/verify_pmd.py
"""
import io, json, math, os, struct, zlib
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_fill_holes, binary_dilation, binary_erosion

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = [
    ('00_exterieur', 'Paysage extérieur interchangeable'),
    ('01_sol', 'Sol et continuité des passages'),
    ('02_structure', 'Structure, murs et ouvertures'),
    ('03_cadres_fenetres', 'Cadres de fenêtres — sans paysage'),
    ('04_tableaux', 'Contenu des tableaux encastrés'),
    ('05_porte_maitre', 'Porte nord du bureau — hall uniquement'),
    ('06_decorations', 'Décorations — vide'),
    ('07_objets', 'Objets — vide'),
    ('08_ombres_acces', 'Ombres de contact des accès'),
    ('09_eclairage_fixe', 'Éclairage complémentaire — vide'),
    ('10_bordure_avant', 'Bordure avant interrompue aux passages'),
    ('11_feuillage_immersion', "Feuillage d'immersion — cadre PMD"),
]
FEUIL = '11_feuillage_immersion'

# ---------------------------------------------------------------- palettes
C_OUTLINE = (7, 18, 10)      # contour des touffes, presque noir
C_CREVICE = (12, 27, 15)     # lignes de séparation entre festons
C_DEEP    = (24, 56, 31)
C_BASE    = (38, 78, 42)
C_MID     = (54, 98, 49)
C_LIGHT   = (74, 120, 58)
C_SUN     = (102, 150, 70)   # touches de lumière, jour uniquement
C_FRANGE  = (5, 12, 7)       # frange externe : fondu vers le fond noir
C_UNDER   = (2, 6, 4)        # ombre portée des touffes sur le bois
C_BOKEH   = (14, 34, 19)     # masses d'arrière-plan
C_BOKEH2  = (8, 21, 12)      # masses proches, plus sombres
C_VINE    = (24, 54, 28)
TONES = [C_DEEP, C_BASE, C_MID, C_MID, C_LIGHT, C_SUN]
PONDERES = [0.14, 0.24, 0.30, 0.18, 0.10, 0.04]


# ------------------------------------------------------------------ outils

def charger(dossier, palette, n):
    return np.array(Image.open(os.path.join(REPO, 'calques', dossier,
                                            palette, n + '.png')).convert('RGBA'))


def nuit(a, soft=None):
    b = a.copy()
    b[:, :, :3] = np.rint(a[:, :, :3] * [.36, .34, .43] + [9, 10, 19]).clip(0, 255).astype('uint8')
    if soft is not None:
        b[soft, :3] = 0          # franges et masses fondues : noir pur la nuit
    b[a[:, :, 3] == 0] = 0
    return b


def png(im, path):
    a = np.array(im.convert('RGBA'))
    colors, idx = np.unique(a.reshape(-1, 4), axis=0, return_inverse=True)
    if len(colors) <= 256:
        q = Image.fromarray(idx.reshape(a.shape[:2]).astype('uint8'), 'P')
        pal = np.zeros((256, 3), np.uint8)
        pal[:len(colors)] = colors[:, :3]
        q.putpalette(pal.ravel())
        q.info['transparency'] = bytes(colors[:, 3])
        q.save(path, optimize=True)
    else:
        im.save(path, optimize=True)


def astr(s):
    b = s.encode()
    return struct.pack('<H', len(b)) + b


def chunk(k, d):
    return struct.pack('<IH', len(d) + 6, k) + d


def ase(path, layers, size):
    w, h = size
    chunks = []
    for n, im in layers:
        chunks.append(chunk(0x2004, struct.pack('<HHHHHHB', 3, 0, 0, 0, 0, 0, 255) + b'\0' * 3 + astr(n)))
    for i, (n, im) in enumerate(layers):
        box = im.getbbox()
        if box:
            x, y, _, _ = box
            q = im.crop(box)
        else:
            x = y = 0
            q = Image.new('RGBA', (1, 1))
        chunks.append(chunk(0x2005, struct.pack('<HhhBHh', i, x, y, 255, 2, 0) + b'\0' * 5 +
                            struct.pack('<HH', q.width, q.height) + zlib.compress(q.tobytes(), 9)))
    data = b''.join(chunks)
    frame = struct.pack('<IHHH2sI', len(data) + 16, 0xF1FA, len(chunks), 100, b'\0\0', len(chunks)) + data
    header = bytearray(128)
    struct.pack_into('<IHHHHHIH', header, 0, len(frame) + 128, 0xA5E0, 1, w, h, 32, 1, 100)
    struct.pack_into('<HBBhhHH', header, 32, 0, 1, 1, 0, 0, 8, 8)
    open(path, 'wb').write(header + frame)


def font(size):
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
    except OSError:
        return ImageFont.load_default()


def valeur_noise(h, w, rng, cell):
    """Bruit de valeur interpolé, en float32 -1..1, grain `cell` px."""
    gh, gw = int(h / cell) + 2, int(w / cell) + 2
    g = rng.uniform(-1, 1, (gh, gw)).astype(np.float32)
    return cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)


# --------------------------------------------------------------- géométrie

def champ_silhouette(calques):
    """Silhouette remplie de la pièce + distances int./ext. + direction
    sortante normalisée."""
    body = np.zeros(calques['01_sol'].shape[:2], bool)
    for n in ('01_sol', '02_structure', '03_cadres_fenetres', '04_tableaux',
              '05_porte_maitre', '10_bordure_avant'):
        body |= calques[n][:, :, 3] > 0
    S = binary_fill_holes(body)
    din = cv2.distanceTransform(S.astype(np.uint8), cv2.DIST_L2, 0)
    dout = cv2.distanceTransform((~S).astype(np.uint8), cv2.DIST_L2, 0)
    F = din.astype(np.float32) - dout.astype(np.float32)
    gy, gx = np.gradient(F)
    nrm = np.hypot(gx, gy)
    nrm[nrm < 1e-6] = 1
    # sortant = opposé du gradient (F croît vers l'intérieur)
    return S, din, dout, (-gx / nrm, -gy / nrm)


def corridors(S, acces):
    """Zones à laisser entièrement dégagées : les passages de sol."""
    h, w = S.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cx = w * .5
    m = np.zeros((h, w), bool)
    if 'N' in acces:
        top = np.where(S[0])[0]
        if len(top):
            m |= _poly(w, h, np.array([(top.min() - 8, 0), (top.max() + 8, 0),
                                       (cx + w * .105, h * .50), (cx - w * .105, h * .50)]))
    if 'S' in acces:
        bot = np.where(S[-1])[0]
        if len(bot):
            m |= _poly(w, h, np.array([(bot.min() - 8, h), (bot.max() + 8, h),
                                       (cx + w * .135, h * .66), (cx - w * .135, h * .66)]))
    for d in ('E', 'O'):
        if d in acces:
            col = S[:, w - 1] if d == 'E' else S[:, 0]
            ys = np.where(col)[0]
            if len(ys):
                m |= (yy >= ys.min() - 8) & (yy <= ys.max() + 8) & \
                     ((xx > w * .78) if d == 'E' else (xx < w * .22))
    return binary_dilation(m, np.ones((5, 5), bool))


def _poly(w, h, pts):
    img = Image.new('L', (w, h))
    ImageDraw.Draw(img).polygon([tuple(p) for p in pts], fill=255)
    return np.array(img) > 0


def points_contour(S, pas):
    """Points échantillonnés régulièrement (en arc) sur le contour
    extérieur de la silhouette."""
    conts, _ = cv2.findContours(S.astype(np.uint8), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_NONE)
    if not conts:
        return []
    c = max(conts, key=cv2.contourArea).reshape(-1, 2)   # x,y, ordre du parcours
    n = max(8, int(cv2.arcLength(c, True) / pas))
    idx = (np.linspace(0, len(c), n, endpoint=False)).astype(int)
    return [(int(p[0]), int(p[1])) for p in c[idx]]


def extremites_bordure(bord, dirx, diry):
    """Pour chaque segment continu de bordure de bois, ses deux bouts."""
    nc, lab, stats, _ = cv2.connectedComponentsWithStats(bord.astype(np.uint8), 8)
    tips = []
    for k in range(1, nc):
        if stats[k, cv2.CC_STAT_AREA] < 220:
            continue
        ys, xs = np.where(lab == k)
        pts = np.stack([xs, ys], 1).astype(np.float64)
        c = pts - pts.mean(0)
        cov = np.cov(c.T)
        ev, evec = np.linalg.eigh(cov)
        ax = evec[:, -1]
        t = c @ ax
        for idx in (int(t.argmin()), int(t.argmax())):
            px, py = int(pts[idx, 0]), int(pts[idx, 1])
            ox, oy = dirx[py, px], diry[py, px]
            if ox * ax[0] + oy * ax[1] < 0:
                ax = -ax
            tips.append((px, py, ox, oy, ax[0], ax[1]))
    return tips


# ----------------------------------------------------------------- peinture

class Toile:
    """Canvas RGBA + masque « doux » (pixels fondus, restés noirs la nuit)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.float32)
        self.a = np.zeros((h, w), np.float32)
        self.soft = np.zeros((h, w), bool)

    def pose(self, x0, y0, pr, pg, pb, pa, soft):
        h, w = self.a.shape
        xa, ya = max(0, x0), max(0, y0)
        xb, yb = min(w, x0 + pa.shape[1]), min(h, y0 + pa.shape[0])
        if xa >= xb or ya >= yb:
            return
        pr = pr[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
        pg = pg[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
        pb = pb[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
        pa = pa[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
        soft = soft[ya - y0:yb - y0, xa - x0:xb - x0]
        dst_a = self.a[ya:yb, xa:xb][:, :, None]
        sa = pa / 255.0
        da = dst_a / 255.0
        oa = sa + da * (1 - sa)
        src = np.concatenate([pr, pg, pb], axis=2)
        with np.errstate(divide='ignore', invalid='ignore'):
            self.rgb[ya:yb, xa:xb] = (src * sa + self.rgb[ya:yb, xa:xb] * da * (1 - sa)) / np.maximum(oa, 1e-6)
        self.a[ya:yb, xa:xb] = oa[:, :, 0] * 255
        self.soft[ya:yb, xa:xb] = np.where(pa[:, :, 0] > 0, soft | self.soft[ya:yb, xa:xb], self.soft[ya:yb, xa:xb])

    def resultat(self):
        a = np.rint(self.a).astype(np.uint8)
        doux = (a > 0) & (a < 255)
        a = np.where(doux, np.clip(((a.astype(int) + 4) // 8) * 8, 8, 248), a).astype(np.uint8)
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[:, :, :3] = np.rint(self.rgb).clip(0, 255).astype(np.uint8)
        out[:, :, 3] = a
        out[a == 0] = 0
        self.soft = self.soft & (a > 0)
        # seuls les pixels non opaques « fondus » deviennent noirs ; une
        # touffe opaque peinte par-dessus une frange reste visible.
        out[self.soft & (a < 255), :3] = 0
        return out


def touffe(T, cx, cy, R, rng):
    """Une touffe de feuillage festonnée, peinte dans la toile T."""
    m = int(R * 2 + 10)
    x0, y0 = int(round(cx - m)), int(round(cy - m))
    yy, xx = np.mgrid[0:2 * m, 0:2 * m].astype(np.float32)
    px, py = xx + x0, yy + y0
    nl = int(rng.integers(5, 9))
    bases = rng.uniform(0, 2 * np.pi, nl)
    dists = rng.uniform(.15, .62, nl) * R
    rays = rng.uniform(.34, .56, nl) * R
    elong = rng.uniform(1.15, 1.75, nl)          # lobes elliptiques, feuillus
    lx = cx + np.cos(bases) * dists
    ly = cy + np.sin(bases) * dists
    # cellule = lobe le plus proche couvrant le pixel
    lab = np.full((2 * m, 2 * m), -1, np.int32)
    best = np.full((2 * m, 2 * m), 1e9, np.float32)
    for i in range(nl):
        dx, dy = px - lx[i], py - ly[i]
        cb_, sb_ = np.cos(bases[i]), np.sin(bases[i])
        u = (dx * cb_ + dy * sb_) / (rays[i] * elong[i])
        v = (dx * -sb_ + dy * cb_) / rays[i]
        d = u * u + v * v
        couvre = d <= 1.0
        mieux = couvre & (d < best)
        lab[mieux] = i
        best[mieux] = d[mieux]
    masse = lab >= 0
    if not masse.any():
        return
    tones = rng.choice(len(TONES), size=nl, p=PONDERES)
    jitter = rng.integers(-7, 8, (nl, 3))
    chanceux = rng.random(nl) < .6          # lobes qui reçoivent la lumière
    pr = np.zeros((2 * m, 2 * m, 3), np.float32)
    for i in range(nl):
        sel = masse & (lab == i)
        pr[sel] = np.array(TONES[tones[i]], np.float32) + jitter[i]
    # festons : frontière entre deux lobes
    b = np.zeros((2 * m, 2 * m), bool)
    b[1:, :] |= (lab[1:, :] != lab[:-1, :]) & (lab[1:, :] >= 0) & (lab[:-1, :] >= 0)
    b[:-1, :] |= (lab[1:, :] != lab[:-1, :]) & (lab[1:, :] >= 0) & (lab[:-1, :] >= 0)
    b[:, 1:] |= (lab[:, 1:] != lab[:, :-1]) & (lab[:, 1:] >= 0) & (lab[:, :-1] >= 0)
    b[:, :-1] |= (lab[:, 1:] != lab[:, :-1]) & (lab[:, 1:] >= 0) & (lab[:, :-1] >= 0)
    contour = masse & ~binary_erosion(masse, np.ones((3, 3), bool))
    bande = binary_dilation(b | contour, np.ones((3, 3), bool)) & masse
    pr[bande] *= .86
    pr[b | contour] = np.array(C_CREVICE, np.float32)
    pr[contour] = np.array(C_OUTLINE, np.float32)
    # lumière du haut-gauche sur le bord des lobes chanceux
    lobe_bord = np.zeros((2 * m, 2 * m), bool)
    for i in range(nl):
        if not chanceux[i]:
            continue
        cell = (lab == i)
        if cell.sum() < 6:
            continue
        cb = cell & ~binary_erosion(cell, np.ones((3, 3), bool))
        nxv = (px - lx[i]) / max(rays[i], 1)
        nyv = (py - ly[i]) / max(rays[i], 1)
        cote = (nxv + nyv) < -0.45
        lobe_bord |= cb & cote
    pr[lobe_bord] = np.minimum(pr[lobe_bord] + np.array((18, 24, 11), np.float32), 255)
    # mouchetures internes : petites feuilles plus sombres, texture feuillue
    for _ in range(int(nl * 1.5)):
        i = int(rng.integers(nl))
        sx = lx[i] + rng.uniform(-.5, .5) * rays[i]
        sy = ly[i] + rng.uniform(-.5, .5) * rays[i]
        si = int(round(sy)) - y0, int(round(sx)) - x0
        if 0 <= si[0] < 2 * m and 0 <= si[1] < 2 * m and lab[si[0], si[1]] >= 0:
            pr[max(0, si[0] - 1):si[0] + 2, max(0, si[1] - 1):si[1] + 2] *= .80
    pa = np.where(masse, 255.0, 0.0)
    softp = np.zeros((2 * m, 2 * m), bool)
    # ombre portée sous la touffe
    dy = max(3, int(R * .28))
    sh = np.zeros((2 * m, 2 * m), bool)
    for i in range(nl):
        sh |= ((px - lx[i]) ** 2 + (py - (ly[i] + dy)) ** 2) <= (rays[i] * 1.06) ** 2
    sh &= ~masse
    prs = np.zeros_like(pr)
    prs[sh] = np.array(C_UNDER, np.float32)
    T.pose(x0, y0, prs[..., 0], prs[..., 1], prs[..., 2], np.where(sh, 190.0, 0), np.ones_like(sh))
    T.pose(x0, y0, pr[..., 0], pr[..., 1], pr[..., 2], pa, softp)
    # halo noir fondu autour de la masse (profondeur sur le bois voisin)
    dmass = cv2.distanceTransform((~masse).astype(np.uint8), cv2.DIST_L2, 0)
    halo = (dmass > 0) & (dmass <= 7)
    ha = np.rint((1 - dmass / 7.0) ** 2 * 95).clip(0, 255)
    T.pose(x0, y0, pr[..., 0], pr[..., 1], pr[..., 2], np.where(halo, ha, 0), np.ones_like(halo) & halo)


def liane(T, x, y, rng, sens):
    """Fine tige pendante avec 2-3 petites feuilles."""
    n = int(rng.integers(9, 17))
    courb = rng.uniform(-.9, .9)
    px, py = float(x), float(y)
    for i in range(n):
        px += sens * rng.uniform(.1, .8) + courb * .35
        py += rng.uniform(.9, 1.7)
        ix, iy = int(px), int(py)
        if 0 <= ix < T.w and 0 <= iy < T.h:
            T.rgb[iy, ix] = np.array(C_VINE, np.float32)
            T.a[iy, ix] = max(T.a[iy, ix], 255 if i > 2 else 200)
            T.soft[iy, ix] = i <= 2
        if i in (3, int(n * .6)) and rng.random() < .8:
            touffe(T, ix + sens * 2, iy + 1, 3.4, rng)


def mass_fondue(T, cx, cy, R, rng, couleur, alpha):
    """Petit groupe de disques d'arrière-plan au contour fondu, presque noir."""
    n = int(rng.integers(3, 6))
    for _ in range(n):
        ox = cx + rng.uniform(-.7, .7) * R
        oy = cy + rng.uniform(-.6, .6) * R
        r = R * rng.uniform(.35, .62)
        m = int(r + 8)
        x0, y0 = int(ox - m), int(oy - m)
        yy, xx = np.mgrid[0:2 * m, 0:2 * m].astype(np.float32)
        d = np.hypot(xx - (ox - x0), yy - (oy - y0))
        feather = max(3.0, r * .5)
        a = np.clip(1 - (d - r * .5) / feather, 0, 1) ** 1.5 * alpha
        a[d <= r * .5] = alpha
        pr = np.zeros((2 * m, 2 * m, 3), np.float32)
        pr[..., 0] = couleur[0]
        pr[..., 1] = couleur[1]
        pr[..., 2] = couleur[2]
        T.pose(x0, y0, pr[..., 0], pr[..., 1], pr[..., 2], a, np.ones_like(a, bool))


def bande_feuillage(T, S, din, dout, dirx, diry, couloir, rng, scale):
    """Garlande continue : bande de feuillage fondu qui épouse tout le
    contour, festonnée par des encoches, assombrie vers la frange externe
    jusqu'au presque-noir (mariage avec le fond)."""
    h, w = S.shape
    yy, xx = np.mgrid[0:h, 0:w]
    bruit = valeur_noise(h, w, rng, max(6, int(9 * scale)))
    # plus épaisse en bas et sur les épaules, fine en haut
    fact_bas = .62 + .50 * np.clip(yy / (h * .5), 0, 1)
    r_out = 22 * scale * fact_bas * (1.0 + .30 * bruit)
    dans = (dout <= r_out) & (din <= 3)
    if not dans.any():
        return
    # encoches festonnées : cercles creusés le long du contour
    morse = np.ones((h, w), np.float32)
    for px, py in points_contour(S, max(7, int(11 * scale))):
        rr = float(np.clip(r_out[py, px] * rng.uniform(.48, .78), 4, 70))
        cx = px + dirx[py, px] * r_out[py, px] * .92
        cy = py + diry[py, px] * r_out[py, px] * .92
        x0, y0 = int(cx - rr - 2), int(cy - rr - 2)
        x1, y1 = int(cx + rr + 3), int(cy + rr + 3)
        xa, ya = max(0, x0), max(0, y0)
        xb, yb = min(w, x1), min(h, y1)
        if xa >= xb or ya >= yb:
            continue
        yy2, xx2 = np.mgrid[ya:yb, xa:xb].astype(np.float32)
        d = np.hypot(xx2 - cx, yy2 - cy) / rr
        morse[ya:yb, xa:xb] = np.minimum(morse[ya:yb, xa:xb], np.clip(d, 0, 1))
    alpha = np.clip((r_out - dout) / np.maximum(r_out * .42, 1), 0, 1) ** 1.2
    alpha = alpha * morse * 255.0
    # couleur : dégradé profond → base, frange externe tirant vers le noir
    t = np.clip(dout / np.maximum(r_out, 1), 0, 1)
    mix_frange = np.clip((t - .55) / .45, 0, 1) ** 1.3
    cd = np.array(C_DEEP, np.float32)
    cb = np.array(C_BASE, np.float32)
    cf = np.array(C_FRANGE, np.float32)
    col = cd[None, None] + (cb - cd)[None, None] * np.clip(t / .55, 0, 1)[..., None]
    col = col + (cf - col) * mix_frange[..., None]
    col += bruit[..., None] * 5          # variation organique
    libre = ~binary_dilation(couloir, np.ones((5, 5), bool))
    alpha *= libre
    T.pose(0, 0, col[..., 0], col[..., 1], col[..., 2], alpha, np.ones((h, w), bool))


# ------------------------------------------------------------------- cadre

def feuillage_salle(room):
    rid = room['id']
    dossier = room['dossier']
    w, h = room['dimensions']
    scale = w / 648.0
    J = {n: charger(dossier, 'jour', n) for n, _ in LABELS if n != FEUIL}
    S, din, dout, (dirx, diry) = champ_silhouette(J)
    bord = J['10_bordure_avant'][:, :, 3] > 0
    acces = [t for t in room['acces'] if t in ('N', 'S', 'E', 'O')]
    couloir = corridors(S, acces)
    protege = binary_dilation(
        (J['03_cadres_fenetres'][:, :, 3] > 0) | (J['04_tableaux'][:, :, 3] > 0) |
        (J['05_porte_maitre'][:, :, 3] > 0), np.ones((5, 5), bool))
    bois = (J['02_structure'][:, :, 3] > 0) | bord
    d_bois = cv2.distanceTransform(bois.astype(np.uint8), cv2.DIST_L2, 0)

    rng = np.random.default_rng(1000 + int(rid))
    T = Toile(w, h)
    yy, xx = np.mgrid[0:h, 0:w]
    diag = math.hypot(w, h)
    dc = np.minimum.reduce([(xx ** 2 + yy ** 2), ((w - xx) ** 2 + yy ** 2),
                            (xx ** 2 + (h - yy) ** 2), ((w - xx) ** 2 + (h - yy) ** 2)]) ** .5
    coins = 1 - dc / (0.55 * diag)
    libre = ~binary_dilation(couloir, np.ones((9, 9), bool))

    # 1. guirlande continue festonnée autour du contour
    bande_feuillage(T, S, din, dout, dirx, diry, couloir, rng, scale)

    # 2. masses d'arrière-plan fondues (canopée hors champ, proche du cadre)
    nb = int(7 * scale + 3)
    poses_bokeh = 0
    for _ in range(nb * 4):
        if poses_bokeh >= nb:
            break
        cx = rng.uniform(0, w)
        cy = rng.uniform(h * .05, h * 1.02)
        i, j = int(np.clip(cy, 0, h - 1)), int(np.clip(cx, 0, w - 1))
        d = dout[i, j]
        if d < 12 or d > 40 * scale or couloir[i, j]:
            continue
        R = rng.uniform(10, 26) * scale
        coul = C_BOKEH if rng.random() < .55 else C_BOKEH2
        alpha = rng.uniform(90, 160) if coul is C_BOKEH else rng.uniform(150, 215)
        mass_fondue(T, cx, cy, R, rng, coul, alpha)
        poses_bokeh += 1

    # 3. touffes : extrémités des segments de bordure (ancrage renforcé)
    centres = []
    for px, py, ox, oy, axo, ayo in extremites_bordure(bord, dirx, diry):
        R = rng.uniform(15, 21) * scale
        tx = px + (ox * .5 + axo * .85) * R * .85
        ty = py + (oy * .5 + ayo * .85) * R * .85
        if couloir[int(np.clip(ty, 0, h - 1)), int(np.clip(tx, 0, w - 1))]:
            continue
        centres.append((tx, ty, R * 1.25))
        centres.append((tx + axo * R * .8, ty + ayo * R * .8, R * .95))

    # 4. guirlande de touffes détaillées le long du contour
    step = max(15, int(17 * scale))
    for gy in range(0, h, step):
        for gx in range(0, w, step):
            x = gx + rng.uniform(0, step)
            y = gy + rng.uniform(0, step)
            i, j = int(np.clip(y, 0, h - 1)), int(np.clip(x, 0, w - 1))
            if not libre[i, j] or protege[i, j]:
                continue
            di, do = din[i, j], dout[i, j]
            if di > 6 or do > 30 * scale:
                continue
            p = .30 + .48 * math.exp(-d_bois[i, j] / (26 * scale)) + .22 * (y / h) + .25 * max(coins[i, j], 0)
            if y < h * .30:
                p *= .6
            if rng.random() > min(p, .96):
                continue
            R = rng.normal(15.5, 4.4) * scale
            R = float(np.clip(R, 8 * scale, 27 * scale))
            if di > 0:
                x2, y2 = x + dirx[i, j] * (di + R * .2), y + diry[i, j] * (di + R * .2)
            elif do > R * .4:
                x2, y2 = x - dirx[i, j] * (do - R * .28), y - diry[i, j] * (do - R * .28)
            else:
                x2, y2 = x, y
            centres.append((x2, y2, R))

    for cx, cy, R in sorted(centres, key=lambda c: c[1]):
        touffe(T, cx, cy, R, rng)
        if cy > h * .45 and rng.random() < .30:
            liane(T, cx, cy + R * .7, rng, 1 if rng.random() < .5 else -1)

    # 5. petites feuilles détachées près de la guirlande
    for _ in range(int(6 * scale + 3)):
        if not centres:
            break
        cx, cy, R = centres[int(rng.integers(len(centres)))]
        i, j = int(np.clip(cy, 0, h - 1)), int(np.clip(cx, 0, w - 1))
        d = rng.uniform(9, 22) * scale
        sx = cx + dirx[i, j] * d + rng.uniform(-d, d) * .5
        sy = cy + diry[i, j] * d + rng.uniform(-d, d) * .5
        touffe(T, sx, sy, rng.uniform(2.4, 3.8) * scale, rng)

    out = T.resultat()
    # nettoyage : passages intacts, pas de feuille profonde dans la pièce
    garde = (~S) | (din <= 6)
    garde &= ~couloir
    garde &= ~binary_dilation(protege, np.ones((3, 3), bool))
    out[:, :, 3] = np.where(garde, out[:, :, 3], 0)
    out[out[:, :, 3] == 0] = 0
    return out


# ----------------------------------------------------------------- exports

def ecrire_salle(room, feuil_jour, feuil_nuit):
    rid, dossier = room['id'], room['dossier']
    w, h = room['dimensions']
    d = os.path.join(REPO, 'calques', dossier)
    for palette, couche in (('jour', feuil_jour), ('nuit', feuil_nuit)):
        png(Image.fromarray(couche, 'RGBA'), os.path.join(d, palette, FEUIL + '.png'))
        comp = Image.new('RGBA', (w, h))
        export = []
        for n, label in LABELS:
            if n == FEUIL:
                q = Image.fromarray(couche, 'RGBA')
            else:
                q = Image.open(os.path.join(d, palette, n + '.png')).convert('RGBA')
            comp.alpha_composite(q)
            export.append((label, q))
        fd = os.path.join(REPO, 'salles', dossier)
        png(comp, os.path.join(fd, 'salle_%s.png' % palette))
        ase(os.path.join(fd, '%s_%s.aseprite' % (rid, palette)), export, (w, h))
        # base_*_transparente / magenta : inchangées (le feuillage est un
        # calque de premier plan, jamais dans la base).
        cols, rows = w // 8, h // 8
        count = cols * rows
        sets, tls = [], []
        for i, (n, label) in enumerate(LABELS):
            qa = (couche if n == FEUIL else
                  np.array(Image.open(os.path.join(d, palette, n + '.png')).convert('RGBA')))
            occ = qa[:, :, 3].reshape(rows, 8, cols, 8).max((1, 3)) > 0
            first = 1 + i * count
            data = np.arange(first, first + count, dtype=np.uint32).reshape(rows, cols)
            data[~occ] = 0
            sets.append({'firstgid': first, 'name': n, 'tilewidth': 8, 'tileheight': 8,
                         'tilecount': count, 'columns': cols,
                         'image': '../calques/%s/%s/%s.png' % (dossier, palette, n),
                         'imagewidth': w, 'imageheight': h, 'margin': 0, 'spacing': 0})
            tls.append({'id': i + 1, 'name': label, 'type': 'tilelayer', 'width': cols,
                        'height': rows, 'x': 0, 'y': 0, 'opacity': 1, 'visible': True,
                        'data': data.ravel().tolist()})
        tm = {'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0',
              'orientation': 'orthogonal', 'renderorder': 'right-down', 'tilewidth': 8,
              'tileheight': 8, 'width': cols, 'height': rows, 'infinite': False,
              'nextlayerid': len(LABELS) + 1, 'nextobjectid': 1, 'layers': tls, 'tilesets': sets}
        with io.open(os.path.join(REPO, 'tiled', '%s_%s.tmj' % (rid, palette)), 'w',
                     encoding='utf-8') as f:
            json.dump(tm, f, ensure_ascii=False, separators=(',', ':'))


def planches(manifest):
    for mode in ['jour', 'nuit']:
        board = Image.new('RGB', (1536, 1240), (18, 20, 47))
        d = ImageDraw.Draw(board)
        d.text((24, 16), 'GUILDE TREEHOUSE / PASSAGES OUVERTS / ' + mode.upper(),
               font=font(21), fill=(237, 226, 190))
        d.text((24, 48), 'Une seule porte nord vers le bureau · fenêtres évidées · paysage séparé · '
               'cadre de feuillage · grille 8 px · images fixes', font=font(13), fill=(178, 192, 180))
        for i, row in enumerate(manifest['salles']):
            q = Image.open(os.path.join(REPO, row['fichiers'][mode]['png'])).convert('RGBA')
            q.thumbnail((494, 250), Image.Resampling.NEAREST)
            x = i % 3 * 512
            y = 80 + i // 3 * 285
            board.paste(q, (x + (512 - q.width) // 2, y + (250 - q.height) // 2), q)
            d.text((x + 20, y + 255), row['id'] + '  ' + row['nom'], font=font(13), fill=(237, 226, 190))
        board.save(os.path.join(REPO, 'apercus', 'planche_%s.png' % mode), optimize=True)


def main(apercu=False):
    M = json.loads(open(os.path.join(REPO, 'kit.json'), encoding='utf-8').read())
    if not any(c['id'] == FEUIL for c in M['calques']):
        M['calques'].append({'id': FEUIL, 'nom': "Feuillage d'immersion — cadre PMD"})
    for room in M['salles']:
        jour = feuillage_salle(room)
        soft = (jour[:, :, 3] > 0) & (jour[:, :, 3] < 255)
        nuitv = nuit(jour, soft)
        px = int((jour[:, :, 3] > 0).sum())
        if apercu:
            w, h = room['dimensions']
            comp = Image.open(os.path.join(REPO, room['fichiers']['jour']['png'])).convert('RGBA')
            comp.alpha_composite(Image.fromarray(jour, 'RGBA'))
            fond = Image.new('RGBA', (w, h), (0, 0, 0, 255))
            fond.alpha_composite(comp)
            fond.convert('RGB').save('/tmp/apercu_feuillage_%s.png' % room['id'])
            Image.fromarray(jour, 'RGBA').save('/tmp/feuillage_seul_%s.png' % room['id'])
            print(room['id'], 'feuillage px', px)
            continue
        ecrire_salle(room, jour, nuitv)
        print(room['id'], room['nom'], '— feuillage', px, 'px')
    if apercu:
        return
    with open(os.path.join(REPO, 'kit.json'), 'w', encoding='utf-8') as f:
        json.dump(M, f, ensure_ascii=False, indent=2)
    planches(M)
    print('Cadre de feuillage ajouté : 12e calque, jour et nuit, passages dégagés.')


if __name__ == '__main__':
    main(apercu='--apercu' in __import__('sys').argv)
