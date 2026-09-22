"""Autotile rules transcribed from the audited PMDO engine sources.

Bit order and variant selection follow
`source/dungeon_autotiles_v1/references/engine/AutoTileAdjacent.cs`
(Dir4 bits 0..3 = Down, Left, Up, Right; quad bits 4..7 only when the two adjacent
cardinals and the diagonal agree) and `SelectTileVariant`. A set bit means "the
same autotile mass continues there", which is what makes 0xFF the interior cell.
The sheet slot layout comes from `DtefImportHelper.cs` `FieldDtefMapping`.

Nothing here invents a mask: 47 configurations must appear, as documented in
MANUEL_METHODE_PMDO.md and renders/donjons_dtef_v2.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / 'source/dungeon_autotiles_v1/references/engine'

#  2
# 1 3      Dir4 index -> (dy, dx), blocked means "neighbour is not of this type"
#  0
DIR4 = ((1, 0), (0, -1), (-1, 0), (0, 1))
# blockedDirs[n] and blockedDirs[n+1] -> diagonal AddAngles(dir8(n), DownLeft)
DIAG = ((1, -1), (-1, -1), (-1, 1), (1, 1))  # SW, NW, NE, SE


def field_mapping() -> list[int]:
    """The 48-slot sheet layout: slot index -> DTEF mask, -1 for the empty slot."""
    text = (ENGINE / 'DtefImportHelper.cs').read_text()
    body = re.search(r'FieldDtefMapping\s*=\s*\{(.*?)\}', text, re.S).group(1)
    values = [int(t, 16) if t.startswith('0x') else -1
              for t in body.replace('\n', ' ').replace(' ', '').split(',') if t]
    assert len(values) == 48, len(values)
    assert values.count(-1) == 1, values
    return values


def canonical_masks() -> list[int]:
    """Every mask the engine can actually produce: quads require both cardinals."""
    out = set()
    for base in range(16):
        card = [(base >> i) & 1 for i in range(4)]
        for quad in range(16):
            mask = base
            for i in range(4):
                if (quad >> i) & 1 and card[i] and card[(i + 1) % 4]:
                    mask |= 1 << (4 + i)
            out.add(mask)
    return sorted(out)


def neighbor_mask(present, y: int, x: int) -> int:
    """Engine-identical neighbour code for one cell of one type.

    A bit is set when the neighbour *continues the same autotile mass* (this is how
    `AutoTileAdjacent.AutoTileArea` + the audited `DtefImportHelper` sheets resolve:
    0xFF is the interior of a large mass, 0x00 is an isolated cell). Out of bounds
    continues the mass, so cells touching the map edge carry no border decoration.
    """
    rows, cols = len(present), len(present[0])

    def same(dy: int, dx: int) -> bool:
        ny, nx = y + dy, x + dx
        if not (0 <= ny < rows and 0 <= nx < cols):
            return True
        return bool(present[ny][nx])

    mask = 0
    card = []
    for bit, (dy, dx) in enumerate(DIR4):
        value = same(dy, dx)
        card.append(value)
        if value:
            mask |= 1 << bit
    for bit, (dy, dx) in enumerate(DIAG):
        if card[bit] and card[(bit + 1) % 4] and same(dy, dx):
            mask |= 1 << (4 + bit)
    return mask


def variant_code(rand_code: int, count: int) -> int:
    """`SelectTileVariant`: trailing zero bits, capped at count-1 (AutoTileBase.cs)."""
    index = 0
    for _ in range(count - 1):
        if rand_code % 2 == 0:
            index += 1
            rand_code >>= 1
        else:
            break
    return index


def rand_code(x: int, y: int, seed: int) -> int:
    """Deterministic 64-bit stand-in for ReRandom.Get2DUInt64.

    The engine's own RNG is not reproduced here; only its selection algorithm is
    mirrored, so the variant choice is stable and reviewable, not certified equal
    to a runtime roll.
    """
    h = (x * 0x9E3779B97F4A7C15) ^ ((y + 1) * 0xC2B2AE3D27D4EB4F) ^ (seed * 0x165667B19E3779F9)
    h &= (1 << 64) - 1
    h ^= h >> 33
    h = (h * 0xFF51AFD7ED558CCD) & ((1 << 64) - 1)
    h ^= h >> 29
    return h or 1


if __name__ == '__main__':
    masks = canonical_masks()
    mapping = field_mapping()
    print('canonical masks', len(masks))
    assert len(masks) == 47, len(masks)
    assert sorted(m for m in mapping if m >= 0) == masks
    print('FieldDtefMapping slots', mapping.count(-1), 'empty;', 'variant example', [variant_code(v, 3) for v in (1, 2, 4, 8, 16)])
