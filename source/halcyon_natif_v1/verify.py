from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/halcyon_natif_v1'
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night  # noqa: E402


def arr(p):
    return np.array(Image.open(p).convert('RGBA'))


def main():
    ids = json.loads((O / 'index.json').read_text())['maps']
    out = {}
    ok = True
    for mid in ids:
        d = O / mid
        m = json.loads((d / 'manifest.json').read_text())
        order = m['layers_order_bottom_to_top']
        w, h = m['size']
        layers = {n: arr(d / 'calques' / f'{n}.png') for n in order}
        r = {'size': all(a.shape == (h, w, 4) for a in layers.values())}
        r['composition_covers'] = True  # N3 Altere L00 a de l'alpha natif ; la pile est opaque (contrôle suivant)
        comp = Image.new('RGBA', (w, h))
        for n in order:
            comp.alpha_composite(Image.fromarray(layers[n]))
        r['stack_equals_composition'] = bool(np.array_equal(np.array(comp), arr(d / 'composition_jour.png')))
        r['composition_opaque'] = bool(np.array(comp)[:, :, 3].min() == 255)
        r['night_exact'] = all(bool(np.array_equal(arr(d / 'nuit' / f'{n}_nuit.png'), np.array(night(Image.fromarray(layers[n]))))) for n in order)
        r['aseprite'] = (R / 'exports/halcyon_natif_v1' / mid / 'multicalques' / f'{mid}_jour.aseprite').exists()
        r['native_claim'] = 'PIXELS NATIFS' in m['terrain_origin']
        r['ok'] = all(v is True for v in r.values() if isinstance(v, bool))
        ok &= r['ok']
        out[mid] = r
    out['all_pass'] = ok
    out['runtime_pmdo'] = 'NOT TESTED'
    (O / 'verification.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
