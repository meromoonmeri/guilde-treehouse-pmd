"""Prépare l'atlas redessiné et applique l'adaptation des bordures au cap.

Les illustrations proviennent du générateur. Python découpe, harmonise la palette
et applique la retouche locale ; il ne redessine ni le terrain ni les motifs.
"""
from pathlib import Path
from PIL import Image
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'source/bordures_pmd'
CAP = ROOT / 'source/sharpedo'


def build_atlas():
    meta = json.loads((BANK / 'definitions.json').read_text(encoding='utf-8'))
    raw = Image.open(BANK / 'atlas_generation_normalisee.png').convert('RGB')
    guide = Image.open(BANK / 'guide_atlas.png').convert('RGB')
    reference = np.array(Image.open(CAP / 'falaise_avant_bordures_pmd.png').convert('RGBA'))
    r, g, b = [reference[:, :, i].astype(int) for i in range(3)]
    grass = (g > r+4) & (g > b+20) & (reference[:, :, 3] > 0)
    rock = (r > g+10) & (r >= 85) & (b < g+40) & (reference[:, :, 3] > 0)
    pg = np.unique(reference[grass, :3], axis=0)
    pr = np.unique(reference[rock, :3], axis=0)
    tg, tr = cKDTree(pg.astype(float)), cKDTree(pr.astype(float))
    atlas = Image.new('RGBA', (meta['columns']*24, meta['rows']*24))
    for tile in meta['motifs']:
        i = tile['id']
        x, y = 12+(i % 5)*60, 12+(i//5)*60
        q = np.array(raw.crop((x, y, x+48, y+48)).resize((24, 24), Image.Resampling.NEAREST))
        proto = np.array(guide.crop((x, y, x+48, y+48)).resize((24, 24), Image.Resampling.NEAREST))
        valid = ~((proto[:, :, 0] > 240) & (proto[:, :, 1] < 30) & (proto[:, :, 2] > 240))
        r, g, b = [q[:, :, j].astype(int) for j in range(3)]
        magenta = (r-g > 70) & (b-g > 45)
        if magenta.any():
            _, indexes = distance_transform_edt(magenta, return_indices=True)
            q[magenta] = q[tuple(indexes[:, magenta])]
        r, g, b = [q[:, :, j].astype(int) for j in range(3)]
        green = (g > r+6) & (g > b+12)
        values = q.astype(float)
        q[green] = pg[tg.query(values[green])[1]]
        q[~green] = pr[tr.query(values[~green])[1]]
        rgba = np.zeros((24, 24, 4), np.uint8)
        rgba[:, :, :3] = q
        rgba[:, :, 3] = valid.astype('uint8')*255
        rgba[~valid] = 0
        atlas.paste(Image.fromarray(rgba), ((i % 5)*24, (i//5)*24))
    atlas.save(BANK / 'bordures_redessinees.png', optimize=True)
    print('Atlas PMD : 20 motifs redessinés, 24 × 24 px, orientations et palette conservées.')


def build_layout():
    # La rive arrière vient du motif N ; le reste du raccord suit la retouche
    # locale au générateur pour épouser les contours non rectangulaires du cap.
    base = np.array(Image.open(CAP / 'falaise_avant_bordures_pmd.png').convert('RGBA'))
    out = np.array(Image.open(CAP / 'bordures_layout_base.png').convert('RGBA'))
    mask = np.array(Image.open(CAP / 'masque_bordures_pmd.png'))
    bank = np.array(Image.open(BANK / 'bordures_redessinees.png').convert('RGBA'))
    placement = json.loads((BANK / 'placements_rive_nord.json').read_text(encoding='utf-8'))
    for point in placement['placement']:
        x, y, col = point['x'], point['y'], point['colonne']
        for depth, row in enumerate(placement['rows']):
            if mask[y+depth, x] and bank[row, col, 3]:
                out[y+depth, x] = bank[row, col]
        # Pas de deuxième ligne de roche isolée dans la prairie sous le rebord.
        for depth in range(len(placement['rows']), 11):
            if y+depth < out.shape[0] and mask[y+depth, x]:
                out[y+depth, x] = base[y+depth, x]
    Image.fromarray(out).save(CAP / 'bordures_layout_generees.png', optimize=True)


def apply_borders(base):
    before = np.array(Image.open(CAP / 'falaise_avant_bordures_pmd.png').convert('RGBA'))
    assert np.array_equal(np.array(base), before), 'La base du cap a changé avant les bordures'
    generated = np.array(Image.open(CAP / 'bordures_layout_generees.png').convert('RGBA'))
    mask = np.array(Image.open(CAP / 'masque_bordures_pmd.png').convert('L'))
    path = np.array(Image.open(CAP / 'masque_chemin_protege.png').convert('L')) > 0
    assert not mask[path].any()
    assert np.all(generated[mask > 0, 3] == 255)
    weight = mask.astype(np.uint32)[:, :, None]
    out = before.copy()
    out[:, :, :3] = ((generated[:, :, :3].astype(np.uint32)*weight
                     + before[:, :, :3].astype(np.uint32)*(255-weight)+127)//255).astype('uint8')
    out[out[:, :, 3] == 0] = 0
    assert np.array_equal(out[mask == 0], before[mask == 0])
    assert np.array_equal(out[path], before[path])
    assert np.array_equal(out[:, :, 3], before[:, :, 3]), 'Emprise modifiée'
    return Image.fromarray(out)


if __name__ == '__main__':
    build_atlas()
    build_layout()
