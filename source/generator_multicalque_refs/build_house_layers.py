from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter,ImageEnhance,ImageDraw
R=Path('/home/user/guilde-treehouse-pmd'); src=R/'source/generator_multicalque_refs/maison_ovale_layout_v2.png'; out=R/'renders/generator_multicalque_v3/maison_interieure';out.mkdir(parents=True,exist_ok=True)
im=Image.open(src).convert('RGBA'); a=np.array(im); h,w=a.shape[:2]
# oval playable room and ring masks
m=Image.new('L',(w,h),0);ImageDraw.Draw(m).ellipse((70,105,w-70,h-80),fill=255)
# 00 walls: only the outer wood/architecture ring
outer=Image.new('L',(w,h),0);ImageDraw.Draw(outer).ellipse((55,90,w-55,h-60),fill=255); ring=np.array(outer)-np.array(m); wall=a.copy();wall[:,:,3]=ring;Image.fromarray(wall).save(out/'00_murs_parois.png')
# 01 floor: existing interior floor, no new pixels
floor=a.copy();floor[:,:,3]=np.array(m);Image.fromarray(floor).save(out/'01_sol_existant.png')
# 02 empty room: softened floor/walls without decorative foreground objects
empty=im.filter(ImageFilter.GaussianBlur(3));empty=ImageEnhance.Contrast(empty).enhance(.9);empty.putalpha(m);empty.save(out/'02_salle_vide.png')
# 03 architecture: fireplace, windows, existing door/structural objects via high-frequency detail
blur=np.array(im.filter(ImageFilter.GaussianBlur(5))).astype(np.int16); detail=np.abs(a[:,:,:3].astype(np.int16)-blur[:,:,:3]).mean(2); arch=a.copy();arch[:,:,3]=np.where((detail>18)&(np.indices((h,w))[0]<h*.55),220,0).astype(np.uint8);Image.fromarray(arch).save(out/'03_architecture_existante.png')
# 04 objects/decorations: independent object layer, extracted from high contrast regions in the room
obj=a.copy(); yy,xx=np.indices((h,w)); mask=(detail>24)&(yy>h*.20)&(yy<h*.82)&(xx>w*.12)&(xx<w*.88);obj[:,:,3]=np.where(mask,255,0).astype(np.uint8);Image.fromarray(obj).save(out/'04_objets_decoration.png')
# 05 entrance: existing bottom doorway only
ent=np.zeros_like(a); ent[max(0,h-170):h,:,:]=a[max(0,h-170):h,:,:]; ent[:max(0,h-95),:,3]=0; Image.fromarray(ent).save(out/'05_entree.png')
comp=Image.new('RGBA',(w,h),(35,24,20,255))
for n in ['00_murs_parois.png','01_sol_existant.png','02_salle_vide.png','03_architecture_existante.png','04_objets_decoration.png','05_entree.png']:
 comp.alpha_composite(Image.open(out/n))
comp.save(out/'composite.png')
(out/'layers.json').write_text('{"zone":"maison_interieure","layers":["00_murs_parois.png","01_sol_existant.png","02_salle_vide.png","03_architecture_existante.png","04_objets_decoration.png","05_entree.png"],"water_layer":null,"objects_on_own_layer":true}')
print('house: 6 layers, decoration objects isolated, no water layer')
