from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/world_map_9_continents_v1';LAY=OUT/'layers';FOND=ROOT/'source/user_committed_map_background.png';RAW=ROOT/'source/world_map_9_continents_v1/raws/continents_9_sur_fond.png'
if OUT.exists():shutil.rmtree(OUT)
LAY.mkdir(parents=True,exist_ok=True)
source_background=Image.open(FOND);base=source_background.convert('RGBA');raw=Image.open(RAW).convert('RGBA').resize(base.size,Image.Resampling.NEAREST)
a=np.array(raw);sample=a[4,4,:3].astype(int);dist=np.sqrt(((a[:,:,:3].astype(int)-sample)**2).sum(axis=2));a[:,:,3]=np.where(dist<26,0,a[:,:,3]);fg=Image.fromarray(a)
# Correct the composition: the ninth landmass is a compact separate continent,
# not a giant floating island. Replace the oversized top-center asset with a much
# smaller isolated landmass, leaving open sea around all nine continents.
top=fg.crop((248,0,386,88)).resize((58,37),Image.Resampling.NEAREST)
clear=Image.new('RGBA',(138,88),(0,0,0,0)); fg.paste(clear,(248,0))
fg.alpha_composite(top,(292,16))
# Add two tiny cloud islands as accents; they are clearly islands, not continents.
d=ImageDraw.Draw(fg)
for x,y in [(180,35),(420,42)]:
    d.ellipse((x-8,y-3,x+8,y+3),fill=(242,238,211,235),outline=(117,104,75,220))
    d.polygon([(x-5,y+2),(x+6,y+2),(x+3,y+7),(x-3,y+7)],fill=(103,77,55,255))
    d.rectangle((x-2,y+7,x+2,y+9),fill=(70,59,48,255))
# Enrich the open sea with small pixel-art islands, reefs, boats and navigation marks.
# These are maritime islets, not additional continents; the nine main landmasses remain unchanged.
from PIL import ImageDraw
d=ImageDraw.Draw(fg)
def island(x,y,w=7,h=4,accent=(105,74,42,255),green=True):
    d.polygon([(x-w,y),(x-w+2,y-h//2),(x-2,y-h),(x+w-2,y-h+1),(x+w,y),(x+w-2,y+h//2),(x,y+h),(x-w+2,y+h//2)],fill=(73,54,43,255))
    d.polygon([(x-w+1,y-1),(x-2,y-h+1),(x+w-2,y-h),(x+w-1,y),(x,y+h-1),(x-w+2,y+1)],fill=accent)
    if green:
        d.rectangle((x-1,y-h-3,x+1,y-h+1),fill=(44,82,42,255)); d.rectangle((x-3,y-h-2,x+3,y-h),fill=(59,112,48,255)); d.point((x+2,y-h-3),fill=(86,139,59,255))
for args in [(30,119,5,3),(57,171,6,3),(84,250,6,3),(127,57,5,3),(157,287,7,3),(215,47,5,3),(235,319,5,3),(327,49,5,3),(370,308,6,3),(424,126,5,3),(481,177,5,3),(526,218,6,3),(512,315,5,3),(47,333,5,3),(201,335,4,2),(402,252,5,3)]: island(*args)
# tiny archipelago chains, reefs and sailing marks
for x,y in [(67,107),(74,104),(81,101),(102,276),(109,280),(116,283),(344,292),(351,289),(358,286),(469,285),(476,289),(484,292)]:
    d.rectangle((x-2,y-1,x+2,y+1),fill=(80,112,65,230)); d.point((x,y-2),fill=(179,145,62,255))
for x,y in [(146,111),(187,166),(342,82),(452,233),(284,285),(508,146)]:
    d.line((x-4,y+3,x+4,y-3),fill=(71,71,58,220),width=1); d.line((x-3,y-3,x+3,y+3),fill=(71,71,58,220),width=1); d.point((x,y),fill=(210,164,62,255))
for x,y in [(72,289),(249,77),(389,337),(513,87)]:
    d.polygon([(x-4,y+3),(x+4,y+3),(x+2,y+1),(x-2,y+1)],fill=(58,50,45,255)); d.line((x,y-5,x,y+1),fill=(55,55,48,255)); d.polygon([(x,y-5),(x,y-1),(x+4,y-2)],fill=(174,83,49,255))
shutil.copy2(FOND, LAY/'00_fond_committe_image.png');fg.save(LAY/'01_continents_iles_lieux.png');full=base.copy();full.alpha_composite(fg);full.save(OUT/'WorldMap_9_Continents_UserBackground.png')
state={'format':'WorldMapUserFondTwoLayer','canvas_px':list(base.size),'source_background':'source/user_committed_map_background.png','layers':['layers/00_fond_committe_image.png','layers/01_continents_iles_lieux.png'],'continents':9,'elements':['small islands','floating islands','spatial rift','varied biomes']}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2));files={}
for p in OUT.rglob('*'):
 if p.is_file():files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':list(base.size),'layer_count':2,'source_background':'source/user_committed_map_background.png','files':files},ensure_ascii=False,indent=2))
print('placed 9-continent foreground on user committed background',base.size)
