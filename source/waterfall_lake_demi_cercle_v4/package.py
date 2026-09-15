from pathlib import Path
import zipfile
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_demi_cercle_v4'
im=Image.new('RGB',(1008,388),(23,44,50));d=ImageDraw.Draw(im);d.text((10,8),'V3 : raccords locaux',fill='white');d.text((514,8),'V4 : nouveau demi-cercle continu',fill='white')
im.paste(Image.open(R/'renders/waterfall_lake_raccords_v3/jour/COMPOSITION.png').convert('RGB'),(0,28));im.paste(Image.open(O/'jour/COMPOSITION.png').convert('RGB'),(504,28));im.save(O/'AVANT_APRES.png')
p=O/'waterfall_lake_demi_cercle_v4.zip'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for q in sorted(O.rglob('*')):
  if q.is_file() and q!=p:z.write(q,str(q.relative_to(R)))
 for q in sorted(Path(__file__).parent.glob('*.py')):z.write(q,str(q.relative_to(R)))
 q=R/'apercu_waterfall_lake_demi_cercle_v4.html';z.write(q,q.name)
print(p,p.stat().st_size)
