from pathlib import Path
import zipfile
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_fidele_v1';dest=O/'waterfall_lake_fidele_v1.zip'
source='Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Waterfall Lake.png'
# Reproducible visual comparison, both panels native456x312.
board=Image.new('RGB',(912,340),'#163644');d=ImageDraw.Draw(board);d.text((10,7),'REFERENCE ORIGINALE',fill='white');d.text((466,7),'EDITION - MEME CADRAGE ET ECHELLE',fill='white');board.paste(Image.open(R/source).convert('RGB'),(0,28));board.paste(Image.open(O/'jour/COMPOSITION_CADRE_ORIGINAL.png').convert('RGB'),(456,28));board.save(O/'COMPARAISON_NATIVE.png')
files=[source,'apercu_waterfall_lake_fidele_v1.html','source/amp_plains_fleurie_v1/inspect_references.py','source/cote_v4_abyss/night.py','source/eau_metano/natifs/Metano_Town_Animation_Tileset.tile']
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in [O,Path(__file__).parent]:
  for p in sorted(folder.rglob('*')):
   if p.is_file() and p!=dest and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(R)))
 for name in files:z.write(R/name,name)
print(dest,dest.stat().st_size,'bytes')
