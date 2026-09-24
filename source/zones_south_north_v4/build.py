"""Lot 04 — deux nouvelles entrées sud -> nord aux pixels natifs.

References: entrancearidedungeonpmdsky.png (entree aride, grotte au nord) et
roadundergound.png (grotte violette a deux issues). Memoire du programme:
V3 zones_south_north_v3 (methode approuvee) et audit zones_bg_audit_v1.
Aucun pixel genere, recoloration, rotation, miroir ou echelle: les calques
portent leurs coordonnees source (NPZ) et les sols/chemins ne sont qu'un
chevauchement de patches natifs sans melange de couleurs.
"""
from pathlib import Path
import json,hashlib,base64,xml.etree.ElementTree as ET
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=R/'exports/zones_south_north_v4'
FILES=['entrancearidedungeonpmdsky.png','roadundergound.png']
A=[np.array(Image.open(R/p).convert('RGBA')) for p in FILES]
BASELINE='3d4ea6f0'  # commit de base de la branche de session (historique linearise)

class Map:
 def __init__(self,id,W,H):self.id=id;self.W=W;self.H=H;self.layers=[];self.ops=[]
 def layer(self,name):
  l=[name,np.zeros((self.H,self.W,4),np.uint8),np.full((self.H,self.W,3),-1,np.int16)];self.layers.append(l);return l
 def fillflat(self,l,color,src):
  l[1][:]=color;l[2][:]=[src,0,0]
 def put(self,l,s,box,pos,mask=None):
  x0,y0,x1,y1=box;x,y=pos;p=A[s][y0:y1,x0:x1];hh,ww=p.shape[:2]
  mask=p[:,:,3]>0 if mask is None else mask&(p[:,:,3]>0)
  assert x>=0 and y>=0 and x+ww<=self.W and y+hh<=self.H,(box,pos)
  sy,sx=np.mgrid[y0:y1,x0:x1];q=np.stack([np.full(sx.shape,s),sx,sy],2)
  l[1][y:y+hh,x:x+ww][mask]=p[mask];l[2][y:y+hh,x:x+ww][mask]=q[mask]
  self.ops.append(dict(layer=l[0],source=s,rect=list(box),position=list(pos)))
 def fill(self,l,s,boxes,mask,seed=11):
  # Chevauchement de patches natifs, uniquement pour materiaux de sol/chemin.
  from source.zones_relayout_v1.build import seam
  rng=np.random.default_rng(seed);hh=boxes[0][3]-boxes[0][1];ww=boxes[0][2]-boxes[0][0];ov=min(8,hh//2,ww//2)
  for y in range(0,self.H,hh-ov):
   for x in range(0,self.W,ww-ov):
    h=min(hh,self.H-y);w=min(ww,self.W-x);want=mask[y:y+h,x:x+w]
    if not want.any():continue
    old=l[1][y:y+h,x:x+w];occupied=(old[:,:,3]>0)&want;best=None
    for idx in rng.permutation(len(boxes))[:24]:
     x0,y0,_,_=boxes[idx];patch=A[s][y0:y0+h,x0:x0+w]
     cost=((old[:,:,:3].astype(float)-patch[:,:,:3])**2).sum(2)
     score=cost[occupied].mean() if occupied.any() else rng.random()
     if best is None or score<best[0]:best=(score,x0,y0,patch,cost)
    _,x0,y0,patch,cost=best;take=want.copy()
    if x and w>=ov:take[:,:ov]&=np.arange(ov)[None,:]>=seam(cost[:,:ov])[:,None]
    if y and h>=ov:take[:ov,:]&=np.arange(ov)[:,None]>=seam(cost[:ov,:].T)[None,:]
    take|=want&(old[:,:,3]==0)
    sy,sx=np.mgrid[y0:y0+h,x0:x0+w];q=np.stack([np.full(sx.shape,s),sx,sy],2)
    old[take]=patch[take];l[2][y:y+h,x:x+w][take]=q[take]
  self.ops.append(dict(layer=l[0],source=s,method='native ground patch overlap, no blending',patches=len(boxes),seed=seed))
 def save(self,title,entrance,pathmask,notes,exits=None):
  d=O/self.id;d.mkdir(parents=True,exist_ok=True)
  comp=Image.new('RGBA',(self.W,self.H));ls=[]
  for name,a,q in self.layers:
   fn=f'SouthNorthV4_{self.id}_{name}.png'
   Image.fromarray(a).save(d/fn);comp.alpha_composite(Image.fromarray(a))
   np.savez_compressed(d/(name+'_source.npz'),source_sxy=q)
   root=ET.Element('tileset',version='1.10',name=Path(fn).stem,tilewidth='8',tileheight='8',columns=str(self.W//8),tilecount=str((self.W//8)*(self.H//8)))
   ET.SubElement(root,'image',source=fn,width=str(self.W),height=str(self.H))
   ET.ElementTree(root).write(d/Path(fn).with_suffix('.tsx').name,encoding='utf-8',xml_declaration=True)
   ls.append(dict(id=name,file=fn,provenance=name+'_source.npz'))
  allowed={l['file'] for l in ls}|{l['provenance'] for l in ls}|{str(Path(l['file']).with_suffix('.tsx')) for l in ls}
  for old in d.iterdir():
   if old.is_file() and (old.name.startswith('SouthNorthV4_') or old.name.endswith('_source.npz')) and old.name not in allowed:old.unlink()
  comp.save(d/'composite.png');Image.fromarray(np.uint8(pathmask)*255).save(d/'path_connectivity_mask.png')
  review=comp.copy();dr=ImageDraw.Draw(review)
  for y in range(entrance[1],self.H,8):
   if pathmask[y].any():
    xs=np.flatnonzero(pathmask[y]);dr.line([(int(xs.mean()),y-4),(int(xs.mean()),y+4)],fill=(255,90,60,255),width=2)
  dr.ellipse((entrance[0]-6,entrance[1]-6,entrance[0]+6,entrance[1]+6),outline=(255,255,0,255),width=2)
  review.save(d/'access_review_NOT_RUNTIME.png')
  out=dict(id=self.id,title=title,size=[self.W,self.H],orientation='SOUTH_TO_NORTH',entrance=entrance,
   entrance_trigger_candidate=[entrance[0]-16,entrance[1]-8,32,16],south_access=[self.W//2-32,self.H-8,64,8],
   exits=exits or [entrance],layers=ls,operations=self.ops,notes=notes,runtime='NOT TESTED',art_approved=False,
   connectivity='Pixel path mask continuity only, not engine collision or warp validation.')
  return out

def boxes_all(mask,box,wh):
 x0,y0,x1,y1=box;w,h=wh;out=[]
 for y in range(y0,y1-h+1):
  for x in range(x0,x1-w+1):
   if mask[y:y+h,x:x+w].all():out.append((x,y,x+w,y+h))
 return out

def arid():
 W,H=480,384;m=Map('arid_cave_entrance',W,H);a=A[0];rgb=a[:,:,:3].astype(float)
 sand=(rgb.sum(2)>520)&(rgb[:,:,0]>=rgb[:,:,1]-2)&(rgb[:,:,0]-rgb[:,:,2]>40)
 brown=(rgb[:,:,0]>rgb[:,:,1])&(rgb[:,:,0]-rgb[:,:,2]>35)&(rgb.sum(2)<520)
 grey=(np.abs(rgb[:,:,0]-rgb[:,:,1])<25)&(np.abs(rgb[:,:,1]-rgb[:,:,2])<25)&(rgb.sum(2)>120)&(rgb.sum(2)<460)
 rocky=brown&(rgb.sum(2)>280)&(rgb.sum(2)<560)
 soil=m.layer('01_sand_ground')
 sboxes=boxes_all(sand,(0,216,408,280),(24,16));assert sboxes,'aucun patch de sol'
 m.fill(soil,0,sboxes,np.mgrid[0:H,0:W][0]>=88,12)
 pathm=np.mgrid[0:H,0:W][0]>=104
 yy,xx=np.mgrid[0:H,0:W]
 middle=np.interp(yy,[104,384],[240,240]);jitter=((yy//8)%5-2)
 pm=(np.abs(xx-middle)<=36+jitter)&pathm
 path=m.layer('02_sand_path')
 pboxes=boxes_all(sand,(180,124,280,200),(24,16));assert pboxes,'aucun patch de chemin'
 m.fill(path,0,pboxes,pm,19)
 wall=m.layer('03_north_wall')
 m.put(wall,0,(0,0,166,112),(0,0));m.put(wall,0,(246,0,408,112),(166,0));m.put(wall,0,(246,0,408,112),(318,0))
 feet=m.layer('04_wall_feet')
 b_w=(np.mgrid[0:288,0:408][1]>=48)&(np.mgrid[0:288,0:408][1]<=112)&(np.mgrid[0:288,0:408][0]>=158)&(np.mgrid[0:288,0:408][0]<=212)
 b_e=(np.mgrid[0:288,0:408][1]>=344)&(np.mgrid[0:288,0:408][1]<=406)&(np.mgrid[0:288,0:408][0]>=160)&(np.mgrid[0:288,0:408][0]<=216)
 fmask=(brown&~b_w&~b_e)
 m.put(feet,0,(0,88,166,196),(0,88),fmask[88:196,0:166])
 m.put(feet,0,(246,88,408,196),(166,88),fmask[88:196,246:408])
 m.put(feet,0,(246,88,408,196),(318,88),fmask[88:196,246:408])
 cave=m.layer('05_cave_entrance');m.put(cave,0,(166,18,246,100),(200,8))
 trees=m.layer('06_dead_trees')
 m.put(trees,0,(0,140,110,224),(0,140),grey[140:224,0:110])
 m.put(trees,0,(318,140,408,224),(318,140),grey[140:224,318:408])
 m.put(trees,0,(124,116,172,172),(124,118),grey[116:172,124:172])
 m.put(trees,0,(266,124,312,176),(266,126),grey[124:176,266:312])
 rocks=m.layer('07_rocks')
 def rockcomp(box):
  x0,y0,x1,y1=box;p=rocky[y0:y1,x0:x1];lab,n=nd.label(p)
  if n==0:raise AssertionError('no rock component in '+str(box))
  sizes=np.bincount(lab.ravel());best=int(np.argmax(sizes[1:]))+1
  return (x0,y0,x1,y1),nd.binary_fill_holes(lab==best)
 # Les deux gros rochers restent a leur emplacement natif (translation nulle) ;
 # une petite pierre est repositionnee sur le sable, plus loin du chemin.
 box,mask=rockcomp((48,158,112,212));m.put(rocks,0,box,(48,158),mask)
 box,mask=rockcomp((344,160,406,216));m.put(rocks,0,box,(344,160),mask)
 box,mask=rockcomp((70,204,100,224));m.put(rocks,0,box,(360,240),mask)
 pebbles=m.layer('08_pebbles')
 darkdots=(rgb.sum(2)<380)
 for srcbox,pos in [((41,266,47,270),(64,224)),((185,226,191,230),(160,286)),((297,242,303,246),(336,258)),
                    ((133,265,140,271),(232,318)),((324,233,332,239),(384,300))]:
  x0,y0,x1,y1=srcbox;m.put(pebbles,0,srcbox,pos,darkdots[y0:y1,x0:x1])
 access=pm.copy();access[96:104,216:264]=True
 return m.save('Entree aride — sud vers la bouche de grotte au nord',[240,104],access,
  'Sol, chemin, falaise et pied de falaise de la reference, bouche de grotte native deplacee au centre (source166,18,246,112). Arbres morts, rochers et cailloux translates sans miroir; les deux gros rochers quittent leur emplace d origine (trous combles par le sol natif) et sont reposes de part et d autre du chemin. Aucun pixel genere ni recolore.',
  exits=[[240,104]])

def purple():
 W,H=424,360;m=Map('purple_two_exit_cave',W,H);b=A[1];rgb=b[:,:,:3].astype(float)
 # Panel : translation pure de source (40,96,464,404) a canvas (0,52), decalage y-44.
 PX0,PY0,PX1,PY1=40,96,464,404
 F=(rgb[:,:,2]>rgb[:,:,0])&(rgb.sum(2)>=460)
 D=(rgb.sum(2)<430)&(rgb[:,:,2]>=rgb[:,:,0])
 panel=np.zeros(rgb.shape[:2],bool);panel[PY0:PY1,PX0:PX1]=True
 floor_mask=(F|D)&panel
 west_mask=(~(F|D))&panel&(np.mgrid[0:408,0:504][1]<180)
 east_mask=(~(F|D))&panel&(np.mgrid[0:408,0:504][1]>=324)
 cent_mask=(~(F|D))&panel&(np.mgrid[0:408,0:504][1]>=180)&(np.mgrid[0:408,0:504][1]<330)&(np.mgrid[0:408,0:504][0]>=PY0)&(np.mgrid[0:408,0:504][0]<170)
 assert (floor_mask|west_mask|east_mask|cent_mask)[PY0:PY1,PX0:PX1].all(),'partition du panneau incomplete'
 back=m.layer('00_dark_backdrop');m.fillflat(back,(47,55,55,255),1)
 floor=m.layer('01_cave_floor');m.put(floor,1,(PX0,PY0,PX1,PY1),(0,52),floor_mask[PY0:PY1,PX0:PX1])
 west=m.layer('02_west_boulders');m.put(west,1,(PX0,PY0,PX1,PY1),(0,52),west_mask[PY0:PY1,PX0:PX1])
 east=m.layer('03_east_boulders');m.put(east,1,(PX0,PY0,PX1,PY1),(0,52),east_mask[PY0:PY1,PX0:PX1])
 north=m.layer('04_north_boulders')
 # Seuls les blocs de roche du centre (source204..296) sont retiles : les
 # modules de coin contenaient des pixels de marge sombre, visibles en haut.
 for srcbox,pos in [((204,44,296,96),(0,0)),((204,44,296,96),(92,0)),((204,44,296,96),(184,0)),
                    ((204,44,296,96),(276,0)),((204,44,260,96),(368,0))]:
  m.put(north,1,srcbox,pos)
 m.put(north,1,(180,96,330,170),(180,52),cent_mask[96:170,180:330])
 exitw=m.layer('05_exit_west');m.put(exitw,1,(96,44,208,168),(36,0))
 exite=m.layer('06_exit_east');m.put(exite,1,(296,44,408,168),(276,0))
 crys=m.layer('07_crystal_stars')
 reg=D.copy();reg[:, :180]=False;reg[:, 330:]=False;reg[:170]=False
 lab,n=nd.label(reg);sizes=np.bincount(lab.ravel());sizes[0]=0
 comps=[]
 for i in np.where((sizes>=8)&(sizes<=120))[0]:
  ys,xs=np.where(lab==i);comps.append((ys.min(),xs.min(),i))
 comps=sorted(comps)[:10];assert len(comps)>=6,'stars insuffisantes'
 for k,(cy,cx,i) in enumerate(comps):
  ys,xs=np.where(lab==i);x0,y0,x1,y1=int(xs.min())-1,int(ys.min())-1,int(xs.max())+2,int(ys.max())+2
  box=(max(x0,PX0),max(y0,170),min(x1,PX1),min(y1,PY1));mask=(lab==i)
  m.put(crys,1,box,(95+(k%5)*34,140+(k//5)*88+(k*13)%17),mask[box[1]:box[3],box[0]:box[2]])
 floorc=(floor_mask|west_mask|east_mask|cent_mask)
 pm=np.zeros((H,W),bool);pm[52:, :]=floorc[PY0:PY1,PX0:PX1]
 pm[96:128,150:274]=True  # seuil entre les deux bouches, comme le portail natif de V3
 assert nd.label(pm)[1]==1,'masque de chemin non connexe'
 return m.save('Grotte violette — deux issues reimplantees au nord, arrivee au sud',[212,110],pm,
  'Chambre du panneau natif droit de la reference, translatee telle quelle (materiaux violets, sol mouchetee, gros cristal du bas gauche conserve sur place). Bande nord reassembledes blocs de roche natifs (aucun miroir) ; les deux bouches sombres et leurs seuils de pierres sont deplaces de source(96..208) a canvas36 et de source(296..408) a canvas276. Grappes de cristaux sombres reimplantees en dix poses. Seuil de marche entre les issues signale, sans pretendre a une collision moteur.',
  exits=[[92,60],[332,60]])

def main():
 O.mkdir(parents=True,exist_ok=True)
 entries=[arid(),purple()]
 sources=[dict(id=i,file=f,sha256=hashlib.sha256((R/f).read_bytes()).hexdigest()) for i,f in enumerate(FILES)]
 manifest=dict(maps=entries,sources=sources,grid=8,baseline_commit=BASELINE,
  status='Lot 04 du programme sud-nord: deux nouvelles entrees aux pixels natifs (entree aride, grotte violette a deux issues). Les lots V1/V2/V3 restent historiques; aucune de leurs cartes n est modifiee.')
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
 data=[{**m,'layers':[{**l,'uri':uri(O/m['id']/l['file'])} for l in m['layers']],'route':uri(O/m['id']/'access_review_NOT_RUNTIME.png')} for m in entries]
 page='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Lot 04 · entrées sud → nord</title><style>body{background:#14251f;color:#e3e8d8;font:16px system-ui;max-width:1250px;margin:32px auto;padding:20px}p{line-height:1.6;color:#c7d1bf}.maps{display:flex;flex-wrap:wrap;gap:24px}article{background:#24382e;border:1px solid #4d6249;border-radius:12px;padding:18px;width:560px;box-sizing:border-box}canvas,img{max-width:100%;image-rendering:pixelated}canvas{background:#454047}label{display:inline-block;margin:8px;font-size:13px}h2{font-size:23px}small{color:#edcf83}details{margin:18px 0}</style><h1>Lot 04 · vraies entrées sud → nord</h1><p>Deux nouvelles references du programme passees a la methode approuvee (V3) : l'entree aride et la grotte violette a deux issues. Chaque pixel visible est preleve a l'identique des sources natives (coordonnees dans les NPZ) ; sols et chemins par chevauchement de patches, parois et decorations par translation de modules. Les bouches de grotte sont deplacees ; aucun pixel genere, recolore, miroire ni mis a l'echelle.</p><div class="maps" id="maps"></div><script>const data=DATA;for(const s of data){const a=document.createElement('article');a.innerHTML='<h2>'+s.title+'</h2><small>NORD · GROTTE ↑<br>'+s.size.join(' × ')+' px · SUD : arrivee au bas de l'image</small>';const c=document.createElement('canvas');c.width=s.size[0];c.height=s.size[1];a.append(c);const controls=document.createElement('div');a.append(controls);const ctx=c.getContext('2d'),imgs=[],checks=[];function draw(){ctx.clearRect(0,0,c.width,c.height);imgs.forEach((im,i)=>{if(checks[i].checked&&im.complete)ctx.drawImage(im,0,0)})}s.layers.forEach(l=>{const label=document.createElement('label'),ch=document.createElement('input');ch.type='checkbox';ch.checked=true;ch.onchange=draw;checks.push(ch);label.append(ch,document.createTextNode(l.id));controls.append(label);const im=new Image();imgs.push(im);im.onload=draw;im.src=l.uri});const d=document.createElement('details');d.innerHTML='<summary>Vérifier le trajet — pas une collision moteur</summary><img src="'+s.route+'">';a.append(d);const p=document.createElement('p');p.textContent=s.notes;a.append(p);document.getElementById('maps').append(a)}</script></html>''';
 (R/'apercu_entrees_sud_nord_v4.html').write_text(page.replace('const data=DATA;','const data='+json.dumps(data,ensure_ascii=False)+';'))
 print('2 south-to-north entrances of lot 04 built.')
if __name__=='__main__':main()
