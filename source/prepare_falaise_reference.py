"""Prépare la reprise complète de la falaise de guilde au générateur, style EoS.

Le sommet ET la paroi viennent de la nouvelle native. L'emprise canonique et le
rectangle d'escalier sont conservés pour empêcher une dérive de disposition.
"""
from pathlib import Path
from PIL import Image
import numpy as np

S = Path(__file__).resolve().parent / 'falaise'


def prepare():
    generated = np.array(Image.open(S / 'falaise_eos_generee.png').convert('RGBA'))
    footprint = np.array(Image.open(S / 'masque_falaise.png').convert('L')) > 0
    assert generated.shape == (408, 480, 4)
    assert np.array_equal(generated[:, :, 3] > 0, footprint)
    result = generated.copy()
    staircase = np.array(Image.open(S / 'reference_escalier.png').convert('RGBA'))
    result[328:408, 196:284] = staircase
    result[result[:, :, 3] == 0] = 0
    assert np.array_equal(result[328:408, 196:284], staircase)
    r, g, b = [result[:, :, i].astype(int) for i in range(3)]
    green = (g > r+8) & (g > b+15)
    assert green[145:300, 150:330].mean() > .35, 'Prairie absente'
    assert green[320:328, 224:256].mean() < .2, 'Chemin déconnecté'
    Image.fromarray(result).save(S / 'falaise_native.png', optimize=True)
    print('Falaise entière issue du générateur ; prairie, bordures EoS, emprise et escalier contrôlés.')


if __name__ == '__main__':
    prepare()
