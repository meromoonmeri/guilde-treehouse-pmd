from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
R=Path('/home/user/guilde-treehouse-pmd'); SRC=R/'source/commit_d5_refs'; OUT=R/'renders/network_zones_multicalques_v3'; SIZE=(480,360)
if OUT.exists():shutil.rmtree(OUT)
items=[('foret_verdoyante','IMG_4998.png','verdant forest','oval'),('grotte_volcanique','IMG_4996.jpeg','volcanic cave','oval'),('grotte_glacee','IMG_4997.jpeg','ice grotto','oval'),('lisiere_foret','IMG_5004.png','forest edge','oval'),('camp_souterrain','IMG_4999.png','earth cave camp','round'),('maison_interieure','IMG_5001.png','warm indoor forest house','round'),('grotte_sinistre','IMG_5002.png','sinister blue grotto','oval'),('ruines_blanches','IMG_5003.png','white sacred ruins','round'),('route_ruines','IMG_5004.png','forest ruins path','oval'),('marais_noir','IMG_5005.png','dark marsh','oval'),('riviere_jungle','IMG_5006.png','jungle river','oval'),('clairiere_fleurs','IMG_5007.png','flower clearing','oval')]
def fit(path):
 im=Image.open(path).convert('RGBA'); im.thumbnail((452,332),Image.Resampling.LANCZOS); o=Image.new('RGBA',SIZE,(0,0,0,0));o.alpha_composite(im,((480-im.width)//2,(360-im.height)//2));return o
def shape_mask(kind):
 m=Image.new('L',SIZE,0);d=ImageDraw.Draw(m)
 if kind=='round':d.ellipse((22,10,458,350),fill=255)
 else:d.rounded_rectangle((14,18,466,342),radius=74,fill=255)
 return m
def masked(im,m):
 a=np.array(im);a[:,:,3]=np.minimum(a[:,:,3],np.array(m));return Image.fromarray(a)
for zid,ref,biome,kind in items:
 d=OUT/zid;d.mkdir(parents=True); src=fit(SRC/ref); m=shape_mask(kind)
 # Generated editing stack: atmospheric fond, terrain, entrance, décor/highlights, and layout frame.
 fond=src.filter(ImageFilter.GaussianBlur(5)); fond=ImageEnhance.Color(fond).enhance(.82);fond=masked(fond,m);fond.save(d/'00_fond_biome_genere.png')
 terrain=src.filter(ImageFilter.GaussianBlur(1));terrain=ImageEnhance.Contrast(terrain).enhance(.92);terrain=masked(terrain,m);terrain.save(d/'01_sol_terrain_genere.png')
 ent=masked(src,m);ent.save(d/'02_entree_angle_reference.png')
 arr=np.array(src).astype(np.int16); blur=np.array(src.filter(ImageFilter.GaussianBlur(2))).astype(np.int16); diff=np.abs(arr[:,:,:3]-blur[:,:,:3]).mean(2); alpha=np.clip((diff-5)*24,0,230).astype(np.uint8);alpha=np.minimum(alpha,np.array(m)); dec=np.array(src);dec[:,:,3]=alpha;Image.fromarray(dec).save(d/'03_decors_lieux_genere.png')
 fx=Image.new('RGBA',SIZE,(0,0,0,0));fd=ImageDraw.Draw(fx);fd.rounded_rectangle((14,18,466,342),radius=74,outline=(211,180,111,210),width=3);fd.ellipse((28,12,452,348),outline=(70,58,43,135),width=2);fx.save(d/'04_cadre_layout_genere.png')
 c=fond.copy();c.alpha_composite(terrain);c.alpha_composite(ent);c.alpha_composite(Image.open(d/'03_decors_lieux_genere.png'));c.alpha_composite(fx);c.save(d/'composite.png')
 (d/'zone.json').write_text(json.dumps({'zone':zid,'biome':biome,'shape':kind,'source_reference':ref,'generated_layers':['00_fond_biome_genere.png','01_sol_terrain_genere.png','02_entree_angle_reference.png','03_decors_lieux_genere.png','04_cadre_layout_genere.png']},ensure_ascii=False,indent=2))
manifest={'version':'v3_generated_layers','source_commit':'d5c79863a63abfb39f68f80adf85ae4c061ed3bd','zones':len(items),'canvas_px':SIZE,'layers_per_zone':5,'method':'generated atmospheric/terrain/entry/decor/frame separation from each supplied reference; entrance angle preserved','biome_assignments':{i[0]:i[2] for i in items}}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));h={}
for p in OUT.rglob('*'):
 if p.is_file():h[str(p.relative_to(OUT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'hashes.json').write_text(json.dumps(h,indent=2));print('generated',len(items),'zone stacks x',5,'layers')
