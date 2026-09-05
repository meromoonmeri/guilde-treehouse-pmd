"""Post-export uniquement : retirer le magenta, sans dessiner/repeindre le décor."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SRC = Path(__file__).parent / 'galerie_est_ouest_retenue.png'
OUT = ROOT / 'tilesheets/propositions_generees'
OUT.mkdir(parents=True, exist_ok=True)
original = np.array(Image.open(SRC).convert('RGBA'))
r, g, b = [original[:, :, i].astype(int) for i in range(3)]
key = (r > g + 45) & (b > g + 35) & (b > 75)
result = original.copy()
result[key] = 0
assert np.array_equal(result[~key], original[~key])
transparent = Image.fromarray(result)
transparent.save(OUT / 'galerie_est_ouest.png', optimize=True)
preview = Image.new('RGBA', transparent.size, (23, 16, 29, 255))
preview.alpha_composite(transparent)
preview.convert('RGB').save(OUT / 'galerie_est_ouest_apercu.png', optimize=True)
report = {'statut': 'Proposition visuelle générée, non intégrée au pack de modules',
          'source': str(SRC.relative_to(ROOT)), 'sha256_source': hashlib.sha256(SRC.read_bytes()).hexdigest(),
          'dimensions': list(transparent.size), 'redimensionnement': False,
          'traitements': ['Fond magenta retiré pour le PNG transparent', 'Fond sombre ajouté uniquement à l’aperçu'],
          'pixels_hors_masque_de_detourage_modifies': 0, 'calques_separes_prepares': False}
(OUT / 'controle_proposition.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
