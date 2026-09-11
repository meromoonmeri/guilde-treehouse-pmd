"""Adapte les dix phases de mer de la référence à notre cadrage et à sa palette.

Pas de déplacement sinusoïdal d'une image unique : les bandes et les crêtes
proviennent des dix images successives de l'animation de référence.
"""
from pathlib import Path
from PIL import Image
import cv2
import json
import numpy as np

S = Path(__file__).resolve().parent / 'sharpedo'


def prepare():
    config = json.loads((S / 'animation_mer_reference.json').read_text(encoding='utf-8'))
    ref_config = config['atlas_reference']
    rw, rh = ref_config['frame_size']
    reference = Image.open(S / ref_config['file']).convert('RGBA')
    frames = []
    for i in range(config['reference']['frames']):
        x, y = (i % ref_config['columns'])*rw, (i//ref_config['columns'])*rh
        q = np.array(reference.crop((x, y, x+rw, y+rh)))
        assert np.all(q[:, :, 3] == 255)
        frames.append(q[:, :, :3])
    raw = np.stack(frames)
    width, height = config['adaptation']['dimensions']
    horizon = config['adaptation']['horizon_y']
    assert rh == height-horizon
    # Fond modal du témoin : retirer sa couleur de profondeur, garder l'évolution
    # des vagues et des bandes lumineuses, puis appliquer la palette de notre mer.
    source_base = np.empty((rh, 3), np.uint8)
    for y in range(rh):
        colors, counts = np.unique(raw[:, y].reshape(-1, 3), axis=0, return_counts=True)
        source_base[y] = colors[counts.argmax()]
    old = np.array(Image.open(S / 'mer_avant_cycle_reference.png').convert('RGBA'))
    profile = np.median(old[horizon:, :, :3], axis=1).astype(np.float32)
    profile = cv2.GaussianBlur(profile[:, None, :], (1, 5), 1)[:, 0, :]
    profile = np.rint(profile).clip(0, 255).astype('uint8')
    water = np.repeat(profile[:, None, :], width, axis=1)
    fixed = np.zeros((height, width, 4), np.uint8)
    fixed[horizon:, :, :3] = water
    fixed[horizon:, :, 3] = 255
    Image.fromarray(fixed).save(S / 'mer_native.png', optimize=True)
    # Extension miroir : les pixels se rejoignent exactement aux limites de bande.
    x = np.arange(width) % (2*rw)
    source_x = np.where(x < rw, x, 2*rw-1-x)
    atlas = Image.new('RGBA', (width*5, height*2))
    max_error = 0
    for i, frame in enumerate(raw):
        delta = frame.astype(float)-source_base[:, None, :].astype(float)
        mapped = np.rint(water.astype(float)+config['adaptation']['amplitude_couleurs']*delta[:, source_x]).clip(0, 255)
        bg = water.astype(float)
        needed = np.where(mapped >= bg, (mapped-bg)/np.maximum(255-bg, 1), (bg-mapped)/np.maximum(bg, 1))
        alpha = np.ceil(needed.max(axis=2)*255).clip(0, 255).astype('uint8')
        weight = alpha[:, :, None].astype(float)/255
        color = np.rint((mapped-bg*(1-weight))/np.maximum(weight, 1/255)).clip(0, 255).astype('uint8')
        overlay = np.zeros_like(fixed)
        overlay[horizon:, :, :3] = color
        overlay[horizon:, :, 3] = alpha
        overlay[overlay[:, :, 3] == 0] = 0
        q = Image.fromarray(overlay)
        atlas.paste(q, ((i % 5)*width, (i//5)*height))
        if i == 0:
            q.save(S / 'vagues_native.png', optimize=True)
        composed = Image.fromarray(fixed)
        composed.alpha_composite(q)
        error = int(np.abs(np.array(composed)[horizon:, :, :3].astype(int)-mapped.astype(int)).max())
        max_error = max(max_error, error)
    assert max_error <= 1
    atlas.save(S / 'vagues_cycle.png', optimize=True)
    print('Mer : 10 phases de référence adaptées ; fond et overlay séparés ; erreur de recomposition maximale', max_error)


if __name__ == '__main__':
    prepare()
