from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageDraw,ImageFilter
R=Path('/home/user/guilde-treehouse-pmd'); SRC=R/'source/commit_d5_refs'; OUT=R/'renders/network_zones_multicalques_v2'; SIZE=(480,360)
if OUT.exists():shutil.rmtree(OUT)
# Every reference receives a concrete zone, biome assignment and independent entrance/fond stack.
items=[
('zone_01_cave_verte','IMG_4995.png','grotte forestiere verdoyante','oval'),('zone_02_cave_volcanique','IMG_4996.jpeg','grotte volcanique rouge','oval'),('zone_03_portail_glace','IMG_4997.jpeg','grotte glacee bleue','oval'),('zone_04_lisiere_foret','IMG_4998.png','lisiere foret verdoyante','oval'),('zone_05_camp_souterrain','IMG_4999.png','caverne terreuse chaleureuse','round'),('zone_06_maison_interieure','IMG_5001.png','maison forestiere interieure','round'),('zone_07_grotte_sombre','IMG_5002.png','grotte sinistre bleue','oval'),('zone_08_sanctuaire_blanc','IMG_5003.png','ruines blanches sacrees','round'),('zone_09_route_ruines','IMG_5004.png','route de ruines en foret','oval'),('zone_10_marais_noir','IMG_5005.png','marais foret sombre','oval'),('zone_11_riviere_jungle','IMG_5006.png','jungle et riviere','oval'),('zone_12_clairiere_fleurs','IMG_5007.png','clairiere fleurie tropicale','oval')]
anims=[('IMG_5009.gif','zone_04_lisiere_foret'),('IMG_5010.gif','zone_06_maison_interieure'),('IMG_5011.gif','zone_11_riviere_jungle'),('IMG_5012.gif','zone_07_grotte_sombre'),('IMG_5013.gif','zone_10_marais_noir')]
def fit(path):
 im=Image.open(path).convert('RGBA'); im.thumbnail((440,320),Image.Resampling.LANCZOS); out=Image.new('RGBA',SIZE,(0,0,0,0));out.alpha_composite(im,((480-im.width)//2,(360-im.height)//2));return out
def mask(shape):
 m=Image.new('L',SIZE,0);d=ImageDraw.Draw(m)
 if shape=='round': d.ellipse((30,10,450,350),fill=255)
 else: d.rounded_rectangle((18,22,462,338),radius=62,fill=255)
 return m
for zid,ref,biome,shape in items:
 d=OUT/zid;d.mkdir(parents=True)
 src=fit(SRC/ref); m=mask(shape)
 # fond: clean biome atmosphere from reference, then a clearly separate oval/rounded playable room
 bg=Image.new('RGBA',SIZE,(23,28,25,255)); low=src.copy();low.putalpha(low.getchannel('A').point(lambda a:int(a*.23)));bg.alpha_composite(low)
 bg.save(d/'00_fond_biome.png')
 sol=Image.new('RGBA',SIZE,(0,0,0,0)); sd=ImageDraw.Draw(sol); sd.ellipse((38,28,442,332),fill=(104,126,59,120) if 'foret' in biome or 'jungle' in biome else (130,104,72,120)); sol.putalpha(m); sol.save(d/'01_sol_ovale.png')
 ent=src.copy(); ent.putalpha(m); ent.save(d/'02_entree_fond_reference.png')
 frame=Image.new('RGBA',SIZE,(0,0,0,0));fd=ImageDraw.Draw(frame);fd.rounded_rectangle((18,22,462,338),radius=62,outline=(214,186,117,230),width=4);fd.ellipse((35,18,445,342),outline=(61,51,40,170),width=2);frame.save(d/'03_nouveau_layout_ovale.png')
 details=Image.new('RGBA',SIZE,(0,0,0,0));dd=ImageDraw.Draw(details);dd.rectangle((26,28,84,46),fill=(34,30,28,210));dd.rectangle((32,32,78,42),fill=(230,212,151,220));details.save(d/'04_repere_entree.png')
 comp=bg.copy();comp.alpha_composite(sol);comp.alpha_composite(ent);comp.alpha_composite(frame);comp.alpha_composite(details);comp.save(d/'composite.png')
 (d/'zone.json').write_text(json.dumps({'zone':zid,'biome':biome,'source':ref,'shape':shape,'layers':['00_fond_biome.png','01_sol_ovale.png','02_entree_fond_reference.png','03_nouveau_layout_ovale.png','04_repere_entree.png']},ensure_ascii=False,indent=2))
for af,zid in anims: shutil.copy2(SRC/af,OUT/zid/'05_animation_reference.gif')
manifest={'source_commit':'d5c79863a63abfb39f68f80adf85ae4c061ed3bd','canvas_px':SIZE,'zones':len(items),'layers_per_zone':5,'animations':len(anims),'interiors':'rounded/oval layouts preserve the reference viewing angle','black_white_biomes':{'IMG_5002.png':'grotte sinistre bleue','IMG_5003.png':'ruines blanches sacrees','IMG_5005.png':'marais foret sombre'},'all_reference_files':[x[1] for x in items]+[x[0] for x in anims]}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
h={}
for p in OUT.rglob('*'):
 if p.is_file():h[str(p.relative_to(OUT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'hashes.json').write_text(json.dumps(h,indent=2));print('v2',len(items),'zones',len(anims),'animations')
