from pathlib import Path
import json,shutil,hashlib
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[2]; SRC=R/'source/commit_d5_refs'; O=R/'renders/network_zones_multicalques_v1'; S=R/'source/network_zones_multicalques_v1'; SIZE=(480,360)
if O.exists(): shutil.rmtree(O)
# Zone-by-zone network derived from d5c79863 references; every zone is a multi-layer editing unit.
zones=[
 ('foret_verdoyante','IMG_4998.png','IMG_5004.png','verdant forest','oval'),
 ('grotte_volcanique','IMG_4996.jpeg','IMG_4995.png','volcanic cave','oval'),
 ('grotte_glacee','IMG_4997.jpeg','IMG_5002.png','ice and blue-rock grotto','oval'),
 ('maison_ronde','IMG_5001.png','IMG_5007.png','warm forest house interior','round'),
 ('ruines_blanches','IMG_5003.png','IMG_5006.png','white stone ruins by river','round'),
 ('foret_sinistre','IMG_5005.png','IMG_5002.png','sinister dark forest','oval'),
 ('lisiere_automne','IMG_5004.png','IMG_5007.png','autumn forest edge','oval'),
 ('clairiere_riviere','IMG_5006.png','IMG_5007.png','river clearing / jungle','oval'),
]
def fit(p):
 im=Image.open(p).convert('RGBA'); im.thumbnail(SIZE,Image.Resampling.LANCZOS); out=Image.new('RGBA',SIZE,(0,0,0,0)); out.alpha_composite(im,((SIZE[0]-im.width)//2,(SIZE[1]-im.height)//2)); return out
def oval_mask():
 m=Image.new('L',SIZE,0); d=ImageDraw.Draw(m); d.ellipse((22,18,458,342),fill=255); return m
for zid,ground,entry,biome,shape in zones:
 d=O/zid; d.mkdir(parents=True)
 g=fit(SRC/ground); e=fit(SRC/entry)
 g.save(d/'00_fond_biome.png')
 # Separate terrain and entry layers; the entry is rounded/oval rather than square.
 terrain=g.copy(); terrain.putalpha(terrain.getchannel('A').point(lambda x:min(x,210))); terrain.save(d/'01_terrain.png')
 mask=oval_mask() if shape in ('oval','round') else Image.new('L',SIZE,255)
 ent=e.copy(); ent.putalpha(mask); ent.save(d/'02_entree_forme_ovale.png')
 details=Image.new('RGBA',SIZE,(0,0,0,0)); dd=ImageDraw.Draw(details); dd.ellipse((22,18,458,342),outline=(84,70,48,210),width=3); details.save(d/'03_cadre_layout.png')
 (d/'layout.json').write_text(json.dumps({'zone':zid,'biome':biome,'shape':shape,'layers':['00_fond_biome.png','01_terrain.png','02_entree_forme_ovale.png','03_cadre_layout.png'],'source_ground':ground,'source_entry':entry},ensure_ascii=False,indent=2))
 # Preview composite.
 c=g.copy(); c.alpha_composite(terrain); c.alpha_composite(ent); c.alpha_composite(details); c.save(d/'composite.png')
manifest={'source_commit':'d5c79863a63abfb39f68f80adf85ae4c061ed3bd','canvas_px':SIZE,'zones':len(zones),'multilayer_per_zone':4,'indoor_shape':'rounded oval/round instead of square','zones':[z[0] for z in zones],'black_white_assignments':{'IMG_5002.png':'grotte_glacee_or_sinister_forest','IMG_5003.png':'ruines_blanches','IMG_5005.png':'foret_sinistre'},'note':'Reference pixels are preserved; layers separate entrance, biome terrain and layout frame for further game integration.'}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
files={}
for p in O.rglob('*'):
 if p.is_file(): files[str(p.relative_to(O))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(O/'hashes.json').write_text(json.dumps(files,indent=2))
print('built',len(zones),'zones x 4 layers')
