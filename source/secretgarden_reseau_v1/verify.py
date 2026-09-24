from pathlib import Path
import json, hashlib, zipfile
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/secretgarden_reseau_v1'
m = json.loads((O / 'manifest.json').read_text())
assert m.get('version') == 2
count = 0

ref = R / 'secretgarden.png'
assert hashlib.sha256(ref.read_bytes()).hexdigest() == m['reference_sha256'], 'reference changed'


def load(p):
    return Image.open(p).convert('RGBA')


for e in m['rooms']:
    d = O / e['id']
    # static stack recomposition (f0) + border + ports == composition
    im = Image.new('RGBA', (512, 512))
    for name in e['layers']:
        layer = load(d / (name + '.png'))
        assert layer.size == (512, 512), (e['id'], name)
        count += 1
        if name not in e['optional']:
            im.alpha_composite(layer)
    assert np.array_equal(np.array(im), np.array(load(d / 'composition.png'))), e['id']
    # terrain partition 01..08 exact
    t = Image.new('RGBA', (512, 512))
    for name in ['01_sol_chemin', '02_vegetation_fond', '03_cimees_arbres', '04_buissons_sous_bois',
                 '05_vegetation_premier_plan', '06_troncs', '07_rochers', '08_fleurs']:
        t.alpha_composite(load(d / (name + '.png')))
    assert np.array_equal(np.array(t), np.array(load(d / 'terrain_detoure.png'))), (e['id'], 'partition')
    # ports opaque in final composition
    comp = np.array(load(d / 'composition.png'))
    for p in e['ports']:
        dd = p['direction']
        band = comp[0:24, 224:288] if dd == 'N' else comp[-24:, 224:288] if dd == 'S' else comp[224:288, 0:24] if dd == 'W' else comp[224:288, -24:]
        assert np.all(band[:, :, 3] == 255), (e['id'], dd)
    # border port windows really clear (inner rect of each window fully transparent)
    b = np.array(load(d / '09_bordure_feuillue.png'))
    for p in e['ports']:
        dd = p['direction']
        w = b[4:40, 232:280] if dd == 'N' else b[-40:-4, 232:280] if dd == 'S' else b[232:280, 4:40] if dd == 'W' else b[232:280, -40:-4]
        assert np.all(w[:, :, 3] == 0), (e['id'], dd, 'window')
    # flower frames: 4 exist, f0 == static layer, neighbors differ, loop closes
    fr = [np.array(load(d / 'fleurs' / f'08_fleurs_f{i}.png')) for i in range(4)]
    assert np.array_equal(fr[0], np.array(load(d / '08_fleurs.png'))), (e['id'], 'f0')
    for i in range(4):
        assert not np.array_equal(fr[i], fr[(i + 1) % 4]), (e['id'], f'f{i}')
    # GIF: 4 frames @200ms
    g = Image.open(d / 'composition_animee.gif')
    assert g.n_frames == 4 and g.info.get('duration') == 200, (e['id'], 'gif')
    # ORA readable, stack matches files
    ora = zipfile.ZipFile(d / (e['id'] + '.ora'))
    assert ora.read('mimetype') == b'image/openraster'
    stack = ora.read('stack.xml').decode()
    for name in e['layers']:
        assert f'data/{name}.png' in stack, (e['id'], name)
        assert f'data/{name}.png' in ora.namelist(), (e['id'], name)

box = tuple(m['patch_box'])
assert np.array_equal(np.array(load(O / 'materiaux/sol_raccord_natif.png')),
                     np.array(load(ref).crop(box))), 'native patch'

report = {'version': 2, 'scenes': len(m['rooms']), 'aligned_layers': count,
          'ports': sum(len(e['ports']) for e in m['rooms']),
          'flower_frames_per_room': 4, 'flower_cadence_ms': 200,
          'checks': ['Reference SHA256 identical since build',
                     '7 compositions identical to full static stack',
                     'Terrain partitions 01..08 exact on all rooms',
                     'All layers 512x512; border port windows clear',
                     'Flower f0==static, 4 distinct frames, loop closed',
                     '7 GIFs 4x200ms; 7 ORAs readable with full stacks',
                     'Native grass patch strictly equal to reference crop',
                     '19 64px connectors, 24px opaque band each'],
          'runtime_validated': False}
(O / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(report)
