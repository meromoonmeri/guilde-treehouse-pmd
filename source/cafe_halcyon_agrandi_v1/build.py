"""Enlarge Halcyon's actual cafe using intact 64px material bands, no resampling."""
from pathlib import Path
import hashlib,json,sys,shutil,zipfile
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];S=R/'source/cafe_multietage_v1/references';O=R/'renders/cafe_halcyon_agrandi_v1';HERE=Path(__file__).parent
SIZE=(840,576);EX=384;EY=256

def load(p):return Image.open(p).convert('RGBA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
def keyed_native():
 a=np.array(load(S/'Metano_Town_Cafe_Base.png'));bg=a[0,0,:3];same=np.all(a[:,:,:3]==bg,axis=2);labels,_=nd.label(same)
 edge=np.unique(np.concatenate([labels[0],labels[-1],labels[:,0],labels[:,-1]]));edge=edge[edge!=0];a[np.isin(labels,edge)]=0
 # Background-keying can leave disconnected dither flecks outside the room.
 labels,n=nd.label(a[:,:,3]>0);counts=np.bincount(labels.ravel());counts[0]=0
 a[labels!=counts.argmax()]=0
 return a

def geometry():
 src=keyed_native()
 # Complete 64px repeats preserve knots, board grain and native side-wall motifs.
 xs=np.r_[np.arange(224),np.tile(np.arange(160,224),6),np.arange(224,456)]
 ys=np.r_[np.arange(224),np.tile(np.arange(160,224),4),np.arange(224,320)]
 sx,sy=np.meshgrid(xs,ys);a=src[sy,sx].copy()
 # Keep ONE south door with its original centre offset, not six repeated doors.
 # Replace old shifted door by intact normal southern edging; move native door.
 for dest,box in [((640,544),(160,288,232,320)),((448,544),(256,288,328,320))]:
  x,y=dest;l,t,r,b=box;yy,xx=np.mgrid[t:b,l:r];sx[y:y+b-t,x:x+r-l]=xx;sy[y:y+b-t,x:x+r-l]=yy;a[y:y+b-t,x:x+r-l]=src[yy,xx]
 # Repair the source atlas's tiny alpha gap across the doorway with the
 # adjacent, unchanged native floor tile; never leave magenta across the route.
 raw=np.array(load(S/'Metano_Town_Cafe_Base.png'))
 gap=(sx>=264)&(sx<320)&(sy>=296)&(sy<304)&(raw[sy,sx,3]==0)
 sx[gap]=264+sx[gap]%8;sy[gap]=296+(sy[gap]-296)%8;a[gap]=src[sy[gap],sx[gap]]
 return a,sx,sy

def terrain():
 a,sx,sy=geometry();h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w]
 source_floor=Image.new('L',(456,320));d=ImageDraw.Draw(source_floor)
 d.polygon([(112,88),(344,88),(429,144),(429,239),(350,296),(109,296),(27,239),(27,144)],fill=255)
 d.rectangle((264,288,319,319),fill=255)
 floor=(np.array(source_floor)[sy,sx]>0)&(a[:,:,3]>0);shell=(a[:,:,3]>0)&~floor
 definitions=[('sol','Plancher et seuil',floor),('mur_fond','Boiseries arrière · Halcyon',shell&(yy<144)),('mur_gauche','Retour gauche',shell&(yy>=144)&(yy<512)&(xx<w//2)),('mur_droit','Retour droit',shell&(yy>=144)&(yy<512)&(xx>=w//2)),('bord_avant','Bordure avant et entrée',shell&(yy>=512))]
 layers=[]
 for ident,title,mask in definitions:
  part=a.copy();part[~mask]=0;p=O/'calques'/f'CafeHalcyon_{ident}.png';save(Image.fromarray(part),p);layers.append({'id':ident,'title':title,'file':str(p.relative_to(O)),'size':[w,h],'origin':[0,0],'role':'terrain','source':'Metano_Town_Cafe_Base.tile'})
 comp=Image.fromarray(a);save(comp,O/'CafeHalcyon_terrain_transparent.png')
 magenta=Image.new('RGBA',SIZE,(255,0,255,255));magenta.alpha_composite(comp);save(magenta,O/'CafeHalcyon_terrain_magenta.png')
 save(Image.fromarray((floor*255).astype('uint8')),O/'guides/CafeHalcyon_surface_libre.png')
 return layers,a,floor

def library():
 assets=[]
 for suffix,label in [('Objects_Under','Ombres et éléments bas'),('Objects','Mobilier du café'),('Objects_Over','Éléments supérieurs'),('Objects_Fringe','Premier plan')]:
  original=S/f'Metano_Town_Cafe_{suffix}.png';target=O/'mobilier'/f'CafeHalcyon_{suffix}.png';save(load(original),target)
  assets.append({'id':suffix,'title':label,'file':str(target.relative_to(O)),'size':list(load(target).size),'source':str(original.relative_to(R)),'source_rgba_sha256':hashlib.sha256(load(original).tobytes()).hexdigest(),'native':True,'placement':None})
 fire=R/'renders/casino_network_v1';frames={}
 for kind,old,h in [('flamme','flamme_native',40),('brasero','brasero_natif',64)]:
  paths=[];strip=Image.new('RGBA',(128,h))
  for i in range(4):
   original=fire/'animations'/f'Casino_{old}_{i:02d}.png';target=O/'animations'/f'CafeHalcyon_{kind}_{i:02d}.png';save(load(original),target);strip.alpha_composite(load(original),(i*32,0));paths.append(str(target.relative_to(O)))
  target=O/'animations'/f'CafeHalcyon_{kind}_4poses.png';save(strip,target)
  frames[kind]={'frames':paths,'sheet':str(target.relative_to(O)),'frame_size':[32,h],'frame_rects':[[32*i,0,32,h] for i in range(4)],'frame_ms':100,'source_ticks':6,'loop_ms':400,'placement':None}
 support=O/'mobilier/CafeHalcyon_support_brasero.png';save(load(fire/'objets/brasero_support.png'),support)
 assets.append({'id':'support','title':'Support de brasero sans feu','file':str(support.relative_to(O)),'size':[32,64],'native':True,'placement':None})
 # The existing generated furnace remains clearly identified as generated,
 # separate from its unchanged native fire. No object instance on the map.
 furnace=O/'mobilier/CafeHalcyon_fourneau_sans_feu.png';save(load(fire/'objets/fourneau.png'),furnace)
 assets.append({'id':'fourneau','title':'Corps de fourneau · généré, non natif','file':str(furnace.relative_to(O)),'size':list(load(furnace).size),'native':False,'source':'renders/casino_network_v1/objets/fourneau.png','flame_offset':[32,32],'placement':None})
 shutil.copyfile(fire/'flammes_provenance.json',O/'flammes_provenance.json')
 return assets,frames

def main():
 O.mkdir(parents=True,exist_ok=True);layers,a,floor=terrain();assets,animations=library()
 original=load(S/'metano_cafe_reference.png');save(original,O/'reference_halcyon.png')
 hashes=json.loads((S/'hashes.json').read_text());sources=[]
 for name in ['metano_cafe.rsground','Metano_Town_Cafe_Base.tile','Metano_Town_Cafe_Objects.tile','Metano_Town_Cafe_Objects_Under.tile','Metano_Town_Cafe_Objects_Over.tile','Metano_Town_Cafe_Objects_Fringe.tile']:
  assert sha(S/name)==hashes[name];sources.append({'file':str((S/name).relative_to(R)),'sha256':sha(S/name)})
 data={'title':'Grand Café Métano','size':list(SIZE),'source_size':[456,320],'grid_px':8,'native_scale':1,'canvas_area_ratio':round(840*576/(456*320),4),'source_repo':'Palikadude/Halcyon','source_commit':(S/'halcyon_commit.txt').read_text().strip(),'sources':sources,'recipe':{'horizontal_insert':{'at':224,'source_band':[160,224],'repeats':6},'vertical_insert':{'at':224,'source_band':[160,224],'repeats':4},'threshold_gap_repair':'Source alpha gaps inside door x264:320,y296:304 filled with unchanged adjacent native 8px floor tile x264,y296','door_repairs':[{'destination':[640,544],'source_rect':[160,288,232,320]},{'destination':[448,544],'source_rect':[256,288,328,320]}]},'layers':layers,'furniture':assets,'animations':animations,'placed_furniture':[],'placed_fire':[],'npc_entities':[],'south_entrance':{'point':[484,568],'width':56,'direction':'S','warp_created':False},'reserved_zones':[{'id':'service','title':'Comptoir / kiosques libres','rect':[136,112,576,128]},{'id':'salle','title':'Salle à aménager','rect':[80,256,672,232]}],'guides_only':True,'fixed_ornaments':'The original ribbons are integrated in the native Base wall artwork and are retained. No movable decoration has been placed.','runtime_PMDO':'NOT TESTED','visible_native_pixels':True,'limits':['New native-pixel arrangement, not a shipped Halcyon Ground.','The terrain PNG is an import/export asset, not a configured PMDO Ground.','Surface and reserved zones are authoring guides, not collision or NPC placements.','Back/side/front layers partition visible wall surfaces; they are not complete movable wall volumes.','Original fixed wall ribbons retained; all furniture, characters and fire remain separate.']}
 (O/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 page=(HERE/'viewer.html').read_text().replace('__DATA__',json.dumps(data,ensure_ascii=False))
 (O/'index.html').write_text(page);(R/'apercu_cafe_halcyon_agrandi_v1.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=renders/cafe_halcyon_agrandi_v1/index.html"><title>Café Halcyon agrandi</title><a href="renders/cafe_halcyon_agrandi_v1/index.html">Ouvrir le café Halcyon agrandi</a></html>\n')
 print('Built native cafe 840×576, 5 terrain layers, zero placed furniture/fire/NPCs.')
if __name__=='__main__':main()
