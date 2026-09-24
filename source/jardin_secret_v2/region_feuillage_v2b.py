"""v2b : masque du feuillage = tout le sous-bois du sol généré (pelouse+chemin fermés, retrait 6 px),
trouée du rayon, dégagement 6 px autour des arbres. Sert de guide magenta au générateur et de masque de recoupe."""
import numpy as np, os
from PIL import Image
from scipy import ndimage as ndi
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import compose_v2 as C
sol, lawn, carpet, void = C.ground()
H, W = C.H, C.W
yy, xx = np.mgrid[0:H, 0:W]
walk = ndi.binary_fill_holes(ndi.binary_closing(lawn | carpet, iterations=6, border_value=1))
region = ~ndi.binary_erosion(walk, iterations=6, border_value=0)
region &= ~(((xx - 408) / 78.0) ** 2 + (yy / 95.0) ** 2 < 1)
occ = np.zeros((H, W), bool)
for n, x, y in C.TREES:
    s = C.spr(n); h, w = s.shape[:2]; occ[y:y + h, x:x + w] |= s[..., 3] > 0
region &= ~ndi.binary_dilation(occ, iterations=6)
region = ndi.binary_opening(region, iterations=3)
lab, n = ndi.label(region); sz = ndi.sum(region, lab, range(1, n + 1)); region = np.isin(lab, 1 + np.flatnonzero(sz >= 3000))
g = np.zeros((H, W, 3), np.uint8); g[:] = (255, 0, 255); g[region] = (31, 71, 47)
rim = region & ~ndi.binary_erosion(region, iterations=5, border_value=1); g[rim] = (71, 111, 47)
Image.fromarray(g).save('guides/v2b_guide_feuillage_magenta.png'); np.save('travail/v2b_region_feuillage.npy', region)
