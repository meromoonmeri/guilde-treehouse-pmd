"""Casino complex: one coherent generated terrain, separately placed decor and native fire."""
from pathlib import Path
import sys,json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from source.casino_network_v1.prepare import OUT,SRC,save,rgba
ROOMS=[{'id':'scene','title':'Scène des braises','rect':[0,0,512,512],'ports':{'E':[512,256],'S':[256,512]}}, {'id':'salon','title':'Salon des mises','rect':[512,0,512,512],'ports':{'W':[512,256],'S':[768,512]}}, {'id':'accueil','title':'Accueil & change','rect':[0,512,512,512],'ports':{'N':[256,512],'E':[512,768],'S':[256,1024]}}, {'id':'jeux','title':'Salle des tables','rect':[512,512,512,512],'ports':{'N':[768,512],'W':[512,768]}}]
EDGES=[['scene','E','salon','W'],['scene','S','accueil','N'],['salon','S','jeux','N'],['accueil','E','jeux','W']]

def rug(w,h):
 src=Image.open(OUT/'objets/tapis_source_natif.png').convert('RGBA');im=Image.new('RGBA',(w,h));sw,sh=src.size
 for y in range(0,h,8):
  for x in range(0,w,8):
   sx=0 if x==0 else sw-8 if x==w-8 else 8+(x-8)%(sw-16)
   sy=0 if y==0 else sh-8 if y==h-8 else 8+(y-8)%(sh-16)
   im.alpha_composite(src.crop((sx,sy,sx+8,sy+8)),(x,y))
 return im

def main():
 terrain=rgba(OUT/'terrain_vide.webp');yy,xx=np.mgrid[:1024,:1024]
 # Coherent visible-surface partitions. Hidden ground is intact because furniture
 # was generated separately, not cut out of a furnished map.
 mask=Image.new('L',(1024,1024));d=ImageDraw.Draw(mask)
 for ox,oy in [(0,0),(512,0),(0,512),(512,512)]:d.rounded_rectangle((ox+72,oy+104,ox+448,oy+440),radius=64,fill=255)
 for box in [(208,344,304,1024),(720,344,816,688),(360,208,664,320),(352,704,704,808),(344,320,696,608)]:d.rectangle(box,fill=255)
 floor=np.array(mask)>0;solid=terrain[:,:,3]>0;floor&=solid;rest=solid&~floor
 defs=[('sol','Sol et passages',floor),('fond','Parois arrière',rest&((yy%512)<208)),('gauche','Bordures rocheuses · gauche',rest&((yy%512)>=208)&((yy%512)<408)&((xx%512)<256)),('droite','Bordures rocheuses · droite',rest&((yy%512)>=208)&((yy%512)<408)&((xx%512)>=256)),('avant','Roches de premier plan',rest&((yy%512)>=408))]
 layers=[]
 for ident,label,m in defs:
  a=terrain.copy();a[~m]=0;p=OUT/'calques'/f'Casino_terrain_{ident}.png';save(a,p);layers.append({'id':ident,'label':label,'group':'terrain','file':str(p.relative_to(OUT)),'position':[0,0],'size':[1024,1024]})
 # All carpet fragments use unscaled native 8px swatches, borders included.
 carpets={'scene':[(224,224,64,288),(272,224,240,64)],'salon':[(512,224,256,64),(736,272,64,240),(680,312,176,104)],'accueil':[(224,512,64,512),(280,736,232,64)],'jeux':[(512,736,256,64),(736,512,64,224),(640,840,224,104),(568,648,144,96),(808,648,144,96)]}
 carpet_mask=np.zeros((1024,1024),bool)
 for rects in carpets.values():
  for x,y,w,h in rects:carpet_mask[y:y+h,x:x+w]=True
 carpet_mask&=solid
 # A single continuous nine-slice texture is partitioned afterwards, avoiding
 # doubled trim across doorways and sector boundaries.
 up=np.zeros((1024,1024),np.int32);down=up.copy();left=up.copy();right=up.copy()
 for k in range(1024):
  up[k]=carpet_mask[k]*(1+(up[k-1] if k else 0));left[:,k]=carpet_mask[:,k]*(1+(left[:,k-1] if k else 0))
  j=1023-k;down[j]=carpet_mask[j]*(1+(down[j+1] if j<1023 else 0));right[:,j]=carpet_mask[:,j]*(1+(right[:,j+1] if j<1023 else 0))
 source=rgba(OUT/'objets/tapis_source_natif.png');sx=8+xx%40;sy=8+yy%24
 sx=np.where((left>0)&(left<=8),left-1,sx);sx=np.where((right>0)&(right<=8),56-right,sx)
 sy=np.where((up>0)&(up<=8),up-1,sy);sy=np.where((down>0)&(down<=8),40-down,sy)
 whole=source[sy,sx].copy();whole[~carpet_mask]=0
 for room in ROOMS:
  ident=room['id'];x,y,w,h=room['rect'];a=np.zeros_like(whole);a[y:y+h,x:x+w]=whole[y:y+h,x:x+w]
  p=OUT/'calques'/f'Casino_tapis_{ident}.png';save(a,p)
  layers.append({'id':'tapis_'+ident,'label':'Tapis · '+ident,'group':'tapis','file':str(p.relative_to(OUT)),'position':[0,0],'size':[1024,1024]})
 def instance(ident,label,asset,x,y,group,footprint=None):
  im=Image.open(OUT/'objets'/f'{asset}.png');entry={'id':ident,'label':label,'group':group,'file':f'objets/{asset}.png','position':[x,y],'size':list(im.size),'asset':asset}
  if footprint:entry['footprint']=footprint
  layers.append(entry)
 instance('estrade','Estrade','estrade',152,128,'scene',[152,160,208,72])
 instance('rideaux','Rideaux de scène','rideaux',152,56,'scene',[152,168,24,32])
 instance('kiosque_accueil','Kiosque de change','kiosque',80,696,'kiosques',[80,768,112,56])
 instance('kiosque_salon','Guichet du salon','kiosque',608,112,'kiosques',[608,184,112,56])
 instance('krow_bank','Krow Bank · objet natif','krow_bank_natif',328,832,'kiosques',[328,880,104,48])
 for ident,x,y in [('salon',712,328),('ouest',584,664),('est',824,664),('centre',680,856)]:instance('table_'+ident,'Table · '+ident,'table_jeu',x,y,'mobilier',[x,y+24,112,48])
 for ident,x,y in [('salon',872,112),('jeux',864,824)]:instance('fourneau_'+ident,'Fourneau · '+ident,'fourneau',x,y,'fourneaux',[x,y+64,104,56])
 torches=[('scene_g',96,224),('scene_d',392,160),('salon_g',584,288),('salon_d',928,288),('accueil_g',144,848),('accueil_d',408,672),('jeux_g',592,856),('jeux_d',936,728)]
 for ident,x,y in torches:instance('support_'+ident,'Brasero · '+ident,'brasero_support',x,y,'braseros',[x,y+40,32,24])
 flamefiles=[f'animations/Casino_flamme_native_{k:02d}.png' for k in range(4)]
 for ident,x,y in torches:
  layers.append({'id':'flamme_'+ident,'label':'Flamme native · '+ident,'group':'flammes','frames':flamefiles,'position':[x,y],'size':[32,40],'frame_ms':100,'count':4,'host':'support_'+ident,'native_unscaled':True})
 for ident,x,y in [('salon',872,112),('jeux',864,824)]:
  layers.append({'id':'feu_fourneau_'+ident,'label':'Feu natif du fourneau · '+ident,'group':'flammes','frames':flamefiles,'position':[x+32,y+32],'size':[32,40],'frame_ms':100,'count':4,'host':'fourneau_'+ident,'native_unscaled':True})
 data={'title':'Casino des braises','size':[1024,1024],'module_size':[512,512],'rooms':ROOMS,'edges':EDGES,'entrance':{'room':'accueil','direction':'S','point':[256,1023]},'layers':layers,'animation':{'frames':4,'frame_ms':100,'period_ms':400,'native_ticks':6},'terrain_origin':'Independently generated continuous network using Ledian materials as visual reference. Not the previously attached room.','geometry':'One continuous 1024-square composition, divided into four 512-square sectors; not four rotated/recoloured copies.','native_fire':'flammes_provenance.json','objects':'objets/manifest.json','runtime_PMDO':'NOT TESTED','limits':['Terrain is generated, not certified native tile art.','Terrain depth partitions are visible-surface masks, not movable complete rock volumes.','Room boundaries share a continuous image; arbitrary rearrangements are not certified seamless.','Object footprints are authoring hints, not implemented collisions.','Passages and decor arrangement require artistic and PMDO review.']}
 (OUT/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 composite=render(data,0);composite.save(OUT/'Casino_reseau_decore.webp',lossless=True,method=6,exact=True)
 composite.save(OUT/'Casino_apercu_anime.webp',save_all=True,append_images=[render(data,k) for k in range(1,4)],duration=100,loop=0,lossless=True,method=6,exact=True)
 page=(Path(__file__).parent/'viewer.html').read_text().replace('__DATA__',json.dumps(data,ensure_ascii=False))
 (ROOT/'apercu_casino_reseau_v1.html').write_text(page);(OUT/'index.html').write_text(page.replace('const ROOT="renders/casino_network_v1/"','const ROOT="./"'))
 from source.casino_network_v1.editor_setup import main as editor_setup
 editor_setup()
 print('Built',len(layers),'independent layer instances, 4 connected sectors, 8 native braziers, 2 furnaces with native fire.')

def render(data,frame=0,groups=None):
 im=Image.new('RGBA',tuple(data['size']))
 for l in data['layers']:
  if groups is not None and l['group'] not in groups:continue
  file=l['frames'][frame%4] if 'frames' in l else l['file'];im.alpha_composite(Image.open(OUT/file).convert('RGBA'),tuple(l['position']))
 return im

if __name__=='__main__':main()
