"""Controles V4 : provenance native, recomposition exacte, nuit Abyss x1, chemin sud->nord."""
from pathlib import Path
import hashlib
import json
import sys

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
import numpy as np
from PIL import Image, ImageChops
from scipy import ndimage as nd
from night import night

OUT = R / 'exports/zones_south_north_v4'
ok = []


def check(name, cond, detail=''):
    assert cond, f'FAIL {name} {detail}'
    ok.append(name)
    print(f'PASS {name} {detail}')


def main():
    man = json.loads((OUT / 'manifest.json').read_text())
    for f, h in man['sha256'].items():
        check('source-intacte-' + Path(f).stem,
              hashlib.sha256((R / f).read_bytes()).hexdigest() == h)
    A = [np.array(Image.open(R / p).convert('RGBA')) for p in man['sources']]
    for info in man['maps']:
        d = OUT / info['id']
        W, H = info['size']
        check(info['id'] + '-dims-8px', W % 8 == 0 and H % 8 == 0, f'{W}x{H}')
        comp = {m: Image.new('RGBA', (W, H)) for m in ('jour', 'nuit')}
        for l in info['layers']:
            for m in ('jour', 'nuit'):
                f = l['file_jour'] if m == 'jour' else l['file_nuit']
                im = Image.open(d / f).convert('RGBA')
                check(f'-taille', im.size == (W, H))
                check(f'-tsx', (d / (Path(f).stem + '.tsx')).exists())
                comp[m].alpha_composite(im)
            a = np.array(Image.open(d / l['file_jour']).convert('RGBA'))
            an = np.array(Image.open(d / l['file_nuit']).convert('RGBA'))
            check(l['id'] + '-nuit-abyss-x1',
                  (np.array(night(Image.open(d / l['file_jour']))) == an).all())
            q = np.load(d / l['provenance'])['source_sxy']
            check(l['id'] + '-npz', q.shape == (H, W, 3))
            op = a[:, :, 3] > 0
            check(l['id'] + '-provenance-complete', (q[op][:, 0] >= 0).all(),
                  f'{op.sum()} px opaques')
            check(l['id'] + '-provenance-vide', (q[~op][:, 0] == -1).all())
            sid = q[:, :, 0]
            for s in range(len(A)):
                m = op & (sid == s)
                if not m.any():
                    continue
                ys, xs = np.nonzero(m)
                src = A[s][q[ys, xs, 2], q[ys, xs, 1]]
                check(f"{l['id']}-pixels-natifs-src{s}", (a[ys, xs] == src).all(),
                      f'{m.sum()} px')
        for m in ('jour', 'nuit'):
            ref = Image.open(d / f'composite_{m}.png').convert('RGBA')
            check(info['id'] + f'-recomposition-{m}',
                  ImageChops.difference(comp[m], ref).getbbox() is None)
        pm = np.array(Image.open(d / 'path_connectivity_mask.png').convert('L')) > 0
        lab, n = nd.label(pm)
        bottom = set(lab[H - 1][pm[H - 1]])
        reached = [lab[e[1], e[0]] in bottom and lab[e[1], e[0]] > 0
                   for e in info['entrances']]
        check(info['id'] + '-chemin-sud-nord', reached[0],
              f'entrees atteintes: {reached}')
        check(info['id'] + '-ops', len(info['operations']) >= 3,
              f"{len(info['operations'])} ops")
    (OUT / 'verification.json').write_text(json.dumps(
        dict(all_pass=True, checks=ok), indent=1, ensure_ascii=False))
    print(f'{len(ok)} controles PASS')


if __name__ == '__main__':
    main()
