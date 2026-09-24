from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/secretgarden_reseau_v1'
m = json.loads((O / 'manifest.json').read_text())
count = 0

# Reference unchanged since build
ref = R / 'secretgarden.png'
assert hashlib.sha256(ref.read_bytes()).hexdigest() == m['reference_sha256'], 'reference changed'


def load(p):
    return Image.open(p).convert('RGBA')


for e in m['rooms']:
    d = O / e['id']
    im = Image.new('RGBA', (512, 512))
    for name in e['layers']:
        layer = load(d / (name + '.png'))
        assert layer.size == (512, 512), (e['id'], name)
        count += 1
        if name not in e['optional']:
            im.alpha_composite(layer)
    assert np.array_equal(np.array(im), np.array(load(d / 'composition.png'))), e['id']
    # Port bands still opaque in final compositions
    comp = np.array(load(d / 'composition.png'))
    for p in e['ports']:
        dd = p['direction']
        band = comp[0:24, 224:288] if dd == 'N' else comp[-24:, 224:288] if dd == 'S' else comp[224:288, 0:24] if dd == 'W' else comp[224:288, -24:]
        assert np.all(band[:, :, 3] == 255), (e['id'], dd)

# Native connector patch identical to reference crop
box = tuple(m['patch_box'])
assert np.array_equal(np.array(load(O / 'materiaux/sol_raccord_natif.png')),
                     np.array(load(ref).crop(box))), 'native patch'

report = {'scenes': len(m['rooms']), 'aligned_layers': count,
          'ports': sum(len(e['ports']) for e in m['rooms']),
          'deferred': m['deferred'],
          'checks': ['Reference SHA256 identical since build',
                     '6 compositions identical to active-layer recomposition',
                     'All layers 512x512',
                     'Native grass patch strictly equal to secretgarden.png crop',
                     'Build+verify: 16 64px connectors, 24px opaque band each'],
          'runtime_validated': False}
(O / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(report)
