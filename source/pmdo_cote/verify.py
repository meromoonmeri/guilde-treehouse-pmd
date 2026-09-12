#!/usr/bin/env python3
"""Independent reader: native asset bytes -> reconstructed V2 pixels, plus installer tests.
This is NOT a running PMDO / .NET deserialization test.
"""
import argparse
import io
import json
from pathlib import Path
import shutil
import struct
import tempfile

import numpy as np
from PIL import Image

from INSTALLER import install, read_index, encode_index

ROOT = Path(__file__).resolve().parents[2]


def expected(path):
    a = np.array(Image.open(path).convert('RGBA'), dtype=np.uint16)
    a[:, :, :3] = a[:, :, :3] * a[:, :, 3:4] // 255
    return a.astype('uint8')


def read_dir(path):
    data = path.read_bytes()
    n, = struct.unpack_from('<q', data)
    im = Image.open(io.BytesIO(data[8:8+n])).convert('RGBA')
    w, h, dirs, frames = struct.unpack_from('<4i', data, 8+n)
    assert (w, h) == im.size and dirs == 0 and frames == 1
    assert len(data) == n + 24
    return im


def read_tile(path):
    data = path.read_bytes()
    size, count = struct.unpack_from('<ii', data)
    assert size == 8 and count > 0
    tiles, offsets = {}, {}
    for i in range(count):
        x, y, address = struct.unpack_from('<iiq', data, 8+i*16)
        assert x >= 0 and y >= 0 and address >= 8+count*16
        if address not in offsets:
            n, = struct.unpack_from('<q', data, address)
            assert n > 0 and address+8+n <= len(data)
            image = Image.open(io.BytesIO(data[address+8:address+8+n])).convert('RGBA')
            assert image.size == (8, 8)
            rgba = np.array(image)
            assert np.all(rgba[:, :, :3] <= rgba[:, :, 3:4])
            offsets[address] = image
        assert (x, y) not in tiles
        tiles[x, y] = offsets[address]
    return tiles


def render_layer(layer, banks, phase, size):
    image = Image.new('RGBA', size)
    for x, column in enumerate(layer['Tiles']):
        for y, tile in enumerate(column):
            assert tile['AutoTileset'] == '' and tile['Associates'] == []
            assert len(tile['Layers']) <= 1
            for animation in tile['Layers']:
                assert animation['FrameLength'] > 0
                frame = animation['Frames'][phase % len(animation['Frames'])]
                pixel = banks[frame['Sheet']][frame['TexLoc']['X'], frame['TexLoc']['Y']]
                image.paste(pixel, (x*8, y*8))
    return image


def cloud_view(strip, size, shift):
    image = Image.new('RGBA', size)
    for x in range(-(shift % strip.width), size[0], strip.width):
        image.paste(strip, (x, 8))
    return image


def verify(pack):
    manifest = json.loads((pack / 'manifest.json').read_text())
    banks = {p.stem: read_tile(p) for p in (pack / 'Content/Tile').glob('*.tile')}
    backgrounds = {p.stem: read_dir(p) for p in (pack / 'Content/BG').glob('*.dir')}
    strip = backgrounds['COTEV2_PMDO_NUAGES']
    assert strip.size == (2200, 344)
    assert np.array_equal(np.array(strip), expected(ROOT / 'sprites/cote_v2/COTEV2_NUAGES_WRAP.png'))
    report = {'result': 'PASS', 'runtime_pmdo_tested': False, 'zones': [],
              'checks': ['native binary headers, offsets, PNG payloads and premultiplied alpha',
                         'all map tile/BG references resolve; X-major 8px grids',
                         'terrain, sky, clouds and all 8 sea phases reconstruct source pixels',
                         'native background wrap period and one-pixel seam continuity',
                         'empty structure/object layers, Top=4, empty collision scaffold',
                         'installer dry-run, legacy/namespaced scripts, index merge/backup, idempotence, conflict refusal']}
    for zone in manifest['zones']:
        doc = json.loads((pack / f'Data/Ground/{zone["asset"]}.rsground').read_text())
        assert doc['Version'] == '0.7.15.1'
        obj = doc['Object']
        assert obj['$type'] == 'RogueEssence.Ground.GroundMap, RogueEssence'
        assert obj['TexSize'] == 1 and obj['AssetName'] == zone['asset']
        w, h = zone['grid']
        assert zone['size_px'] == [w*8, h*8]
        size = tuple(zone['size_px'])
        for layer in obj['Layers']:
            assert layer['Visible'] and len(layer['Tiles']) == w
            assert all(len(column) == h for column in layer['Tiles'])
        assert obj['Layers'][-1]['Layer'] == 4
        assert all(not t['Layers'] for layer in obj['Layers'][2:] for c in layer['Tiles'] for t in c)
        assert len(obj['obstacles']) == w
        for x, col in enumerate(obj['obstacles']):
            assert len(col) == h
            for y, wall in enumerate(col):
                assert wall == {'Bounds': {'X': x*8, 'Y': y*8, 'Width': 8, 'Height': 8}, 'Tags': 0}
        assert obj['ActiveChar'] is None
        ent = obj['Entities'][0]
        assert not ent['MapChars'] and not ent['GroundObjects'] and not ent['Spawners']
        assert len(ent['Markers']) == 1 and ent['Markers'][0]['EntName'] == 'entrance'
        source = ROOT / 'sprites/cote_v2' / zone['source']
        files = json.loads((source / 'animation.json').read_text())['files']
        terrain = render_layer(obj['Layers'][1], banks, 0, size)
        assert np.array_equal(np.array(terrain), expected(source / files['terrain']))
        sky = backgrounds[zone['sky']]
        assert np.array_equal(np.array(sky), expected(source / files['sky']))
        assert obj['Background']['$type'] == 'RogueEssence.Dungeon.LayeredBG, RogueEssence'
        bgs = [entry['BG'] for entry in obj['Background']['Layers']]
        assert len(bgs) == 2
        assert all(bg['Parallax'] == '1, 1' and not bg['RepeatY'] for bg in bgs)
        assert bgs[0]['BGAnim']['AnimIndex'] == zone['sky']
        assert bgs[1]['BGAnim']['AnimIndex'] == 'COTEV2_PMDO_NUAGES'
        assert bgs[1]['RepeatX'] and bgs[1]['BGMovement'] == {'X': -12, 'Y': 0}
        assert bgs[1]['MapLoc'] == {'X': 0, 'Y': 8}
        clouds = cloud_view(strip, size, 0)
        assert np.array_equal(np.array(clouds), expected(source / files['clouds_static']))
        assert clouds.tobytes() == cloud_view(strip, size, 2200).tobytes()
        assert cloud_view(strip, size, 2199).crop((1, 0, size[0], size[1])).tobytes() == clouds.crop((0, 0, size[0]-1, size[1])).tobytes()
        for col in obj['Layers'][0]['Tiles']:
            for cell in col:
                for animation in cell['Layers']:
                    assert len(animation['Frames']) == 8 and animation['FrameLength'] == 10
        for phase in range(8):
            sea = render_layer(obj['Layers'][0], banks, phase, size)
            assert np.array_equal(np.array(sea), expected(source / files['sea'][phase]))
        # All current artwork has binary alpha, so straight and premultiplied
        # compositions are identical. Refuse to assume this for future inputs.
        for image in [sky, strip, terrain, sea]:
            assert set(np.unique(np.array(image.getchannel('A')))) <= {0, 255}
        composition = Image.alpha_composite(sky, clouds)
        composition = Image.alpha_composite(composition, render_layer(obj['Layers'][0], banks, 0, size))
        composition = Image.alpha_composite(composition, terrain)
        reference = next(source.glob('*_COMPOSITION_00.png'))
        assert composition.tobytes() == Image.open(reference).convert('RGBA').tobytes()
        report['zones'].append({'asset': zone['asset'], 'pixels': size,
                                'reconstructed_sea_phases': 8, 'pixel_differences': 0})
    # A fake mod with a pre-existing tileset/index tests that nothing is dropped.
    with tempfile.TemporaryDirectory() as tmp:
        mod = Path(tmp) / 'testmod'
        tile_dir = mod / 'Content/Tile'
        tile_dir.mkdir(parents=True)
        (mod / 'Mod.xml').write_text('<Header><Name>Test</Name><Namespace>testmod</Namespace></Header>')
        original = next((pack / 'Content/Tile').glob('*.tile'))
        shutil.copyfile(original, tile_dir / 'Existing.tile')
        data = original.read_bytes()
        _, count = struct.unpack_from('<ii', data)
        original_index = encode_index({'Existing': data[:8+count*16]})
        (tile_dir / 'index.idx').write_bytes(original_index)
        install(pack, mod, dry_run=True)
        assert not (mod / 'Data').exists()
        install(pack, mod)
        nodes = read_index(tile_dir / 'index.idx')
        assert nodes['Existing'] == data[:8+count*16]
        assert len(nodes) == len(banks) + 1
        backups = list(tile_dir.glob('*.bak'))
        assert len(backups) == 1 and backups[0].read_bytes() == original_index
        before = {p.relative_to(mod): p.read_bytes() for p in mod.rglob('*') if p.is_file()}
        install(pack, mod)
        assert before == {p.relative_to(mod): p.read_bytes() for p in mod.rglob('*') if p.is_file()}
        for zone in manifest['zones']:
            assert (mod / f'Data/Script/testmod/ground/{zone["asset"]}/init.lua').is_file()
        existing_map = next((mod / 'Data/Ground').glob('*.rsground'))
        existing_map.write_text('user edited structure')
        try:
            install(pack, mod)
            raise AssertionError('Installer overwrote an edited map!')
        except ValueError as exc:
            assert 'Conflits' in str(exc)
        assert existing_map.read_text() == 'user edited structure'
    (pack / 'verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pack', nargs='?', type=Path, default=Path('/home/user/.cache/cote_pmdo_pack'))
    verify(parser.parse_args().pack.resolve())
