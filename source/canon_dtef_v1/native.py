"""Exact native extraction from the pinned PMDO DumpAsset banks.

A bank cell is used as stored: no resize, no rotation, no mirror, no recolour.
Two views of every tile are kept, because MANUEL_METHODE_PMDO.md §14 requires
comparing in the right alpha space:

* ``stored``   : RGBA exactly as it sits inside the ``.tile`` file (premultiplied)
                 -> used for the ``.tile`` / Ground export;
* ``straight`` : the same pixels de-multiplied -> used for the layered PNG previews.

Sheet layout follows the audited ``DtefImportHelper.cs`` and the convention already
used by `renders/donjons_dtef_v2`: one 432x192 sheet per variant, three 6x8 blocks
(Wall / Secondary / Floor), animated groups as extra frame sheets. Unlike V2, no
native-pixel "bombing" is applied here: every cell is a whole bank tile.
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / 'source/donjons_dtef_v2/references'
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / 'source/cote_v4_abyss'))
from night import night  # the existing, user-requested Abyss filter  # noqa: E402

TYPES = ('wall', 'secondary', 'floor')
TYPE_INDEX = {n: i for i, n in enumerate(TYPES)}
COLS, ROWS, TILE = 6, 8, 24
SHEET = (COLS * len(TYPES) * TILE, ROWS * TILE)


def straight(im: Image.Image) -> Image.Image:
    a = np.array(im, dtype='uint32')
    alpha = a[:, :, 3:4]
    a[:, :, :3] = np.minimum(255, (a[:, :, :3] * 255 + alpha // 2) // np.maximum(alpha, 1))
    a[alpha[:, :, 0] == 0] = 0
    return Image.fromarray(a.astype('uint8'))


def decode_tile(path: Path) -> dict:
    """.tile = int32 tileSize, int32 count, count * (int32 x, int32 y, int64 off), payload."""
    raw = path.read_bytes()
    size, count = struct.unpack_from('<ii', raw)
    assert size == TILE, (path, size)
    out, seen = {}, {}
    for i in range(count):
        x, y, off = struct.unpack_from('<iiq', raw, 8 + i * 16)
        length, = struct.unpack_from('<q', raw, off)
        if off not in seen:
            im = Image.open(io.BytesIO(raw[off + 8:off + 8 + length])).convert('RGBA')
            assert im.size == (TILE, TILE), (path, x, y, im.size)
            seen[off] = im
        out[(x, y)] = seen[off]
    return out


class Bank:
    """One dungeon theme: its autotile definitions and the single native sheet they cite."""

    def __init__(self, theme: str, source: str, verify_hashes: bool = True):
        self.theme, self.source = theme, source
        from autotile import field_mapping
        mapping = field_mapping()
        self.slot = {m: i for i, m in enumerate(mapping) if m >= 0}
        self.base, self.anim, self.groups, self.gid_of, self.variant_count = {}, {}, {}, {}, {}
        self._read_autotiles()
        sheets = sorted({name for name in self._sheets})
        assert len(sheets) == 1, (source, sheets)  # one native bank per dungeon here
        self.sheet_name = sheets[0]
        self.tile_path = REFS / 'DumpAsset/Content/Tile' / f'{self.sheet_name}.tile'
        self.sha256 = hashlib.sha256(self.tile_path.read_bytes()).hexdigest()
        if verify_hashes:
            prov = json.loads((REFS / 'provenance.json').read_text())
            entry = next((p for p in prov if p['path'].endswith(self.tile_path.name)), None)
            assert entry is None or entry['sha256'] == self.sha256, self.tile_path.name
        self.stored = decode_tile(self.tile_path)
        self.view = {k: straight(v) for k, v in self.stored.items()}
        self.night_view = {k: night(v) for k, v in self.view.items()}
        for loc in list(self.base.values()) + [l for g in self.anim.values() for locs in g.values() for l in locs]:
            assert loc in self.stored, (source, loc)

    def _read_autotiles(self):
        for typ, kind in enumerate(TYPES):
            obj = json.loads((REFS / 'DumpAsset/Data/AutoTile' / f'{self.source}_{kind}.json')
                             .read_text(encoding='utf-8-sig'))['Object']['Tiles']
            if not hasattr(self, '_sheets'):
                self._sheets = set()
            entries = {int(k[5:], 16): v for k, v in obj.items() if k.startswith('Tilex')}
            assert len(entries) == 47, (self.source, kind, len(entries))
            for mask in sorted(entries):
                variants = entries[mask]
                self.variant_count[(typ, mask)] = max(1, len(variants))
                for vi, layers in enumerate(variants):
                    for layer in layers:
                        for f in layer['Frames']:
                            self._sheets.add(f['Sheet'])
                    assert len(layers[0]['Frames']) == 1, (kind, mask, vi)
                    self.base[(typ, vi, mask)] = (layers[0]['Frames'][0]['TexLoc']['X'],
                                                   layers[0]['Frames'][0]['TexLoc']['Y'])
                    for li, layer in enumerate(layers[1:], start=1):
                        key = (typ, li, len(layer['Frames']), layer['FrameLength'])
                        if key not in self.gid_of:
                            self.gid_of[key] = len(self.groups)
                            self.groups[len(self.groups)] = key
                        gid = self.gid_of[key]
                        locs = [(f['TexLoc']['X'], f['TexLoc']['Y']) for f in layer['Frames']]
                        self.anim.setdefault((typ, vi, mask), {})[gid] = locs

    # ---- addressing -------------------------------------------------------
    def xy(self, typ: int, mask: int) -> tuple[int, int]:
        s = self.slot[mask]
        return ((typ * COLS + s % COLS) * TILE, s // COLS * TILE)

    def tile(self, loc, mode: str = 'jour') -> Image.Image:
        return self.night_view[loc] if mode == 'nuit' else self.view[loc]

    def frame_count(self, typ: int, variant: int, mask: int) -> dict:
        return {g: len(l) for g, l in self.anim.get((typ, variant, mask), {}).items()}

    def duration(self, gid: int) -> int:
        return self.groups[gid][3]

    # ---- sheets -----------------------------------------------------------
    def sheet(self, variant: int, mode: str = 'jour', gid: int | None = None,
              frame: int = 0) -> Image.Image:
        """One 432x192 sheet; ``gid=None`` is the static base of the three types."""
        out = Image.new('RGBA', SHEET)
        for (typ, vi, mask), loc in (self.base.items() if gid is None else []):
            if vi == variant:
                out.alpha_composite(self.tile(loc, mode), self.xy(typ, mask))
        if gid is not None:
            for (typ, vi, mask), groups in self.anim.items():
                if vi != variant or gid not in groups:
                    continue
                locs = groups[gid]
                if frame < len(locs):
                    out.alpha_composite(self.tile(locs[frame], mode), self.xy(typ, mask))
        return out

    def sheet_names(self) -> list[str]:
        names = [f'tileset_{v}.png' for v in range(3)]
        for gid, (typ, li, count, dur) in sorted(self.groups.items()):
            variants = sorted({v for (t, v, m) in self.anim if t == typ and gid in self.anim[(t, v, m)]})
            for v in variants:
                for fi in range(count):
                    names.append(f'tileset_{v}_frame{gid}_{fi}.{dur}.png')
        return [n for n in names]
