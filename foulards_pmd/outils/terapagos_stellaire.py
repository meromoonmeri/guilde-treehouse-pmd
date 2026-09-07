"""
terapagos_stellaire.py — construit la forme Stellaire de Terapagos (#1024)
au format PMDCollab / SpriteCollab.

SpriteCollab possède la forme Normale (racine) et la forme Terastal (0001),
mais pas la forme Stellaire. Or, d'après les sources officielles, le corps de
la forme Stellaire est *identique* à celui de la forme Terastal : ce qui change
est ce qui l'entoure. La forme Stellaire est donc construite par composition,
sur les planches Terastal de SpriteCollab :

  * les symboles de type de la carapace virent au cyan ;
  * le corps flotte au-dessus d'un dôme de cristal indigo à facettes
    hexagonales, posé au sol (ancré sur le pixel blanc de Shadow.png) ;
  * dix-huit gemmes hexagonales, une par type, tournent autour du dôme ;
  * la gemme centrale de la carapace s'élève en une couronne sertie de
    losanges colorés ;
  * au-dessus flottent un Terapagos miniature en cristal et le symbole
    Terastal.

Chaque case est recadrée dans une grille plus grande, et les trois planches du
format (Anim / Offsets / Shadow) sont régénérées de façon cohérente.

Sortie : sprite/1024/0002/ prêt à déposer dans une arborescence SpriteCollab,
plus les sources .aseprite en calques séparés.
"""

import os
import sys
import math
import shutil
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P
import aseprite

SRC = os.path.join(P.DOS_SPRITE, "1024", "0001")     # forme Terastal
RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                      "terapagos_stellaire"))
DST = os.path.join(RACINE, "sprite", "1024", "0002")
DOS_ASE = os.path.join(RACINE, "aseprite")

PADX, PADT, PADB = 8, 22, 8

# --------------------------------------------------------------------------
# Palettes
# --------------------------------------------------------------------------

# Les dix-huit types, dans l'ordre du jeu.
TYPES = [
    ("normal",   (0xB8, 0xB8, 0x98)), ("feu",      (0xF8, 0x80, 0x30)),
    ("eau",      (0x68, 0x90, 0xF0)), ("electrik", (0xF8, 0xD0, 0x30)),
    ("plante",   (0x78, 0xC8, 0x50)), ("glace",    (0x98, 0xD8, 0xD8)),
    ("combat",   (0xD0, 0x40, 0x38)), ("poison",   (0xB0, 0x50, 0xB0)),
    ("sol",      (0xE0, 0xC0, 0x68)), ("vol",      (0xA8, 0x98, 0xF0)),
    ("psy",      (0xF8, 0x58, 0x88)), ("insecte",  (0xB8, 0xC8, 0x28)),
    ("roche",    (0xC8, 0xB0, 0x48)), ("spectre",  (0x80, 0x68, 0xB0)),
    ("dragon",   (0x78, 0x38, 0xF8)), ("tenebres", (0x80, 0x68, 0x58)),
    ("acier",    (0xC0, 0xC0, 0xD8)), ("fee",      (0xEE, 0x99, 0xAC)),
]

DOME = {
    "contour": (0x10, 0x12, 0x40),
    "ombre":   (0x21, 0x27, 0x74),
    "base":    (0x33, 0x3C, 0xA8),
    "clair":   (0x4E, 0x5C, 0xD4),
    "lumiere": (0x82, 0x92, 0xF0),
    "facette": (0x1B, 0x20, 0x60),
}

CRISTAL = {
    "contour": (0x14, 0x1B, 0x52),
    "ombre":   (0x3E, 0x8E, 0xB8),
    "base":    (0x7F, 0xDF, 0xEF),
    "lumiere": (0xE8, 0xFF, 0xFF),
}

# Les accents colorés des scutes de la forme Terastal passent au cyan.
VERS_CYAN = {
    (0xE7, 0x4F, 0x87): (0x4F, 0xD7, 0xEF),
    (0x7F, 0xDF, 0x57): (0x6F, 0xEF, 0xEF),
    (0xFF, 0xE7, 0x37): (0x9F, 0xF7, 0xFF),
    (0xFF, 0x2A, 0x2A): (0x37, 0xBF, 0xE7),
    (0xA7, 0x4F, 0xEF): (0x5F, 0xCF, 0xF7),
    (0xFF, 0x77, 0x37): (0x7F, 0xE7, 0xF7),
}


# --------------------------------------------------------------------------
# Primitives de dessin
# --------------------------------------------------------------------------

class Calque:
    def __init__(self, w, h):
        self.a = np.zeros((h, w, 4), dtype=np.uint8)
        self.h, self.w = h, w

    def set(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x, 0:3] = c
            self.a[y, x, 3] = 255

    def img(self):
        return Image.fromarray(self.a, "RGBA")


def _melange(c1, c2, t):
    return tuple(max(0, min(255, int(round(int(c1[i]) + (int(c2[i]) - int(c1[i])) * t))))
                 for i in range(3))


def _hex_id(x, y, s):
    """Identifiant de tuile hexagonale (grille pointe en haut) pour (x, y)."""
    q = (math.sqrt(3) / 3.0 * x - y / 3.0) / s
    r = (2.0 / 3.0 * y) / s
    xc, zc = q, r
    yc = -xc - zc
    rx_, ry_, rz_ = round(xc), round(yc), round(zc)
    dx, dy, dz = abs(rx_ - xc), abs(ry_ - yc), abs(rz_ - zc)
    if dx > dy and dx > dz:
        rx_ = -ry_ - rz_
    elif dy > dz:
        ry_ = -rx_ - rz_
    else:
        rz_ = -rx_ - ry_
    return (int(rx_), int(rz_))


def profil_dome(rx, hd, rb, y, cy):
    """Demi-largeur du dôme à l'ordonnée y."""
    if y <= cy:
        t = (cy - y) / max(hd, 1e-6)
        if t > 1.0:
            return None
        return rx * math.sqrt(max(0.0, 1.0 - t * t))
    t = (y - cy) / max(rb, 1e-6)
    if t > 1.0:
        return None
    return rx * math.sqrt(max(0.0, 1.0 - t * t))


def dessiner_dome(cal, cx, cy, rx, hd, rb, phase):
    """
    Dôme de cristal : calotte haute à facettes hexagonales, posée au sol en
    (cx, cy), éclairée en haut à gauche. Renvoie sa hauteur.
    """
    pts = set()
    for y in range(int(cy - hd) - 1, int(cy + rb) + 2):
        hw = profil_dome(rx, hd, rb, y, cy)
        if hw is None:
            continue
        for x in range(int(cx - hw), int(cx + hw) + 1):
            pts.add((x, y))

    s = max(2.8, rx / 2.5)
    for (x, y) in pts:
        dx = (x - cx) / max(rx, 1e-6)
        dy = (y - cy) / max(hd, 1e-6)
        ecl = max(0.0, min(1.0, (-dx * 0.40 - dy * 0.90 + 0.55) / 1.55))
        if ecl > 0.82:
            c = DOME["lumiere"]
        elif ecl > 0.62:
            c = DOME["clair"]
        elif ecl > 0.36:
            c = DOME["base"]
        else:
            c = DOME["ombre"]
        # facettes hexagonales, aplaties selon la vue oblique
        interieur = all((x + a, y + b) in pts
                        for a in (-2, -1, 0, 1, 2) for b in (-1, 0, 1))
        if interieur:
            h0 = _hex_id(x - cx, (y - cy) * 1.20, s)
            if any(_hex_id(x + a - cx, (y + b - cy) * 1.20, s) != h0
                   for a, b in ((1, 0), (0, 1))):
                c = _melange(c, DOME["facette"], 0.72)
        if not all((x + a, y + b) in pts
                   for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            c = DOME["contour"]
        cal.set(x, y, c)

    # bourrelet sombre à la base : le dôme se pose au sol au lieu de flotter
    for x in range(int(cx - rx), int(cx + rx) + 1):
        for y in range(int(cy + rb) - 1, int(cy + rb) + 1):
            if (x, y) in pts:
                cal.set(x, y, DOME["contour"])
    # reflet sur la calotte
    for i in range(9):
        t = i / 8.0
        cal.set(cx - rx * 0.42 + t * rx * 0.30,
                cy - hd * (0.90 - 0.16 * t), DOME["lumiere"])
    return hd


def dessiner_gemmes(cal_arr, cal_av, cx, cy, rx, hd, rb, phase, ech):
    """Dix-huit gemmes de type serties en couronne autour du dôme."""
    n = len(TYPES)
    ay = cy - hd * 0.40
    ax, by = rx * 0.88, hd * 0.36
    gw = max(2, int(round(1.7 * ech)))
    gh = max(1, int(round(1.3 * ech)))
    sol = cy + rb - 1
    for i, (_, coul) in enumerate(TYPES):
        a = 2 * math.pi * (i / n) + phase * 2 * math.pi
        px = cx + math.cos(a) * ax
        py = ay + math.sin(a) * by
        devant = math.sin(a) > -0.10
        cal = cal_av if devant else cal_arr
        sombre = _melange(coul, (10, 10, 30), 0.52)
        clair = _melange(coul, (255, 255, 255), 0.50)
        for dy in range(-gh, gh + 1):
            for dx in range(-gw, gw + 1):
                if abs(dx) / (gw + 0.5) + abs(dy) / (gh + 0.5) > 1.0:
                    continue
                if py + dy > sol:
                    continue
                bord = abs(dx) / (gw + 0.5) + abs(dy) / (gh + 0.5) > 0.60
                c = sombre if bord else (clair if (dx <= 0 and dy <= 0) else coul)
                cal.set(px + dx, py + dy, c)


def dessiner_couronne(cal, cx, cy, larg, ech, phase):
    """Couronne sertie qui prolonge la gemme centrale de la carapace."""
    demi = max(2, int(round(larg * 0.17)))
    for x in range(-demi - 1, demi + 2):
        cal.set(cx + x, cy + 1, CRISTAL["contour"])
        cal.set(cx + x, cy + 2, CRISTAL["contour"])
    for x in range(-demi, demi + 1):
        cal.set(cx + x, cy, CRISTAL["base"] if x <= 0 else CRISTAL["ombre"])
    nb = max(3, demi + 1)
    for i in range(nb):
        t = (i + 0.5) / nb
        cal.set(cx - demi + t * 2 * demi, cy, TYPES[(i * 4 + 2) % len(TYPES)][1])

    h_max = max(4, int(round(4.4 * ech)))
    profils = [0.45, 0.78, 1.0, 0.78, 0.45] if demi >= 4 else [0.62, 1.0, 0.62]
    # teintes prismatiques, comme la couronne de l'artwork officiel
    teintes = [(0x9A, 0x7C, 0xF0), (0x6F, 0xD8, 0xF0), (0xE8, 0xFF, 0xFF),
               (0x8F, 0xF0, 0xC8), (0xF0, 0xA8, 0xD8)]
    n = len(profils)
    pas = max(1, int(round(demi * 2 / (n - 1))))
    sommet = cy
    for i, p in enumerate(profils):
        px = cx + (i - (n - 1) / 2) * pas
        haut = max(2, int(round(h_max * p)))
        sommet = min(sommet, cy - haut)
        teinte = teintes[i * len(teintes) // n]
        for j in range(haut):
            t = j / max(haut - 1, 1)
            l = 0 if t > 0.60 else 1
            for dx in range(-l, l + 1):
                if t > 0.62:
                    c = _melange(CRISTAL["lumiere"], teinte, 0.45)
                elif dx <= 0:
                    c = _melange(CRISTAL["base"], teinte, 0.55)
                else:
                    c = _melange(CRISTAL["ombre"], teinte, 0.35)
                cal.set(px + dx, cy - 1 - j, c)
        cal.set(px, cy - haut, CRISTAL["lumiere"])
    return cy - sommet


def dessiner_astre(cal, cx, cy, ech, phase):
    """Terapagos miniature en cristal, surmonté du symbole Terastal."""
    flot = math.sin(phase * 2 * math.pi) * 0.8
    my = cy + flot
    # carapace
    for dx in range(-2, 3):
        cal.set(cx + dx, my, CRISTAL["base"] if dx <= 0 else CRISTAL["ombre"])
    cal.set(cx - 1, my - 1, CRISTAL["lumiere"])
    cal.set(cx, my - 1, CRISTAL["lumiere"])
    cal.set(cx + 1, my - 1, CRISTAL["base"])
    # petite tête à gauche, pattes dessous, liseré sombre
    cal.set(cx - 3, my, CRISTAL["lumiere"])
    cal.set(cx - 2, my + 1, DOME["ombre"])
    cal.set(cx + 1, my + 1, DOME["ombre"])
    for dx in range(-3, 3):
        if dx not in (-2, 1):
            cal.set(cx + dx, my + 1, DOME["contour"])

    sy = my - 5 + flot * 0.5
    for dx, dy in ((0, -2), (0, 2), (-2, -1), (2, -1), (-2, 1), (2, 1)):
        cal.set(cx + dx, sy + dy, CRISTAL["lumiere"])
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        cal.set(cx + dx, sy + dy, CRISTAL["base"])
    cal.set(cx, sy, CRISTAL["lumiere"])


def dessiner_etincelles(cal, cx, cy, rx, hd, phase, ech):
    for i in range(5):
        a = 2 * math.pi * (i / 5.0) + phase * 2 * math.pi * 1.7
        d = rx * (1.12 + 0.12 * math.sin(phase * 6.28 + i))
        px = cx + math.cos(a) * d
        py = cy - hd * 0.60 + math.sin(a) * hd * 0.70
        vif = (math.sin(phase * 6.28 * 2 + i * 1.9) + 1) / 2
        if vif < 0.42:
            continue
        cal.set(px, py, CRISTAL["lumiere"])
        if vif > 0.78:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                cal.set(px + dx, py + dy, CRISTAL["base"])


def recolorer_corps(cell):
    """Symboles de type au cyan, corps légèrement irisé."""
    out = cell.copy()
    rgb = out[..., :3]
    a = out[..., 3] > 0
    for src, dst in VERS_CYAN.items():
        m = a & (rgb[..., 0] == src[0]) & (rgb[..., 1] == src[1]) & (rgb[..., 2] == src[2])
        out[m, 0], out[m, 1], out[m, 2] = dst
    return out


def aura_irisee(cell, phase):
    """Liseré arc-en-ciel sur le bord supérieur de la silhouette."""
    a = cell[..., 3] > 0
    h, w = a.shape
    bord = np.zeros_like(a)
    bord[1:] = a[1:] & ~a[:-1]
    ys, xs = np.nonzero(bord)
    out = cell.copy()
    for x, y in zip(xs, ys):
        t = (x / max(w - 1, 1) + phase) % 1.0
        c = _hsv(t, 0.38, 1.0)
        out[y, x, 0:3] = _melange(tuple(int(v) for v in out[y, x, 0:3]), c, 0.45)
    return out


def _hsv(h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


# --------------------------------------------------------------------------
# Assemblage des planches
# --------------------------------------------------------------------------

def point_sol(shadow, x0, y0, w, h):
    """Pixel blanc de Shadow.png = centre au sol de la case."""
    sub = shadow[y0:y0 + h, x0:x0 + w]
    m = ((sub[..., 0] == 255) & (sub[..., 1] == 255) & (sub[..., 2] == 255)
         & (sub[..., 3] > 0))
    ys, xs = np.nonzero(m)
    if len(xs):
        return float(xs.mean()), float(ys.mean())
    a = sub[..., 3] > 0
    if not a.any():
        return w / 2.0, h * 0.75
    ys, xs = np.nonzero(a)
    return float(xs.mean()), float(ys.max())


def rendre_anim(nom, a, ombre_src):
    """Renvoie (anim, offsets, shadow, calques, dims) pour une animation."""
    src_anim = np.array(Image.open(f"{SRC}/{nom}-Anim.png").convert("RGBA"))
    src_off = np.array(Image.open(f"{SRC}/{nom}-Offsets.png").convert("RGBA"))
    src_sh = np.array(Image.open(f"{SRC}/{nom}-Shadow.png").convert("RGBA"))
    w, h = a["w"], a["h"]
    cols, rows = src_anim.shape[1] // w, src_anim.shape[0] // h
    W, H = w + 2 * PADX, h + PADT + PADB

    # Décalage vertical du corps : constant sur l'animation pour ne pas
    # écraser le mouvement. Calculé pour poser le corps sur la calotte.
    m0 = src_anim[0:h, 0:w, 3] > 0
    ys0, xs0 = np.nonzero(m0)
    largeur_corps = float(xs0.max() - xs0.min() + 1)
    rx = max(9.0, largeur_corps * 0.60)
    hd = rx * 1.02
    rb = rx * 0.30
    ech = max(0.8, min(2.4, largeur_corps / 22.0))

    # Ancrage vertical du corps, calculé une fois par direction (le corps
    # doit poser sur la calotte) puis appliqué à toutes les images de la
    # direction, pour ne pas écraser le mouvement de l'animation.
    dy_par_dir = {}
    for rr in range(rows):
        mm = src_anim[rr * h:(rr + 1) * h, 0:w, 3] > 0
        if not mm.any():
            dy_par_dir[rr] = 0
            continue
        yy = np.nonzero(mm)[0]
        gxx, gyy = point_sol(src_sh, 0, rr * h, w, h)
        dy_par_dir[rr] = int(round((gyy - hd * 0.90) - float(yy.max())))

    noms_calques = ["gemmes_arriere", "dome", "corps", "couronne",
                    "astre", "gemmes_avant", "etincelles"]
    planches = {n: Image.new("RGBA", (W * cols, H * rows)) for n in noms_calques}

    anim = np.zeros((H * rows, W * cols, 4), dtype=np.uint8)
    off = np.zeros_like(anim)
    sha = np.zeros_like(anim)

    for r in range(rows):
        for c in range(cols):
            phase = (c / cols) if cols > 1 else 0.0
            cell = src_anim[r * h:(r + 1) * h, c * w:(c + 1) * w]
            if not (cell[..., 3] > 0).any():
                continue
            gx, gy = point_sol(src_sh, c * w, r * h, w, h)
            cx, cy = gx + PADX, gy + PADT

            cals = {n: Calque(W, H) for n in noms_calques}
            dy_corps = dy_par_dir[r]
            hd_r = dessiner_dome(cals["dome"], cx, cy, rx, hd, rb, phase)
            dessiner_gemmes(cals["gemmes_arriere"], cals["gemmes_avant"],
                            cx, cy, rx, hd, rb, phase, ech)

            # corps
            corps = aura_irisee(recolorer_corps(cell), phase)
            bob = int(round(math.sin(phase * 2 * math.pi) * 0.9))
            cal_corps = Calque(W, H)
            ys, xs = np.nonzero(corps[..., 3] > 0)
            for y, x in zip(ys, xs):
                yy = y + PADT + dy_corps + bob
                xx = x + PADX
                if 0 <= xx < W and 0 <= yy < H:
                    cal_corps.a[yy, xx] = corps[y, x]
            cals["corps"] = cal_corps

            haut_corps = int(ys.min()) + PADT + dy_corps + bob
            cxc = int(round((xs.min() + xs.max()) / 2)) + PADX
            hk = dessiner_couronne(cals["couronne"], cxc, haut_corps + 1,
                                   largeur_corps, ech, phase)
            dessiner_astre(cals["astre"], cxc, haut_corps + 1 - hk - 3, ech, phase)
            dessiner_etincelles(cals["etincelles"], cx, cy, rx, hd_r, phase, ech)

            base = Image.new("RGBA", (W, H))
            for n in noms_calques:
                im = cals[n].img()
                base = Image.alpha_composite(base, im)
                planches[n].paste(im, (c * W, r * H))
            anim[r * H:(r + 1) * H, c * W:(c + 1) * W] = np.array(base)

            # offsets : marqueurs déplacés comme le corps
            so = src_off[r * h:(r + 1) * h, c * w:(c + 1) * w]
            ys2, xs2 = np.nonzero(so[..., 3] > 0)
            for y, x in zip(ys2, xs2):
                yy, xx = y + PADT + dy_corps + bob, x + PADX
                if 0 <= xx < W and 0 <= yy < H:
                    off[r * H + yy, c * W + xx] = so[y, x]

            # ombre : reconstruite à l'emprise du dôme
            for y in range(H):
                for x in range(W):
                    dx = (x - cx) / rx
                    dy = (y - cy) / max(rb * 1.05, 1e-6)
                    d = dx * dx + dy * dy
                    if d <= 0.34:
                        cc = (0, 255, 0)
                    elif d <= 0.66:
                        cc = (255, 0, 0)
                    elif d <= 1.06:
                        cc = (0, 0, 255)
                    else:
                        continue
                    sha[r * H + y, c * W + x] = (*cc, 255)
            sha[r * H + int(round(cy)), c * W + int(round(cx))] = (255, 255, 255, 255)

    return anim, off, sha, planches, (W, H)


def main():
    _, anims = P.lire_animdata(SRC)
    # On ne vide que ce que ce script produit : le dossier contient aussi
    # le README et les aperçus, qui ne doivent pas disparaître à chaque appel.
    for dossier in (DST, DOS_ASE):
        if os.path.isdir(dossier):
            shutil.rmtree(dossier)
        os.makedirs(dossier, exist_ok=True)

    faites, dims = [], {}
    for a in anims:
        if a["copie_de"]:
            continue
        anim, off, sha, planches, (W, H) = rendre_anim(a["nom"], a, 2)
        Image.fromarray(anim).save(f"{DST}/{a['nom']}-Anim.png", optimize=True)
        Image.fromarray(off).save(f"{DST}/{a['nom']}-Offsets.png", optimize=True)
        Image.fromarray(sha).save(f"{DST}/{a['nom']}-Shadow.png", optimize=True)
        aseprite.ecrire(f"{DOS_ASE}/{a['nom']}.aseprite",
                        [(n, im) for n, im in planches.items()],
                        planches["corps"].size)
        dims[a["nom"]] = (W, H)
        faites.append(a["nom"])
        print(f"  {a['nom']:<10} {W}x{H}  planche {anim.shape[1]}x{anim.shape[0]}")

    # AnimData.xml : mêmes animations, nouvelles dimensions, grande ombre
    for a in anims:
        if not a["copie_de"]:
            a["w"], a["h"] = dims[a["nom"]]
    P.ecrire_animdata(f"{DST}/AnimData.xml", 2, anims)

    shutil.copy(f"{SRC}/../credits.txt", f"{DST}/credits.txt")
    print(f"\n{len(faites)} animations écrites dans {DST}")


if __name__ == "__main__":
    main()
