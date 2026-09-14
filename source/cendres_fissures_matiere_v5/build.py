"""Rock fissures and regenerated eruptions with material sampled from the live magma."""
from pathlib import Path
import sys,json,io,zipfile,base64,heapq,shutil,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];V4=R/'renders/cendres_palette_raccord_v4';SRC=V4/'cendres_palette_raccord';O=R/'renders/cendres_fissures_matiere_v5';P=O/'cendres_fissures_matiere';P.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
M=json.loads((V4/'manifest.json').read_text());PAL=json.loads((V4/'PALETTES_064.json').read_text());HEAT=np.array(PAL['master_heat_rgb'],dtype='uint8');W,H=M['size'];N=M['frames'];DT=M['frame_ms'];NN=Image.Resampling.NEAREST

def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def compose(ls):
 c=Image.new('RGBA',(W,H))
 for _,im in ls:c.alpha_composite(im.convert('RGBA'))
 return c
def rgba(rgb,alpha):
 a=np.zeros((H,W,4),dtype='uint8');a[:,:,:3]=rgb;a[:,:,3]=alpha;a[a[:,:,3]==0]=0;return Image.fromarray(a)
static=[(n,load(SRC/f'grotte_v4_{n}.png')) for n in M['static_layers']]
terrain=compose([(n,im) for n,im in static if n!='03a_contact_refroidi']);solid=np.array(terrain)[:,:,3]>0
walk=np.array(Image.open(V4/'masque_approche_grotte.png'))>0;protected=nd.binary_dilation(walk,iterations=10)
cave=np.array(dict(static)['06_profondeur_grotte'])[:,:,3]>0
# Branching fissures originate at the lava/rock contact and stay on walls and approach margins.
paths=[
 [(30,194),(47,157),(27,134),(42,110),(36,85)],[(47,157),(71,151),(82,127),(102,121)],[(42,110),(61,95),(57,75)],
 [(146,270),(136,218),(154,196),(141,177),(162,151),(148,126),(172,104)],[(141,177),(113,166),(119,144)],[(162,151),(183,138),(178,120)],
 [(375,242),(393,205),(382,179),(406,158),(400,127),(369,114),(365,90)],[(393,205),(425,210),(441,194),(470,198)],[(406,158),(433,147),(444,121),(460,110)],
 [(598,245),(590,211),(610,192),(602,166),(622,141)],[(610,192),(573,179),(562,158)],
 [(266,449),(282,437),(279,421),(298,412)],[(282,437),(295,447),(302,465)],
 [(485,348),(453,356),(445,337),(430,329)],[(453,356),(441,373),(451,390)]
]
mask=Image.new('L',(W,H));d=ImageDraw.Draw(mask)
rng=np.random.default_rng(512)
for j,pts in enumerate(paths):
 # Broken, uneven rock edges rather than ruler-straight glowing wires.
 for seg,(a,b) in enumerate(zip(pts,pts[1:])):
  a=np.array(a,float);b=np.array(b,float);delta=b-a;length=np.linalg.norm(delta);normal=np.array([-delta[1],delta[0]])/length
  samples=[];count=max(3,round(length/4))
  for z,t in enumerate(np.linspace(0,1,count)):
   offset=0 if z in [0,count-1] else rng.uniform(-2.2,2.2)
   q=np.rint(a+t*delta+normal*offset).astype(int);samples.append(tuple(q))
  for z,(a,b) in enumerate(zip(samples,samples[1:])):
   width=int(rng.choice([4,5,6])) if j in [0,3,6,9] else int(rng.choice([2,3]))
   if seg==len(pts)-2:width=max(1,width-1)
   d.line([a,b],fill=255,width=width)
cracks=(np.array(mask)>0)&solid&~protected&~cave
labels,num=nd.label(cracks,np.ones((3,3)));shore,nearest=nd.distance_transform_edt(solid,return_indices=True);keep=[];roots=[]
for lab in range(1,num+1):
 ys,xs=np.where(labels==lab)
 if len(xs)<18 or np.min(shore[ys,xs])>3:continue
 j=int(np.argmin(shore[ys,xs]));ry,rx=int(ys[j]),int(xs[j]);keep.append(lab);roots.append({'label':lab,'rock_anchor':[rx,ry],'lava_anchor':[int(nearest[1,ry,rx]),int(nearest[0,ry,rx])]})
cracks=np.isin(labels,keep);assert len(roots)>=4;assert not np.any(cracks&protected)
# Travel through the crack branches, from their molten roots; this sets the palette phase along each vein.
parent_indices=np.array(Image.open(V4/'MAGMA_INDICES_FIXES.png'));phase=np.zeros((H,W),int);travel=np.full((H,W),np.inf)
for root in roots:
 rx,ry=root['rock_anchor'];lx,ly=root['lava_anchor'];lab=root['label'];queue=[(0.,ry,rx)];travel[ry,rx]=0
 while queue:
  cost,y,x=heapq.heappop(queue)
  if cost!=travel[y,x]:continue
  phase[y,x]=(int(parent_indices[ly,lx])%16+round(cost/6))%16
  for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
   ny,nx=y+dy,x+dx
   if not(0<=ny<H and 0<=nx<W) or labels[ny,nx]!=lab:continue
   val=cost+(1.414 if dx and dy else 1)
   if val<travel[ny,nx]:travel[ny,nx]=val;heapq.heappush(queue,(val,ny,nx))
depth=nd.distance_transform_edt(cracks)
classes=np.clip(parent_indices.astype(int)//16+1+np.where(depth>=2,1,-1),5,13);fissure_indices=(classes*16+phase).astype('uint8')
Image.fromarray(cracks.astype('uint8')*255).save(O/'MASQUE_FISSURES.png');Image.fromarray(fissure_indices).save(O/'INDICES_FISSURES.png');Image.fromarray((protected*255).astype('uint8')).save(O/'CORRIDOR_PROTEGE.png')
groove=nd.binary_dilation(cracks,iterations=1)&solid&~protected&~cave
static.append(('08_gorges_fissures',rgba([24,14,17],(groove*225).astype('uint8'))))
for n,im in static:im.save(P/f'grotte_v5_{n}.png')
# New 8-pose generation: domes, rupture and textured liquid jets rather than old flat flame symbols.
sheet=key(load(O/'bruts/eruption_matiere_huit_poses.png'));sprites=[]
for k in range(8):
 # The generated tall lower-row jet enters the mathematical upper half: split in the actual empty gutter.
 x=k%4*sheet.width//4;cut=round(sheet.height*.38);y=0 if k<4 else cut;bottom=cut if k<4 else sheet.height
 im=sheet.crop((x,y,(k%4+1)*sheet.width//4,bottom));im=im.crop(im.getbbox());im=im.resize((max(1,round(im.width*.18)),max(1,round(im.height*.18))),NN);sprites.append(im);im.save(O/f'pose_generee_{k:02}.png')
stages=M['event_stages'];vents=M['vents']
def state(local):
 for stage,(lo,hi) in enumerate([(0,4),(4,8),(8,12),(12,14),(14,18),(18,24),(24,29),(29,35)]):
  if lo<=local<hi:return stage,(local-lo)/(hi-lo)
 return None,0
codes=(HEAT[:,0].astype(int)<<16)+(HEAT[:,1].astype(int)<<8)+HEAT[:,2];order=np.argsort(codes);sorted_codes=codes[order]
def heatmap(im):
 a=np.array(im);c=(a[:,:,0].astype(int)<<16)+(a[:,:,1].astype(int)<<8)+a[:,:,2];return order[np.searchsorted(sorted_codes,c)]
def material_pose(pose,stage,u,x,y,scale,field):
 stretch=1+.035*np.sin(2*np.pi*u) if stage in [4,5,6] else 1
 im=pose.resize((round(pose.width*scale),round(pose.height*scale*stretch)),NN);alpha=np.array(im)[:,:,3];h,w=alpha.shape;v,uu=np.mgrid[:h,:w];rise=h-1-v;z=rise/max(h-1,1)
 # Exact ground coordinates at the foot; the raised surface stretches the very same live texture.
 sx=x+(uu-w//2)*(1-.12*np.sin(np.pi*z));sy=y-rise*(.48 if stage<=3 else .32)
 sx=np.clip(np.rint(sx).astype(int),0,W-1);sy=np.clip(np.rint(sy).astype(int),0,H-1)
 material=field[sy,sx].astype(int)
 if stage<=2:
  lateral=(uu-w/2)/max(w/2,1)
  lift=((1.5-2.5*lateral)*np.sin(np.pi*z)+.7*z)*np.clip(rise/4,0,1)
 elif stage in [3,4,5]:lift=(1+z)*np.clip(rise/5,0,1)
 elif stage==6:lift=(1-u)*np.clip(rise/5,0,1)
 else:lift=np.zeros_like(z)
 mapped=np.clip(material+np.rint(lift).astype(int),0,15)
 # Bottom row has no color offset or UV drift: it matches the magma below pixel-for-pixel.
 assert np.all(mapped[-1]==field[y,np.clip(x+np.arange(w)-w//2,0,W-1)])
 a=np.zeros((h,w,4),dtype='uint8');a[:,:,:3]=HEAT[mapped];a[:,:,3]=alpha
 if stage==7:a[:,:,3]=np.rint(alpha*(1-u)).astype('uint8')
 a[a[:,:,3]==0]=0;return Image.fromarray(a)
anim=['01_magma_palette_cycling','02_chauffe_locale','09_magma_fissures']+[f'10_eruption_matiere_{k:02}' for k in range(6)];groups={n:[] for n in anim};frames=[];timeline=[];material_board=[]
for i in range(N):
 magma=load(SRC/f'grotte_v4_01_magma_palette_cycling_{i:03}.png');heating=load(SRC/f'grotte_v4_02_chauffe_locale_{i:03}.png');live=Image.alpha_composite(magma,heating);field=heatmap(live)
 table=np.array(PAL['palette_by_frame'][i],dtype='uint8');fissures=rgba(table[fissure_indices],cracks.astype('uint8')*255)
 ims=[magma,heating,fissures];states=[]
 for k,vent in enumerate(vents):
  x,y=vent['anchor'];stage,u=state((i+vent['offset'])%N);layer=Image.new('RGBA',(W,H))
  if stage is not None:
   pose=material_pose(sprites[stage],stage,u,x,y,vent['scale'],field);layer.alpha_composite(pose,(x-pose.width//2,y-pose.height+1))
  assert not np.any(np.array(layer)[:,:,3][solid]),'Eruption overlaps rock'
  ims.append(layer);states.append('repos' if stage is None else stages[stage])
 for n,im in zip(anim,ims):
  groups[n].append(im)
  if n=='01_magma_palette_cycling':shutil.copyfile(SRC/f'grotte_v4_{n}_{i:03}.png',P/f'grotte_v5_{n}_{i:03}.png')
  else:im.save(P/f'grotte_v5_{n}_{i:03}.png')
 ls=list(zip(anim[:2],ims[:2]))+static+list(zip(anim[2:],ims[2:]));c=compose(ls);assert np.all(np.array(c)[:,:,3]==255);c.save(P/f'grotte_v5_scene_{i:03}.png');frames.append(c);timeline.append(states)
 if i==0:
  first=ls;c.save(P/'COMPOSITION.png')
  for stage in range(8):
   pose=material_pose(sprites[stage],stage,0,547,331,1,field);pose.save(O/f'pose_matiere_{stage:02}.png');material_board.append(pose)
frames[0].save(P/'ANIMATION_COMPLETE.webp',save_all=True,append_images=frames[1:],duration=DT,loop=0,lossless=True)
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'cendres_fissures_matiere.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(name,im) in reversed(list(enumerate(first))):
  fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
with zipfile.ZipFile(P/'cendres_fissures_matiere.ora') as z:
 st=ET.fromstring(z.read('stack.xml')).find('stack');im=compose([(n.get('name'),load(io.BytesIO(z.read(n.get('src'))))) for n in reversed(st)]);assert np.array_equal(np.array(im),np.array(frames[0]))
shutil.copyfile(V4/'PALETTES_064.json',O/'PALETTES_064.json');shutil.copyfile(V4/'MAGMA_INDICES_FIXES.png',O/'MAGMA_INDICES_FIXES.png')
manifest={'size':[W,H],'frames':N,'frame_ms':DT,'cycle_ms':N*DT,'static_layers':[n for n,_ in static],'animation_groups':anim,'render_order':anim[:2]+[n for n,_ in static]+anim[2:],'vents':vents,'event_stages':stages,'timeline':timeline,'fissures':{'roots':roots,'pixels':int(cracks.sum()),'mask':'MASQUE_FISSURES.png','fixed_indices':'INDICES_FISSURES.png','phase_travel_pixels_per_bin':6},'origin':{'terrain':'V4 preserved; dark cut grooves and animated fissure overlay added','magma':'V4 fixed-index cycling PNGs copied byte-for-byte','eruptions':'new 8-pose generation; live magma texture reprojected onto each shape, lifted/stretching UVs and bounded thermal relief, exact material match at feet'},'tests':{'opaque_compositions':True,'ora_exact':True,'eruption_feet_match_live_magma':True,'eruptions_off_terrain':True,'central_corridor_free_of_fissures':True},'runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
board=Image.new('RGB',(960,142),(33,23,24));d=ImageDraw.Draw(board)
for k,im in enumerate(material_board):board.paste(im,(k*120+60-im.width//2,109-im.height),im);d.text((k*120+4,119),f'{k+1}. '+stages[k],fill=(255,196,107))
board.save(O/'SEQUENCE_MATIERE_COMMUNE.png')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition complète','src':uri((P/'ANIMATION_COMPLETE.webp').read_bytes(),'image/webp')}]
for name,seq in groups.items():
 b=io.BytesIO();seq[0].save(b,format='WEBP',save_all=True,append_images=seq[1:],duration=DT,loop=0,lossless=True);items.append({'name':name,'src':uri(b.getvalue(),'image/webp')})
for name,im in static:items.append({'name':name,'src':uri(png(im))})
stills=[]
for im in frames:
 b=io.BytesIO();im.save(b,format='WEBP',lossless=True);stills.append(uri(b.getvalue(),'image/webp'))
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Grotte — fissures et matière commune</title><style>body{background:#1c181a;color:#eedbc7;font:16px system-ui;max-width:1080px;margin:28px auto;padding:0 20px}h1{color:#ffc277}p{line-height:1.6}img{image-rendering:pixelated;max-width:100%;background:repeating-conic-gradient(#33292c 0 25%,#483335 0 50%) 0/16px 16px}select,button{padding:10px;margin:8px;background:#382a25;color:#ffdab1;border:1px solid #8c5b38}input{width:230px}</style><h1>Grotte · fissures de magma & matière commune</h1><p>Fissures animées dans les parois et rebords, sur un calque indépendant. Nouvelles formes de bulles et jets : la texture du magma de chaque frame est projetée sur leur surface, pas seulement une palette ressemblante. Pieds raccordés à la matière sous-jacente. Chemin central dégagé, éruptions dans la lave uniquement. 64 phases · 100 ms · pas de validation PMDO.</p><select id="sel"></select><button id="play">Pause</button><input id="scrub" type="range" min="0" max="63" value="0"><span id="label">Boucle 6,4 s</span><br><img id="view" alt="Grotte avec fissures et éruptions de magma"><h2>Gonflement → rupture → jet → retombée</h2><img alt="Séquence de la même matière" src="'''+uri(png(board))+'''"><script>const items='''+json.dumps(items)+',frames='+json.dumps(stills)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>{view.src=items[sel.value].src;play.textContent='Pause'};play.onclick=()=>{if(play.textContent==='Pause'){view.src=frames[+scrub.value];play.textContent='Reprendre'}else{view.src=items[sel.value].src;play.textContent='Pause'}};scrub.oninput=()=>{view.src=frames[+scrub.value];play.textContent='Reprendre';label.textContent='Phase '+(+scrub.value+1)+' / 64'};</script>'''
(R/'apercu_cendres_fissures_matiere_v5.html').write_text(html);print(json.dumps(manifest['tests'],indent=2));print('Fissure roots:',roots)
