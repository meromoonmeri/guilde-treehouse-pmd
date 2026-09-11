"""Animations et exports communs aux deux extérieurs, sans toucher au kit intérieur.

Les mêmes phases sont exportées en Aseprite, Tiled et dans l'aperçu autonome.
Les étoiles ont une période de 24 images ; la lune ne change jamais d'opacité.
"""
from pathlib import Path
from PIL import Image, ImageChops
import cv2
import json
import math
import numpy as np
import struct
import zlib

DURATION = 250


def save_png(im, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    im.convert('RGBA').save(path, optimize=True)


def stars_spec(image, root):
    alpha = np.array(image.convert('RGBA'))[:, :, 3]
    n, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 0).astype('uint8'), 8)
    moon = max(range(1, n), key=lambda i: stats[i, 4])
    labels[labels == moon] = 0
    path = root / 'animations/etoiles_groupes.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(labels.astype('uint8' if n < 256 else 'uint16')).save(path, optimize=True)
    lut = []
    for frame in range(24):
        row = [255]
        for group in range(1, n):
            period = 12 if group % 3 == 0 else 24
            phase = 2*math.pi*((group*7) % 24)/24
            depth = .40 + .16*(group % 5)/4
            level = 1-depth*math.sin(math.pi*frame/period)**2*(.65+.35*math.sin(2*math.pi*frame/period+phase)**2)
            row.append(int(math.floor(level*255+.5)))
        lut.append(row)
    assert all(x == 255 for x in lut[0])
    return {'kind': 'stars', 'period': 24, 'prefix': 'etoiles',
            'groups': str(path.relative_to(root)), 'levels': lut,
            'moon_box': [int(v) for v in stats[moon, :4]], 'moon_steady': True}


def waves_spec():
    phases = []
    for f in range(24):
        a = 2*math.pi*f/24
        phases.append([int(round(3*math.sin(a))), int(round(math.sin(a))),
                       int(math.floor(255-32*math.sin(math.pi*f/24)**2+.5))])
    return {'kind': 'waves', 'period': 24, 'prefix': 'vagues', 'phases': phases}


class AnimatedLayer:
    def __init__(self, image, spec, root):
        self.image = image.convert('RGBA')
        self.array = np.array(self.image)
        self.spec = spec
        self.period = spec['period'] if spec else 1
        self.cache = {}
        self.groups = np.array(Image.open(root / spec['groups'])).astype(int) if spec and spec['kind'] == 'stars' else None
        self.source_atlas = Image.open(root / spec['source_atlas']).convert('RGBA') if spec and spec['kind'] == 'frames' else None

    def at(self, frame):
        if not self.spec:
            return self.image
        phase = int(frame) % self.period
        if phase in self.cache:
            return self.cache[phase]
        kind = self.spec['kind']
        if kind == 'scroll':
            q = ImageChops.offset(self.image, -phase, 0)
        elif kind == 'stars':
            a = self.array.copy()
            levels = np.asarray(self.spec['levels'][phase], dtype=np.uint32)[self.groups]
            a[:, :, 3] = ((a[:, :, 3].astype(np.uint32)*levels+127)//255).astype('uint8')
            a[a[:, :, 3] == 0] = 0
            q = Image.fromarray(a)
        elif kind == 'frames':
            width, height = self.spec['source_frame_size']
            x = (phase % self.spec['source_columns'])*width
            y = (phase//self.spec['source_columns'])*height
            q = self.source_atlas.crop((x, y, x+width, y+height))
        elif kind == 'waves':
            dx, dy, opacity = self.spec['phases'][phase]
            a = np.array(ImageChops.offset(self.image, dx, dy))
            a[:, :, 3] = ((a[:, :, 3].astype(np.uint32)*opacity+127)//255).astype('uint8')
            a[a[:, :, 3] == 0] = 0
            q = Image.fromarray(a)
        else:
            raise ValueError(kind)
        if self.period <= 48:
            self.cache[phase] = q
        return q


def compose(operators, size, frame=0, base_start=0):
    im = Image.new('RGBA', size)
    for op in operators[base_start:]:
        im.alpha_composite(op.at(frame))
    return im


def _string(s):
    b = s.encode('utf-8')
    return struct.pack('<H', len(b))+b


def _chunk(kind, payload):
    return struct.pack('<IH', len(payload)+6, kind)+payload


def _image_cel(index, image):
    box = image.getbbox()
    x, y = box[:2] if box else (0, 0)
    q = image.crop(box) if box else Image.new('RGBA', (1, 1))
    header = struct.pack('<HhhBHh', index, x, y, 255, 2, 0)+b'\0'*5
    return _chunk(0x2005, header+struct.pack('<HH', q.width, q.height)+zlib.compress(q.tobytes(), 9)), (x, y)


def write_ase(path, operators, definitions, size, frames):
    content = bytearray()
    positions = {}
    for frame in range(frames):
        chunks = []
        if frame == 0:
            for layer in definitions:
                chunks.append(_chunk(0x2004, struct.pack('<HHHHHHB', 3, 0, 0, 0, 0, 0, 255)+b'\0'*3+_string(layer['nom'])))
            tag = struct.pack('<HHBH', 0, frames-1, 0, 0)+b'\0'*6+bytes([155, 189, 114, 0])+_string('Extérieur — boucle')
            chunks.append(_chunk(0x2018, struct.pack('<H', 1)+b'\0'*8+tag))
        for i, op in enumerate(operators):
            phase = frame % op.period
            if frame >= op.period:
                x, y = positions[i, phase]
                data = struct.pack('<HhhBHh', i, x, y, 255, 1, 0)+b'\0'*5+struct.pack('<H', phase)
                chunks.append(_chunk(0x2005, data))
            else:
                data, pos = _image_cel(i, op.at(frame))
                positions[i, phase] = pos
                chunks.append(data)
        payload = b''.join(chunks)
        content.extend(struct.pack('<IHHH2sI', len(payload)+16, 0xF1FA, len(chunks), DURATION, b'\0\0', len(chunks)))
        content.extend(payload)
    header = bytearray(128)
    struct.pack_into('<IHHHHHIH', header, 0, len(content)+128, 0xA5E0, frames, *size, 32, 1, DURATION)
    struct.pack_into('<HBBhhHH', header, 32, 0, 1, 1, 0, 0, 8, 8)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header+content)


def write_tiled(path, root, mode, operators, definitions, size, markers):
    width, height = size
    layers, sets, atlases = [], [], {}
    gid, object_id = 1, 1
    for i, (op, definition) in enumerate(zip(operators, definitions)):
        layer = {'id': i+1, 'name': definition['nom'], 'visible': True, 'opacity': 1, 'x': 0, 'y': 0}
        key = definition['id']
        if op.spec:
            if op.spec['kind'] == 'scroll':
                y, bottom = op.image.getbbox()[1::2]
            else:
                boxes = [op.at(f).getbbox() for f in range(op.period)]
                y, bottom = min(b[1] for b in boxes if b), max(b[3] for b in boxes if b)
            band, columns = bottom-y, min(8, op.period)
            atlas = Image.new('RGBA', (width*columns, band*math.ceil(op.period/columns)))
            for f in range(op.period):
                atlas.paste(op.at(f).crop((0, y, width, bottom)), ((f % columns)*width, (f//columns)*band))
            relative = f"animations/{op.spec['prefix']}_{mode}.png"
            save_png(atlas, root / relative)
            info = {'atlas': relative, 'period': op.period, 'columns': columns,
                    'frame_size': [width, band], 'offset': [0, y]}
            atlases[key] = info
            sets.append({'firstgid': gid, 'name': op.spec['prefix']+'_'+mode, 'tilewidth': width,
                         'tileheight': band, 'tilecount': op.period, 'columns': columns,
                         'margin': 0, 'spacing': 0, 'objectalignment': 'bottomleft',
                         'image': '../'+relative, 'imagewidth': atlas.width, 'imageheight': atlas.height,
                         'tiles': [{'id': 0, 'animation': [{'tileid': f, 'duration': DURATION} for f in range(op.period)]}]})
            layer.update(type='objectgroup', draworder='index', objects=[{
                'id': object_id, 'name': definition['nom'], 'type': '', 'gid': gid,
                'x': 0, 'y': bottom, 'width': width, 'height': band, 'rotation': 0, 'visible': True,
            }])
            gid += op.period
            object_id += 1
        else:
            layer.update(type='imagelayer', image=f'../calques/{mode}/{key}.png')
        layers.append(layer)
    objects = []
    for marker in markers:
        x, y, w, h = marker['rectangle_px']
        objects.append({'id': object_id, 'name': marker['nom'], 'type': 'repere', 'x': x, 'y': y,
                        'width': w, 'height': h, 'rotation': 0, 'visible': True})
        object_id += 1
    layers.append({'id': len(layers)+1, 'name': 'Repères — pas des collisions intégrées', 'type': 'objectgroup',
                   'visible': False, 'opacity': 1, 'x': 0, 'y': 0, 'draworder': 'index', 'objects': objects})
    data = {'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0', 'orientation': 'orthogonal',
            'renderorder': 'right-down', 'tilewidth': 8, 'tileheight': 8, 'width': width//8, 'height': height//8,
            'infinite': False, 'nextlayerid': len(layers)+1, 'nextobjectid': object_id, 'layers': layers, 'tilesets': sets}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return atlases


def export_variant(root, mode, definitions, images, specs, size, frames, base_start, markers):
    files = {'calques': {}, 'composition': f'compositions/{mode}.png', 'base': f'bases/{mode}_transparente.png',
             'magenta': f'bases/{mode}_magenta.png', 'aseprite': f'aseprite/falaise_{mode}.aseprite',
             'tiled': f'tiled/falaise_{mode}.tmj', 'operations': specs}
    operators = []
    for definition, image in zip(definitions, images):
        key = definition['id']
        rel = f'calques/{mode}/{key}.png'
        save_png(image, root / rel)
        files['calques'][key] = rel
        op = AnimatedLayer(image, specs.get(key), root)
        assert frames % op.period == 0
        assert np.array_equal(np.array(op.at(0)), np.array(image)), 'Les PNG doivent rester l’image 0'
        operators.append(op)
    save_png(compose(operators, size), root / files['composition'])
    base = compose(operators, size, base_start=base_start)
    save_png(base, root / files['base'])
    magenta = Image.new('RGBA', size, (255, 0, 255, 255))
    magenta.alpha_composite(base)
    save_png(magenta, root / files['magenta'])
    write_ase(root / files['aseprite'], operators, definitions, size, frames)
    files['animations'] = write_tiled(root / files['tiled'], root, mode, operators, definitions, size, markers)
    return files
