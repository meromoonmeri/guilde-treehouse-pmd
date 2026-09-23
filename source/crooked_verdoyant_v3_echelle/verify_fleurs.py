"""Vérif fleurs Halcyon sur Crooked V3 : sprites = atlas natif, compositions opaques, webp boucle."""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
P = R / 'renders/crooked_verdoyant_v3_echelle/fleurs_halcyon'
ATLAS = R / 'banque_canonique/atlas/Vast_Steppe_Flower_Animations.png'
W, H = 928, 1152
POSES = [0, 1, 0, 2]


def arr(p):
    return np.array(Image.open(p).convert('RGBA'))


def main():
    m = json.loads((P / 'manifest.json').read_text())
    res = {}
    atlas = arr(ATLAS)
    res['atlas_72x24'] = atlas.shape[1] == 72 and atlas.shape[0] == 24
    for i, pose in enumerate(POSES):
        sp = arr(P / 'sprites' / f'fleur_vast_phase_{i:02}.png')
        crop = atlas[:, pose * 24:(pose + 1) * 24]
        res[f'phase_{i}_equals_atlas_pose_{pose}'] = bool(np.array_equal(sp, crop))
    res['composition_opaque'] = bool(arr(P / 'COMPOSITION.png')[:, :, 3].min() == 255)
    res['composition_size'] = list(Image.open(P / 'COMPOSITION.png').size) == [W, H]
    res['nuit_size'] = list(Image.open(P / 'COMPOSITION_nuit.png').size) == [W, H]
    res['pose_pngs'] = all((P / f'COMPOSITION_pose_{i:02}.png').exists() for i in range(4))
    with Image.open(P / 'ANIMATION_1x.webp') as im:
        res['webp_1x_n_frames'] = getattr(im, 'n_frames', 1)
        res['webp_1x_size'] = list(im.size) == [W, H]
    with Image.open(P / 'ANIMATION_COMPLETE.webp') as im:
        res['webp_complete_n_frames'] = getattr(im, 'n_frames', 1)
        res['webp_complete_size'] = list(im.size) == [W // 2, H // 2]
    with Image.open(P / 'ANIMATION_1x_nuit.webp') as im:
        res['webp_1x_nuit_frames'] = getattr(im, 'n_frames', 1)
    res['loop_game_frames'] = m['loop_game_frames'] == math.lcm(32, 40, 56)
    res['n_sites'] = len(m['flower_sites'])
    res['sites_have_clocks'] = all(s['clock'] in (8, 10, 14) for s in m['flower_sites'])
    res['runtime_pmdo'] = 'NOT TESTED'
    bools = [v for v in res.values() if isinstance(v, bool)]
    res['all_pass'] = all(bools) and res['webp_1x_n_frames'] == 4 and res['webp_complete_n_frames'] == m['frame_events']
    (P / 'verification_fleurs.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if res['all_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
