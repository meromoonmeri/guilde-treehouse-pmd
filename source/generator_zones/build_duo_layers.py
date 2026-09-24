from pathlib import Path
import numpy as np,json,hashlib,shutil
from PIL import Image,ImageFilter,ImageEnhance
R=Path('/home/user/guilde-treehouse-pmd'); SRC=R/'source/generator_zones'; OUT=R/'renders/generator_zones_duo_v1';
if OUT.exists(): shutil.rmtree(OUT)
items=[('maison_interieure_ovale.png','maison_interieure_ovale','water'),('clairiere_riviere_multicalque.png','clairiere_riviere','water'),('grotte_sinistre_multicalque.png','grotte_sinistre','water')]
for fn,z,kind in items:
 d=OUT/z;d.mkdir(parents=True); im=Image.open(SRC/fn).convert('RGBA'); a=np.array(im).astype(np.int16); bg=im.filter(ImageFilter.GaussianBlur(7)); bg=ImageEnhance.Contrast(bg).enhance(.85); bg.save(d/'00_fond.png'); terrain=im.filter(ImageFilter.GaussianBlur(1));terrain.save(d/'01_terrain.png')
 rgb=a[:,:,:3];
 if z.startswith('maison'): mask=(rgb[:,:,2]>rgb[:,:,0]*.85)&(rgb[:,:,1]>rgb[:,:,0]*.65)&(rgb[:,:,2]>90)
 elif z.startswith('clairiere'): mask=(rgb[:,:,2]>rgb[:,:,0]*.8)&(rgb[:,:,1]>rgb[:,:,0]*.8)&(rgb[:,:,2]>70)&(rgb[:,:,1]>70)
 else: mask=(rgb[:,:,2]>rgb[:,:,0]*.9)&(rgb[:,:,2]>80)&(rgb[:,:,1]<130)
 water=np.zeros_like(a,dtype=np.uint8);water[:,:,:3]=np.clip(a[:,:,:3],0,255).astype(np.uint8);water[:,:,3]=np.where(mask,255,0).astype(np.uint8);Image.fromarray(water).save(d/'04_eau_palette_cycling.png')
 detail=np.array(im);detail[:,:,3]=np.where(~mask,255,0).astype(np.uint8);Image.fromarray(detail).save(d/'02_entree_decors.png')
 frame=Image.new('RGBA',im.size,(0,0,0,0)); frame.save(d/'03_layout_ovale.png')
 frames=[]
 for i in range(4):
  wa=water.copy(); shift=np.roll(wa[:,:,:3],i*2,axis=1); wa[:,:,:3]=np.clip(shift.astype(int)+np.array([0,i*3,i*6]),0,255).astype(np.uint8); Image.fromarray(wa).save(d/f'04_eau_palette_cycling_phase_{i+1}.png');frames.append(Image.fromarray(wa))
 comp=bg.copy();comp.alpha_composite(terrain);comp.alpha_composite(Image.open(d/'02_entree_decors.png'));comp.save(d/'composite.png')
 (d/'zone.json').write_text(json.dumps({'zone':z,'source_generator':fn,'layers':['00_fond.png','01_terrain.png','02_entree_decors.png','03_layout_ovale.png','04_eau_palette_cycling_phase_1..4.png'],'water_animation':True,'palette_cycling_frames':4},indent=2))
manifest={'method':'generator image -> duo-style separated layers; generated zone layouts, separate water/palette-cycling layer','zones':[z for _,z,_ in items],'layer_order':['00_fond','01_terrain','02_entree_decors','03_layout_ovale','04_eau_palette_cycling'],'generator_sources':[f for f,_,_ in items]}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print('generated duo layers',len(items))
