"""Vérif 4 cartes : taille, sol opaque, pile = composition, nuit Abyss, pas de magenta."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/forets_lisiere_v2'
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night  # noqa: E402
W, H = 928, 1152
ORDER = json.loads((O / 'E_foret_entree_est' / 'manifest.json').read_text())['layers_order_bottom_to_top']


def arr(p):
    return np.array(Image.open(p).convert('RGBA'))


def main():
    maps = json.loads((O / 'index.json').read_text())['maps']
    all_ok = True
    out = {}
    for mid in maps:
        d = O / mid
        r = {}
        layers = {n: arr(d / 'calques' / f'{n}.png') for n in ORDER}
        r['size'] = all(a.shape == (H, W, 4) for a in layers.values())
        r['sol_opaque'] = bool(layers['01_sol_herbe'][:, :, 3].min() == 255)
        def mag(a):
            r_, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
            return int(((a[:, :, 3] > 0) & (r_ > 150) & (b > 150) & (g < 100)).sum())
        r['residual_magenta'] = sum(mag(a) for a in layers.values())
        r['no_magenta'] = r['residual_magenta'] == 0
        comp = Image.new('RGBA', (W, H))
        for n in ORDER:
            comp.alpha_composite(Image.fromarray(layers[n]))
        r['stack_equals_composition'] = bool(np.array_equal(np.array(comp), arr(d / 'composition_jour.png')))
        r['composition_opaque'] = bool(np.array(comp)[:, :, 3].min() == 255)
        r['night_exact'] = all(bool(np.array_equal(arr(d / 'nuit' / f'{n}_nuit.png'), np.array(night(Image.fromarray(layers[n]))))) for n in ORDER)
        r['mc_jour_exists'] = (R / 'exports/forets_lisiere_v2' / mid / 'multicalques' / f'{mid}_jour.aseprite').exists()
        r['ok'] = all(v is True for k, v in r.items() if isinstance(v, bool))
        all_ok &= r['ok']
        out[mid] = r
    out['all_pass'] = all_ok
    out['runtime_pmdo'] = 'NOT TESTED'
    (O / 'verification.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
