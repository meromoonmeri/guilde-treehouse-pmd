from pathlib import Path
import json
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/layouts_magenta_v1'
for mf,folder,target,cols,cell in [('manifest.json','zones','PLANCHE_8_PALETTES.png',2,(600,325)),('enhancements_manifest.json','variantes','PLANCHE_VARIANTES.png',3,(500,490))]:
 scenes=json.loads((O/mf).read_text())['scenes'];cw,ch=cell;o=Image.new('RGB',(cols*cw,((len(scenes)+cols-1)//cols)*ch),'#202630');d=ImageDraw.Draw(o)
 for i,e in enumerate(scenes):
  im=Image.open(O/folder/e['id']/'COMPOSITION.png');im.thumbnail((cw-12,ch-40),Image.Resampling.NEAREST);x=i%cols*cw;y=i//cols*ch;o.paste(im,(x,y+30));d.text((x+8,y+8),e['title'],fill='white')
 o.save(O/target)
