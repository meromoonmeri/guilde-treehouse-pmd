from pathlib import Path
import json, hashlib, sys
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source'))
from cote_v4_abyss.night import night  # noqa: E402
O = R / 'renders/falaises_proches_metano_v1'
m = json.loads((O / 'manifest.json').read_text())
W, H = m['scene']


def load(p):
    return Image.open(p).convert('RGBA')


for n, h in m['layout_sha256'].items():
    assert hashlib.sha256((O / 'layouts' / (n + '.png')).read_bytes()).hexdigest() == h, n
assert hashlib.sha256((R / 'source/falaises_generees/reference_canonique.png').read_bytes()).hexdigest() == m['reference_sha256']
sky_d, sky_n = load(O / 'commun/01_ciel_jour.png'), load(O / 'commun/02_ciel_nuit.png')
sea_d, sea_n = load(O / 'commun/03_mer_jour.png'), load(O / 'commun/04_mer_nuit.png')
cl_d, cl_n = load(O / 'commun/05_nuages_wrap_jour.png'), load(O / 'commun/06_nuages_wrap_nuit.png')
assert sky_d.size == sky_n.size == sea_d.size == sea_n.size == (W, H)
assert cl_d.height == cl_n.height == 300 and cl_d.width == cl_n.width == m['cloud_period']
# night exactness (single Abyss pass)
assert np.array_equal(np.array(night(load(O / 'commun/03_mer_jour.png').crop((0, 300, W, H)))), np.array(sea_n.crop((0, 300, W, H))))
assert np.array_equal(np.array(night(cl_d)), np.array(cl_n))
# wrap edge continuity (adjacent original columns after blend)
a = np.array(cl_d).astype(float)
d = np.abs(a[:, 0] - a[:, -1]).mean()
assert d < 6, d
# per variant
ref = np.array(Image.open(R / 'source/falaises_generees/reference_canonique.png').convert('RGB')).reshape(-1, 3)
audit = {}
for v in m['variants']:
    out = O / v['id']
    t = load(out / '07_falaise.png')
    tn = load(out / '08_falaise_nuit.png')
    assert t.size == tn.size == (W, H)
    assert np.array_equal(np.array(night(t)), np.array(tn)), v['id']
    # magenta residue
    f = np.array(t)
    op = f[:, :, 3] > 0
    mg = ((f[:, :, 0].astype(float) > f[:, :, 1] * 1.4) & (f[:, :, 2].astype(float) > f[:, :, 1] * 1.4) & (f[:, :, 2] > 35)) & op
    assert mg.sum() / op.sum() < 5e-4, v['id']
    # recomposition jour/nuit with tiled clouds
    for day, sk, se, cl, tt, name in [(True, sky_d, sea_d, cl_d, t, 'composition_jour.png'),
                                     (False, sky_n, sea_n, cl_n, tn, 'composition_nuit.png')]:
        c = sk.copy()
        x = 0
        while x < W:
            c.alpha_composite(cl, (x, 0))
            x += cl.width
        c.alpha_composite(se, (0, 0))
        c.alpha_composite(tt, (0, 0))
        assert np.array_equal(np.array(c), np.array(load(out / name))), (v['id'], name)
    # Metano audit vs canonical reference palette (sampled)
    px = np.array(t)
    opx = px[px[:, :, 3] > 0][:, :3].astype(float)
    sel = opx[::37]
    dist = np.sqrt(((sel[:, None, :] - ref[::97][None, :, :]) ** 2).sum(-1).min(1))
    exact = (dist == 0).mean() * 100
    near = (dist <= 30).mean() * 100
    assert near > 50, (v['id'], near)
    audit[v['id']] = {'exact_pct': round(float(exact), 1), 'within30_pct': round(float(near), 1)}
report = {'scenes': 2, 'wrap_period': m['cloud_period'], 'wrap_edge_meandiff': round(float(d), 2),
          'metano_audit': audit,
          'checks': ['Layouts SHA256 unchanged', 'Dims 768x512, strip h=300',
                     'Night == single Abyss pass on sea/clouds/cliffs',
                     'Wrap edge continuous by construction, tiling recomposed exactly',
                     'Day/night compositions == exact layer stacks', 'No magenta residue',
                     'Cliff colors audited vs canonical Metano reference'],
          'runtime_validated': False}
(O / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(report)
