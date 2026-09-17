#!/usr/bin/env python3
"""Build native RogueEssence Ground/Tile/Dir assets from the approved V2 PNGs.
Run with the repository .venv (Pillow, numpy); output staging is outside Git.
Binary layouts are from RogueEssence 8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b.
"""
import argparse
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'sprites/cote_v2'


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def premult(image):
    a = np.array(image.convert('RGBA'), dtype=np.uint16)
    a[:, :, :3] = a[:, :, :3] * a[:, :, 3:4] // 255
    return Image.fromarray(a.astype('uint8'))


def png_bytes(image, archive_tiles=False):
    stream = io.BytesIO()
    # Raw DEFLATE inside tiny tile PNGs lets the outer ZIP compress similarities
    # across adjacent tiles; fully standard PNG, decoded pixels unchanged.
    image.save(stream, format='PNG', compress_level=0 if archive_tiles else 9)
    return stream.getvalue()


def write_dir(path, image):
    raw = png_bytes(premult(image))
    save(path, struct.pack('<q', len(raw)) + raw + struct.pack('<4i', *image.size, 0, 1))


class TileBank:
    def __init__(self, name, preserve_layout=False):
        self.name = name
        self.preserve_layout = preserve_layout
        self.data = {}
        self.ids = {}

    def add(self, tile, x, y):
        tile = premult(tile)
        if not tile.getchannel('A').getbbox():
            return None
        raw = tile.tobytes()
        if self.preserve_layout:
            loc = (x, y)
        else:
            if raw not in self.ids:
                n = len(self.ids)
                self.ids[raw] = (n % 32, n // 32)
            loc = self.ids[raw]
        self.data[loc] = raw
        return {'Sheet': self.name, 'TexLoc': {'X': loc[0], 'Y': loc[1]}}

    def write(self, path):
        # Native TileIndexNode header followed by BaseSheet records. Shared offsets
        # are legal and exactly how ImportHelper.SaveTileSheet deduplicates tiles.
        offset = 8 + 16 * len(self.data)
        offsets, payload, entries = {}, bytearray(), []
        for (x, y), raw in self.data.items():
            if raw not in offsets:
                data = png_bytes(Image.frombytes('RGBA', (8, 8), raw), archive_tiles=True)
                offsets[raw] = offset + len(payload)
                payload.extend(struct.pack('<q', len(data)) + data)
            entries.append(struct.pack('<iiq', x, y, offsets[raw]))
        save(path, struct.pack('<ii', 8, len(entries)) + b''.join(entries) + payload)


def auto(frames=(), length=60):
    return {'AutoTileset': '', 'Associates': [],
            'Layers': [{'Frames': list(frames), 'FrameLength': length}] if frames else [],
            'NeighborCode': 0 if frames else -1}


def layer(name, width, height, frames=None, length=60, draw=0):
    return {'Name': name, 'Layer': draw, 'Visible': True,
            'Tiles': [[auto(frames(x, y), length) if frames else auto()
                       for y in range(height)] for x in range(width)]}


def background(name, y=0, movement=0, wrap=False):
    return {'$type': 'RogueEssence.Dungeon.MapBG, RogueEssence',
            'MapLoc': {'X': 0, 'Y': y},
            'BGAnim': {'AnimIndex': name, 'FrameTime': 1, 'StartFrame': -1,
                       'EndFrame': -1, 'AnimDir': -1, 'Alpha': 255, 'AnimFlip': 0},
            'BGMovement': {'X': movement, 'Y': 0}, 'Parallax': '1, 1',
            'RepeatX': wrap, 'RepeatY': False}


def build(out):
    cloud_name = 'COTEV2_PMDO_NUAGES'
    write_dir(out / f'Content/BG/{cloud_name}.dir', Image.open(SOURCE / 'COTEV2_NUAGES_WRAP.png'))
    manifest = {'native_schema_version': '0.7.15.1', 'tex_size': 1, 'tile_px': 8,
                'sea_frame_length': 10, 'sea_frame_ms': 1000 / 6,
                'sea_loop_ms': 8000 / 6, 'cloud_speed_px_s': -12,
                'cloud_period_px': 2200, 'collisions': 'empty/editor scaffold',
                'runtime_tested': False, 'zones': []}
    for number, slug, label in [(1, '01_promontoire', 'Promontoire'), (2, '02_terrasse', 'Terrasse')]:
        directory = SOURCE / slug
        metadata = json.loads((directory / 'animation.json').read_text())
        files = metadata['files']
        terrain = Image.open(directory / files['terrain']).convert('RGBA')
        sea = [Image.open(directory / name).convert('RGBA') for name in files['sea']]
        sky = Image.open(directory / files['sky']).convert('RGBA')
        width, height = terrain.width // 8, terrain.height // 8
        asset = f'cote_v2_{slug.split("_", 1)[1]}'
        prefix = f'COTEV2_PMDO_{number:02d}'
        sky_name = prefix + '_CIEL'
        write_dir(out / f'Content/BG/{sky_name}.dir', sky)
        banks = [TileBank(prefix + '_MER'), TileBank(prefix + '_TERRAIN', True)]

        def terrain_frames(x, y):
            f = banks[1].add(terrain.crop((x*8, y*8, x*8+8, y*8+8)), x, y)
            return [f] if f else []

        def sea_frames(x, y):
            frames = [banks[0].add(im.crop((x*8, y*8, x*8+8, y*8+8)), x, y) for im in sea]
            assert all(f is None for f in frames) or all(f is not None for f in frames)
            return frames if frames[0] is not None else []

        layers = [layer('00 Mer - cycle palette 8 phases', width, height, sea_frames, 10),
                  layer('01 Terrain - falaises et herbe', width, height, terrain_frames),
                  layer('02 Vos sols et chemins', width, height),
                  layer('03 Vos structures - base', width, height),
                  layer('04 Vos structures - avant-plan', width, height, draw=4)]
        # Pick an opaque grass patch, not a sea/cliff location. This is only an
        # editor entry marker: no player, NPC, buildings or automatic collisions.
        pixels = np.array(terrain).astype('int16')
        green = ((pixels[:, :, 1] >= pixels[:, :, 0] - 8) &
                 (pixels[:, :, 1] > pixels[:, :, 2] + 50) &
                 (pixels[:, :, 1] > 170) & (pixels[:, :, 3] == 255))
        candidates = []
        for y in range(24, terrain.height - 24, 8):
            for x in range(24, terrain.width - 24, 8):
                score = green[y-16:y+16, x-16:x+16].mean()
                candidates.append((score, -abs(x-terrain.width//2)-abs(y-terrain.height//3), x, y))
        score, _, x, y = max(candidates)
        assert score > .8, (asset, score)
        marker = {'EntName': 'entrance', 'Direction': 0, 'EntEnabled': True,
                  'triggerType': 0, 'Collider': {'X': x-8, 'Y': y-8, 'Width': 16, 'Height': 16}}
        obj = {'$type': 'RogueEssence.Ground.GroundMap, RogueEssence',
               'TexSize': 1, 'Name': {'DefaultText': f'Cote V2 - {label}', 'LocalTexts': {}},
               'Released': False, 'Comment': 'Base editable V2. Collisions et gameplay a creer. Art genere, non canonique.',
               'obstacles': [[{'Bounds': {'X': xx*8, 'Y': yy*8, 'Width': 8, 'Height': 8}, 'Tags': 0}
                              for yy in range(height)] for xx in range(width)],
               'rand': {'$type': 'RogueElements.ReRandom, RogueElements', 'FirstSeed': 0,
                        's': [16294208416658607535, 7960286522194355700, 487617019471545679, 17909611376780542444]},
               'Status': {}, 'Background': {'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence',
                                            'Layers': [{'BG': background(sky_name)},
                                                       {'BG': background(cloud_name, 8, -12, True)}]},
               'BlankBG': auto(), 'Layers': layers, 'AssetName': asset, 'Music': '',
               'EdgeView': 0, 'NoSwitching': False, 'ViewCenter': None, 'ViewOffset': {'X': 0, 'Y': 0},
               'ActiveChar': None,
               'Decorations': [{'Name': 'Vos decorations', 'Layer': 2, 'Visible': True, 'Anims': []}],
               'Entities': [{'Name': 'Vos objets et personnages', 'Visible': True, 'MapChars': [],
                             'GroundObjects': [], 'Spawners': [], 'Markers': [marker]}]}
        doc = {'Version': '0.7.15.1', 'Object': obj}
        save(out / f'Data/Ground/{asset}.rsground', json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode())
        save(out / f'Data/Script/ground/{asset}/init.lua',
             f'-- Editable coastal scaffold. Animation is native, not scripted.\nlocal {asset} = {{}}\nreturn {asset}\n'.encode())
        for bank in banks:
            bank.write(out / f'Content/Tile/{bank.name}.tile')
        manifest['zones'].append({'asset': asset, 'source': slug, 'size_px': terrain.size,
                                  'grid': [width, height], 'entry_px': [x-8, y-8],
                                  'tilesets': [b.name for b in banks], 'sky': sky_name})
        print(asset, terrain.size, 'marker', (x-8, y-8), 'grass ratio', score)
    save(out / 'manifest.json', json.dumps(manifest, indent=2).encode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('/home/user/.cache/cote_pmdo_pack'))
    args = parser.parse_args()
    build(args.output.resolve())
