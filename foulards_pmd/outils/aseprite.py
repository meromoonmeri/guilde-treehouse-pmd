"""
aseprite.py — écriture de fichiers .aseprite.

Trois niveaux :
  ecrire        une image, plusieurs calques
  ecrire_anime  plusieurs images, plusieurs calques
  ecrire_avance groupes de calques, modes de fusion, opacités, tags
                d'animation et palette embarquée

Format binaire repris de source/rebuild_kit.py et étendu. Les chunks Layer ne
sont écrits que dans la première image ; chaque image porte ensuite ses Cel.
Les calques de type groupe n'ont pas de Cel, mais comptent dans l'indice.
"""

import struct
import zlib
from PIL import Image

# Modes de fusion Aseprite
NORMAL, MULTIPLIER, ECRAN, INCRUSTATION = 0, 1, 2, 3
ECLAIRCIR, LUMIERE_CRUE, DIFFERENCE = 5, 8, 10
ADDITION, SOUSTRACTION = 16, 17

# Sens de lecture des tags
AVANT, ARRIERE, PING_PONG = 0, 1, 2


def _astr(s):
    b = s.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def _chunk(kind, data):
    return struct.pack("<IH", len(data) + 6, kind) + data


def _layer(nom, type_=0, niveau=0, fusion=NORMAL, opacite=255, visible=True,
           collapse=False):
    flags = (1 if visible else 0) | 2 | (32 if collapse else 0)
    return _chunk(0x2004,
                  struct.pack("<HHHHHHB", flags, type_, niveau, 0, 0,
                              fusion, opacite)
                  + b"\0" * 3 + _astr(nom))


def _cel(index, im):
    box = im.getbbox()
    if box:
        x, y, _, _ = box
        q = im.crop(box)
    else:
        x = y = 0
        q = Image.new("RGBA", (1, 1))
    return _chunk(0x2005,
                  struct.pack("<HhhBHh", index, x, y, 255, 2, 0)
                  + b"\0" * 5
                  + struct.pack("<HH", q.width, q.height)
                  + zlib.compress(q.tobytes(), 9))


def _palette(couleurs):
    """Chunk palette 0x2019, plus l'ancien 0x0004 pour la compatibilité."""
    n = len(couleurs)
    d = struct.pack("<III", n, 0, n - 1) + b"\0" * 8
    for (r, g, b) in couleurs:
        d += struct.pack("<HBBBB", 0, r, g, b, 255)
    vieux = struct.pack("<H", 1) + struct.pack("<BB", 0, min(n, 255))
    for (r, g, b) in couleurs[:255]:
        vieux += bytes((r, g, b))
    return _chunk(0x2019, d) + _chunk(0x0004, vieux)


def _tags(tags):
    """tags : liste de (nom, debut, fin, sens, (r, g, b))."""
    d = struct.pack("<H", len(tags)) + b"\0" * 8
    for nom, deb, fin, sens, coul in tags:
        d += struct.pack("<HHB", deb, fin, sens) + b"\0" * 8
        d += bytes(coul) + b"\0"
        d += _astr(nom)
    return _chunk(0x2018, d)


def _frame(chunks, duree_ms):
    data = b"".join(chunks)
    return struct.pack("<IHHH2sI", len(data) + 16, 0xF1FA,
                       min(len(chunks), 0xFFFF), int(duree_ms),
                       b"\0\0", len(chunks)) + data


def _ecrire_fichier(chemin, frames, taille, duree0):
    w, h = taille
    corps = b"".join(frames)
    header = bytearray(128)
    struct.pack_into("<IHHHHHIH", header, 0, len(corps) + 128, 0xA5E0,
                     len(frames), w, h, 32, 1, int(duree0))
    struct.pack_into("<HBBhhHH", header, 32, 0, 1, 1, 0, 0, 8, 8)
    with open(chemin, "wb") as f:
        f.write(bytes(header) + corps)


# --------------------------------------------------------------------------

def ecrire(chemin, calques, taille, duree_ms=100):
    ecrire_anime(chemin, [n for n, _ in calques],
                 [{n: im for n, im in calques}], taille, duree_ms)


def ecrire_anime(chemin, noms_calques, images, taille, duree_ms=100):
    structure = [{"nom": n} for n in noms_calques]
    ecrire_avance(chemin, structure, images, taille, duree_ms)


def ecrire_avance(chemin, structure, images, taille, duree_ms=100,
                  palette=None, tags=None):
    """
    structure : liste ordonnée, du fond vers l'avant, de dictionnaires
        nom       str
        type      "calque" (défaut) ou "groupe"
        niveau    profondeur d'imbrication, 0 à la racine
        fusion    mode de fusion, voir les constantes du module
        opacite   0 à 255
        visible   bool
        collapse  bool, groupe replié à l'ouverture
    images  : liste de {nom_calque: image RGBA}, une entrée par image
    tags    : liste de (nom, debut, fin, sens, (r, g, b))
    """
    w, h = taille
    if isinstance(duree_ms, int):
        duree_ms = [duree_ms] * len(images)
    vide = Image.new("RGBA", (w, h))

    frames = []
    for i, jeu in enumerate(images):
        chunks = []
        if i == 0:
            if palette:
                chunks.append(_palette(palette))
            for c in structure:
                chunks.append(_layer(
                    c["nom"],
                    1 if c.get("type") == "groupe" else 0,
                    c.get("niveau", 0),
                    c.get("fusion", NORMAL),
                    c.get("opacite", 255),
                    c.get("visible", True),
                    c.get("collapse", False)))
            if tags:
                chunks.append(_tags(tags))
        for j, c in enumerate(structure):
            if c.get("type") == "groupe":
                continue
            chunks.append(_cel(j, jeu.get(c["nom"], vide)))
        frames.append(_frame(chunks, duree_ms[i]))

    _ecrire_fichier(chemin, frames, taille, duree_ms[0])
