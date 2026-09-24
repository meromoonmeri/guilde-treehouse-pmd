"""Plan de layout 928x1152 : GUIDE pour le generateur, aucun pixel final."""
from pathlib import Path
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[2]
W, H = 928, 1152
im = Image.new('RGB', (W, H), (110, 187, 86))  # prairie
d = ImageDraw.Draw(im)
d.rectangle([0, 0, W, 400], fill=(167, 142, 94))          # paroi crooked
d.rectangle([404, 90, 524, 250], fill=(20, 12, 8))        # bouche
d.rectangle([344, 250, 584, 450], fill=(231, 210, 160))   # parvis sable
d.rectangle([424, 450, 504, H], fill=(231, 210, 160))     # chemin sud
for x, y in [(60, 620), (720, 680), (120, 950), (740, 980)]:
    d.ellipse([x, y, x + 144, y + 120], fill=(49, 111, 36))  # arbres
    d.rectangle([x + 56, y + 64, x + 104, y + 120], fill=(135, 108, 77))
import random
rng = random.Random(7)
for _ in range(24):
    x = rng.randrange(40, W - 40)
    if 400 < x < 530:
        continue
    y = rng.randrange(480, H - 40)
    d.ellipse([x, y, x + 14, y + 14], fill=(255, 150, 200))  # fleurs
for x, y in [(300, 380), (600, 360), (250, 500), (680, 520)]:
    d.ellipse([x, y, x + 48, y + 32], fill=(140, 120, 90))   # rochers
im.save(R / 'source/entree_crooked_v1/plan_zones.png')
print('plan OK', im.size)
