"""bruts/ -> pixels/ (1:1, palettes canoniques). Usage : .venv/bin/python source/crooked_applewoods_v1/convert.py"""
import json, sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pixels_lib import palette_of, to_pixels  # noqa: E402

AW = HERE / "refs" / "reference_apple_woods.png"
CC = HERE / "refs" / "reference_crooked_cavern.png"
PAL_AW = palette_of(AW)
VERTS_AW = palette_of(AW, filt=lambda c: c[:, 1] > c[:, 0] + 15)
import numpy as np  # noqa: E402
PAL_ROCHE = np.unique(np.concatenate([palette_of(CC), VERTS_AW]), axis=0)

JOBS = [
    ("01_sol.png", "01_sol.png", PAL_AW, False),
    ("02_falaise_magenta.png", "02_falaise.png", PAL_ROCHE, True),
    ("03_arbres_magenta.png", "03_arbres.png", PAL_AW, True),
    ("04_rochers_magenta.png", "04_rochers.png", PAL_ROCHE, True),
    ("05_vegetation_magenta.png", "05_vegetation.png", PAL_AW, True),
]


def main(only=None):
    stats = {}
    for src, dst, pal, keyed in JOBS:
        if only and src not in only:
            continue
        a, st = to_pixels(HERE / "bruts" / src, pal, keyed=keyed)
        Image.fromarray(a).save(HERE / "pixels" / dst)
        stats[dst] = st
        print(st)
    p = HERE / "pixels" / "stats.json"
    old = json.loads(p.read_text()) if p.exists() else {}
    old.update(stats)
    p.write_text(json.dumps(old, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
