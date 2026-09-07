#!/usr/bin/env python3
"""Moteur paramétrique de sprites PMD SpriteCollab.

Le générateur d'image fournit le langage artistique (placement des pixels,
outlines, clusters, ombres). Ce moteur ne dessine rien : il garantit la
structure technique — grille, palette, cadrage, frames, directions, export.

Étapes :
  1. détramage    : ramène l'image générée à sa vraie résolution pixel
  2. nettoyage    : fond retiré, marges recalculées
  3. palette      : quantification sur une palette commune verrouillée
  4. cadrage      : centrage dans la cellule, ancrage au sol PMD
  5. directions   : 8 directions (4 générées + 4 miroirs)
  6. frames       : animation Idle par déplacements entiers (jamais de flou)
  7. export       : feuilles -Anim.png, AnimData.xml, offsets, aperçu GIF
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

RACINE = Path(__file__).resolve().parent
GENERATION = RACINE / "generation"
SORTIE = RACINE / "terapagos"

# --- paramètres techniques -------------------------------------------------

CELLULE = 64          # taille d'une case d'animation PMD
LARGEUR_CIBLE = 54     # largeur utile visée du sprite, en pixels réels
COULEURS_MAX = 30      # palette SpriteCollab volontairement courte
MARGE_SOL = 4          # pixels entre le bas du sprite et le bas de la cellule

DIRECTIONS = [
    "Bas", "BasDroite", "Droite", "HautDroite",
    "Haut", "HautGauche", "Gauche", "BasGauche",
]
# ordre des lignes dans les feuilles SpriteCollab
ORDRE_FEUILLE = [
    "Bas", "BasDroite", "Droite", "HautDroite",
    "Haut", "HautGauche", "Gauche", "BasGauche",
]
GENEREES = {
    "Bas": "brut_bas.png",
    "BasDroite": "brut_bas_droite.png",
    "Droite": "brut_droite.png",
    "HautDroite": "brut_haut_droite.png",
    "Haut": "brut_haut.png",
}
MIROIRS = {
    "BasGauche": "BasDroite",
    "Gauche": "Droite",
    "HautGauche": "HautDroite",
}


@dataclass
class Animation:
    """Description paramétrique d'une animation PMD."""

    nom: str
    duree: list[int]
    # décalages entiers (dx, dy) appliqués au sprite, frame par frame
    deplacements: list[tuple[int, int]]
    # facteur d'écrasement vertical par frame, en pixels entiers
    ecrasements: list[int] = field(default_factory=list)
    boucle: bool = True

    @property
    def frames(self) -> int:
        return len(self.duree)


ANIMATIONS = [
    # respiration : le corps monte d'un pixel puis se tasse d'un pixel
    Animation(
        nom="Idle",
        duree=[12, 10, 12, 10],
        deplacements=[(0, 0), (0, -1), (0, 0), (0, 1)],
        ecrasements=[0, 0, 0, 1],
    ),
    # marche : Terapagos rampe, le corps oscille latéralement d'un pixel
    Animation(
        nom="Walk",
        duree=[6, 6, 6, 6],
        deplacements=[(0, 0), (-1, -1), (0, 0), (1, -1)],
        ecrasements=[0, 0, 0, 0],
    ),
    # dégât : recul net puis retour
    Animation(
        nom="Hurt",
        duree=[8, 10],
        deplacements=[(0, 1), (0, 2)],
        ecrasements=[1, 2],
        boucle=False,
    ),
]


# --- 1. détramage ----------------------------------------------------------

def detecter_pas(masque: np.ndarray) -> int:
    """Retrouve la taille du bloc de pixels utilisée par l'image générée."""
    meilleurs = []
    for axe in (0, 1):
        proj = masque.any(axis=1 - axe)
        transitions = np.flatnonzero(np.diff(proj.astype(np.int8)) != 0) + 1
        if len(transitions) < 2:
            continue
        ecarts = np.diff(transitions)
        ecarts = ecarts[ecarts > 0]
        if len(ecarts):
            meilleurs.append(int(np.gcd.reduce(ecarts)))
    if not meilleurs:
        return 1
    pas = int(np.gcd.reduce(np.array(meilleurs)))
    return max(1, pas)


def detramer(img: Image.Image) -> Image.Image:
    """Ramène l'image à un pixel réel par pixel logique."""
    rgba = img.convert("RGBA")
    a = np.array(rgba)
    masque = a[..., 3] > 8
    if not masque.any():
        return rgba
    pas = detecter_pas(masque)
    if pas <= 1:
        return rgba
    w, h = rgba.size
    return rgba.resize((max(1, w // pas), max(1, h // pas)), Image.NEAREST)


# --- 2. nettoyage ----------------------------------------------------------

def retirer_fond(img: Image.Image) -> Image.Image:
    """Retire le fond magenta ou blanc, sans manger l'outline du sprite."""
    a = np.array(img.convert("RGBA")).astype(np.int16)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    magenta = (r > 200) & (b > 200) & (g < 110)
    blanc = (r > 238) & (g > 238) & (b > 238)
    fond = magenta | blanc

    # on ne supprime que le fond connecté aux bords, pour garder
    # les éclats clairs internes (facettes, spéculaires)
    h, w = fond.shape
    vu = np.zeros_like(fond)
    pile = [(0, x) for x in range(w) if fond[0, x]]
    pile += [(h - 1, x) for x in range(w) if fond[h - 1, x]]
    pile += [(y, 0) for y in range(h) if fond[y, 0]]
    pile += [(y, w - 1) for y in range(h) if fond[y, w - 1]]
    while pile:
        y, x = pile.pop()
        if vu[y, x] or not fond[y, x]:
            continue
        vu[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and fond[ny, nx] and not vu[ny, nx]:
                pile.append((ny, nx))

    al[vu] = 0
    a[..., 3] = al
    out = np.clip(a, 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., 3] > 128, 255, 0)  # alpha binaire, jamais semi-transparent
    return Image.fromarray(out, "RGBA")


def recadrer(img: Image.Image) -> Image.Image:
    boite = img.getbbox()
    return img.crop(boite) if boite else img


# --- 3. palette ------------------------------------------------------------

def palette_commune(images: list[Image.Image], couleurs: int) -> np.ndarray:
    """Palette unique partagée par toutes les directions.

    Median-cut sur la mosaïque de toutes les directions : contrairement à un
    k-means pondéré par la fréquence, cette découpe conserve les accents rares
    mais essentiels — pupilles cyan, éclats de gemmes, outline sombre.
    """
    largeur = max(im.size[0] for im in images)
    hauteur = sum(im.size[1] for im in images)
    mosaique = Image.new("RGB", (largeur, hauteur), (0, 0, 0))
    masque = Image.new("L", (largeur, hauteur), 0)
    y = 0
    for im in images:
        mosaique.paste(im.convert("RGB"), (0, y))
        masque.paste(im.split()[3], (0, y))
        y += im.size[1]

    # les pixels de fond ne doivent pas peser dans la découpe
    a = np.array(mosaique)
    m = np.array(masque) > 0
    utiles = a[m]
    compact = Image.fromarray(utiles.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    reserve = 8  # entrées gardées pour les extrêmes et les accents
    reduite = compact.quantize(colors=max(2, couleurs - reserve),
                               method=Image.MEDIANCUT, dither=Image.NONE)
    corps = np.array(reduite.getpalette()[: (couleurs - reserve) * 3],
                     dtype=np.uint8).reshape(-1, 3)

    # on complète — sans rien écraser — par les extrêmes et les accents :
    # outline le plus sombre, spéculaire le plus clair, et les teintes les
    # plus saturées (éclats de gemmes, pupilles) que la découpe moyennerait
    u = utiles.astype(np.int32)
    lum = u.sum(1)
    ajouts = [utiles[lum.argmin()], utiles[lum.argmax()]]

    chroma = u.max(1) - u.min(1)
    for i in np.argsort(-chroma):
        if len(ajouts) >= reserve or chroma[i] < 60:
            break
        c = utiles[i]
        if all(int(((c.astype(np.int32) - d.astype(np.int32)) ** 2).sum()) > 1200
               for d in list(corps) + ajouts):
            ajouts.append(c)

    return np.concatenate([corps, np.array(ajouts, dtype=np.uint8)])


def appliquer_palette(img: Image.Image, palette: np.ndarray) -> Image.Image:
    a = np.array(img).astype(np.int16)
    masque = a[..., 3] > 0
    px = a[masque][:, :3].astype(np.float32)
    if len(px):
        d = ((px[:, None, :] - palette[None, :, :].astype(np.float32)) ** 2).sum(2)
        px = palette[d.argmin(1)]
        a[masque, 0:3] = px
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


# --- 4. cadrage ------------------------------------------------------------

def mettre_a_echelle(img: Image.Image, largeur: int) -> Image.Image:
    w, h = img.size
    if w == 0:
        return img
    facteur = largeur / w
    return img.resize((max(1, round(w * facteur)), max(1, round(h * facteur))), Image.NEAREST)


def poser_en_cellule(img: Image.Image, dx: int = 0, dy: int = 0,
                     ecrasement: int = 0) -> Image.Image:
    """Centre le sprite dans la cellule, pieds ancrés au sol PMD."""
    corps = img
    if ecrasement:
        w, h = corps.size
        corps = corps.resize((w, max(1, h - ecrasement)), Image.NEAREST)
    cel = Image.new("RGBA", (CELLULE, CELLULE), (0, 0, 0, 0))
    x = (CELLULE - corps.size[0]) // 2 + dx
    y = CELLULE - MARGE_SOL - corps.size[1] + dy + (ecrasement if ecrasement else 0)
    cel.alpha_composite(corps, (x, y))
    return cel


# --- 5/6/7. construction et export ----------------------------------------

def charger_directions() -> dict[str, Image.Image]:
    base: dict[str, Image.Image] = {}
    for direction, fichier in GENEREES.items():
        chemin = GENERATION / fichier
        if not chemin.exists():
            raise SystemExit(f"source manquante : {chemin}")
        im = recadrer(retirer_fond(detramer(Image.open(chemin))))
        base[direction] = im
    for cible, source in MIROIRS.items():
        base[cible] = base[source].transpose(Image.FLIP_LEFT_RIGHT)
    return base


def harmoniser(base: dict[str, Image.Image]) -> dict[str, Image.Image]:
    """Même échelle et même palette pour les huit directions."""
    reference = base["Bas"]
    facteur = LARGEUR_CIBLE / reference.size[0]
    mis = {}
    for nom, im in base.items():
        w, h = im.size
        mis[nom] = im.resize((max(1, round(w * facteur)), max(1, round(h * facteur))),
                             Image.NEAREST)
    # deuxième passe d'alpha binaire après redimensionnement
    for nom, im in mis.items():
        a = np.array(im)
        a[..., 3] = np.where(a[..., 3] > 128, 255, 0)
        mis[nom] = recadrer(Image.fromarray(a, "RGBA"))

    palette = palette_commune(list(mis.values()), COULEURS_MAX)
    return {nom: appliquer_palette(im, palette) for nom, im in mis.items()}, palette


def construire_feuille(dirs: dict[str, Image.Image], anim: Animation) -> Image.Image:
    feuille = Image.new("RGBA", (CELLULE * anim.frames, CELLULE * len(ORDRE_FEUILLE)),
                        (0, 0, 0, 0))
    for ligne, nom in enumerate(ORDRE_FEUILLE):
        for i in range(anim.frames):
            dx, dy = anim.deplacements[i]
            ec = anim.ecrasements[i] if anim.ecrasements else 0
            cel = poser_en_cellule(dirs[nom], dx, dy, ec)
            feuille.alpha_composite(cel, (CELLULE * i, CELLULE * ligne))
    return feuille


def construire_ombres(anim: Animation) -> Image.Image:
    """Feuille -Shadow.png : un point d'ombre par frame, comme SpriteCollab."""
    feuille = Image.new("RGBA", (CELLULE * anim.frames, CELLULE * len(ORDRE_FEUILLE)),
                        (0, 0, 0, 0))
    point = Image.new("RGBA", (2, 2), (255, 255, 255, 255))
    for ligne in range(len(ORDRE_FEUILLE)):
        for i in range(anim.frames):
            x = CELLULE * i + CELLULE // 2 - 1
            y = CELLULE * ligne + CELLULE - MARGE_SOL - 2
            feuille.alpha_composite(point, (x, y))
    return feuille


def ecrire_animdata(animations: list[Animation], dossier: Path) -> None:
    racine = ET.Element("AnimData")
    ET.SubElement(racine, "ShadowSize").text = "1"
    anims = ET.SubElement(racine, "Anims")
    for a in animations:
        n = ET.SubElement(anims, "Anim")
        ET.SubElement(n, "Name").text = a.nom
        ET.SubElement(n, "Index").text = str(ANIMATIONS.index(a))
        ET.SubElement(n, "FrameWidth").text = str(CELLULE)
        ET.SubElement(n, "FrameHeight").text = str(CELLULE)
        durees = ET.SubElement(n, "Durations")
        for d in a.duree:
            ET.SubElement(durees, "Duration").text = str(d)
    ET.indent(racine, space="  ")
    (dossier / "AnimData.xml").write_bytes(
        ET.tostring(racine, encoding="utf-8", xml_declaration=True))


def ecrire_gif(dirs: dict[str, Image.Image], anim: Animation, chemin: Path) -> None:
    frames = []
    for i in range(anim.frames):
        bande = Image.new("RGBA", (CELLULE * len(ORDRE_FEUILLE), CELLULE), (34, 40, 56, 255))
        for col, nom in enumerate(ORDRE_FEUILLE):
            dx, dy = anim.deplacements[i]
            ec = anim.ecrasements[i] if anim.ecrasements else 0
            bande.alpha_composite(poser_en_cellule(dirs[nom], dx, dy, ec), (CELLULE * col, 0))
        z = bande.resize((bande.size[0] * 2, bande.size[1] * 2), Image.NEAREST)
        frames.append(z.convert("P", palette=Image.ADAPTIVE))
    frames[0].save(chemin, save_all=True, append_images=frames[1:],
                   duration=[int(d * 1000 / 60) for d in anim.duree], loop=0, disposal=2)


def main() -> None:
    SORTIE.mkdir(parents=True, exist_ok=True)
    base = charger_directions()
    dirs, palette = harmoniser(base)

    for anim in ANIMATIONS:
        construire_feuille(dirs, anim).save(SORTIE / f"{anim.nom}-Anim.png")
        construire_ombres(anim).save(SORTIE / f"{anim.nom}-Shadow.png")
    ecrire_animdata(ANIMATIONS, SORTIE)
    ecrire_gif(dirs, ANIMATIONS[0], SORTIE / "apercu_idle.gif")

    # planche de contrôle : les huit directions côte à côte
    planche = Image.new("RGBA", (CELLULE * 8, CELLULE), (0, 0, 0, 0))
    for col, nom in enumerate(ORDRE_FEUILLE):
        planche.alpha_composite(poser_en_cellule(dirs[nom]), (CELLULE * col, 0))
    planche.save(SORTIE / "planche_directions.png")
    planche.resize((planche.size[0] * 3, planche.size[1] * 3), Image.NEAREST).save(
        SORTIE / "planche_directions_x3.png")

    fiche = {
        "pokemon": "Terapagos",
        "forme": "Normale",
        "cellule": CELLULE,
        "largeur_utile": LARGEUR_CIBLE,
        "marge_sol": MARGE_SOL,
        "directions": ORDRE_FEUILLE,
        "miroirs": MIROIRS,
        "palette": ["#%02X%02X%02X" % tuple(c) for c in palette],
        "animations": [
            {"nom": a.nom, "frames": a.frames, "durees": a.duree, "boucle": a.boucle}
            for a in ANIMATIONS
        ],
    }
    (SORTIE / "sprite.json").write_text(json.dumps(fiche, indent=2, ensure_ascii=False))
    print("palette :", " ".join(fiche["palette"]))
    print("écrit dans", SORTIE)


if __name__ == "__main__":
    main()
