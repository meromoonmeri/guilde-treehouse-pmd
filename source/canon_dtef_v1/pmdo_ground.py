"""Native PMDO asset writers (Ground + .tile), following the audited formats.

`MANUEL_METHODE_PMDO.md` sections 14-16 describe these layouts; the writer adapts
`source/pmdo_cote/build.py`, whose serialisations were deserialised by the real
PMDO 0.8.12 loader during the coast packs (`source/cote_v5_expeditions`).

Scale rule: our Ground packs use TexSize=1 (8 px cells) while the DTEF banks are
24 px, so one native tile becomes nine 8 px cells, cropped without touching a
single pixel: ground cell (X, Y) = (3*TX + dx, 3*TY + dy).
"""
from __future__ import annotations

import io
import json
import struct
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

CELL = 8
NATIVE_TILE = 24
SUB = NATIVE_TILE // CELL


def save(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def premult(image: Image.Image) -> Image.Image:
    a = np.array(image.convert('RGBA'), dtype=np.uint16)
    a[:, :, :3] = a[:, :, :3] * a[:, :, 3:4] // 255
    return Image.fromarray(a.astype('uint8'))


def png_bytes(image: Image.Image) -> bytes:
    stream = io.BytesIO()
    image.save(stream, format='PNG', compress_level=0)  # raw DEFLATE; outer ZIP compresses
    return stream.getvalue()


class TileBank:
    """Sparse (x, y) -> 8 px PNG payload bank, deduplicated like SaveTileSheet."""

    def __init__(self, name: str, cell: int = CELL):
        self.name, self.cell = name, cell
        self.data: dict[tuple[int, int], bytes] = {}
        self.registered = 0

    def add_tile(self, loc: tuple[int, int], payload: Image.Image):
        """Split one native tile into SUB*SUB ground cells at natural coordinates."""
        for dy in range(SUB):
            for dx in range(SUB):
                crop = payload.crop((dx * self.cell, dy * self.cell,
                                     (dx + 1) * self.cell, (dy + 1) * self.cell))
                self.data[(loc[0] * SUB + dx, loc[1] * SUB + dy)] = crop.tobytes()
        self.registered += 1

    def write(self, path: Path):
        size = self.cell
        header_len = 8 + 16 * len(self.data)
        offsets, payload, entries = {}, bytearray(), []
        for (x, y), raw in sorted(self.data.items()):
            if raw not in offsets:
                data = png_bytes(Image.frombytes('RGBA', (size, size), raw))
                offsets[raw] = header_len + len(payload)
                payload.extend(struct.pack('<q', len(data)) + data)
            entries.append(struct.pack('<iiq', x, y, offsets[raw]))
        save(path, struct.pack('<ii', size, len(entries)) + b''.join(entries) + bytes(payload))
        return {'bank': self.name, 'cells': len(self.data), 'unique_png': len(offsets),
                'native_tiles_registered': self.registered}


def empty_cell():
    return {'AutoTileset': '', 'Associates': [], 'Layers': [], 'NeighborCode': -1}


def ground_layer(name: str, cells, draw: int = 0):
    """cells[X][Y] is None, or a list of (frames, frame_length) engine layers."""
    grid = []
    for X in range(len(cells)):
        column = []
        for Y in range(len(cells[0])):
            entry = cells[X][Y]
            if entry is None:
                column.append(empty_cell())
            else:
                column.append({'AutoTileset': '', 'Associates': [],
                               'Layers': [{'Frames': list(frames), 'FrameLength': dur} for frames, dur in entry],
                               'NeighborCode': -1})
        grid.append(column)
    return {'Name': name, 'Layer': draw, 'Visible': True, 'Tiles': grid}


def marker(name: str, x: int, y: int, w: int = 16, h: int = 16):
    return {'EntName': name, 'Direction': 0, 'EntEnabled': True, 'triggerType': 0,
            'Collider': {'X': int(x - w / 2), 'Y': int(y - h / 2), 'Width': w, 'Height': h}}


def ground_doc(asset: str, title: str, comment: str, layers, obstacles, markers):
    width, height = len(obstacles), len(obstacles[0])
    obj = {
        '$type': 'RogueEssence.Ground.GroundMap, RogueEssence',
        'TexSize': 1,
        'Name': {'DefaultText': title, 'LocalTexts': {}},
        'Released': False, 'Comment': comment,
        'obstacles': [[{'Bounds': {'X': x * CELL, 'Y': y * CELL, 'Width': CELL, 'Height': CELL},
                        'Tags': obstacles[x][y]} for y in range(height)] for x in range(width)],
        'rand': {'$type': 'RogueElements.ReRandom, RogueElements', 'FirstSeed': 0,
                 's': [16294208416658607535, 7960286522194355700, 487617019471545679, 17909611376780542444]},
        'Status': {},
        # No sky layer: the DTEF banks carry no background art, and inventing one
        # would be the kind of unannounced addition the manual forbids.
        'Background': {'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
        'BlankBG': empty_cell(),
        'Layers': layers, 'AssetName': asset, 'Music': '', 'EdgeView': 0, 'NoSwitching': False,
        'ViewCenter': None, 'ViewOffset': {'X': 0, 'Y': 0}, 'ActiveChar': None,
        'Decorations': [{'Name': 'Decorations (aucune posee)', 'Layer': 2, 'Visible': True, 'Anims': []}],
        'Entities': [{'Name': 'Marqueurs de reprise', 'Visible': True, 'MapChars': [],
                      'GroundObjects': [], 'Spawners': [], 'Markers': markers}],
    }
    return {'Version': '0.8.12.0', 'Object': obj}


MOD_XML = """<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Canonia DTEF - cartes en cellules natives</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : 4 cartes souterraines composees de cellules natives DTEF (Jungle, Foret). Jour et nuit. Aucune tuile peinte ; pas une aventure jouable.</Description>
  <Namespace>{namespace}</Namespace>
  <UUID>{uuid}</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>0.8.12.0</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
"""


def write_mod_xml(path: Path, namespace: str):
    ident = uuid.uuid5(uuid.NAMESPACE_URL, f'https://github.com/meromoonmeri/guilde-treehouse-pmd/{namespace}')
    save(path, MOD_XML.format(namespace=namespace, uuid=ident).encode())


def read_index_node(path: Path) -> bytes:
    with path.open('rb') as f:
        header = f.read(8)
        size, count = struct.unpack('<ii', header)
        assert size > 0 and 0 <= count <= 10_000_000, path
        return header + f.read(count * 16)


def read_index(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_bytes()
    count, = struct.unpack_from('<i', raw)
    off, nodes = 4, {}
    for _ in range(count):
        size, shift = 0, 0
        while True:
            b = raw[off]
            off += 1
            size |= (b & 127) << shift
            if b < 128:
                break
            shift += 7
        name = raw[off:off + size].decode('utf-8')
        off += size
        _, n = struct.unpack_from('<ii', raw, off)
        node = raw[off:off + 8 + n * 16]
        off += len(node)
        nodes[name] = node
    return nodes


def encode_index(nodes: dict) -> bytes:
    out = bytearray(struct.pack('<i', len(nodes)))
    for name in sorted(nodes):
        raw = name.encode('utf-8')
        size, header = len(raw), bytearray()
        while size >= 128:
            header.append((size & 127) | 128)
            size >>= 7
        header.append(size)
        out += bytes(header) + raw + nodes[name]
    return bytes(out)


def merge_index(index_path: Path, banks: dict[str, Path]) -> tuple[bytes, list[str]]:
    """Destination-first merge: a partial index would delete other tilesets."""
    nodes = read_index(index_path)
    before = sorted(nodes)
    for name, path in sorted(banks.items()):
        nodes[name] = read_index_node(path)
    return encode_index(nodes), before
