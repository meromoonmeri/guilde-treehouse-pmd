"""Aperçu autonome des deux scènes : images et courtes phases d'animation embarquées."""
from pathlib import Path
from PIL import Image
import base64
import hashlib
import io
import json

R = Path(__file__).resolve().parents[1]


def build():
    assets, hashes = {}, {}

    def embed(image, thumb=False):
        im = image.convert('RGBA')
        if thumb:
            im.thumbnail((240, 204), Image.Resampling.NEAREST)
        raw = io.BytesIO()
        im.save(raw, format='WEBP', lossless=True, exact=True, method=4)
        b = raw.getvalue()
        digest = hashlib.sha256(b).hexdigest()
        if digest not in hashes:
            key = 'i'+str(len(hashes))
            hashes[digest] = key
            assets[key] = 'data:image/webp;base64,'+base64.b64encode(b).decode()
        return hashes[digest]

    scenes = []
    for directory, label in [('falaise', 'Prairie de la guilde'), ('sharpedo', 'Falaise côtière'), ('paysages/littoral', 'Cap des Alizés'), ('paysages/plateaux', 'Prairies suspendues'), ('paysages/etang', 'Clairière des sources'), ('paysages/cascades', 'Ressauts célestes')]:
        root = R / directory
        manifest = json.loads((root / 'kit.json').read_text(encoding='utf-8'))
        variants = {}
        for mode in manifest['ambiances']:
            f = manifest['fichiers'][mode]
            layers = [Image.open(root / f['calques'][layer['id']]).convert('RGBA') for layer in manifest['calques']]
            motion = {}
            palette_maps = {}
            for key, spec in f['operations'].items():
                if spec['kind'] == 'palette_cycle':
                    palette_maps[key] = embed(Image.open(root / spec['indices']))
                    continue
                if spec['kind'] in ['scroll', 'waves']:
                    continue
                info = f['animations'][key]
                atlas = Image.open(root / info['atlas']).convert('RGBA')
                w, h = info['frame_size']
                frames = []
                for i in range(info['period']):
                    x, y = (i % info['columns'])*w, (i//info['columns'])*h
                    frames.append(embed(atlas.crop((x, y, x+w, y+h))))
                motion[key] = {'frames': frames, 'offset': info['offset']}
            variants[mode] = {'layers': [embed(q) for q in layers], 'empty': [q.getbbox() is None for q in layers],
                              'thumb': embed(Image.open(root / f['composition']), thumb=True), 'files': f, 'motion': motion, 'palette_maps': palette_maps}
        scenes.append({'id': manifest.get('id',directory), 'directory': directory, 'label': label, 'manifest': manifest, 'variants': variants})
    data = json.dumps({'scenes': scenes, 'assets': assets}, ensure_ascii=False, separators=(',', ':'))
    html = (R / 'source/exterieurs_preview.html').read_text(encoding='utf-8')
    html = html.replace('__STYLE__', (R / 'source/exterieurs_preview.css').read_text(encoding='utf-8'))
    html = html.replace('__SCRIPT__', (R / 'source/exterieurs_preview.js').read_text(encoding='utf-8')).replace('__DATA__', data)
    path = R / 'apercu_falaise.html'
    path.write_text(html, encoding='utf-8')
    print('Aperçu autonome :', len(scenes), 'scènes ;', len(assets), 'images uniques ;', path.stat().st_size, 'octets.')


if __name__ == '__main__':
    build()
