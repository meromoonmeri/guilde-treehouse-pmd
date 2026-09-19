"""Lecteurs/rendu pour les feuilles `.tile` (TexSize 3 = cellules 24 px) et les
Ground `.rsground` de PMDO/EoSO. Aucune écriture d'image ici : les cellules
sont manipulées comme des blobs PNG natifs, jamais redessinées.
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REF = HERE / 'references'
CELL = 24  # TexSize 3 x 8 px

# Feuille EoSO -> nom unique livré (l'importateur PMDO nomme les tilesets par le
# nom de fichier : des noms neufs évitent toute collision avec un autre mod).
SHEETS = {
    'D01P11A_layer1': 'PLAGE_BC1_LAYER1',
    'D01P11A_layer2': 'PLAGE_BC1_LAYER2',
    'beach_animation': 'PLAGE_BC1_ANIM',
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


class TileSheet:
    """Feuille native : cellule (x, y) -> blob PNG et image RGBA prémultipliée."""

    def __init__(self, path: Path):
        data = path.read_bytes()
        self.path = path
        self.size, count = struct.unpack_from('<ii', data)
        if self.size != CELL or count <= 0:
            raise ValueError(f'{path.name}: en-tête inattendu {self.size}/{count}')
        self.blobs: dict[tuple[int, int], bytes] = {}
        self.images: dict[tuple[int, int], Image.Image] = {}
        cache: dict[int, tuple[bytes, Image.Image]] = {}
        for i in range(count):
            x, y, address = struct.unpack_from('<iiq', data, 8 + i * 16)
            if address not in cache:
                n, = struct.unpack_from('<q', data, address)
                blob = data[address + 8:address + 8 + n]
                image = Image.open(io.BytesIO(blob)).convert('RGBA')
                if image.size != (CELL, CELL):
                    raise ValueError(f'{path.name}: cellule {x},{y} de taille {image.size}')
                cache[address] = (blob, image)
            self.blobs[x, y], self.images[x, y] = cache[address]
        self.width = max(x for x, _ in self.blobs) + 1
        self.height = max(y for _, y in self.blobs) + 1

    def payload_id(self, x: int, y: int) -> str:
        return hashlib.sha256(self.blobs[x, y]).hexdigest()[:16]


def load_sheets(directory: Path = REF, prefix: str = 'EoSO__') -> dict[str, TileSheet]:
    return {name: TileSheet(directory / f'{prefix}{name}.tile') for name in SHEETS}


def load_ground(path: Path) -> dict:
    return json.loads(path.read_bytes().decode('utf-8-sig'))


def dump_ground(document: dict) -> bytes:
    # Même forme que les fichiers natifs : JSON indenté, UTF-8 sans BOM.
    return json.dumps(document, ensure_ascii=False, indent=2).encode('utf-8')


def cell_frames(tile: dict) -> list[tuple[str, int, int]] | None:
    """Séquence (feuille, X, Y) d'une cellule, ou None si vide."""
    if not tile['Layers']:
        return None
    if len(tile['Layers']) != 1:
        raise ValueError('cellule multi-animation non prévue')
    anim = tile['Layers'][0]
    return [(f['Sheet'], f['TexLoc']['X'], f['TexLoc']['Y']) for f in anim['Frames']]


def render_layer(layer: dict, sheets: dict[str, TileSheet], phase: int, alias: dict[str, str] | None = None) -> Image.Image:
    """Compose un calque à la phase donnée (phase = index de frame, modulo)."""
    alias = alias or {}
    columns = layer['Tiles']
    width, height = len(columns), len(columns[0])
    image = Image.new('RGBA', (width * CELL, height * CELL), (0, 0, 0, 0))
    for x, column in enumerate(columns):
        for y, tile in enumerate(column):
            frames = cell_frames(tile)
            if not frames:
                continue
            sheet, tx, ty = frames[phase % len(frames)]
            sheet = alias.get(sheet, sheet)
            image.alpha_composite(sheets[sheet].images[tx, ty], (x * CELL, y * CELL))
    return image


def unpremultiply(image: Image.Image) -> Image.Image:
    a = np.asarray(image.convert('RGBA'), dtype=np.uint16)
    alpha = a[:, :, 3:4]
    rgb = np.where(alpha > 0, np.minimum(255, (a[:, :, :3] * 255 + alpha // 2) // np.maximum(alpha, 1)), 0)
    return Image.fromarray(np.concatenate([rgb, alpha], axis=2).astype(np.uint8), 'RGBA')


def composite(ground: dict, sheets: dict[str, TileSheet], phase: int, alias: dict[str, str] | None = None) -> Image.Image:
    layers = [render_layer(layer, sheets, phase, alias) for layer in ground['Layers']]
    out = layers[0]
    for layer in layers[1:]:
        out.alpha_composite(layer)
    return out
