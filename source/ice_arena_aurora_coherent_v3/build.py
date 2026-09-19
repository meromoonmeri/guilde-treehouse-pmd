"""Generated coherent terrain proposal; the existing native-derived BG is reused unchanged.
Only the generated terrain is keyed, cropped and resized. No native BG pixels are resampled.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import shutil
import struct
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw

R = Path(__file__).resolve().parents[2]
S = Path(__file__).resolve().parent
O = R / 'renders/ice_arena_aurora_coherent_v3'
N = R / 'exports/ice_arena_aurora_native_v2'
P = 'IceAuroraCoherentV3'
PARTS = ['Sky', 'Ribbons', 'Stars', 'Haze', 'DistantIce']
SIZE = (512, 720)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def png(im):
    b = io.BytesIO(); im.save(b, format='PNG'); return b.getvalue()


def write_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def dir_static(path, im):
    a = np.array(im.convert('RGBA'), dtype=np.uint16)
    a[:, :, :3] = a[:, :, :3] * a[:, :, 3:4] // 255
    data = png(Image.fromarray(a.astype(np.uint8)))
    path.write_bytes(struct.pack('<q', len(data)) + data + struct.pack('<4i', *im.size, 0, 1))


def mapbg(name, pos, animated=False):
    return {'$type': 'RogueEssence.Dungeon.MapBG, RogueEssence', 'MapLoc': {'X': pos[0], 'Y': pos[1]},
            'BGAnim': {'AnimIndex': P + '_' + name, 'FrameTime': 1, 'StartFrame': 0,
                       'EndFrame': 239 if animated else 0, 'AnimDir': -1, 'Alpha': 255, 'AnimFlip': 0},
            'BGMovement': {'X': 0, 'Y': 0}, 'Parallax': '1, 1', 'RepeatX': False, 'RepeatY': False}


def build():
    for d in ['layers', 'review', 'pmdo/Content/BG']:
        (O / d).mkdir(parents=True, exist_ok=True)
    checks = []
    def check(name, condition):
        assert condition, name
        checks.append({'check': name, 'status': 'PASS'})

    raw_path = O / 'bruts/terrain_generated_refined.png'
    raw = Image.open(raw_path).convert('RGBA')
    a = np.array(raw)
    rgb = a[:, :, :3].astype(np.int16)
    magenta = (rgb[:, :, 0] > rgb[:, :, 1] + 24) & (rgb[:, :, 2] > rgb[:, :, 1] + 24)
    a[magenta] = 0
    keyed = Image.fromarray(a)
    keyed.save(O / 'bruts/terrain_keyed_original_size.png')
    bounds = keyed.getbbox()
    # The generator returned 864x1232, not the requested 512x720. Crop empty top,
    # then fit ONLY this generated art into a 512x576 region below 144 px of sky.
    cropped = keyed.crop((0, bounds[1], raw.width, raw.height))
    fitted = cropped.resize((512, 576), Image.Resampling.NEAREST)
    terrain = Image.new('RGBA', SIZE)
    terrain.alpha_composite(fitted, (0, 144))
    terrain_path = O / 'layers' / (P + '_Terrain.png')
    terrain.save(terrain_path)
    check('Generated terrain alpha is empty in upper 144 rows', not np.asarray(terrain)[:144, :, 3].any())
    check('Generated terrain uses binary alpha, transparent RGB zero', set(np.unique(np.asarray(terrain)[:, :, 3])) <= {0, 255} and not np.asarray(terrain)[np.asarray(terrain)[:, :, 3] == 0, :3].any())
    t = np.asarray(terrain).astype(np.int16)
    check('No chroma-key magenta remains in visible terrain', not np.any((t[:, :, 0] > t[:, :, 1] + 24) & (t[:, :, 2] > t[:, :, 1] + 24) & (t[:, :, 3] > 0)))
    check('Open southern snow approach is present at bottom center', terrain.getpixel((256, 719))[3] == 255 and terrain.getpixel((256, 719))[0] > 160)

    dependencies = []
    def register(path):
        dependencies.append({'path': str(path.relative_to(R)), 'sha256': sha(path)})
    source_sky = N / 'static/IceAuroraNativeV2_01_dark_sky.png'
    sky_path = O / 'layers' / (P + '_SkyBase.png')
    shutil.copyfile(source_sky, sky_path)
    register(source_sky)
    sky = Image.open(sky_path).convert('RGBA')
    check('Outer sky copied byte-for-byte from native V2', sky_path.read_bytes() == source_sky.read_bytes())
    register(N / 'timeline.json')
    timeline = json.loads((N / 'timeline.json').read_text())
    write_json(O / 'timeline.json', {'native_source': '../../exports/ice_arena_aurora_native_v2/timeline.json', **timeline})
    first_state = timeline['states'][timeline['samples'][0]['state']]
    first_parts = []
    for part in PARTS:
        source = N / 'frames' / part / Path(first_state['file']).name.replace('_BGComposite.png', '_' + part + '.png')
        target = O / 'layers' / f'{P}_{part}_phase0.png'
        shutil.copyfile(source, target)
        check('Native initial ' + part + ' copied byte-for-byte', source.read_bytes() == target.read_bytes())
        first_parts.append((part, target, (120, 0)))

    frames = []
    native_frames = []
    opaque = np.asarray(terrain)[:, :, 3] == 255
    terrain_pixels = np.asarray(terrain)
    for state in timeline['states']:
        file = N / state['file']; register(file)
        bg = Image.open(file).convert('RGBA')
        native_frames.append(bg)
        base = sky.copy(); base.alpha_composite(bg, (120, 0))
        comp = base.copy(); comp.alpha_composite(terrain)
        aa, bb = np.asarray(comp), np.asarray(base)
        assert np.array_equal(aa[~opaque], bb[~opaque])
        assert np.array_equal(aa[opaque], terrain_pixels[opaque])
        frames.append(comp)
        for part in PARTS:
            register(N / 'frames' / part / Path(state['file']).name.replace('_BGComposite.png', '_' + part + '.png'))
    check('All 33 compositions preserve exposed native background pixels exactly', True)
    check('Terrain remains exactly identical across all 33 states', True)
    samples = timeline['samples']
    seq = [frames[r['state']] for r in samples]
    seq[0].save(O / 'composition.webp', save_all=True, append_images=seq[1:],
                duration=[r['preview_ms'] for r in samples], loop=0, lossless=True, method=6)
    frames[samples[0]['state']].save(O / 'composition_upper.png')
    frames[samples[120]['state']].save(O / 'composition_lower.png')
    before = Image.open(N / 'review/scene_upper.png').convert('RGBA')
    compare = Image.new('RGB', (1024, 752), '#0e1d30')
    draw = ImageDraw.Draw(compare)
    draw.text((16, 9), 'AVANT - terrain V1', fill='white')
    draw.text((528, 9), 'PROPOSITION - falaise continue generee', fill='white')
    compare.paste(before, (0, 32)); compare.paste(frames[samples[0]['state']], (512, 32))
    compare.save(O / 'review/before_after.png')
    check('Canvas unchanged, source BG remains at (120,0), no BG scale', all(f.size == SIZE for f in frames) and all(f.size == (264, 216) for f in native_frames))
    check('Original 240-tick timing reused without edits', samples == json.loads((N / 'timeline.json').read_text())['samples'] and sum(x['preview_ms'] for x in samples) == 4000)

    # Editable OpenRaster at phase zero: one generated terrain layer and the exact BG parts.
    ordered = [('SkyBase', sky_path, (0, 0)), *first_parts, ('Terrain_genere', terrain_path, (0, 0))]
    ora = ET.Element('image', w='512', h='720', name='Falaise continue generee / ciel natif conserve', version='0.0.3')
    stack = ET.SubElement(ora, 'stack')
    with zipfile.ZipFile(O / (P + '_layers.ora'), 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for i, (name, path, pos) in reversed(list(enumerate(ordered))):
            dest = f'data/layer{i}.png'; archive.writestr(dest, path.read_bytes())
            ET.SubElement(stack, 'layer', name=name, src=dest, x=str(pos[0]), y=str(pos[1]), opacity='1.0', visibility='visible', **{'composite-op': 'svg:src-over'})
        archive.writestr('stack.xml', ET.tostring(ora, encoding='utf-8', xml_declaration=True))
        archive.writestr('mergedimage.png', png(frames[samples[0]['state']]))
        thumb = frames[samples[0]['state']].copy(); thumb.thumbnail((256, 256), Image.Resampling.NEAREST)
        archive.writestr('Thumbnails/thumbnail.png', png(thumb))
    merged = Image.new('RGBA', SIZE)
    for _, path, pos in ordered:
        merged.alpha_composite(Image.open(path).convert('RGBA'), pos)
    check('Seven editable ORA layers recompose phase zero exactly', merged.tobytes() == frames[samples[0]['state']].tobytes())

    bgdir = O / 'pmdo/Content/BG'
    old_dir = N / 'pmdo/Content/BG/IceAuroraNativeV2_BGComposite.dir'
    new_dir = bgdir / (P + '_BGComposite.dir')
    register(old_dir); shutil.copyfile(old_dir, new_dir)
    check('Native-derived animated .dir is byte-identical, only basename changes', old_dir.read_bytes() == new_dir.read_bytes())
    dir_static(bgdir / (P + '_SkyBase.dir'), sky)
    dir_static(bgdir / (P + '_Terrain.dir'), terrain)
    for name, image in [('SkyBase', sky), ('Terrain', terrain)]:
        rawdir = (bgdir / f'{P}_{name}.dir').read_bytes()
        length, = struct.unpack_from('<q', rawdir)
        decoded = Image.open(io.BytesIO(rawdir[8:8+length])).convert('RGBA')
        check('Static PMDO container roundtrip: ' + name, decoded.tobytes() == image.tobytes() and struct.unpack_from('<4i', rawdir, 8 + length) == (512, 720, 0, 1))
    write_json(O / 'pmdo/placement_recipe.json', {'schema': 'placement_recipe_NOT_a_Ground', 'draw_back_to_front':
               [mapbg('SkyBase', (0, 0)), mapbg('BGComposite', (120, 0), True), mapbg('Terrain', (0, 0))],
               'collision': 'NOT PROVIDED', 'runtime_tested': False})

    manifest = {'title': 'Falaise continue - proposition generee, fond valide conserve', 'date': '2026-09-20',
                'canvas': SIZE, 'old_versions_untouched': True, 'native_background_reference_commit': 'f10176369e707128d97a4590d5c8a78895433fe5',
                'terrain_origin': 'AI GENERATED, two generator passes; NOT native terrain reconstruction',
                'generator_output_size': raw.size, 'generated_only_transform': {'key': 'R>G+24 and B>G+24', 'crop': [0, bounds[1], raw.width, raw.height],
                'resize': [512, 576], 'filter': 'nearest-neighbor', 'placement': [0, 144], 'aspect_ratio_preserved': False},
                'terrain_fit_note': 'Only generated art is fitted to the canvas; native pixels and timing are never scaled or changed.',
                'layout': 'General V1 composition retained: northern cliff, central arena, southern entrance. Generated terrain geometry differs; not a byte-identical terrain edit.',
                'native_BG_origin': [120, 0], 'native_BG_size': [264, 216], 'native_BG_modified': False,
                'native_BG_color_limit': 'Existing RGB8 port, not a bit-exact DS RGB555/LCD capture; unchanged from native V2.',
                'layer_count': 7, 'terrain_layer_count': 1, 'hidden_terrain_reconstructed': False,
                'art_approval': 'PENDING USER REVIEW', 'PMDO_GPU_validated': False, 'collision_validated': False,
                'raws': [{'file': str(p.relative_to(O)), 'sha256': sha(p)} for p in sorted((O / 'bruts').glob('terrain_generated*.png'))],
                'unchanged_native_dependencies': dependencies}
    write_json(O / 'manifest.json', manifest)
    check('Every recorded native dependency still has its original hash', all(sha(R / d['path']) == d['sha256'] for d in dependencies))
    expected_native = json.loads((N / 'files.sha256.json').read_text())
    check('Reused BG files match the published V2 SHA256 inventory', all(d['sha256'] == expected_native[str((R / d['path']).relative_to(N))] for d in dependencies))
    movie = Image.open(O / 'composition.webp'); elapsed = 0
    tick_times = [0]
    for row in samples: tick_times.append(tick_times[-1] + row['preview_ms'])
    import bisect
    for i in range(movie.n_frames):
        movie.seek(i); movie.load(); duration = movie.info['duration']
        start = bisect.bisect_right(tick_times, elapsed) - 1
        for tick in range(start, 240):
            if tick_times[tick] >= elapsed + duration: break
            assert movie.convert('RGBA').tobytes() == frames[samples[tick]['state']].tobytes()
        elapsed += duration
    check('Lossless animated WebP preserves every visible frame and totals 4000ms', elapsed == 4000)
    write_json(O / 'audit.json', {'status': 'PASS', 'count': len(checks), 'checks': checks,
                                'type': 'file/pixel/container checks only', 'GPU_tested': False, 'collision_tested': False})
    build_viewer(timeline, sky_path, terrain_path)
    print(f'{len(checks)} file/pixel checks PASS. Generated terrain, native BG unchanged. No GPU/collision validation.')


def build_viewer(timeline, sky, terrain):
    def uri(path): return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()
    parts = {}
    for part in PARTS:
        parts[part] = [uri(N / 'frames' / part / Path(row['file']).name.replace('_BGComposite.png', '_' + part + '.png')) for row in timeline['states']]
    data = {'timeline': timeline['samples'], 'parts': parts, 'static': [uri(sky), uri(terrain)]}
    (O / 'index.html').write_text((S / 'viewer.html').read_text().replace('__DATA__', json.dumps(data)))


if __name__ == '__main__':
    build()
