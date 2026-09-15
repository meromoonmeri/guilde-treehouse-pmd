from pathlib import Path
import json,zipfile
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_raccords_v3';OLD=R/'renders/waterfall_lake_trois_v2';m=json.loads((OLD/'manifest.json').read_text());dest=O/'waterfall_lake_raccords_v3.zip'
board=Image.new('RGB',(1008,386),'#163644');d=ImageDraw.Draw(board);d.text((10,6),'AVANT - V2',fill='white');d.text((514,6),'APRES - ROCHE ET EAU DESSINEES ENSEMBLE',fill='white');board.paste(Image.open(OLD/'jour/COMPOSITION.png').convert('RGB'),(0,26));board.paste(Image.open(O/'jour/COMPOSITION.png').convert('RGB'),(504,26));board.save(O/'AVANT_APRES.png')
files={OLD/'manifest.json',R/m['source'],R/'source/layouts_magenta_v1/palette.py',R/'source/cote_v4_abyss/night.py',R/'apercu_waterfall_lake_raccords_v3.html',R/'renders/waterfall_lake_fidele_v1/sprites/matiere_cascade_gba.png'}
for mode in ['jour','nuit']:
 files.update((OLD/mode).glob('*.png'));files.add(OLD/mode/'ANIMATION.webp')
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in [O,Path(__file__).parent]:
  for p in sorted(folder.rglob('*')):
   if p.is_file() and p!=dest and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
 for p in sorted(files):z.write(p,str(p.relative_to(R)))
print(dest,dest.stat().st_size,'bytes')
