"""Textures de rêve générées -> couches et atlas circulaire de 36 phases RGBA."""
from pathlib import Path
from PIL import Image
from scipy.ndimage import map_coordinates
import numpy as np
import json

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / 'source/reve'
OUT = ROOT / 'reve/assets'


def hue(rgb, angle):
    c, s = np.cos(angle), np.sin(angle)
    m = np.array([[.299+.701*c+.168*s, .587-.587*c+.330*s, .114-.114*c-.497*s],
                  [.299-.299*c-.328*s, .587+.413*c+.035*s, .114-.114*c+.292*s],
                  [.299-.300*c+1.250*s, .587-.588*c-1.050*s, .114+.886*c-.203*s]])
    return np.clip(rgb @ m.T, 0, 1)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    Image.open(S / 'nebuleuse_generee.png').convert('RGB').resize((1280, 720), Image.Resampling.LANCZOS).save(OUT / 'nebuleuse.webp', lossless=True, method=4)
    ring = np.array(Image.open(S / 'anneaux_generes.png').convert('RGB').resize((768, 768), Image.Resampling.LANCZOS), dtype=float)/255
    n, count, cols, gutter = 256, 36, 6, 2
    y, x = np.mgrid[0:n, 0:n].astype(float)
    x = (x+.5-n/2)/(n/2);y = (y+.5-n/2)/(n/2)
    radius, theta = np.hypot(x, y), np.arctan2(y, x)
    tile = n+gutter*2
    atlas = Image.new('RGBA', (cols*tile, cols*tile))
    for f in range(count):
        phase = f/count
        a = 2*np.pi*phase
        rr = radius*(1+.035*np.sin(a)) + .012*np.sin(4*theta+a)
        tt = theta+.08*np.sin(a)+.035*np.sin(2*a)
        sx, sy = (rr*np.cos(tt)+1)*383.5, (rr*np.sin(tt)+1)*383.5
        rgb = np.stack([map_coordinates(ring[:, :, k], [sy, sx], order=1, mode='constant', cval=0) for k in range(3)], axis=2)
        rgb = hue(rgb, .32*np.sin(a))
        fade = np.clip((1-radius)/.11, 0, 1)*np.clip((radius-.19)/.07, 0, 1)
        alpha = np.sqrt(rgb.max(2))*fade
        rgba = np.zeros((n, n, 4), dtype=np.uint8)
        rgba[:, :, :3] = np.rint(np.clip(rgb/np.maximum(alpha[:, :, None], 1/255), 0, 1)*255).astype('uint8')
        rgba[:, :, 3] = np.rint(alpha*255).astype('uint8')
        rgba[rgba[:, :, 3] == 0] = 0
        rgba[[0, -1], :, :] = 0
        rgba[:, [0, -1], :] = 0
        padded = np.pad(rgba, ((gutter, gutter), (gutter, gutter), (0, 0)), mode='edge')
        atlas.paste(Image.fromarray(padded), ((f % cols)*tile, (f//cols)*tile))
        if f == 0:Image.fromarray(rgba).save(OUT / 'anneau_phase_0.png', optimize=True)
    atlas.save(OUT / 'anneaux_36_phases.png', optimize=True)
    manifest = {'dimensions_reference_quiz': [320, 240], 'sortie_reference_quiz': [960, 720],
                'halo_reference': [1280, 720], 'rendu': 'plein viewport adaptatif, caméra perspective 3D',
                'atlas': {'file': 'assets/anneaux_36_phases.png', 'frames': count, 'columns': cols,
                          'frame_size': [n, n], 'gutter': gutter, 'cycle_seconds': 6},
                'couches': ['nébuleuse multicolore à trois vitesses de parallaxe', 'anneaux circulaires multiframes en profondeur',
                            'étoiles et poussières 3D', 'sphère lumineuse 3D', 'interface du test'],
                'mouvement': 'avance dans le tunnel et orbite gauche/droite à chaque validation ; pas de progression automatique',
                'references': {'depot': 'meromoonmeri/mypmdproject', 'code_commit': 'e3fa166525d08202503200c77482a2c1cc9cabad',
                               'art_commit': '319d10f69605331a07c817227c85ec8d0aba3dab'}}
    (ROOT / 'reve/kit.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Rêve : nébuleuse et 36 phases circulaires RGBA préparées.')


if __name__ == '__main__':
    build()
