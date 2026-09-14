"""Apple Woods-inspired layered entrance with Sky Peak-style grass and native flower phases."""
from pathlib import Path
import sys,json,io,zipfile,base64,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[2];O=R/'renders/applewoods_skygrass_v1';P=O/'entree_pommier';P.mkdir(parents=True,exist_ok=True);D=O/'sprites';D.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
W,H=552,408;NN=Image.Resampling.NEAREST;yy,xx=np.mgrid[:H,:W]
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def compose(ls):
 c=Image.new('RGBA',(W,H))
 for _,im in ls:c.alpha_composite(im)
 return c
def part(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def color_trees(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);green=(g>r*1.07)&(g>b*1.10)&(a[:,:,3]>0);lum=.2126*r+.7152*g+.0722*b
 ramp=np.array([[12,49,29],[30,83,33],[61,128,40],[104,178,55],[156,220,92],[194,239,131]])
 for j in range(3):a[:,:,j][green]=np.rint(np.interp(lum[green],[0,65,110,155,200,255],ramp[:,j])).astype('uint8')
 a[a[:,:,3]==0]=0;return Image.fromarray(a)
# Full hidden grass plate plus a separately removable earth path/fringe.
floor=load(O/'bruts/sol_chemin.png').resize((W,H),NN);a=np.array(floor);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
candidate=(r>g*.98)&(r>150)&(g>125);labels,n=nd.label(candidate);counts=np.bincount(labels.ravel());counts[0]=0;path=nd.binary_fill_holes(nd.binary_closing(labels==counts.argmax(),iterations=2))
# Preserve the open south boundary (binary closing otherwise trims border pixels).
path[-3:]=candidate[-3:];outside=nd.distance_transform_edt(~path);alpha=np.rint(np.clip((8-outside)/8,0,1)*255).astype('uint8');alpha[path]=255
pa=a.copy();pa[:,:,3]=alpha;pa[alpha==0]=0;pathlayer=Image.fromarray(pa)
grass=load(O/'bruts/herbe_seule.png').resize((W,H),NN);ga=np.array(grass);reference=np.median(a[~nd.binary_dilation(path,iterations=12),:3],axis=0);shift=reference-np.median(ga[:,:,:3].reshape(-1,3),axis=0);ga[:,:,:3]=np.clip(ga[:,:,:3].astype(float)+shift,0,255).astype('uint8');grass=Image.fromarray(ga)
static=[('01_herbe_reconstituee',grass),('02_chemin_et_lisiere',pathlayer)]
Image.fromarray(path.astype('uint8')*255).save(O/'MASQUE_CHEMIN.png')
# Four complete ordinary-tree sprite variants, separately instanced on aligned layers.
sheet=key(load(O/'bruts/pommiers_magenta.png'));trees=[]
for k in range(4):
 x=k%2*sheet.width//2;y=k//2*sheet.height//2;q=sheet.crop((x,y,(k%2+1)*sheet.width//2,(k//2+1)*sheet.height//2));q=q.crop(q.getbbox());q=color_trees(q);trees.append(q)
 q.resize((112,round(q.height*112/q.width)),NN).save(D/f'pommier_variante_{k:02}.png')
big=key(load(O/'bruts/arbre_entree_magenta.png'));big=big.crop(big.getbbox());big=color_trees(big);big=big.resize((260,round(big.height*260/big.width)),NN);big.save(D/'pommier_ancien_entier.png')
a=np.array(big);h,w=a.shape[:2];by,bx=np.mgrid[:h,:w];dark=(a[:,:,0]<60)&(a[:,:,1]<43)&(a[:,:,2]<34)&(by>h*.60)&(bx>w*.32)&(bx<w*.68)&(a[:,:,3]>0)
lab,n=nd.label(dark);cnt=np.bincount(lab.ravel());cnt[0]=0;door=lab==cnt.argmax();dy,dx=np.where(door);doorx=round((dx.min()+dx.max())/2);origin=(276-doorx,174-h)
# The giant's complete sprite is available; these three layers partition its visible canopy/trunk/opening.
leaf=(a[:,:,1]>a[:,:,0].astype(float)*1.07)&(a[:,:,1]>a[:,:,2].astype(float)*1.1)&(by<h*.71);crown=((by<h*.46)|leaf)&(a[:,:,3]>0)&~door
bigparts=[]
for name,mask in [('20_entree_profondeur',door),('21_entree_tronc_racines',(a[:,:,3]>0)&~door&~crown),('22_entree_canopee',crown)]:
 layer=Image.new('RGBA',(W,H));layer.alpha_composite(part(a,mask),origin);bigparts.append((name,layer))
# Similar orchard borders to Apple Woods, with small staggered placements and an open central approach.
placements=[];rng=np.random.default_rng(84)
for row,foot in enumerate([69,150,239,331,438]):
 for col,x in enumerate([34,137,417,522]):
  k=(row+col*2)%4;width=int([113,108,110,115][col]+rng.integers(-4,5));q=trees[k];q=q.resize((width,round(q.height*width/q.width)),NN);rootx=int(x+rng.integers(-5,6));rooty=int(foot+rng.integers(-5,6));xy=(rootx-q.width//2,rooty-q.height);layer=Image.new('RGBA',(W,H));layer.alpha_composite(q,xy)
  placements.append({'name':f'10_pommier_{len(placements):02}','image':layer,'variant':k,'root':[rootx,rooty],'width':width})
# Ground contact shadows are independent, not baked into the grass or the sprites.
shade=Image.new('L',(W,H));sd=ImageDraw.Draw(shade)
for t in placements:
 x,y=t['root'];r=t['width']*.33;sd.ellipse((round(x-r),y-8,round(x+r),y+2),fill=60)
sd.ellipse((207,149,346,174),fill=74);sh=np.zeros((H,W,4),dtype='uint8');sh[:,:,:3]=[32,68,30];sh[:,:,3]=np.array(shade.filter(ImageFilter.GaussianBlur(.8)));sh[sh[:,:,3]==0]=0
static.append(('04_ombres_contact',Image.fromarray(sh)))
# Sort full tree instances by their foot depth, with the giant inserted at its root height.
objects=[(t['root'][1],[(t['name'],t['image'])]) for t in placements]+[(174,bigparts)];objects.sort(key=lambda x:x[0]);tree_layers=[l for _,ls in objects for l in ls]
tree_alpha=np.maximum.reduce([np.array(im)[:,:,3] for _,im in tree_layers])>0
# Extract actual four flower phases from the local Sky Peak reference, without palette recoloring or resizing.
refs=[np.array(load(R/f'source/sky_peak_v1/gif_{i}.png')) for i in range(4)];sy,sx=np.mgrid[:504,:504];petals=[]
for ar in refs:
 r,g,b=ar[:,:,:3].astype(float).transpose(2,0,1);petals.append((r>190)&(r>=g)&(r>b*1.08)&(sy>130))
union=np.logical_or.reduce(petals);lab,n=nd.label(nd.binary_dilation(union,iterations=1),np.ones((3,3)));candidates=[]
for k,sl in enumerate(nd.find_objects(lab),1):
 if sl is None:continue
 gy,gx=sl;height=gy.stop-gy.start;width=gx.stop-gx.start;mask=lab==k
 if not(7<=width<=30 and 7<=height<=28 and gx.start>2 and gy.stop<502):continue
 ims=[]
 for i,ar in enumerate(refs):
  visible=nd.binary_fill_holes(petals[i]&mask);out=ar[gy,gx].copy();out[~visible[gy,gx]]=0;ims.append(Image.fromarray(out))
 if len({png(im) for im in ims})<3:continue
 candidates.append({'bbox':[gx.start,gy.start,gx.stop,gy.stop],'images':ims})
assert len(candidates)>=8
flowers=candidates[::max(1,len(candidates)//10)][:10]
for k,entry in enumerate(flowers):
 for i,im in enumerate(entry['images']):im.save(D/f'fleur_sky_{k:02}_phase_{i:02}.png')
# Plant flowers in the meadow along the path, never over trees or the walkable earth.
free=(~tree_alpha)&(~nd.binary_dilation(path,iterations=3));clearance=nd.distance_transform_edt(free);distance_to_path=nd.distance_transform_edt(~path)
spots=np.argwhere((clearance>=8)&(distance_to_path<72)&(distance_to_path>12)&(yy>143)&(yy<399));rng.shuffle(spots);sites=[]
for y,x in spots:
 if any((x-v['center'][0])**2+(y-v['center'][1])**2<25**2 for v in sites):continue
 k=len(sites)%len(flowers);ims=flowers[k]['images'];fw,fh=ims[0].size;tx=int(x-fw//2);ty=int(y-fh//2)
 if tx<0 or ty<0 or tx+fw>W or ty+fh>H:continue
 if any(np.any((np.array(im)[:,:,3]>0)&~free[ty:ty+fh,tx:tx+fw]) for im in ims):continue
 sites.append({'center':[int(x),int(y)],'origin':[tx,ty],'sprite':k,'phase_offset':len(sites)%4})
 if len(sites)==36:break
assert len(sites)>=16,len(sites)
leaves=Image.new('RGBA',(W,H));ld=ImageDraw.Draw(leaves)
for site in sites:
 x,y=site['center'];ld.line((x,y+3,x,y+7),fill=(65,145,62));ld.ellipse((x-4,y+3,x,y+5),fill=(87,169,70));ld.ellipse((x+1,y+4,x+4,y+6),fill=(105,187,78))
la=np.array(leaves);la[~free]=0;leaves=Image.fromarray(la)
static.append(('03_feuillage_bas_des_fleurs',leaves));static+=tree_layers
# Three spatial flower layers, each with the four aligned native poses (phase offsets only).
anim_names=['30_fleurs_gauche','31_fleurs_droite','32_fleurs_autour_entree'];groups={n:[] for n in anim_names};frames=[]
for phase in range(4):
 layers=[Image.new('RGBA',(W,H)) for _ in range(3)]
 for site in sites:
  x,y=site['center'];g=2 if y<195 else (0 if x<276 else 1);im=flowers[site['sprite']]['images'][(phase+site['phase_offset'])%4];layers[g].alpha_composite(im,site['origin'])
 for n,im in zip(anim_names,layers):groups[n].append(im);im.save(P/f'apple_sky_{n}_{phase:03}.png')
 all_layers=static+list(zip(anim_names,layers));c=compose(all_layers);assert np.all(np.array(c)[:,:,3]==255);frames.append(c);c.save(P/f'apple_sky_scene_{phase:03}.png')
 if phase==0:first=all_layers;c.save(P/'COMPOSITION.png')
for n,im in static:im.save(P/f'apple_sky_{n}.png')
frames[0].save(P/'ANIMATION_COMPLETE.webp',save_all=True,append_images=frames[1:],duration=200,loop=0,lossless=True)
# A conservative south-to-tree approach, stopping at the visible root threshold (not a collision map).
corridor=Image.new('L',(W,H));ImageDraw.Draw(corridor).line([(276,407),(276,174)],fill=255,width=24);cm=np.array(corridor)>0
assert np.all(path[cm]);assert not np.any(tree_alpha&cm&(yy>179));corridor.save(O/'APPROCHE_TRONC.png')
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'entree_pommier.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(name,im) in reversed(list(enumerate(first))):
  fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
with zipfile.ZipFile(P/'entree_pommier.ora') as z:
 st=ET.fromstring(z.read('stack.xml')).find('stack');re=compose([(n.get('name'),load(io.BytesIO(z.read(n.get('src'))))) for n in reversed(st)]);assert np.array_equal(np.array(re),np.array(frames[0]))
manifest={'size':[W,H],'frames':4,'frame_ms':200,'cycle_ms':800,'static_layers':[n for n,_ in static],'animation_groups':anim_names,'render_order':[n for n,_ in static]+anim_names,'trees':[{'name':t['name'],'variant':t['variant'],'root':t['root'],'width':t['width']} for t in placements],'entrance_tree':{'origin':list(origin),'size':list(big.size),'door_local_bbox':[int(dx.min()),int(dy.min()),int(dx.max()+1),int(dy.max()+1)]},'flower_sources':[{'bbox':f['bbox']} for f in flowers],'flower_sites':sites,'sources':{'layout':'Apple_Woods_entrance_TDS.png, reference commit46e93da','grass':'Sky Peak gif_0.png style, generated ground layers','flowers':'source/sky_peak_v1/gif_0.png to gif_3.png, four original200ms phases, extracted/repositioned without recoloring or resizing','trees':'new isolated magenta generations; shared foliage palette'},'tests':{'opaque_compositions':True,'ora_exact':True,'approach_to_trunk_clear':True},'related_water_delivery':'renders/siphons_ecoulement_v3; forest completed first as requested.','runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Review sheet of complete tree sprites (the scene itself uses individual aligned layers).
board=Image.new('RGBA',(560,280),(32,58,38,255));dd=ImageDraw.Draw(board)
for k in range(4):
 im=load(D/f'pommier_variante_{k:02}.png');board.alpha_composite(im,(k*140+14,25));dd.text((k*140+12,170),f'Pommier {k+1}',fill=(237,239,187))
board.save(O/'PLANCHE_POMMIERS.png')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition animée','src':uri((P/'ANIMATION_COMPLETE.webp').read_bytes(),'image/webp')}]
for n,seq in groups.items():
 b=io.BytesIO();seq[0].save(b,format='WEBP',save_all=True,append_images=seq[1:],duration=200,loop=0,lossless=True);items.append({'name':n,'src':uri(b.getvalue(),'image/webp')})
for n,im in static:items.append({'name':n,'src':uri(png(im))})
stills=[uri(png(im)) for im in frames]
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Apple Woods · entrée du vieux pommier</title><style>body{background:#14251c;color:#e4ecd5;font:16px system-ui;max-width:1100px;margin:28px auto;padding:0 20px}h1{color:#d8e997}p{line-height:1.6}img{image-rendering:pixelated;max-width:100%;background:repeating-conic-gradient(#284337 0 25%,#365744 0 50%) 0/16px 16px}button,select{padding:10px;margin:8px;background:#294a35;color:#edf0c7;border:1px solid #73946a}input{width:190px}</style><h1>Apple Woods · entrée du vieux pommier</h1><p>Passage central conservé dans son esprit, herbe claire inspirée de Sky Peak et chemin crème-ocre. Entrée dans le gros tronc au nord. Chaque pommier possède son propre calque ; sol, chemin, ombres, tronc et canopée sont séparés. Fleurs natives Sky Peak : quatre phases à200ms, repositionnées sur trois calques. Pas de validation PMDO.</p><select id="sel"></select><button id="play">Pause</button><input id="scrub" type="range" min="0" max="3" value="0"><span id="label">4 phases · boucle 0,8 s</span><br><img id="view" alt="Entrée Apple Woods avec prairie et fleurs Sky Peak"><h2>Pommiers détourés</h2><img alt="Quatre sprites de pommiers" src="'''+uri(png(board))+'''"><script>const items='''+json.dumps(items)+',frames='+json.dumps(stills)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>{view.src=items[sel.value].src;play.textContent='Pause'};play.onclick=()=>{if(play.textContent==='Pause'){view.src=frames[+scrub.value];play.textContent='Reprendre'}else{view.src=items[sel.value].src;play.textContent='Pause'}};scrub.oninput=()=>{view.src=frames[+scrub.value];play.textContent='Reprendre';label.textContent='Phase '+(+scrub.value+1)+' / 4'};</script>'''
(R/'apercu_applewoods_skygrass_v1.html').write_text(html);print('Trees',len(placements),'flower sources',len(flowers),'flower sites',len(sites),'entrance',manifest['entrance_tree']);print(manifest['tests'])
