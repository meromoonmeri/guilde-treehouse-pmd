"""
aseprite.py — écriture de fichiers .aseprite multi-calques et multi-images.

Reprend le format binaire déjà utilisé dans source/rebuild_kit.py de ce dépôt
et l'étend à l'animation : les chunks Layer ne sont écrits que dans la
première image, chaque image portant ensuite ses propres chunks Cel.
"""

import struct
import zlib
from PIL import Image


def _astr(s):
    b = s.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def _chunk(kind, data):
    return struct.pack("<IH", len(data) + 6, kind) + data


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


def _frame(chunks, duree_ms):
    data = b"".join(chunks)
    return struct.pack("<IHHH2sI", len(data) + 16, 0xF1FA,
                       min(len(chunks), 0xFFFF), int(duree_ms),
                       b"\0\0", len(chunks)) + data


def ecrire(chemin, calques, taille, duree_ms=100):
    """Fichier à une seule image. calques : liste de (nom, image RGBA)."""
    ecrire_anime(chemin, [n for n, _ in calques],
                 [{n: im for n, im in calques}], taille, duree_ms)


def ecrire_anime(chemin, noms_calques, images, taille, duree_ms=100):
    """
    Fichier animé.

    noms_calques : ordre des calques, du fond vers l'avant
    images       : liste de dictionnaires {nom_calque: image RGBA}, une entrée
                   par image de l'animation ; un calque absent est vide
    duree_ms     : entier, ou liste d'entiers de même longueur que `images`
    """
    w, h = taille
    if isinstance(duree_ms, int):
        duree_ms = [duree_ms] * len(images)
    vide = Image.new("RGBA", (w, h))

    frames = []
    for i, jeu in enumerate(images):
        chunks = []
        if i == 0:
            for nom in noms_calques:
                chunks.append(_chunk(0x2004,
                                     struct.pack("<HHHHHHB", 3, 0, 0, 0, 0, 0, 255)
                                     + b"\0" * 3 + _astr(nom)))
        for j, nom in enumerate(noms_calques):
            chunks.append(_cel(j, jeu.get(nom, vide)))
        frames.append(_frame(chunks, duree_ms[i]))

    corps = b"".join(frames)
    header = bytearray(128)
    struct.pack_into("<IHHHHHIH", header, 0, len(corps) + 128, 0xA5E0,
                     len(frames), w, h, 32, 1, int(duree_ms[0]))
    struct.pack_into("<HBBhhHH", header, 32, 0, 1, 1, 0, 0, 8, 8)
    with open(chemin, "wb") as f:
        f.write(bytes(header) + corps)
