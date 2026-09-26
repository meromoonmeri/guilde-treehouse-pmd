"""Entrée Grotte des Cascades — carte PMD générée sur magenta, format 4:3.

Le générateur produit la composition complète et un sol sous-jacent séparé.
Le magenta sert de clé pour l'eau et le hors-carte; la matière d'eau et son
palette-cycling sont générés pour ce lot. Aucun fragment de map n'est assemblé.
Les ressources générées ne sont pas des pixels de tiles natives certifiés.

Lancer : .venv/bin/python source/entree_grotte_cascade_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import shutil
import struct
import uuid
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = ROOT / 'renders/entree_grotte_cascade_sud_nord_v1'
STAGE = ROOT / '.cache/entree_grotte_cascade_sud_nord_v1/entree_grotte_cascade_sud_nord'
NAMESPACE = 'entree_grotte_cascade_sud_nord'
ASSET = 'egc1_entree_grotte_cascade'
PREFIX = 'EGC1'
REFERENCE = ROOT / 'Waterfall_Cave_ledge_TDS.png'
W, H = 768, 576
SRC_W, SRC_H = 1200, 896
SCALE = H / SRC_H
SCALED_W = round(SRC_W * SCALE)
CROP_X = (SCALED_W - W) // 2
WATER_FRAMES, WATER_TICKS = 12, 10
LOOP_TICKS = WATER_FRAMES * WATER_TICKS


def loadmod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rgb(path):
    return np.asarray(Image.open(path).convert('RGB'), dtype=np.uint8)


def key_magenta(rgb):
    """Key the generated magenta and anti-aliased violet fringe with wider RGB tolerance."""
    a = rgb.astype(np.int16)
    r, g, b = a.transpose(2, 0, 1)
    return (r > 35) & (b > 45) & (g < np.minimum(r, b) * 1.20) & (np.abs(r - b) < 130)


def resize_plane(plane):
    im = Image.fromarray(np.asarray(plane, dtype=np.float32), 'F')
    scaled = np.asarray(im.resize((SCALED_W, H), Image.Resampling.BOX), dtype=np.float32)
    return scaled[:, CROP_X:CROP_X + W]


def resize_color_class(rgb, mask):
    """Uniform BOX reduction of one semantic class, without magenta bleeding."""
    weight = resize_plane(mask.astype(np.float32))
    channels = []
    for c in range(3):
        numer = resize_plane(rgb[..., c].astype(np.float32) * mask)
        channels.append(numer / np.maximum(weight, 1e-6))
    out = np.clip(np.rint(np.stack(channels, axis=2)), 0, 255).astype(np.uint8)
    return out, weight


def resize_mask(mask, threshold=0.40):
    return resize_plane(mask.astype(np.float32)) >= threshold


def nearest_fill(rgb, valid):
    """Fill keyed holes from the nearest real pixel; used only for hidden underlay."""
    if valid.all():
        return rgb.copy()
    if not valid.any():
        raise ValueError('Aucun pixel de sol valide pour compléter le calque de base.')
    nearest = ndi.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    result = rgb.copy()
    holes = ~valid
    result[holes] = rgb[nearest[0][holes], nearest[1][holes]]
    return result


def component_masks(magenta):
    labels, count = ndi.label(magenta)
    sizes = np.bincount(labels.ravel(), minlength=count + 1)
    edge = np.concatenate((labels[0], labels[-1], labels[:, 0], labels[:, -1]))
    edge_ids = set(int(v) for v in np.unique(edge) if v)
    exterior_ids = edge_ids
    water_ids = [i for i in range(1, count + 1) if i not in exterior_ids and sizes[i] >= 800]
    water = np.isin(labels, water_ids)
    exterior = np.isin(labels, list(exterior_ids)) if exterior_ids else np.zeros_like(magenta)
    # Include only small edge antialias/key pixels that belong to the off-map void.
    exterior |= ndi.binary_dilation(exterior, iterations=2) & magenta
    return water, exterior, [{'id': int(i), 'pixels': int(sizes[i]), 'is_water': i in water_ids,
                              'touches_canvas': i in exterior_ids}
                             for i in range(1, count + 1) if sizes[i] >= 80]


def shared_palette(layers, max_colors=96):
    """Apply one small opaque palette to all generated static layers."""
    opaque = [a[a[..., 3] == 255, :3] for a in layers.values() if np.any(a[..., 3] == 255)]
    if not opaque:
        return layers, []
    pixels = np.concatenate(opaque, axis=0)
    sample = Image.fromarray(pixels.reshape(-1, 1, 3), 'RGB')
    palette_image = sample.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT,
                                    dither=Image.Dither.NONE)
    palette = np.asarray(palette_image.getpalette(), dtype=np.uint8).reshape(-1, 3)[:max_colors]
    result = {}
    for name, rgba in layers.items():
        arr = rgba.copy()
        mask = arr[..., 3] == 255
        if mask.any():
            indices = np.asarray(Image.fromarray(arr[..., :3], 'RGB').quantize(
                palette=palette_image, dither=Image.Dither.NONE), dtype=np.uint8)
            arr[..., :3][mask] = palette[indices[mask]]
        arr[arr[..., 3] == 0] = 0
        result[name] = arr
    return result, palette.tolist()


def rgba(colors, mask):
    out = np.zeros((H, W, 4), dtype=np.uint8)
    out[..., :3] = colors
    out[..., 3] = np.asarray(mask, dtype=np.uint8) * 255
    out[~mask] = 0
    return out


def corridor_mask():
    """Broad south-to-north walk corridor measured from the generated composition."""
    yy = np.arange(SRC_H)[:, None]
    xx = np.arange(SRC_W)[None, :]
    half = np.interp(np.arange(SRC_H), [0, 120, 190, 250, 320, 430, 620, 760, 895],
                     [44, 52, 70, 110, 175, 190, 185, 230, 260])[:, None]
    center = SRC_W / 2 + 6 * np.sin(np.arange(SRC_H)[:, None] / 160.0)
    return np.abs(xx - center) <= half


def water_texture():
    """Read and quantize the separately generated magenta-keyed water material."""
    source = read_rgb(RAW / 'eau_matiere_magenta.png')
    key = key_magenta(source)
    material = ~key
    if not material.any():
        raise ValueError('La matière d’eau est entièrement magenta.')
    ys, xs = np.nonzero(material)
    crop = source[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    crop_valid = material[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    crop = nearest_fill(crop, crop_valid)
    # A compact repeated patch preserves the generated water's broad ripple motifs.
    target_h = 112
    target_w = max(48, round(crop.shape[1] * target_h / crop.shape[0]))
    patch = Image.fromarray(crop, 'RGB').resize((target_w, target_h), Image.Resampling.NEAREST)
    q = patch.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = np.asarray(q, dtype=np.uint8)
    pal = np.asarray(q.getpalette(), dtype=np.uint8).reshape(-1, 3)[:16]
    if len(pal) < 16:
        pal = np.pad(pal, ((0, 16 - len(pal)), (0, 0)), mode='edge')
    lum = pal @ np.array([0.299, 0.587, 0.114])
    order = np.argsort(lum, kind='stable')
    inverse = np.empty_like(order)
    inverse[order] = np.arange(16)
    levels = inverse[idx]
    ordered_palette = pal[order]
    return levels.astype(np.uint8), ordered_palette, {
        'source': 'source/entree_grotte_cascade_sud_nord_v1/bruts/eau_matiere_magenta.png',
        'source_role': 'matière générée sur magenta, référencée Waterfall Cave Ledge; non native',
        'palette_size': 16, 'palette_rgb_by_luminance': ordered_palette.tolist(),
        'patch_px': [target_w, target_h], 'cycle_frames': WATER_FRAMES,
        'frame_length_ticks': WATER_TICKS, 'loop_seconds': LOOP_TICKS / 60,
        'animation': 'palette-cycling spatial et scintillement subtil; masque constant; mouvement proposé, non officiel'
    }


def make_water_frames(mask, levels, palette):
    """Compose the indexed generated texture inside keyed pools with a closed LUT cycle."""
    yy, xx = np.mgrid[:H, :W]
    ph, pw = levels.shape
    frames = []
    # Mirrored repetition avoids a hard seam at the patch's tile boundaries.
    levels_tile = np.tile(levels, (int(np.ceil(H / ph)) + 2, int(np.ceil(W / pw)) + 2))
    labels, count = ndi.label(mask)
    component_phase = {}
    for i in range(1, count + 1):
        if np.any(labels == i):
            component_phase[i] = (i * 2.37) % (2 * np.pi)
    for t in range(WATER_FRAMES):
        base_levels = levels_tile[yy % ph, xx % pw].astype(np.float32)
        spatial = (2 * np.pi * (xx / 88.0 + yy / 126.0) - 2 * np.pi * t / WATER_FRAMES)
        delta = np.rint(0.75 * np.sin(spatial)).astype(np.int16)
        phase_idx = np.zeros((H, W), dtype=np.float32)
        for i, phase in component_phase.items():
            phase_idx[labels == i] = phase
        local_delta = np.rint(0.45 * np.sin(spatial + phase_idx)).astype(np.int16)
        cycle_index = np.clip(base_levels.astype(np.int16) + delta + local_delta, 0, 15).astype(np.uint8)
        rgb = palette[cycle_index]
        # Dim the deep outlines very slightly while preserving the fixed generated color motif.
        out = np.zeros((H, W, 4), dtype=np.uint8)
        out[..., :3] = rgb
        out[..., 3] = mask.astype(np.uint8) * 255
        out[~mask] = 0
        frames.append(out)
    return frames


def cell_grid(blocked):
    return blocked.reshape(H // 8, 8, W // 8, 8).mean(axis=(1, 3)) > 0.25


def free_grid(blocked, clearance=2):
    gh, gw = blocked.shape
    free = np.zeros_like(blocked, dtype=bool)
    for y in range(gh - clearance + 1):
        for x in range(gw - clearance + 1):
            free[y, x] = not blocked[y:y + clearance, x:x + clearance].any()
    return free


def reachable(blocked, start, goals, clearance=2, free=None):
    from collections import deque
    gh, gw = blocked.shape
    if free is None:
        free = free_grid(blocked, clearance)
    sy, sx = start
    if not (0 <= sy < gh and 0 <= sx < gw) or not free[sy, sx]:
        return False, None, 0, free
    queue = deque([start])
    seen = np.zeros_like(free)
    seen[start] = True
    parent = {start: None}
    goalset = set(goals)
    while queue:
        current = queue.popleft()
        if current in goalset:
            return True, current, int(seen.sum()), free
        y, x = current
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (y + dy, x + dx)
            if 0 <= nxt[0] < gh - 1 and 0 <= nxt[1] < gw - 1 and free[nxt] and not seen[nxt]:
                seen[nxt] = True
                parent[nxt] = current
                queue.append(nxt)
    return False, None, int(seen.sum()), free


def choose_markers(blocked):
    gh, gw = blocked.shape
    starts = [(y, x) for y in range(gh - 5, gh - 1) for x in range(gw // 2 - 4, gw // 2 + 4)]
    starts.sort(key=lambda p: (abs(p[1] - gw // 2), -p[0]))
    goals = [(y, x) for y in range(16, 28) for x in range(gw // 2 - 8, gw // 2 + 8)]
    goals.sort(key=lambda p: (p[0], abs(p[1] - gw // 2)))
    free = free_grid(blocked)
    for start in starts:
        if not free[start]:
            continue
        ok, goal, explored, _ = reachable(blocked, start, goals, free=free)
        if ok:
            return [start[1] * 8, start[0] * 8], [goal[1] * 8, goal[0] * 8], explored
    raise AssertionError('Aucun chemin libre 16×16 entre le sud et le seuil nord.')


def write_ora(path, layers):
    root = ET.Element('image', w=str(W), h=str(H), name='Entrée Grotte des Cascades')
    stack = ET.SubElement(root, 'stack')
    merged = Image.new('RGBA', (W, H))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        items = list(layers.items())
        for i, (name, arr) in reversed(list(enumerate(items))):
            filename = f'data/layer{i:02d}.png'
            ET.SubElement(stack, 'layer', name=name, src=filename, x='0', y='0', opacity='1.0',
                          visibility='visible', **{'composite-op': 'svg:src-over'})
            stream = io.BytesIO(); Image.fromarray(arr).save(stream, format='PNG')
            z.writestr(filename, stream.getvalue())
        for arr in layers.values():
            merged.alpha_composite(Image.fromarray(arr))
        stream = io.BytesIO(); merged.save(stream, format='PNG')
        z.writestr('mergedimage.png', stream.getvalue())
        thumb = merged.copy(); thumb.thumbnail((256, 256))
        stream = io.BytesIO(); thumb.save(stream, format='PNG')
        z.writestr('Thumbnails/thumbnail.png', stream.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))


def ground_project(stack, blocked, entry_px, threshold_px):
    gfx = loadmod('egc_pmdo_codec', ROOT / 'source/pmdo_cote/build.py')
    tools = loadmod('egc_index_tools', ROOT / 'source/pmdo_cote/INSTALLER.py')
    if STAGE.exists():
        shutil.rmtree(STAGE)
    with zipfile.ZipFile(ROOT / 'mod_metano_expeditions_pmdo_0812.zip') as archive:
        template = json.loads(archive.read(
            'metano_expeditions/Data/Ground/v50812_01_crete_sillage_jour.rsground'))
    obj = template['Object']
    gw, gh = W // 8, H // 8
    layers, banks = [], []
    for i, (name, frame_arrays, ticks) in enumerate(stack):
        bank = gfx.TileBank(f'{PREFIX}_{i:02d}_{name.split()[0].upper()}')
        bank.ids[bytes(256)] = (0, 0)
        bank.data[(0, 0)] = bytes(256)

        def frames_at(x, y, bank=bank, frame_arrays=frame_arrays):
            refs = []
            for frame in frame_arrays:
                tile = Image.fromarray(frame[y * 8:y * 8 + 8, x * 8:x * 8 + 8], 'RGBA')
                ref = bank.add(tile, x, y)
                refs.append(ref if ref is not None else {'Sheet': bank.name, 'TexLoc': {'X': 0, 'Y': 0}})
            if all(ref['TexLoc'] == {'X': 0, 'Y': 0} for ref in refs):
                return []
            if len(refs) == 1:
                return refs
            return refs

        layers.append(gfx.layer(name, gw, gh, frames_at, ticks))
        banks.append(bank)
    layers.append(gfx.layer('05 Vos éléments avant-plan (Top)', gw, gh, draw=4))
    for bank in banks:
        bank.write(STAGE / f'Content/Tile/{bank.name}.tile')
    obj.update(
        Name={'DefaultText': 'Entrée Grotte des Cascades - sud vers nord', 'LocalTexts': {}},
        AssetName=ASSET, Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None,
        ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={}, Layers=layers,
        Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
        Comment=('PMDO 0.8.12. Composition générée sur magenta, référence Waterfall Cave Ledge. '
                 'Eau générée et animée par palette-cycling; pixels non natifs. '
                 'Arrivée sud et seuil nord; destination à raccorder; collisions à contrôler en jeu.'))
    obj['obstacles'] = [[{'Bounds': {'X': x * 8, 'Y': y * 8, 'Width': 8, 'Height': 8},
                          'Tags': int(blocked[y, x])} for y in range(gh)] for x in range(gw)]
    marker = lambda name, point: {'EntName': name, 'Direction': 4, 'EntEnabled': True, 'triggerType': 0,
                                  'Collider': {'X': point[0], 'Y': point[1], 'Width': 16, 'Height': 16}}
    obj['Entities'] = [{'Name': 'Entrées et acteurs à ajouter', 'Visible': True, 'MapChars': [],
                        'GroundObjects': [], 'Spawners': [],
                        'Markers': [marker('entrance', entry_px), marker('donjon_seuil', threshold_px)]}]
    obj['Decorations'] = [{'Name': 'Décorations à ajouter', 'Layer': 2, 'Visible': True, 'Anims': []}]
    template['Version'] = '0.8.12.0'
    gfx.save(STAGE / f'Data/Ground/{ASSET}.rsground',
             json.dumps(template, ensure_ascii=False, separators=(',', ':')).encode())
    lua = (f'-- {ASSET}: carte de base; aucune destination de donjon n’est configurée.\n'
           f'local {ASSET} = {{}}\nreturn {ASSET}\n').encode()
    gfx.save(STAGE / f'Data/Script/{NAMESPACE}/ground/{ASSET}/init.lua', lua)
    nodes = {}
    for tile in sorted((STAGE / 'Content/Tile').glob('*.tile')):
        with tile.open('rb') as stream:
            nodes[tile.stem] = tools.read_node(stream)
    (STAGE / 'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    ident = uuid.uuid5(uuid.NAMESPACE_URL,
                       'https://github.com/meromoonmeri/guilde-treehouse-pmd/' + NAMESPACE)
    (STAGE / 'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Entrée Grotte des Cascades - Atelier PMDO 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Carte d'édition 4:3 générée d'après Waterfall Cave Ledge; calques et eau animée. Pas une aventure jouable.</Description>
  <Namespace>{NAMESPACE}</Namespace>
  <UUID>{ident}</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>0.8.12.0</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
''')
    installer = (ROOT / 'source/pmdo_cote/INSTALLER.py').read_text()
    needle = '            relative = src.relative_to(source)\n'
    if needle not in installer:
        raise RuntimeError('Le point d’insertion de l’index de l’installateur PMDO a changé.')
    installer = installer.replace(needle, needle +
        "            if relative.as_posix() == 'Content/Tile/index.idx':\n                continue\n")
    (STAGE / 'INSTALLER.py').write_text(installer)
    shutil.copyfile(HERE / 'README_PACK.md', STAGE / 'README.md')
    return {bank.name: len(bank.data) for bank in banks}


def build():
    for sub in ['calques', 'animation/eau', 'masques', 'review']:
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    decor_src = read_rgb(RAW / 'decor_magenta.png')
    floor_src = read_rgb(RAW / 'sol_complet.png')
    if decor_src.shape != (SRC_H, SRC_W, 3) or floor_src.shape != decor_src.shape:
        raise ValueError(f'Les bruts doivent mesurer {SRC_W}×{SRC_H}, reçu {decor_src.shape[1]}×{decor_src.shape[0]}.')

    key = key_magenta(decor_src)
    water_src, outside_src, components = component_masks(key)
    map_src = ~outside_src
    # Small internal magenta specks are not turned into water: restore them from the matching generated floor.
    floor_key = key_magenta(floor_src)
    floor_filled = nearest_fill(floor_src, ~floor_key)
    decor_filled = decor_src.copy()
    repairs = key & ~water_src & ~outside_src
    decor_filled[repairs] = floor_filled[repairs]

    yy = np.arange(SRC_H)[:, None]
    corridor = corridor_mask()
    lum = decor_filled @ np.array([0.299, 0.587, 0.114])
    land_src = map_src & ~water_src
    path_src = land_src & corridor & (lum > 82)
    path_src = ndi.binary_closing(path_src, structure=np.ones((7, 7), dtype=bool), iterations=1)
    path_src &= land_src & corridor
    # Keep the original composition partitioned, not re-generated or re-tiled.
    vault_src = land_src & (yy < 250) & ~path_src
    rock_src = land_src & ~path_src & ~vault_src
    class_src = {'outside': outside_src, 'water': water_src,
                 'parois_et_rochers': rock_src, 'chemin': path_src, 'voute_nord': vault_src}
    class_order = list(class_src)
    weights = {k: resize_plane(v.astype(np.float32)) for k, v in class_src.items()}
    weight_stack = np.stack([weights[k] for k in class_order])
    winner = weight_stack.argmax(axis=0)
    coverage = weight_stack.max(axis=0) > 0.04
    exclusive = {k: (winner == i) & coverage for i, k in enumerate(class_order)}
    class_colors = {}
    for k in ('parois_et_rochers', 'chemin', 'voute_nord'):
        class_colors[k], _ = resize_color_class(decor_filled, class_src[k])

    # Complete hidden underlay, constrained to the generated map's footprint.
    floor_colors, _ = resize_color_class(floor_filled, map_src)
    map_mask = resize_mask(map_src, threshold=0.40)
    static = {
        '00_sol_complet': rgba(floor_colors, map_mask),
        '02_parois_rocheuses': rgba(class_colors['parois_et_rochers'], exclusive['parois_et_rochers']),
        '03_chemin': rgba(class_colors['chemin'], exclusive['chemin']),
        '04_voute_et_seuil_nord': rgba(class_colors['voute_nord'], exclusive['voute_nord']),
    }
    static, shared_pal = shared_palette(static, 96)
    water_mask = exclusive['water']
    levels, water_pal, water_meta = water_texture()
    water_frames = make_water_frames(water_mask, levels, water_pal)

    # Collision corridor is derived from the generated layout and the water key, then reduced uniformly.
    walk_src = corridor & land_src & (lum > 70)
    walk_src = ndi.binary_closing(walk_src, structure=np.ones((9, 9), dtype=bool), iterations=1)
    walk_src &= corridor & land_src
    walk_pixels = resize_mask(walk_src, threshold=0.40) & ~water_mask
    blocked = cell_grid(~walk_pixels)
    entry_px, threshold_px, explored = choose_markers(blocked)

    for t, frame in enumerate(water_frames):
        Image.fromarray(frame).save(OUT / 'animation/eau' / f'{PREFIX}_01_eau_caverne_f{t:02d}.png')
    for k, arr in static.items():
        Image.fromarray(arr).save(OUT / 'calques' / f'{PREFIX}_{k}.png')
    Image.fromarray(water_mask.astype(np.uint8) * 255).save(OUT / 'masques' / f'{PREFIX}_masque_eau.png')
    Image.fromarray(walk_pixels.astype(np.uint8) * 255).save(OUT / 'masques' / f'{PREFIX}_masque_praticable.png')
    Image.fromarray(outside_src.astype(np.uint8) * 255).resize((SCALED_W, H), Image.Resampling.NEAREST).crop(
        (CROP_X, 0, CROP_X + W, H)).save(OUT / 'masques' / f'{PREFIX}_masque_hors_carte.png')

    stack_named = [
        ('00 Sol complet', [static['00_sol_complet']], 60),
        ('01 Eau caverne — palette-cycling', water_frames, WATER_TICKS),
        ('02 Parois rocheuses', [static['02_parois_rocheuses']], 60),
        ('03 Chemin sud → nord', [static['03_chemin']], 60),
        ('04 Voûte et seuil nord', [static['04_voute_et_seuil_nord']], 60),
    ]
    def compose(frame_index):
        image = Image.new('RGBA', (W, H))
        for _, frames, _ in stack_named:
            image.alpha_composite(Image.fromarray(frames[frame_index % len(frames)]))
        return image
    scenes = [compose(t) for t in range(WATER_FRAMES)]
    # Empty Top layer is part of the Ground, not a visible PNG.
    write_ora(OUT / f'{PREFIX}_entree_grotte_cascade_calques.ora',
              {name: frames[0] for name, frames, _ in stack_named})
    scenes[0].save(OUT / 'review' / f'{PREFIX}_scene_phase00.png')
    scenes[0].resize((W * 2, H * 2), Image.Resampling.NEAREST).save(
        OUT / 'review' / f'{PREFIX}_scene_x2.png')
    scenes[0].save(OUT / 'review' / f'{PREFIX}_scene_animee.webp', save_all=True,
                   append_images=scenes[1:], duration=round(WATER_TICKS * 1000 / 60),
                   loop=0, lossless=True)
    overlay = Image.new('RGBA', (W, H))
    draw = ImageDraw.Draw(overlay)
    for y, x in zip(*np.nonzero(blocked)):
        draw.rectangle((x * 8, y * 8, x * 8 + 7, y * 8 + 7), fill=(235, 35, 55, 105))
    for point, color in ((entry_px, (255, 230, 45, 255)), (threshold_px, (45, 220, 255, 255))):
        draw.rectangle((point[0], point[1], point[0] + 15, point[1] + 15), outline=color, width=2)
    coll = scenes[0].copy(); coll.alpha_composite(overlay)
    coll.save(OUT / 'review' / f'{PREFIX}_collisions_marqueurs.png')
    viewport_x = min(max(entry_px[0] + 8 - 160, 0), W - 320)
    viewport_y = min(max(entry_px[1] + 8 - 120, 0), H - 240)
    scenes[0].crop((viewport_x, viewport_y, viewport_x + 320, viewport_y + 240)).save(
        OUT / 'review' / f'{PREFIX}_viewport_arrivee.png')

    bank_counts = ground_project(stack_named, blocked, entry_px, threshold_px)
    raw_inputs = []
    for filename in ['decor_magenta.png', 'sol_complet.png', 'eau_matiere_magenta.png']:
        path = RAW / filename
        raw_inputs.append({'file': f'source/{HERE.name}/bruts/{filename}', 'sha256': sha(path),
                           'size_px': list(Image.open(path).size)})
    manifest = {
        'lot': 'entree_grotte_cascade_sud_nord_v1', 'name': 'Entrée Grotte des Cascades',
        'reference': {'file': REFERENCE.name, 'sha256': sha(REFERENCE),
                      'role': 'référence d’ambiance et de composition; aucun pixel de la map source n’est assemblé'},
        'method': ('Générateur : décor complet sur magenta + sol complet séparé + matière d’eau sur magenta; '
                   'normalisation uniforme et segmentation en calques alignés. Pas d’assemblage de morceaux de maps.'),
        'terrain_origin': 'dessin généré en DA PMD; pas une texture native pixel-exacte et pas un tileset officiel',
        'size_px': [W, H], 'ratio': '4:3', 'grid_8px': [W // 8, H // 8],
        'normalization': {'raw_px': [SRC_W, SRC_H], 'scale': SCALE, 'scaled_px': [SCALED_W, H],
                          'crop_x_px': [CROP_X, SCALED_W - W - CROP_X],
                          'method': 'réduction BOX uniforme, couleurs pondérées par classe, attribution exclusive; jamais d’étirement anisotrope'},
        'raw_inputs': raw_inputs, 'magenta_key': {'rule': 'R>35, B>45, G<1.20×min(R,B), |R-B|<130 (tolérance élargie aux franges magenta/violettes anti-crénelées)',
                                                  'water_components': components,
                                                  'selected_water_component_min_px': 800,
                                                  'small_internal_key_pixels': 'remplis avec le sol généré sous-jacent'},
        'static_palette': {'colors_max': 96, 'shared_palette_rgb': shared_pal,
                           'alpha': 'droit, 0 ou 255'},
        'layers_bottom_to_top': [
            {'name': '00 Sol complet', 'origin': 'sol généré séparément; sous-couche éditable'},
            {'name': '01 Eau caverne — palette-cycling', 'frames': WATER_FRAMES,
             'frame_length_ticks': WATER_TICKS, 'origin': 'matière générée séparément; animation proposée'},
            {'name': '02 Parois rocheuses', 'origin': 'composition générée sur magenta'},
            {'name': '03 Chemin sud → nord', 'origin': 'composition générée sur magenta'},
            {'name': '04 Voûte et seuil nord', 'origin': 'composition générée sur magenta'},
            {'name': '05 Top', 'origin': 'calque vide prévu pour les éléments d’avant-plan'}],
        'water': water_meta,
        'scene_loop_ticks': LOOP_TICKS, 'scene_loop_seconds': LOOP_TICKS / 60,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'clearance_px': [16, 16],
                   'path_found': True, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'collision_method': 'corridor généré réduit à la grille; à contrôler avec le collider PMDO en jeu'},
        'pmdo': {'target': '0.8.12', 'serialization': '0.8.12.0', 'asset': ASSET,
                 'namespace': NAMESPACE, 'tex_size': 1, 'tile_px': 8,
                 'layer_count_including_empty_top': len(stack_named) + 1,
                 'tile_banks': bank_counts, 'runtime_tested': False,
                 'warp': 'aucun; le marqueur donjon_seuil reste à raccorder'},
        'art_approved': False, 'gameplay_validated': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    shutil.copyfile(HERE / 'README_PACK.md', STAGE / 'README.md')
    print(json.dumps({'size_px': [W, H], 'water_mask_px': int(water_mask.sum()), 'entry_px': entry_px,
                      'threshold_px': threshold_px, 'blocked_cells': int(blocked.sum()),
                      'water_components': [v for v in components if v['is_water']],
                      'tile_banks': bank_counts}, ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    build()
