from pathlib import Path
import json,hashlib
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/entrees_six_donjons_v1/sakura_validee';O.mkdir(exist_ok=True);SRC=R/'renders/entrees_six_donjons_v1/bruts/sakura_printemps_A.png'
im=Image.open(SRC).convert('RGBA');a=np.array(im);h,w=a.shape[:2];rgb=a[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1);yy,xx=np.mgrid[:h,:w];struct=np.ones((3,3),bool)
plate=Image.open(O/'travail/sol_reconstitue.png').convert('RGBA');assert plate.size==im.size
pa=np.array(plate);grass=(pa[:,:,1].astype(int)-pa[:,:,0]>20)&(pa[:,:,0]<155);pa[grass,:3]=np.clip(pa[grass,:3].astype(int)+[-1,6,6],0,255);plate=Image.fromarray(pa);plate.save(O/'SOL_PROPRE_alternative.png')
pink=(r-g>3)&(b-g>0);brown=(r-g>3)&(g-b>3)&(g<170)&(r<215)
lab,n=nd.label(pink|brown,struct);sizes=np.bincount(lab.ravel());canopies=sizes[lab]>2000;canopies[lab==0]=False
trees=canopies|(brown&nd.binary_dilation(canopies,iterations=32));trees=nd.binary_fill_holes(nd.binary_closing(trees,struct));trees[:2]=canopies[:2];trees[-2:]=canopies[-2:];trees[:,:2]=canopies[:,:2];trees[:,-2:]=canopies[:,-2:]
# The shaded gap between the trunks is a separate, removable entrance-depth layer.
p=Image.new('L',im.size);ImageDraw.Draw(p).polygon([(589,116),(618,146),(651,180),(659,208),(643,229),(610,214),(570,229),(535,229),(524,194),(547,157)],fill=255)
portal=(np.array(p)>0)&(r<90)&(g<100)&(b>g*.72);trees=nd.binary_dilation(trees,iterations=2);trees&=~portal
# Low vegetation and petals: color islands plus local plant masks, never rectangular sprite cutouts.
vegetation=pink&~trees&~portal
plantboxes=[(451,724,515,781),(1026,724,1080,780),(568,781,618,827),(674,559,742,605),(671,604,709,650),(711,596,758,642),(455,335,508,381),(345,678,386,713)]
for x0,y0,x1,y1 in plantboxes:
 crop=rgb[y0:y1,x0:x1];edge=np.concatenate([crop[0],crop[-1],crop[:,0],crop[:,-1]]);bg=np.median(edge,axis=0);local=np.linalg.norm(crop-bg,axis=2)>28;local=nd.binary_fill_holes(nd.binary_closing(local,struct));vegetation[y0:y1,x0:x1]|=local
shadow=(g-r>10)&(g<145)&(b>=r*.9)&~trees&~vegetation&~portal
smallgrass=(g>r*1.18)&(g-b>40)&(g<150)&~trees&~vegetation&~shadow&~portal
labs,n=nd.label(smallgrass,struct);counts=np.bincount(labs.ravel());smallgrass=(counts[labs]>=3)&(counts[labs]<=260)&(labs>0);vegetation|=smallgrass;vegetation&=~trees&~portal
vegetation=nd.binary_dilation(vegetation,iterations=3)&~trees&~portal
shade=Image.new('L',im.size);ImageDraw.Draw(shade).polygon([(522,208),(541,262),(488,310),(565,329),(650,329),(701,315),(650,259),(646,208)],fill=255)
shadow=nd.binary_dilation(nd.binary_fill_holes(shadow),iterations=3)|(np.array(shade)>0);shadow&=~trees&~vegetation&~portal
# Explicit isolated trees keep their full visible crowns and trunks; no regenerated sprites.
individuals={}
for name,box in [('arbre_centre',(347,397,531,591)),('arbre_avant_gauche',(137,563,329,756))]:
 x0,y0,x1,y1=box;m=np.zeros((h,w),bool);m[y0:y1,x0:x1]=trees[y0:y1,x0:x1];m&=(pink|brown|(g<50));m=nd.binary_fill_holes(m);lab,n=nd.label(m,struct);counts=np.bincount(lab.ravel());counts[0]=0;m=lab==int(np.argmax(counts));individuals[name]=(m,box)
for mm,box in individuals.values():
 fringe=nd.binary_dilation(mm,iterations=2)&trees&~mm
 trees[fringe]=False;shadow[fringe]=True
used=np.zeros((h,w),bool)
for m,box in individuals.values():used|=m
massif=trees&~used
masks={'02_ombres_portees':shadow,'03_vegetation_basse_petales':vegetation,'04_profondeur_entree':portal,'05_arbres_lisiere':massif,'06_arbre_centre':individuals['arbre_centre'][0],'07_arbre_avant_gauche':individuals['arbre_avant_gauche'][0]}
allmask=np.zeros((h,w),bool)
for m in masks.values():assert not np.any(allmask&m);allmask|=m
base=a.copy();base[allmask]=np.array(plate)[allmask];layers={'01_sol_chemin_reconstitue':Image.fromarray(base)}
for name,m in masks.items():
 ar=a.copy();ar[~m]=0;layers[name]=Image.fromarray(ar)
for name,l in layers.items():l.save(O/(name+'.png'))
# Convenient combined tree layer is an alternative to05+06+07, not an additional overlay.
ar=a.copy();ar[~trees]=0;Image.fromarray(ar).save(O/'ARBRES_TOUS_alternative.png')
comp=layers['01_sol_chemin_reconstitue'].copy()
for name,l in layers.items():
 if name!='01_sol_chemin_reconstitue':comp.alpha_composite(l)
assert np.array_equal(np.array(comp),a);comp.save(O/'composition_identique.png')
# Full isolated sprites, grid8 aligned atlas, no resizing. Anchor is at trunk contact.
atlas=Image.new('RGBA',(416,216));atlasmeta=[]
for idx,(name,(m,box)) in enumerate(individuals.items()):
 out=a.copy();out[~m]=0;crop=Image.fromarray(out).crop(box);sprite=Image.new('RGBA',(((crop.width+7)//8)*8,((crop.height+7)//8)*8));sprite.paste(crop,(0,0));sprite.save(O/(name+'_sprite.png'));x=8+idx*208;y=8;atlas.alpha_composite(sprite,(x,y));bbox=sprite.getbbox();atlasmeta.append({'name':name,'source_box':list(box),'atlas_box':[x,y,x+sprite.width,y+sprite.height],'origin_scene':list(box[:2]),'anchor':[(bbox[0]+bbox[2])//2,bbox[3]-1],'complete_visible_sprite':True})
atlas.save(O/'SAKURA_ARBRES_tilesheet_8px.png')
# Source-size masks and manual edition helpers.
md=O/'masques';md.mkdir(exist_ok=True)
for name,m in masks.items():Image.fromarray((m*255).astype('uint8')).save(md/(name+'.png'))
manifest={'size':[w,h],'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'layers':list(layers),'composition_pixel_identical':True,'trees_tilesheet':{'file':'SAKURA_ARBRES_tilesheet_8px.png','size':list(atlas.size),'grid':8,'sprites':atlasmeta},'ground_hidden_areas':'reconstructed by generator; visible uncovered source pixels unchanged','shadow_method':'Original painted shadow pixels on transparent canvas; position-bound, not a universal black multiply mask','runtime_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('7 aligned layers,2 isolated tree sprites,exact original recomposition')
# Inspection preview without altering export resolution.
board=Image.new('RGB',(1200,900),'#252b26');d=ImageDraw.Draw(board)
for i,(name,l) in enumerate(list(layers.items())[:5]+[('composition',comp)]):
 q=l.copy();q.thumbnail((396,270),Image.Resampling.NEAREST);x=i%3*400;y=i//3*450;board.paste(q,(x,y+28),q);d.text((x+8,y+8),name,fill='white')
board.save(O/'inspection_calques.png')
