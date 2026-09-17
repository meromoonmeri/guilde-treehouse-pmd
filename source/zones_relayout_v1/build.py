"""Two layout candidates rebuilt from unchanged uploaded reference pixels.
Complete architectural modules; overlap seams only for homogeneous floor texture.
No rotation, mirror, scale, recolor, generated output pixel or runtime import.
"""
from pathlib import Path
import json,hashlib,base64,zipfile
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;O=R/'exports/zones_relayout_v1';W,H=768,360

def seam(cost):
 h,w=cost.shape;dist=cost.astype(float).copy();prev=np.zeros((h,w),int)
 for y in range(1,h):
  for x in range(w):
   lo=max(0,x-1);hi=min(w,x+2);p=lo+np.argmin(dist[y-1,lo:hi]);prev[y,x]=p;dist[y,x]+=dist[y-1,p]
 x=int(np.argmin(dist[-1]));path=[]
 for y in reversed(range(h)):path.append(x);x=prev[y,x]
 return np.array(path[::-1])
class Map:
 def __init__(self,name,file):
  self.name=name;self.file=file;self.a=np.array(Image.open(R/file).convert('RGBA'));self.layers=[];self.moves=[]
 def layer(self,label):
  a=np.zeros((H,W,4),np.uint8);xy=np.full((H,W,2),-1,np.int16);self.layers.append((label,a,xy));return a,xy
 def put(self,layer,box,pos,mask=None):
  a,xy=layer;x0,y0,x1,y1=box;x,y=pos;part=self.a[y0:y1,x0:x1];hh,ww=part.shape[:2]
  assert x>=0 and y>=0 and x+ww<=W and y+hh<=H,(box,pos)
  mask=np.ones((hh,ww),bool) if mask is None else mask
  yy,xx=np.mgrid[y0:y1,x0:x1];a[y:y+hh,x:x+ww][mask]=part[mask];xy[y:y+hh,x:x+ww][mask]=np.stack([xx,yy],2)[mask]
  self.moves.append({'layer':self.layers[-1][0],'source_rect':list(box),'destination':list(pos),'masked':not mask.all()})
 def floor(self,label,boxes,seed,start=0):
  a,xy=self.layer(label);rng=np.random.default_rng(seed);ph=boxes[0][3]-boxes[0][1];pw=boxes[0][2]-boxes[0][0];overlap=8
  for y in range(start,H,ph-overlap):
   for x in range(0,W,pw-overlap):
    hh=min(ph,H-y);ww=min(pw,W-x);best=None
    for index in rng.permutation(len(boxes)):
     x0,y0,_,_=boxes[index];patch=self.a[y0:y0+hh,x0:x0+ww];old=a[y:y+hh,x:x+ww];occupied=old[:,:,3]>0;cost=((old[:,:,:3].astype(float)-patch[:,:,:3])**2).sum(2);score=cost[occupied].mean() if occupied.any() else float(rng.random())
     if best is None or score<best[0]:best=(score,patch.copy(),x0,y0,cost)
    _,patch,x0,y0,cost=best;take=np.ones((hh,ww),bool)
    if x and ww>=overlap:
     cut=seam(cost[:,:overlap]);take[:,:overlap]=np.arange(overlap)[None,:]>=cut[:,None]
    if y>start and hh>=overlap:
     cut=seam(cost[:overlap,:].T);take[:overlap,:]&=np.arange(overlap)[:,None]>=cut[None,:]
    old=a[y:y+hh,x:x+ww];take|=old[:,:,3]==0;yy,xx=np.mgrid[y0:y0+hh,x0:x0+ww];old[take]=patch[take];xy[y:y+hh,x:x+ww][take]=np.stack([xx,yy],2)[take]
  self.moves.append({'layer':label,'operation':'native homogeneous floor patch quilting, 8px minimum-error overlap, no blending','source_rectangles':boxes,'seed':seed,'start_y':start})
 def save(self,description,limits,route):
  dest=O/self.name;dest.mkdir(parents=True,exist_ok=True);comp=Image.new('RGBA',(W,H));layers=[]
  for label,a,xy in self.layers:
   filename=f'RelayoutV1_{self.name}_{label}.png';im=Image.fromarray(a);im.save(dest/filename);comp.alpha_composite(im);np.savez_compressed(dest/f'{label}_provenance.npz',source_xy=xy)
   layers.append({'id':label,'png':filename,'provenance':f'{label}_provenance.npz','pixels':int((a[:,:,3]>0).sum())})
  comp.save(dest/'composite.png');original=Image.open(R/self.file).convert('RGBA');original.save(dest/'reference_copy.png')
  # Advisory centerline only, deliberately not rasterized as a purported collision map.
  review=comp.copy();draw=ImageDraw.Draw(review);draw.line(route,fill=(255,125,75,255),width=2)
  for p in route:draw.ellipse((p[0]-3,p[1]-3,p[0]+3,p[1]+3),fill=(255,220,120,255))
  review.save(dest/'route_review_NOT_COLLISION.png')
  return {'id':self.name,'source':self.file,'source_sha256':hashlib.sha256((R/self.file).read_bytes()).hexdigest(),'dimensions':[W,H],'description':description,'layers':layers,'operations':self.moves,'route_guide':route,'limits':limits,'art_approved':False,'runtime_PMDO':'NOT TESTED','collision':'NOT PROVIDED; route is a review guide, not verified passability.'}
def forest():
 m=Map('forest_clearing','forêtglomypmdsky.png');a=m.a
 m.floor('01_ground',[(x,y,x+48,y+24) for x in [0,24,48,72,96] for y in [144,152,160,168]],37)
 back=m.layer('02_back_canopy')
 # Two 336px-wide tree masses; 192px repeat measured in native upper woodland.
 for x in [0,192]:
  box=(0,0,336,144);p=a[:144,:336];yy,xx=np.mgrid[:144,:336];rgb=p[:,:,:3].astype(float)
  mask=(rgb[:,:,1]>rgb[:,:,2]*1.4)&((rgb[:,:,0]<170)|(yy<100))
  # Retain complete tree silhouettes and native shadows, rather than isolated leaf tiles.
  mask=nd.binary_fill_holes(mask);m.put(back,box,(x,0),mask)
 cliff=m.layer('03_cliff_entrance');box=(288,0,600,216);p=a[:216,288:600];rgb=p[:,:,:3].astype(float);mask=(rgb[:,:,0]>=rgb[:,:,1]*.97)&(rgb[:,:,2]>=rgb[:,:,1]*.56)
 labs,n=nd.label(mask);ids=np.bincount(labs.ravel());keep=ids>=12;keep[0]=False;mask=nd.binary_fill_holes(keep[labs]);m.put(cliff,box,(456,0),mask)
 path=m.layer('04_earth_patches');boxes=[(176,144,240,176),(240,160,280,192),(320,144,368,168)]
 for i,pos in enumerate([(32,192),(112,216),(192,232),(272,216),(352,192),(432,168),(512,152)]):
  box=boxes[i%3];x0,y0,x1,y1=box;p=a[y0:y1,x0:x1];rgb=p[:,:,:3].astype(float);mask=(rgb[:,:,0]>rgb[:,:,1]*1.015)&(rgb[:,:,2]>rgb[:,:,1]*.5);mask=nd.binary_dilation(nd.binary_fill_holes(mask));m.put(path,box,pos,mask)
 stones=m.layer('05_stones')
 for box,pos in [((400,184,440,208),(360,232)),((96,96,136,120),(240,160)),((400,184,440,208),(544,216))]:
  x0,y0,x1,y1=box;p=a[y0:y1,x0:x1];rgb=p[:,:,:3].astype(float);mask=(rgb[:,:,2]>rgb[:,:,1]*.65)&(rgb[:,:,0]>rgb[:,:,1]*.95);mask=nd.binary_dilation(nd.binary_fill_holes(mask));m.put(stones,box,pos,mask)
 front=m.layer('06_front_bushes');box=(0,184,240,312);p=a[184:312,:240];rgb=p[:,:,:3].astype(float);mask=(rgb[:,:,1]>rgb[:,:,0]*1.04)&(rgb[:,:,0]<168)&(rgb[:,:,2]<rgb[:,:,1]*.65);mask=nd.binary_fill_holes(mask);labs,n=nd.label(mask);bottom=np.unique(labs[-1]);mask=np.isin(labs,bottom[bottom>0])
 for x in [0,240,480,720]:
  width=min(240,W-x);m.put(front,(0,184,width,312),(x,232),mask[:,:width])
 # Native foreground clumps overlap along a stepped bank to cover the originally hidden cliff foot.
 # Whole 80px strips overlap by32px; no geometric diagonal slicing of foliage.
 bank=m.layer('07_cliff_foot_cover')
 for x,y in [(432,232),(480,232),(528,224),(576,216),(624,192),(672,184),(720,184)]:
  sx=(x-168)%240;ww=min(80,W-x);p=a[184:312,sx:sx+ww];rgb=p[:,:,:3].astype(float);mask=(rgb[:,:,1]>rgb[:,:,0]*1.04)&(rgb[:,:,0]<168)&(rgb[:,:,2]<rgb[:,:,1]*.65);mask=nd.binary_fill_holes(mask);labs,n=nd.label(mask);ids=np.unique(labs[-1]);mask=np.isin(labs,ids[ids>0]);m.put(bank,(sx,184,sx+ww,312),(x,y),mask)
 return m.save('Clairière élargie, falaise entière déplacée de168px vers l’est ; sentier de terre en courbe, pierres redistribuées et buissons avancés de48px.', 'Pas de BG de ciel. Les ombres natives restent attachées à leurs modules. Entrée et route à vérifier dans PMDO ; aucune animation d’eau ou de feuillage inventée.',[(8,208),(144,224),(232,240),(368,208),(480,176),(624,152)])
def rock():
 m=Map('blue_rock_passage','rockroadpmd.png');a=m.a
 assert np.count_nonzero(np.any(a[:,240:]!=a[:,:-240],axis=2))==1,'Expected one known right-edge mismatch in the 240px source repeat.'
 bg=m.layer('01_void');bg[0][:]=a[0,80];bg[1][:]=[80,0]
 m.floor('02_ground',[(x,208,x+24,224) for x in [0,64,136,168]],61,start=160)
 wall=m.layer('03_back_wall')
 for x in [0,240,480,720]:
  ww=min(240,W-x);p=a[:216,:ww];mask=np.any(p[:,:,:3]!=a[0,80,:3],axis=2);m.put(wall,(0,0,ww,216),(x,0),mask)
 front=m.layer('04_front_ridge');p=a[216:288,:240];rgb=p[:,:,:3].astype(float);mask=(rgb[:,:,0]<65)&(rgb[:,:,1]<110);mask=nd.binary_fill_holes(mask);labs,n=nd.label(mask);bottom=np.unique(labs[-1]);mask=np.isin(labs,bottom[bottom>0])
 for x in [0,240,480,720]:
  ww=min(240,W-x);m.put(front,(0,216,ww,288),(x,288),mask[:,:ww])
 return m.save('Passage horizontal élargi : bande de premier plan reculée de72px, modules complets de240px conservés et prolongés à768px.', 'Le guide proposait un coude ; non reproduit faute de retours de paroi natifs dans cette référence. Ne pas inventer de raccords par déformation. Sol élargi uniquement avec pixels du couloir natif ; pas de ciel ni d’eau. Grain et jonctions du sol à examiner.',[(8,248),(192,256),(384,256),(576,256),(752,248)])
def main():
 O.mkdir(parents=True,exist_ok=True);entries=[forest(),rock()];result={'maps':entries,'workflow':'Generated composition studies only; all exported visible RGB/alpha pixels copied from the unchanged uploaded references with source coordinates. Ground quilting is not applied to cliffs.','source_identity':'User-provided PMD references from9ec9a081; official scene identity/licensing not independently established.','grid_px':8,'runtime':'NOT TESTED','scope':'First two relayout candidates, not completion of all zones or global guild programme.'};(O/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
 data=[]
 for e in entries:data.append({**e,'original_uri':uri(O/e['id']/'reference_copy.png'),'composite_uri':uri(O/e['id']/'composite.png'),'route_uri':uri(O/e['id']/'route_review_NOT_COLLISION.png'),'layers':[{**l,'uri':uri(O/e['id']/l['png'])} for l in e['layers']]})
 page='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Relayouts · premiers terrains</title><style>body{background:#14231e;color:#e4e7d5;font:16px system-ui;margin:35px auto;padding:20px;max-width:1200px}p{line-height:1.6;color:#c1cbbd}article{padding:24px;background:#24382f;margin:28px 0;border-radius:12px}canvas{max-width:100%;image-rendering:pixelated;background:#403949}img{max-width:100%;image-rendering:pixelated}label{display:inline-block;margin:12px 18px 12px 0}button{padding:10px;background:#d8c17c;color:#18251d;border:0;border-radius:6px}small{color:#c6bb94}details{margin:20px 0}</style><h1>Terrains · changer le layout, conserver les pixels</h1><p>Deux premiers candidats reconstruits depuis les références originales. Aucun pixel généré, aucune recoloration, rotation, miroir ou mise à l’échelle dans les exports. Falaises et masses végétales gardées en grands modules ; seuls les sols homogènes utilisent des raccords de texture par chevauchement, sans fondu.</p><p>Les guides de composition ne sont pas les images finales. Calques activables ci-dessous ; la ligne de parcours est indicative, pas une collision validée. Aucun import PMDO revendiqué.</p><main id="maps"></main><script>const DATA=__DATA__;for(const s of DATA){const card=document.createElement('article');card.innerHTML='<h2>'+s.id.replaceAll('_',' ')+'</h2><p>'+s.description+'</p><small>768 × 360 px · grille 8 px · candidat non validé en jeu</small>';const canvas=document.createElement('canvas');canvas.width=768;canvas.height=360;card.append(canvas);const controls=document.createElement('div');card.append(controls);const ctx=canvas.getContext('2d'),imgs=[],checks=[];function draw(){ctx.clearRect(0,0,768,360);imgs.forEach((im,i)=>{if(checks[i].checked&&im.complete)ctx.drawImage(im,0,0)})}s.layers.forEach(l=>{const label=document.createElement('label'),c=document.createElement('input');c.type='checkbox';c.checked=true;c.onchange=draw;checks.push(c);label.append(c,document.createTextNode(l.id));controls.append(label);const im=new Image();imgs.push(im);im.onload=draw;im.src=l.uri});for(const [title,url] of [['Référence originale intacte',s.original_uri],['Parcours indicatif — pas une collision',s.route_uri]]){const d=document.createElement('details');d.innerHTML='<summary>'+title+'</summary><img src="'+url+'">';card.append(d)}const p=document.createElement('p');p.textContent=s.limits;card.append(p);document.getElementById('maps').append(card)}</script></html>'''
 (R/'apercu_zones_relayout_v1.html').write_text(page.replace('__DATA__',json.dumps(data,ensure_ascii=False)))
 print('2 maps, 11 layers, exact per-pixel source coordinates, gallery.')
if __name__=='__main__':main()
