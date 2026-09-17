"""Local coast repair and actual fixed-index thermal palette cycling."""
from pathlib import Path
import sys,io,json,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];V3=R/'renders/cendres_grotte_eruptions_v3';O=R/'renders/cendres_palette_raccord_v4';P=O/'cendres_palette_raccord';P.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
W,H=648,504;N=64;DT=100;NN=Image.Resampling.NEAREST;yy,xx=np.mgrid[:H,:W]
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def part(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def compose(ls):
 c=Image.new('RGBA',(W,H))
 for _,im in ls:c.alpha_composite(im.convert('RGBA'))
 return c
# Preserve the approved V3 terrain; add ONLY the missing local cliff in the square notch.
oldm=json.loads((V3/'manifest.json').read_text());static=[(n,load(V3/'cendres_grotte'/f'grotte_v3_{n}.png')) for n in oldm['static_layers']]
oldterrain=compose(static);a=np.array(oldterrain);oldsolid=a[:,:,3]>0
patch=key(load(O/'bruts/raccord_roche_genere.png').resize((140,125),NN));pa=np.zeros((H,W,4),dtype='uint8');pa[175:300,70:210]=np.array(patch)
add=(pa[:,:,3]>0)&~oldsolid&(xx>=107)&(xx<189)&(yy>=198)&(yy<294)
lum=np.rint(pa[:,:,:3]@np.array([.2126,.7152,.0722])).astype('uint8')
for j in range(3):pa[:,:,j]=np.clip(lum.astype(int)+[0,0,2][j],0,255)
pa[~add]=0;static.append(('06b_raccord_roche',Image.fromarray(pa)));terrain=compose(static);a=np.array(terrain);solid=a[:,:,3]>0
assert solid[235,135] and not oldsolid[235,135]
assert np.array_equal(a[oldsolid],np.array(oldterrain)[oldsolid])
Image.fromarray((add*255).astype('uint8')).save(O/'masque_reparation_locale.png')
walk=load(V3/'masque_approche_grotte.png').convert('L');wm=np.array(walk)>0;assert np.all(solid[wm]);walk.save(O/'masque_approche_grotte.png')
# Shared temperature ramp: all visible magma, bubbles, droplets and flames use these same 16 RGB colors.
HEAT=np.array([[34,12,15],[55,15,16],[79,20,15],[105,26,14],[133,33,12],[160,43,10],[185,56,8],[208,73,8],[228,94,10],[243,118,15],[252,144,25],[255,168,41],[255,190,62],[255,210,87],[255,226,118],[255,239,156]],dtype='uint8')
def temperatures(im):
 ar=np.array(im);l=ar[:,:,:3]@np.array([.2126,.7152,.0722]);return np.rint(np.interp(l,[0,35,75,125,175,225,255],[0,2,6,10,13,15,15])).astype('uint8')
base=load(V3/'magma_cle_00.png');heat=temperatures(base)
# Phase advances along the generated hot veins, using a lower travel cost in hotter connected material.
sh=heat[::2,::2];h,w=sh.shape;ids=np.arange(h*w).reshape(h,w);cost=1+((15-sh.astype(float))/15)**3*10;cost[solid[::2,::2]]=10000
u=np.concatenate([ids[:,:-1].ravel(),ids[:-1,:].ravel()]);v=np.concatenate([ids[:,1:].ravel(),ids[1:,:].ravel()]);weights=np.concatenate([((cost[:,:-1]+cost[:,1:])/2).ravel(),((cost[:-1,:]+cost[1:,:])/2).ravel()])
graph=coo_matrix((np.r_[weights,weights],(np.r_[u,v],np.r_[v,u])),shape=(h*w,h*w)).tocsr()
vents=oldm['vents'];seeds=[ids[y//2,x//2] for x,y in [v['anchor'] for v in vents]]
travel=dijkstra(graph,directed=False,indices=seeds,min_only=True).reshape(h,w)
phasebin=(np.floor(travel/5).astype('int64')%16).astype('uint8');phasebin=np.array(Image.fromarray(phasebin).resize((W,H),NN))
indices=(heat.astype('uint16')*16+phasebin).astype('uint8');Image.fromarray(indices).save(O/'MAGMA_INDICES_FIXES.png')
Image.fromarray(heat).save(O/'MAGMA_CLASSES_THERMIQUES.png')
# No optical flow and no texture morphing: every magma frame has exactly the SAME index plane.
magma=[];tables=[];heats=[]
for i in range(N):
 table=[];levels=[]
 for cl in range(16):
  for ph in range(16):
   amp=0 if cl<=3 else .55+(cl-4)*.073
   value=int(np.clip(cl+round(amp*np.cos(2*np.pi*(ph/16-i/N))),0,15));levels.append(value);table.append(HEAT[value].tolist())
 table=np.array(table,dtype='uint8');levels=np.array(levels,dtype='uint8');im=Image.fromarray(indices).convert('P');im.putpalette(table.ravel().tolist());magma.append(im);tables.append(table.tolist());heats.append(levels[indices])
(O/'PALETTES_064.json').write_text(json.dumps({'master_heat_rgb':HEAT.tolist(),'palette_by_frame':tables,'cold_classes_fixed':[0,1,2,3]},indent=1)+'\n')
# A narrow cooled contact film follows the repaired rock silhouette, never a wave displaced from it.
shore=nd.distance_transform_edt(~solid);contact=(~solid)&(shore<=2);cool=np.zeros((H,W,4),dtype='uint8');cool[:,:,:3]=HEAT[np.maximum(heat.astype(int)-2,0)];cool[:,:,3]=contact*255;cool[~contact]=0
static=[('03a_contact_refroidi',Image.fromarray(cool))]+static
for name,im in static:im.save(P/f'grotte_v4_{name}.png')
# Eight generated eruption stages, common scale and ground anchor. Never normalize each pose's height.
sheet=key(load(V3/'bruts/bulle_eruption_huit_phases.png'));sprites=[]
for k in range(8):
 x=(k%4)*sheet.width//4;y=(k//4)*sheet.height//2;im=sheet.crop((x,y,x+sheet.width//4,y+sheet.height//2));im=im.crop(im.getbbox());im=im.resize((max(1,round(im.width*.20)),max(1,round(im.height*.20))),NN);ar=np.array(im);ar[:,:,:3]=HEAT[temperatures(im)];ar[ar[:,:,3]==0]=0;Image.fromarray(ar).save(O/f'eruption_pose_{k:02}.png');sprites.append(im)
stages=['bulle_basse','gonflement','bulle_fissuree','eclatement','jet_naissant','colonne','retombee','residu']
def event_state(phase):
 for stage,(lo,hi) in enumerate([(0,4),(4,8),(8,12),(12,14),(14,18),(18,24),(24,29),(29,35)]):
  if lo<=phase<hi:return stage,(phase-lo)/(hi-lo)
 return None,0
# Keep all six established lava-side anchors and the causal V3 schedule.
def pressure(local):
 return float(np.interp(local,[0,4,12,18,24,35,59,60,63],[.4,.6,1,.8,.6,0,0,0,.3]))
def sprite_heat(stage,u):
 return [(-1+u),(-.5+u),u,1.5,1.5,1.5,(1-u),(-2*u)][stage]
anim_names=['01_magma_palette_cycling','02_chauffe_locale']+[f'07_eruption_{k:02}' for k in range(len(vents))]
groups={n:[] for n in anim_names};frames=[];events_timeline=[];shore=nd.distance_transform_edt(~solid)
for i in range(N):
 # Local incandescence grows BEFORE a bubble, peaks around bursting, then cools.
 g=np.zeros((H,W,4),dtype='uint8');boost=np.zeros((H,W),float)
 for v in vents:
  x,y=v['anchor'];local=(i+v['offset'])%N;r=((xx-x)/31)**2+((yy-y)/11)**2
  boost=np.maximum(boost,np.clip(1-r,0,1)*pressure(local)*2)
 delta=np.rint(boost).astype(int);hotmask=(delta>0)&~solid&(heat>=4)
 g[:,:,:3]=HEAT[np.clip(heats[i].astype(int)+delta,0,15)];g[:,:,3]=hotmask*255;g[~hotmask]=0;glow=Image.fromarray(g)
 ims=[magma[i],glow];states=[]
 for k,v in enumerate(vents):
  x,y=v['anchor'];local=(i+v['offset'])%N;stage,u=event_state(local);layer=Image.new('RGBA',(W,H))
  if stage is not None:
   sprite=sprites[stage];scale=v['scale'];stretch=1+.045*np.sin(u*2*np.pi) if stage in [4,5,6] else 1
   im=sprite.resize((round(sprite.width*scale),round(sprite.height*scale*stretch)),NN)
   ar=np.array(im);temp=temperatures(im).astype(int)
   # Same generated material grain on bubble bodies, with cracks and dark outlines preserved.
   if stage<=2:
    texture=heat[y-im.height+1:y+1,x-im.width//2:x-im.width//2+im.width].astype(float)
    grain=np.clip(np.rint((texture-nd.gaussian_filter(texture,2))*.22),-1,1).astype(int)
    temp+=grain*((temp>=3)&(temp<=11))
   temp=np.clip(temp+round(sprite_heat(stage,u)),0,15);ar[:,:,:3]=HEAT[temp];ar[ar[:,:,3]==0]=0;im=Image.fromarray(ar)
   if stage==7:
    ar=np.array(im);ar[:,:,3]=np.rint(ar[:,:,3]*(1-u)).astype('uint8');ar[ar[:,:,3]==0]=0;im=Image.fromarray(ar)
   layer.alpha_composite(im,(x-im.width//2,y-im.height+1))
  assert not np.any(np.array(layer)[:,:,3][solid]),'An eruption overlaps the path or cave'
  ims.append(layer);states.append('repos' if stage is None else stages[stage])
 for name,im in zip(anim_names,ims):groups[name].append(im);im.save(P/f'grotte_v4_{name}_{i:03}.png')
 ls=list(zip(anim_names[:2],ims[:2]))+static+list(zip(anim_names[2:],ims[2:]));c=compose(ls);assert np.all(np.array(c)[:,:,3]==255);frames.append(c);c.save(P/f'grotte_v4_scene_{i:03}.png');events_timeline.append(states)
 if i==0:first=ls;c.save(P/'COMPOSITION.png')
frames[0].save(P/'ANIMATION_COMPLETE.webp',save_all=True,append_images=frames[1:],duration=DT,loop=0,lossless=True)
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'cendres_palette_raccord.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(name,im) in reversed(list(enumerate(first))):
  fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
with zipfile.ZipFile(P/'cendres_palette_raccord.ora') as z:
 st=ET.fromstring(z.read('stack.xml')).find('stack');im=compose([(n.get('name'),load(io.BytesIO(z.read(n.get('src'))))) for n in reversed(st)]);assert np.array_equal(np.array(im),np.array(frames[0]))
manifest={'size':[W,H],'frames':N,'frame_ms':DT,'cycle_ms':N*DT,'static_layers':[n for n,_ in static],'animation_groups':anim_names,'render_order':anim_names[:2]+[n for n,_ in static]+anim_names[2:],'vents':vents,'event_stages':stages,'timeline':events_timeline,'origin':{'terrain':'V3 unchanged except additive generated cliff repair in local ROI','magma':'fixed generated V3 keyframe; 256 fixed indices = 16 thermal classes times 16 vein phases; 64 generated palette tables, no optical flow','eruptions':'V3 eight generated poses recolored with shared 16-color heat ramp, bubble grain and causal local heating'},'repair':{'roi':[107,198,189,294],'added_rock_pixels':int(add.sum()),'old_rock_pixels_unchanged':True},'tests':{'south_to_cave_32px_corridor_on_terrain':True,'all_eruption_pixels_outside_terrain_all_frames':True,'opaque_compositions':True,'ora_recomposition_exact':True},'runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Chronology sheet helps inspect the causal sequence without relying on playback.
board=Image.new('RGB',(8*120,132),(42,23,25));d=ImageDraw.Draw(board)
for k in range(8):
 im=load(O/f'eruption_pose_{k:02}.png')
 board.paste(im,(k*120+60-im.width//2,100-im.height),im);d.text((k*120+5,110),f'{k+1}. '+stages[k],fill=(255,198,122))
board.save(O/'SEQUENCE_BULLE_FLAMME.png')
# Before/after crop is a delivered control image, not a regenerated full scene.
comparison=Image.new('RGB',(600,288),(30,25,28));draw=ImageDraw.Draw(comparison)
for k,(title,im) in enumerate([('V3 : decoupe verticale',load(V3/'cendres_grotte/COMPOSITION.png')),('V4 : raccord rocheux continu',frames[0])]):
 comparison.paste(im.crop((70,175,210,300)).resize((280,250),NN),(k*300+10,28));draw.text((k*300+10,8),title,fill=(255,203,140))
comparison.save(O/'RACCORD_AVANT_APRES.png')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition animée','src':uri((P/'ANIMATION_COMPLETE.webp').read_bytes(),'image/webp')}]
for name,seq in groups.items():
 b=io.BytesIO();seq[0].save(b,format='WEBP',save_all=True,append_images=seq[1:],duration=DT,loop=0,lossless=True);items.append({'name':name,'src':uri(b.getvalue(),'image/webp')})
for name,im in static:items.append({'name':name,'src':uri(png(im))})
# Individual stills stored in lossless WebP inside HTML; full PNGs remain in the pack.
stills=[]
for im in frames:
 b=io.BytesIO();im.save(b,format='WEBP',lossless=True);stills.append(uri(b.getvalue(),'image/webp'))
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Grotte cendrée — raccord et palette thermique</title><style>body{background:#1b181a;color:#ebded0;font:16px system-ui;max-width:1080px;margin:28px auto;padding:0 20px}h1{color:#ffc078}p{line-height:1.6}img{image-rendering:pixelated;max-width:100%;background:repeating-conic-gradient(#31282a 0 25%,#493538 0 50%) 0/16px 16px}select,button{padding:10px;margin:8px;background:#392b27;color:#ffd5a7;border:1px solid #895f43}input{width:230px}</style><h1>Grotte cendrée · raccord & palette thermique</h1><p>Le chemin venant du sud mène à la grotte. Toutes les éruptions sont dans la lave latérale : aucun jet sur le passage. Raccord rocheux réparé près de la grotte. Magma, bulles et flammes partagent 16 couleurs thermiques. 64 palettes sur une texture fixe : veines incandescentes, croûtes froides stables, chauffe locale avant les bulles. Animation évocatrice, pas une simulation physique. Pas de test PMDO/collisions.</p><select id="sel"></select><button id="play">Pause</button><input id="scrub" type="range" min="0" max="63" value="0"><span id="label">64 phases · 100 ms · 6,4 s</span><br><img id="view" alt="Chemin vers la grotte, lave et éruptions sur les côtés"><h2>Raccord près de la grotte</h2><img alt="Comparaison du raccord rocheux avant et après" src="'''+uri(png(comparison))+'''"><h2>Ordre des événements</h2><img alt="Bulle basse, gonflement, fissures, éclatement, jet, colonne, retombée, résidu" src="'''+uri(png(board))+'''"><p>Chaque site suit cet ordre, puis reste au repos avant un nouveau gonflement. Les sites sont décalés dans le temps. L’aperçu peut commencer au milieu du cycle d’un site.</p><script>const items='''+json.dumps(items)+',frames='+json.dumps(stills)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>{view.src=items[sel.value].src;play.textContent='Pause'};play.onclick=()=>{if(play.textContent==='Pause'){view.src=frames[+scrub.value];play.textContent='Reprendre'}else{view.src=items[sel.value].src;play.textContent='Pause'}};scrub.oninput=()=>{view.src=frames[+scrub.value];play.textContent='Reprendre';label.textContent='Phase '+(+scrub.value+1)+' / 64'};</script>'''
(R/'apercu_cendres_palette_raccord_v4.html').write_text(html)
print(json.dumps(manifest['tests'],indent=2));print(vents)
