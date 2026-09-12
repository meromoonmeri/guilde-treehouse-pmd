"""Rebuild the 1:1 comparison and the small PNG-only PMDO import archive."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,zipfile
from zones_guidees.native_tools import Bank,BASE,CLIFF,ROOT
O=ROOT/'sprites/metano_import_png';assert json.loads((O/'verification.json').read_text())['status']=='PASS'
b=Bank();ref=Image.new('RGBA',(320,192))
for name in [BASE,CLIFF]:
    layer=Image.new('RGBA',(320,192))
    for y in range(48,72):
        for x in range(78,118):
            g=b.get(name,x,y)
            if g:layer.paste(b.image(g),(x*8-624,y*8-384))
    ref=Image.alpha_composite(ref,layer)
new=Image.open(O/'01_cirque/METANO_V3_CIRQUE_SCENE.png').crop((192,192,512,384))
out=Image.new('RGB',(704,280),'#1c3026');d=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
for x,label,im in [(16,'Métano original · pixels natifs',ref),(368,'Nouveau rendu · pixels natifs',new)]:
    d.text((x,16),label,font=font,fill='#ead39b');out.paste(im.convert('RGB'),(x,48))
d.text((16,250),'Deux extraits de 320 × 192 px. Aucun redimensionnement. Lieux différents.',font=font,fill='#bed1b3')
preview=ROOT/'apercus/metano_import_comparaison_1x.png';out.save(preview,optimize=True)
with zipfile.ZipFile(ROOT/'metano_png_import_v3.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(O.rglob('*')):
        if p.is_file():z.write(p,Path('METANO_PNG_IMPORT_V3')/p.relative_to(O))
    z.write(preview,'APERCU_NE_PAS_IMPORTER/comparaison_1x.png')
print('PNG import archive and 1:1 native comparison ready.')
