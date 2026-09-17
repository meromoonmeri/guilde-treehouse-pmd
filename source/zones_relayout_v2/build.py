"""Ice arena relayout and two layered native BGs. Static candidates, not engine imports."""
from pathlib import Path
import json,hashlib,base64,sys,zipfile,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;O=R/'exports/zones_relayout_v2'
class Asset:
 def __init__(self,id,file,size):
  self.id=id;self.file=file;self.native=np.array(Image.open(R/file).convert('RGBA'));self.w,self.h=size;self.layers=[];self.operations=[]
 def layer(self,name):
  layer=[name,np.zeros((self.h,self.w,4),np.uint8),np.full((self.h,self.w,2),-1,np.int16)];self.layers.append(layer);return layer
 def put(self,l,box,pos,mask=None):
  _,a,xy=l;x0,y0,x1,y1=box;x,y=pos;p=self.native[y0:y1,x0:x1];h,w=p.shape[:2];assert 0<=x and 0<=y and x+w<=self.w and y+h<=self.h
  use=np.ones((h,w),bool) if mask is None else mask;yy,xx=np.mgrid[y0:y1,x0:x1];a[y:y+h,x:x+w][use]=p[use];xy[y:y+h,x:x+w][use]=np.stack([xx,yy],2)[use];self.operations.append({'layer':l[0],'source_rect':box,'position':pos,'mask':mask is not None})
 def sampled(self,l,xy,mask=None):
  valid=(xy[:,:,0]>=0) if mask is None else mask;p=xy[valid];l[1][valid]=self.native[p[:,1],p[:,0]];l[2][valid]=p
 def save(self,title,kind,limits,extra=None):
  d=O/self.id;d.mkdir(parents=True,exist_ok=True);composite=Image.new('RGBA',(self.w,self.h));records=[]
  for name,a,xy in self.layers:
   namefile=f'ZonesV2_{self.id}_{name}.png';im=Image.fromarray(a);im.save(d/namefile);composite.alpha_composite(im);np.savez_compressed(d/(name+'_source.npz'),source_xy=xy)
   tile=ET.Element('tileset',version='1.10',name=Path(namefile).stem,tilewidth='8',tileheight='8',tilecount=str(self.w//8*(self.h//8)),columns=str(self.w//8));ET.SubElement(tile,'image',source=namefile,width=str(self.w),height=str(self.h));ET.ElementTree(tile).write(d/(Path(namefile).stem+'.tsx'),encoding='utf-8',xml_declaration=True)
   records.append({'id':name,'file':namefile,'provenance':name+'_source.npz'})
  composite.save(d/'composite.png');Image.open(R/self.file).save(d/'reference.png')
  return dict(id=self.id,title=title,kind=kind,source=self.file,sha256=hashlib.sha256((R/self.file).read_bytes()).hexdigest(),size=[self.w,self.h],layers=records,operations=self.operations,limits=limits,art_approved=False,runtime='NOT TESTED',animation='NONE: static layers only',**(extra or {}))
def ice():
 b=Asset('ice_arena','pmdskyicearena.png',(768,480));a=b.native;sky=b.layer('01_sky');xy=np.zeros((480,768,2),np.int16);b.sampled(sky,xy)
 floor=b.layer('02_snow_floor');xy[:]=[100,248];mask=np.indices((480,768))[0]>=200;b.sampled(floor,xy,mask)
 # Whole native width192 wall module. No sorting or warping of ice fragments.
 # Distant blue needles and main wall are a visible partition, not reconstructed hidden relief.
 distant=b.layer('03_distant_needles');wall=b.layer('04_back_ice_wall')
 for x in range(0,768,192):
  p=a[:256,:192];rgb=p[:,:,:3];yy=np.indices(p.shape[:2])[0];allmask=np.any(rgb!=a[0,0,:3],axis=2)&np.any(rgb!=a[248,100,:3],axis=2)
  eligible=allmask&(yy<104)&(rgb[:,:,0]>=103)&(rgb[:,:,0]<=175)&(rgb[:,:,1]>=159)&(rgb[:,:,1]<=207)&(rgb[:,:,2]>=215)
  components,_=nd.label(eligible);seed=np.all(rgb==[111,159,231],axis=2)&(yy<48);ids=np.unique(components[seed]);far=np.isin(components,ids[ids>0])
  b.put(distant,(0,0,192,256),(x,0),far);b.put(wall,(0,0,192,256),(x,0),allmask&~far)
 foreground=b.layer('05_front_ice_ridge')
 for x in range(0,768,192):
  p=a[272:408,:192];mask=np.any(p[:,:,:3]!=a[248,100,:3],axis=2);b.put(foreground,(0,272,192,408),(x,344),mask)
 # Keep complete native ground fissure groups rather than draw new cracks.
 marks=b.layer('06_approach_fissures')
 for box,pos in [((0,272,80,296),(64,296)),((112,224,168,256),(576,264))]:
  x0,y0,x1,y1=box;p=a[y0:y1,x0:x1];mask=np.any(p[:,:,:3]!=a[248,100,:3],axis=2);b.put(marks,box,pos,mask)
 return b.save('Arène de glace élargie','terrain_relayout','La neige lisse est un aplat réellement présent dans la source, pas une nouvelle texture. Fond cyan et aiguilles lointaines séparés. Les aiguilles cachées par la paroi ne sont pas reconstruites : ne pas déplacer ces deux reliefs indépendamment sans compléter les occultations. Pas de collisions ni accès moteur.',{'route_guide':[[8,288],[208,296],[384,304],[576,296],[752,288]],'layout':'Paroi native conservée à sa hauteur ; premier plan reculé de72px et terrain prolongé à768px. Petits groupes de fissures repositionnés.'})
def full_xy(h,w):
 yy,xx=np.mgrid[:h,:w];return np.stack([xx,yy],2).astype(np.int16)
def nearest_clean(native,removed,allowed):
 valid=allowed&~removed;assert valid.any();_,indices=nd.distance_transform_edt(~valid,return_indices=True);xy=full_xy(*allowed.shape);xy[removed]=np.stack([indices[1],indices[0]],2)[removed];return xy

def night():
 b=Asset('night_sea','bgnightbackgroundpmdskyda.png',(456,240));a=b.native;h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w]
 moon=(xx-152)**2+(yy-52)**2<=33**2
 # Reef silhouette: full native rock pixels, including detached stacks, not a rectangular background crop.
 region=Image.new('L',(w,h));d=ImageDraw.Draw(region);d.polygon([(304,120),(304,113),(323,110),(342,110),(356,110),(369,111),(376,104),(387,107),(397,113),(423,113),(443,115),(455,116),(455,215),(296,215),(296,132)],fill=255)
 sea_row=np.repeat(a[:,8:9,:3],w,1);reef=(np.array(region)>0)&np.any(a[:,:,:3]!=sea_row,axis=2)
 c=(a[:,:,0]>30)&(a[:,:,1]>45)&(a[:,:,2]>80)&(yy<132)&~moon&~reef;labels,n=nd.label(c);counts=np.bincount(labels.ravel());large=np.isin(labels,np.flatnonzero(counts>500));large[labels==0]=False
 clouds=nd.binary_dilation(nd.binary_fill_holes(large))&(yy<132)&~moon&~reef
 stars=nd.binary_dilation(c&~large&(yy<100))&~clouds&~moon&~reef
 upper_ids=[i for i in range(1,n+1) if counts[i]>500 and np.where(labels==i)[0].min()<80];upper=nd.binary_dilation(nd.binary_fill_holes(np.isin(labels,upper_ids)))&clouds;horizon=clouds&~upper
 # The sky behind the upper clouds is a native radial halo, not arbitrary nearest-edge cloud colors.
 cloud_boxes=((xx<128)&(yy>=48)&(yy<96))|((xx>=176)&(xx<316)&(yy>=16)&(yy<88))
 removed=clouds|stars|moon|reef|cloud_boxes;skyxy=nearest_clean(a,removed,yy<132)
 radius=np.sqrt((xx-152)**2+(yy-52)**2);safe=(yy<19)&~stars&(a[:,:,0]<48)&(a[:,:,1]<64)&(a[:,:,2]<176)
 sy,sx=np.where(safe);radii=radius[sy,sx];order=np.argsort(radii);radii=radii[order];sx=sx[order];sy=sy[order]
 target=cloud_boxes&~moon;indices=np.searchsorted(radii,radius[target]);indices=np.clip(indices,0,len(radii)-1);skyxy[target]=np.stack([sx[indices],sy[indices]],1)
 sky=b.layer('01_sky_with_native_glow');b.sampled(sky,skyxy,yy<132)
 st=b.layer('02_stars');b.put(st,(0,0,w,h),(0,0),stars)
 ml=b.layer('03_moon');b.put(ml,(0,0,w,h),(0,0),moon)
 # Split upper clouds into independently translated full native silhouettes; retain horizon at original height.
 up=b.layer('04_upper_clouds');left=upper&(xx<160);right=upper&(xx>=160)
 b.put(up,(0,48,128,96),(16,40),left[48:96,:128]);b.put(up,(176,16,328,88),(240,24),right[16:88,176:328])
 # Horizon is the separate connected native cloud bank, not the low tails of upper clouds.
 hz=b.layer('05_horizon_clouds');b.put(hz,(0,0,w,h),(0,0),horizon)
 sea=b.layer('06_sea');reflection=(yy>=128)&(xx>=104)&(xx<208)&np.any(a[:,:,:3]!=sea_row,axis=2)
 xy=full_xy(h,w);clean=reef|reflection;xy[clean,0]=8;b.sampled(sea,xy,yy>=132)
 rf=b.layer('07_moon_reflection');b.put(rf,(0,0,w,h),(0,0),reflection)
 coast=b.layer('08_reef');b.put(coast,(296,104,456,216),(296,104),reef[104:216,296:456])
 return b.save('Mer nocturne — nuages redisposés','BG_relayout','La lune garde son diamètre64px et sa position native, liée au halo du ciel et à son reflet. Nuages hauts déplacés ; horizon et récif conservés. Les zones découvertes du ciel sont réparées par prélèvement de couleurs du halo natif à rayon correspondant : ce ne sont pas des pixels cachés authentifiés. La découpe nuages/horizon reste à examiner avant animation. Aucun sol praticable.',{'sky_repair':'Native halo samples from clear top rows, matched by radius behind upper clouds. Other covered sky pixels use nearest clean native donors. No interpolation or generated colors.','layout':'Nuage gauche +16,-8 ; nuage haut droit +64,+8 ; récif, lune et reflet inchangés.'})
def aurora():
 b=Asset('aurora','aurorepmdsky.png',(264,216));a=b.native;h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w]
 # Native ice foreground occupies the lower perimeter. Retain its original placement.
 polys=[[(0,151),(21,144),(19,158),(0,190)],[(0,183),(54,163),(61,171),(35,216),(0,216)],[(32,216),(66,181),(75,177),(82,194),(81,216)],[(77,216),(92,190),(100,190),(104,216)],[(103,216),(116,192),(121,207),(122,216)],[(160,216),(169,190),(173,191),(183,216)],[(179,216),(183,176),(190,178),(201,216)],[(201,216),(211,174),(218,173),(233,216)],[(223,216),(235,169),(246,177),(264,208),(264,216)],[(247,172),(248,137),(254,137),(264,150),(264,200)]]
 pm=Image.new('L',(w,h));d=ImageDraw.Draw(pm)
 for p in polys:d.polygon(p,fill=255)
 # Includes native dark outlines, not just the bright cyan crystal interiors.
 ice=(np.array(pm)>0);different=np.any(a[:,:,:3]!=a[0,0,:3],axis=2);labels,n=nd.label(different&~ice&(yy<150));counts=np.bincount(labels.ravel());stars=np.isin(labels,np.flatnonzero((counts>0)&(counts<=16)));stars[labels==0]=False
 sky=b.layer('01_dark_sky');xy=np.zeros((h,w,2),np.int16);b.sampled(sky,xy)
 st=b.layer('02_stars');b.put(st,(0,0,w,h),(0,0),stars)
 lights=b.layer('03_aurora_ribbons');b.put(lights,(0,0,w,h),(0,0),different&~stars&~ice&(yy<152))
 haze=b.layer('04_distant_haze');b.put(haze,(0,0,w,h),(0,0),different&~stars&~ice&(yy>=152))
 fg=b.layer('05_ice_foreground');b.put(fg,(0,0,w,h),(0,0),ice)
 return b.save('Aurore — préparation en cinq calques','BG_layer_preparation','Composition native conservée, pas un relayout annoncé terminé. Répartition visible en ciel, étoiles, aurore, brume lointaine et glace. Les pointes sont découpées par masques tracés contre la référence ; la brume cachée derrière elles n’est pas reconstruite. Aucune phase animée inventée et aucun terrain praticable.',{'layout':'Unchanged native composition; layered preparation only.'})
def main():
 O.mkdir(parents=True,exist_ok=True);assets=[ice(),night(),aurora()];manifest={'assets':assets,'grid':8,'scope':'One additional terrain relayout, one BG layout candidate, one native-composition BG layer preparation. Not three playable maps.','credits':'User references from commit9ec9a081, originally PMD artwork; scene identity and redistribution rights not independently verified. Original files untouched.','runtime':'NOT TESTED'};(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
 data=[]
 for e in assets:data.append({**e,'ref':uri(O/e['id']/'reference.png'),'layers':[{**l,'uri':uri(O/e['id']/l['file'])} for l in e['layers']]})
 page='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Lot glacé et panoramas</title><style>body{font:16px system-ui;background:#13232e;color:#e6e9e8;margin:36px auto;padding:20px;max-width:1200px}p{line-height:1.6;color:#c3d2d9}article{background:#213844;border:1px solid #385363;padding:24px;margin:24px 0;border-radius:12px}canvas,img{image-rendering:pixelated;max-width:100%}canvas{background:#494453}label{display:inline-block;margin:12px 16px 10px 0}small{color:#c9dca5}details{margin:20px 0}</style><h1>Glace & panoramas · lot 02</h1><p>Une arène réagencée, une proposition de mer nocturne et une préparation de BG d’aurore. Pixels issus des références, jamais des guides générés. Images fixes uniquement ; pas de collisions ni de test PMDO.</p><main id="cards"></main><script>const data=__DATA__;for(const s of data){const a=document.createElement('article');a.innerHTML='<h2>'+s.title+'</h2><small>'+s.kind+' · '+s.size.join(' × ')+' px</small><p>'+s.layout+'</p>';const c=document.createElement('canvas');c.width=s.size[0];c.height=s.size[1];c.style.width=Math.min(1000,c.width*2)+'px';a.append(c);const inputs=[],imgs=[],ctx=c.getContext('2d');function draw(){ctx.clearRect(0,0,c.width,c.height);imgs.forEach((im,i)=>{if(inputs[i].checked&&im.complete)ctx.drawImage(im,0,0)})}const controls=document.createElement('div');a.append(controls);s.layers.forEach(l=>{const label=document.createElement('label'),ch=document.createElement('input');ch.type='checkbox';ch.checked=true;ch.onchange=draw;inputs.push(ch);label.append(ch,document.createTextNode(l.id));controls.append(label);const im=new Image();imgs.push(im);im.onload=draw;im.src=l.uri});const d=document.createElement('details');d.innerHTML='<summary>Référence originale</summary><img src="'+s.ref+'">';a.append(d);const p=document.createElement('p');p.textContent=s.limits;a.append(p);document.getElementById('cards').append(a)}</script></html>''';(R/'apercu_zones_relayout_v2.html').write_text(page.replace('__DATA__',json.dumps(data,ensure_ascii=False)));print('3 assets,19layers; only one additional terrain map.')
if __name__=='__main__':main()
