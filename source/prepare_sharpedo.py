"""Assemble prairie/chemin et nouvelle paroi naturelle, sans profil de créature."""
from pathlib import Path
from PIL import Image
import numpy as np
from prepare_bordures_pmd import apply_borders

S = Path(__file__).resolve().parent / 'sharpedo'


def prepare():
    # Conserver exactement la prairie déjà retenue.
    original = np.array(Image.open(S / 'falaise_avant_prairie.png').convert('RGBA'))
    meadow = np.array(Image.open(S / 'sommet_genere.png').convert('RGBA'))
    mask = np.array(Image.open(S / 'masque_harmonisation_sol.png').convert('L'))
    surface = np.array(Image.open(S / 'masque_sommet.png').convert('L')) > 0
    assert original.shape == meadow.shape == (384, 504, 4)
    assert np.all(mask[surface] == 255)
    w = mask.astype(np.uint32)[:, :, None]
    before = original.copy()
    before[:, :, :3] = ((meadow[:, :, :3].astype(np.uint32)*w
                        + original[:, :, :3].astype(np.uint32)*(255-w)+127)//255).astype('uint8')
    before[before[:, :, 3] == 0] = 0
    snapshot = np.array(Image.open(S / 'falaise_avant_paroi_naturelle.png').convert('RGBA'))
    assert np.array_equal(before, snapshot)
    # Le remplacement comprend la silhouette inférieure : ne pas conserver
    # l'ancienne mâchoire en ne changeant que la couleur des trous.
    wall = np.array(Image.open(S / 'paroi_naturelle_generee.png').convert('RGBA'))
    blend = np.array(Image.open(S / 'masque_paroi_naturelle.png').convert('L')).astype(np.uint32)[:, :, None]
    assert not blend[surface].any(), 'La prairie ne doit pas être repeinte'
    a = before[:, :, 3:4].astype(np.uint32)
    b = wall[:, :, 3:4].astype(np.uint32)
    alpha_numerator = a*(255-blend)+b*blend
    premultiplied = before[:, :, :3].astype(np.uint32)*a*(255-blend)+wall[:, :, :3].astype(np.uint32)*b*blend
    out = np.zeros_like(before)
    out[:, :, :3] = ((premultiplied+alpha_numerator//2)//np.maximum(alpha_numerator, 1)).clip(0, 255).astype('uint8')
    out[:, :, 3] = ((alpha_numerator[:, :, 0]+127)//255).astype('uint8')
    out[out[:, :, 3] == 0] = 0
    protected = blend[:, :, 0] == 0
    replaced = blend[:, :, 0] == 255
    assert np.array_equal(out[protected], before[protected])
    assert np.array_equal(out[replaced], wall[replaced])
    assert np.array_equal(out[surface], meadow[surface])
    assert np.count_nonzero(out[:, :, 3] != before[:, :, 3]) > 500, 'Ancien profil encore conservé'
    result = apply_borders(Image.fromarray(out))
    result.save(S / 'falaise_native.png', optimize=True)
    print('Paroi et bordures PMD assemblées ; chemin, prairie intérieure et emprise conservés.')


if __name__ == '__main__':
    prepare()
