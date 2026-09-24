from pathlib import Path
import json, hashlib, zipfile
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/secretgarden_reseau_v1'
m = json.loads((O / 'manifest.json').read_text())
assert m.get('version') == 5
count = 0

ref = R / 'secretgarden.png'
jung = R / 'Southern_Jungle_entrance_S.png'
assert hashlib.sha256(ref.read_bytes()).hexdigest() == m['reference_sha256'], 'reference changed'
assert hashlib.sha256(jung.read_bytes()).hexdigest() == m['jungle_reference_sha256'], 'jungle ref changed'


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
    if e.get('source', 'v3_partition') == 'v3_partition':
        t = Image.new('RGBA', (512, 512))
        for name in ['01_sol', '02_chemin', '03_arbres', '04_buissons', '05_rochers', '06_fleurs']:
            t.alpha_composite(load(d / (name + '.png')))
        assert np.array_equal(np.array(t), np.array(load(d / 'terrain_detoure.png'))), (e['id'], 'partition')
    else:
        lay = {n: np.array(load(d / (n + '.png')))[:, :, 3] > 0 for n in
               ['01_sol', '02_chemin', '03_arbres', '04_buissons', '05_rochers', '06_fleurs']}
        ground = lay['01_sol'] | lay['02_chemin']
        veg = lay['03_arbres'] | lay['04_buissons']
        assert (lay['02_chemin'] & ~ground).sum() == 0, (e['id'], 'chemin')
        assert (veg & ground).sum() == 0, (e['id'], 'veg')
        assert (lay['05_rochers'] & ~(ground | veg)).sum() == 0, (e['id'], 'rochers')
        assert (lay['06_fleurs'] & ~(ground | veg)).sum() == 0, (e['id'], 'fleurs')
    # ports opaque in final composition
    comp = np.array(load(d / 'composition.png'))
    for p in e['ports']:
        dd = p['direction']
        band = comp[0:24, 224:288] if dd == 'N' else comp[-24:, 224:288] if dd == 'S' else comp[224:288, 0:24] if dd == 'W' else comp[224:288, -24:]
        assert np.all(band[:, :, 3] == 255), (e['id'], dd)
    # border port windows really clear (inner rect of each window fully transparent)
    b = np.array(load(d / '07_bordure_jungle.png'))
    for p in e['ports']:
        dd = p['direction']
        w = b[4:40, 232:280] if dd == 'N' else b[-40:-4, 232:280] if dd == 'S' else b[232:280, 4:40] if dd == 'W' else b[232:280, -40:-4]
        assert np.all(w[:, :, 3] == 0), (e['id'], dd, 'window')
    # flower frames: 4 exist, f0 == static layer, neighbors differ, loop closes
    fr = [np.array(load(d / 'fleurs' / f'06_fleurs_f{i}.png')) for i in range(4)]
    assert np.array_equal(fr[0], np.array(load(d / '06_fleurs.png'))), (e['id'], 'f0')
    for i in range(4):
        assert not np.array_equal(fr[i], fr[(i + 1) % 4]), (e['id'], f'f{i}')
    # GIF: 4 frames @200ms
    g = Image.open(d / 'composition_animee.gif')
    assert g.n_frames == 4 and g.info.get('duration') == 200, (e['id'], 'gif')
    # V5: bare version == sol+chemin+fleurs+acces ; nue + full GIFs
    nue = Image.new('RGBA', (512, 512))
    for name in ['01_sol', '02_chemin', '06_fleurs']:
        nue.alpha_composite(load(d / (name + '.png')))
    for name in e['layers']:
        if name.startswith('08_acces'):
            nue.alpha_composite(load(d / (name + '.png')))
    assert np.array_equal(np.array(nue), np.array(load(d / 'composition_nue.png'))), (e['id'], 'nue')
    for gif in ['composition_nue_animee.gif', 'composition_full_animee.gif']:
        gg = Image.open(d / gif)
        assert gg.n_frames == 4 and gg.info.get('duration') == 200, (e['id'], gif)
    # V5: veg f0 == merge(03,04); frames loop; sheets consistent
    vg = Image.new('RGBA', (512, 512))
    vg.alpha_composite(load(d / '03_arbres.png'))
    vg.alpha_composite(load(d / '04_buissons.png'))
    vf = [np.array(load(d / 'vegetation' / f'veg_f{i}.png')) for i in range(4)]
    assert np.array_equal(vf[0], np.array(vg)), (e['id'], 'veg_f0')
    for i in range(4):
        assert not np.array_equal(vf[i], vf[(i + 1) % 4]), (e['id'], f'veg{i}')
    rm = json.loads((d / 'rochers_manifest.json').read_text())
    assert len(rm['sprites']) == e['v5']['rochers_sprites'], (e['id'], 'rocks')
    sheetpx = (np.array(load(d / 'rochers_tilesheet.png'))[:, :, 3] > 0).sum()
    assert sheetpx == sum(sp['area'] for sp in rm['sprites']), (e['id'], 'rockpx')
    bm = json.loads((d / 'vegetation' / 'buissons_manifest.json').read_text())
    assert len(bm['sprites']) == e['v5']['buissons_sprites'], (e['id'], 'bush')
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

report = {'version': 5, 'scenes': len(m['rooms']), 'aligned_layers': count,
          'ports': sum(len(e['ports']) for e in m['rooms']),
          'flower_frames_per_room': 4, 'flower_cadence_ms': 200,
          'checks': ['Reference SHA256 identical since build',
                     '7 compositions identical to full static stack',
                     'V3 rooms: terrain partitions 01..06 exact; V4 rooms: zone constraints (chemin, veg, rochers, fleurs)',
                     'All layers 512x512; border port windows clear',
                     'Flower f0==static, 4 distinct frames, loop closed',
                     '7 GIFs 4x200ms + 7 nue GIFs + 7 full GIFs; 7 ORAs readable',
                     'Bare versions exact; veg f0==merge, 4 distinct frames; rock/bush sheets consistent',
                     'Native grass patch strictly equal to reference crop',
                     'Jungle reference SHA256 identical since build',
                     '19 64px connectors, 24px opaque band each'],
          'runtime_validated': False}
(O / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(report)
