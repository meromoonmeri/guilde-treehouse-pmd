from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageDraw
R=Path('/home/user/guilde-treehouse-pmd'); SRC=R/'source/commit_d5_refs'; OUT=R/'renders/network_zones_multicalques_v4'; SIZE=(480,360)
if OUT.exists():shutil.rmtree(OUT)
items=[('foret_verdoyante','IMG_4998.png','verdant forest','external'),('grotte_volcanique','IMG_4996.jpeg','volcanic cave','external'),('grotte_glacee','IMG_4997.jpeg','ice grotto','external'),('lisiere_foret','IMG_5004.png','forest edge','external'),('camp_souterrain','IMG_4999.png','earth cave camp','interior'),('maison_interieure','IMG_5001.png','interior house','interior'),('grotte_sinistre','IMG_5002.png','sinister grotto','external'),('ruines_blanches','IMG_5003.png','white ruins interior','interior'),('route_ruines','IMG_5004.png','forest ruins path','external'),('marais_noir','IMG_5005.png','dark marsh','external'),('riviere_jungle','IMG_5006.png','jungle river','external_water'),('clairiere_fleurs','IMG_5007.png','flower clearing','external')]
def fit(path):
 im=Image.open(path).convert('RGBA');im.thumbnail((460,340),Image.Resampling.LANCZOS);o=Image.new('RGBA',SIZE,(0,0,0,0));o.alpha_composite(im,((480-im.width)//2,(360-im.height)//2));return o
def region(im,box):
 out=Image.new('RGBA',SIZE,(0,0,0,0)); crop=im.crop(box);out.alpha_composite(crop,((SIZE[0]-crop.width)//2,(SIZE[1]-crop.height)//2));return out
for zid,ref,biome,kind in items:
 d=OUT/zid;d.mkdir(parents=True);im=fit(SRC/ref)
 # No generated content: every layer is a crop/mask of the supplied reference only.
 if kind=='interior':
  wall=im.copy();floor=region(im,(40,90,440,340));empty=region(im,(85,80,395,300));deco=region(im,(110,70,370,270))
  mask=Image.new('L',SIZE,0);ImageDraw.Draw(mask).ellipse((28,18,452,342),fill=255);empty.putalpha(mask);deco.putalpha(mask)
 else:
  wall=region(im,(0,0,480,150));floor=im.copy();empty=Image.new('RGBA',SIZE,(0,0,0,0));deco=region(im,(0,0,480,360))
 wall.save(d/'00_fond_murs_parois.png');floor.save(d/'01_sol_terrain_existant.png');empty.save(d/'02_salle_vide_layout.png');deco.save(d/'03_decor_existant.png')
 frame=Image.new('RGBA',SIZE,(0,0,0,0));fd=ImageDraw.Draw(frame);fd.ellipse((24,14,456,346),outline=(116,92,57,190),width=3) if kind=='interior' else None;frame.save(d/'04_cadre_layout.png')
 comp=wall.copy();comp.alpha_composite(floor);comp.alpha_composite(empty);comp.alpha_composite(deco);comp.alpha_composite(frame);comp.save(d/'composite.png')
 z={'zone':zid,'biome':biome,'source_reference':ref,'policy':'reference pixels only; layout/crops changed, no new water or invented landmarks','layers':['00_fond_murs_parois.png','01_sol_terrain_existant.png','02_salle_vide_layout.png','03_decor_existant.png','04_cadre_layout.png']}
 if kind=='external_water':z['water_animation']='allowed only for water pixels already present in the source zone';z['water_source']='IMG_5011.gif'
 (d/'zone.json').write_text(json.dumps(z,ensure_ascii=False,indent=2))
manifest={'version':'v4_conservative_layout_layers','source_commit':'d5c79863a63abfb39f68f80adf85ae4c061ed3bd','rule':'no invented water, no invented landmarks, no new biome elements; only layout extension/crop/masking of existing reference content','zones':len(items),'layers_per_zone':5,'interior_policy':'walls, floor, empty room and existing decor separated; oval mask only for interior layout','water_policy':'animate only source zones that already visibly contain water'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));h={}
for p in OUT.rglob('*'):
 if p.is_file():h[str(p.relative_to(OUT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'hashes.json').write_text(json.dumps(h,indent=2));print('built conservative reference-only layers',len(items))
