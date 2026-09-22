"""Map blueprints: authored geometry, then frozen as hand-editable text.

A blueprint starts as a list of carving primitives (organic masses, corridors,
pools) so silhouettes stay continuous instead of rectangular platform stacks.
The first build rasterises them and writes ``layouts/<id>.txt``; that text file is
then the authority for every later build, so a reviewer can retune a corridor by
hand without touching code.

Legend: ``#`` wall mass, ``.`` floor, ``~`` secondary (water / ledge, native),
``S`` arrival cell, ``X`` exit passage cell, ``R`` reserved empty floor (future
structures, props or scripts - deliberately left bare).
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYOUT_DIR = HERE / 'layouts'
W, H = 27, 21  # cells; at 24 px this is 648x504, the audited Brine Cave size

# ellipse: (cx, cy, rx, ry) in cell units, centre-based and inclusive
def ellipse(box):
    cx, cy, rx, ry = box
    return dict(kind='e', cx=cx, cy=cy, rx=rx, ry=ry)


def rect(*box):
    x0, y0, x1, y1 = box
    return dict(kind='r', x0=x0, y0=y0, x1=x1, y1=y1)


def _in(shape, x, y):
    if shape['kind'] == 'r':
        return shape['x0'] <= x <= shape['x1'] and shape['y0'] <= y <= shape['y1']
    dx = (x - shape['cx']) / shape['rx']
    dy = (y - shape['cy']) / shape['ry']
    return dx * dx + dy * dy <= 1.0


BLUEPRINTS = {
    # Les salles sont organiques, les obstacles sont des blocs : ce sont les masses
    # compactes qui déclenchent les raccords pleins de l'autotile natif (mask 0xFF),
    # donc les seuls volumes qui rendent correctement à 1x.
    'JC1_entree': dict(
        label='Jungle - hall central, ilots denses, passee nord',
        source='southern_jungle',
        floor=[ellipse((13, 11, 10.8, 7.4)), rect(11, 0, 15, 4), rect(10, 16, 16, 20)],
        rock=[rect(4, 3, 8, 4), rect(18, 3, 22, 4), rect(2, 9, 4, 12), rect(22, 9, 24, 12),
              rect(4, 17, 8, 18), rect(18, 17, 22, 18)],
        secondary=[rect(8, 7, 11, 9), rect(15, 7, 18, 9), rect(8, 13, 11, 15),
                   rect(15, 13, 18, 15), rect(8, 5, 11, 6), rect(15, 5, 18, 6)],
        protected=[rect(12, 0, 14, 20)],
        reserved=[rect(10, 17, 16, 19)],
        spawn=(13, 19), exit=(13, 0),
        connections=dict(north='JC1_finale', south='exterieur (a brancher)'),
    ),
    'JC1_finale': dict(
        label='Jungle - arene, fosse annulaire, pont central',
        source='southern_jungle',
        floor=[ellipse((13, 10.5, 11.5, 8.6)), rect(12, 17, 14, 20), rect(12, 0, 14, 3)],
        rock=[rect(2, 3, 9, 5), rect(17, 3, 24, 5), rect(2, 16, 9, 18), rect(17, 16, 24, 18)],
        secondary=[rect(5, 6, 10, 14), rect(16, 6, 21, 14)],
        protected=[rect(12, 0, 14, 20)],
        reserved=[rect(11, 9, 15, 11)],
        spawn=(13, 20), exit=(13, 0),
        connections=dict(north='sortie reservee (boss / relique)', south='JC1_entree'),
    ),
    'TC1_entree': dict(
        label='Foret - clairiere large, bosquets, entree sud',
        source='treeshroud_forest_1',
        floor=[ellipse((13, 11, 11.0, 7.6)), rect(11, 0, 15, 4), rect(10, 16, 16, 20)],
        rock=[rect(3, 4, 9, 6), rect(17, 4, 23, 6), rect(2, 12, 7, 14), rect(19, 12, 24, 14),
              rect(9, 9, 11, 11), rect(15, 9, 17, 11)],
        secondary=[rect(4, 15, 8, 16), rect(19, 15, 23, 16), rect(8, 6, 11, 7),
                   rect(15, 6, 18, 7), rect(4, 9, 6, 10), rect(20, 9, 22, 10)],
        protected=[rect(12, 0, 14, 20)],
        reserved=[rect(10, 16, 16, 17)],
        spawn=(13, 19), exit=(13, 0),
        connections=dict(north='TC1_finale', south='exterieur (a brancher)'),
    ),
    'TC1_finale': dict(
        label='Foret -allee centrale, deux miroirs d\'eau, bout du bosquet',
        source='treeshroud_forest_1',
        floor=[ellipse((13, 10.5, 11.2, 8.4)), rect(12, 17, 14, 20), rect(12, 0, 14, 3)],
        rock=[rect(11, 4, 15, 5), rect(11, 16, 15, 17), rect(4, 4, 7, 6), rect(19, 4, 22, 6)],
        secondary=[rect(5, 7, 9, 13), rect(17, 7, 21, 13)],
        protected=[rect(12, 0, 14, 5), rect(12, 14, 14, 20)],
        reserved=[rect(11, 7, 15, 13)],
        spawn=(13, 20), exit=(13, 0),
        connections=dict(north='sortie reservee (etage suivant)', south='TC1_entree'),
    ),
}


def rasterise(bp: dict) -> list[str]:
    walls = [[True] * W for _ in range(H)]
    for shape in bp['floor']:
        for y in range(H):
            for x in range(W):
                if _in(shape, x, y):
                    walls[y][x] = False
    for shape in bp.get('rock', []):
        for y in range(H):
            for x in range(W):
                if _in(shape, x, y):
                    walls[y][x] = True
    water = [[False] * W for _ in range(H)]
    for shape in bp.get('secondary', []):
        for y in range(H):
            for x in range(W):
                if _in(shape, x, y):
                    water[y][x] = True
    for shape in bp.get('secondary_cut', []):
        for y in range(H):
            for x in range(W):
                if _in(shape, x, y):
                    water[y][x] = False
    # A through-passage is protected last: reliefs must never seal the route.
    for shape in bp.get('protected', []):
        for y in range(H):
            for x in range(W):
                if _in(shape, x, y):
                    walls[y][x] = False
                    water[y][x] = False
    # A walkable cell sealed by rock or water is a mistake, not a room: fold it
    # back into the mass so the floor layer stays one connected piece.
    sx, sy = bp['spawn']
    reach = {(sx, sy)}
    queue = [(sx, sy)]
    while queue:
        x, y = queue.pop(0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not walls[ny][nx] and not water[ny][nx] and (nx, ny) not in reach:
                reach.add((nx, ny))
                queue.append((nx, ny))
    sealed = 0
    for y in range(H):
        for x in range(W):
            if not walls[y][x] and not water[y][x] and (x, y) not in reach:
                walls[y][x] = True
                sealed += 1
    reserved = [[False] * W for _ in range(H)]
    for shape in bp.get('reserved', []):
        for y in range(H):
            for x in range(W):
                if _in(shape, x, y):
                    reserved[y][x] = True
    bp['sealed_cells'] = sealed
    rows = []
    for y in range(H):
        line = ''
        for x in range(W):
            if walls[y][x]:
                line += '#'
            elif water[y][x]:
                line += '~'
            elif reserved[y][x]:
                line += 'R'
            else:
                line += '.'
        rows.append(list(line))
    for y in range(H):
        for x in range(W):
            if reserved[y][x]:
                assert not walls[y][x] and not water[y][x], ('reservation sur un mur ou une eau', bp.get('label'), x, y)
    for (x, y) in (bp['spawn'], bp['exit']):
        rows[y][x] = 'S' if (x, y) == tuple(bp['spawn']) else 'X'
        assert not walls[y][x] and not water[y][x], (bp, x, y)
    return [''.join(r) for r in rows]


def load(map_id: str) -> tuple[list[str], dict]:
    """Frozen text file wins; the primitives only seed a first run."""
    bp = BLUEPRINTS[map_id]
    LAYOUT_DIR.mkdir(exist_ok=True)
    path = LAYOUT_DIR / f'{map_id}.txt'
    if path.exists():
        # every non-empty line is a row: a row of walls starts with '#', so a
        # comment filter here would silently delete the map.
        rows = [line.rstrip('\n') for line in path.read_text().splitlines() if line.strip()]
    else:
        rows = rasterise(bp)
        path.write_text('\n'.join(rows) + '\n')
    assert len(rows) == H and all(len(r) == W for r in rows), (map_id, len(rows), {len(r) for r in rows})
    assert set(''.join(rows)) <= set('#.~RSX'), (map_id, sorted(set(''.join(rows))))
    return rows, bp


def grids(map_id: str):
    rows, bp = load(map_id)
    chars = [[c for c in r] for r in rows]
    wall = [[c in '#' for c in r] for r in chars]
    floor = [[not c for c in r] for r in wall]
    secondary = [[c in '~' for c in r] for r in chars]
    reserved = [[c in 'R' for c in r] for r in chars]
    # walkable = floor present and secondary (water/ledge) absent
    walk = [[w and not s for w, s in zip(fr, se)] for fr, se in zip(floor, secondary)]
    spawn = next((x, y) for y, r in enumerate(chars) for x, c in enumerate(r) if c == 'S')
    exit_ = next((x, y) for y, r in enumerate(chars) for x, c in enumerate(r) if c == 'X')
    return dict(wall=wall, floor=floor, secondary=secondary, reserved=reserved, walk=walk,
                spawn=spawn, exit=exit_, blueprint=bp, rows=rows)


def check(map_id: str) -> dict:
    """Fast geometry audit: through-path exists, connections are not pinched."""
    g = grids(map_id)
    walk, (sx, sy), (ex, ey) = g['walk'], g['spawn'], g['exit']
    seen = {(sx, sy)}
    queue = [(sx, sy)]
    while queue:
        x, y = queue.pop(0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and walk[ny][nx] and (nx, ny) not in seen:
                seen.add((nx, ny))
                queue.append((nx, ny))
    assert (ex, ey) in seen, f'{map_id}: sortie inatteignable depuis l arrivee'
    # A cell whose four cardinal neighbours are all blocked is a trap.
    dead = [(x, y) for y in range(H) for x in range(W)
            if walk[y][x] and (x, y) != (sx, sy) and not any(
                0 <= x + dx < W and 0 <= y + dy < H and walk[y + dy][x + dx]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    reachable_ratio = len(seen) / max(1, sum(sum(r) for r in walk))
    assert reachable_ratio > .97, f'{map_id}: {len(seen)}/{sum(sum(r) for r in walk)} cases atteignables'
    # Edge connections must be at least three cells wide, or fully walled.
    def run_width(row):
        best = cur = 0
        for c in row:
            cur = cur + 1 if c else 0
            best = max(best, cur)
        return best
    edges = dict(north=run_width(walk[0]), south=run_width(walk[H - 1]),
                 west=run_width([walk[y][0] for y in range(H)]),
                 east=run_width([walk[y][W - 1] for y in range(H)]))
    for side, width in edges.items():
        assert width in (0,) or width >= 3, f'{map_id}: connexion {side} de {width} case(s)'
    return dict(reachable_cells=len(seen), reachable_ratio=round(reachable_ratio, 4),
                total_walkable=sum(sum(r) for r in walk),
                dead_end_cells=dead, edge_openings={k: v for k, v in edges.items() if v},
                floor_cells=W * H - sum(sum(r) for r in g['wall']),
                wall_cells=sum(sum(r) for r in g['wall']),
                secondary_cells=sum(sum(r) for r in g['secondary']),
                reserved_cells=sum(sum(r) for r in g['reserved']),
                sealed_pockets=g['blueprint'].get('sealed_cells', 0))


MAPS = list(BLUEPRINTS)
