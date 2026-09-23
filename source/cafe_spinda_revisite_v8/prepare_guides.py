"""Future wall-generation references only. Never replaces production room layers."""
from pathlib import Path
import io,json,zipfile
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'.cache/spinda8/references';O.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(R/'renders/cafe_spinda_revisite_v7/SpindaV7_complet.zip') as z:
 for r in json.loads(z.read('manifest.json'))['rooms']:
  im=Image.new('RGBA',(600,448))
  for l in r['layers']:
   if l['id']!='fenetres':im.alpha_composite(Image.open(io.BytesIO(z.read(l['file']))).convert('RGBA'))
  im.save(O/(r['id']+'.png'))
  if r['id']=='cafe':
   crop=im.crop((140,36,460,136)).resize((1280,400),Image.Resampling.NEAREST);crop.save(O/'mur_fenetres.png');d=ImageDraw.Draw(crop)
   for x,y in [(84,68),(236,68)]:d.ellipse(((x-14)*4,(y-14)*4,(x+14)*4,(y+14)*4),fill='#ff00ff')
   crop.save(O/'mur_fenetres_guide.png')
print('Guides only:',O)
