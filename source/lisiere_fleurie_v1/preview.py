"""Aperçu de travail (hors livrable) : composite 1x + problèmes de composition."""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import layout_problems  # noqa: E402
from compose import compose  # noqa: E402
from layout import make_layout  # noqa: E402
from modules import build_modules, load_sheets  # noqa: E402


def stack(out, pose=0):
    names = ['sol', 'corniche', 'vegetation_basse', 'fleurs', 'troncs_rochers', 'canopees']
    im = Image.new('RGBA', (out['sol'].w, out['sol'].h))
    for n in names:
        c = out['fleurs_poses'][pose] if n == 'fleurs' else out[n]
        im.alpha_composite(Image.fromarray(c.rgba))
    return im


if __name__ == '__main__':
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    dest = sys.argv[2] if len(sys.argv) > 2 else '/tmp/lfl_preview.png'
    S = load_sheets()
    M = build_modules(S)
    lay = make_layout(seed, S, M)
    out = compose(lay, S, M)
    stack(out).save(dest)
    print('arbres', len(lay['trees']), 'rochers', len(lay['rocks']), 'fleurs', len(lay['flowers']),
          'petits', len(lay['small']), '->', dest)
    for line in lay['resolve_log']:
        print('  resolve:', line)
    for p in layout_problems(lay, out, M, S):
        print('  PROBLEME:', p)
