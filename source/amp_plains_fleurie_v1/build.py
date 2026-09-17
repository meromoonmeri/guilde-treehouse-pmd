"""Amp Plains geometry, warm rocks, actual Metano sand and Vast Steppe plants."""
from pathlib import Path
import sys,io,json,math,hashlib,zipfile,xml.etree.ElementTree as ET,base64
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[2];REF=Path(__file__).resolve().parent/'references';O=R/'renders/amp_plains_fleurie_v1';P=O/'amp_plains_fleurie';D=O/'sprites';P.mkdir(parents=True,exist_ok=True);D.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'source/layouts_magenta_v1'));from palette import key
W,H=456,408;NN=Image.Resampling.NEAREST;yy,xx=np.mgrid[:H,:W]
def load(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def part(a,m):
 out=a.copy();out[~m]=0;return Image.fromarray(out)
def compose(layers):
 c=Image.new('RGBA',(W,H))
 for _,im in layers:c.alpha_composite(im)
 return c
# Canonical Amp Plains rocks and the two dead trees are separable connected components.
reference=load(R/'Amp_Plains_entrance_TD.png');a=np.array(reference);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);gray=(b>=r)&(b>=g*.86)
labels,n=nd.label(gray,np.ones((3,3)));dead=[];cliffs=[];blocks=[];pebbles=[]
for lab,sl in enumerate(nd.find_objects(labels),1):
 sy,sx=sl;count=int((labels==lab).sum())
 if sy.start>=160 and sy.stop-sy.start>=95 and sx.stop-sx.start<100:dead.append(lab)
 elif sy.start==0:cliffs.append(lab)
 elif count>=500:blocks.append(lab)
 else:pebbles.append(lab)
assert len(dead)==2;rockmask=gray&~np.isin(labels,dead);Image.fromarray((np.isin(labels,dead)*255).astype('uint8')).save(O/'MASQUE_ANCIENS_ARBRES_RETIRES.png')
# Native grass material from Vast Steppe, without its cliff layout or its pale northern fade.
grasstex=load(REF/'Vast_Steppe_Base.png').crop((240,264,288,312));grasstex.save(REF/'vast_herbe_48.png');ga=np.tile(np.array(grasstex),(math.ceil(H/48),math.ceil(W/48),1))[:H,:W];assert np.all(ga[:,:,3]==255)
grass=Image.fromarray(ga)
# Generated magenta guide provides only the new path silhouette. Its pixels are replaced by actual Metano sand.
guide=key(load(O/'bruts/chemin_guide_magenta.png').resize((W,H),NN));gm=np.array(guide)[:,:,3]>0;path=np.zeros_like(gm)
for y in range(H):
 shift=round(5*np.sin(np.pi*y/(H-1))**2*np.sin(2*np.pi*y/(H-1)));path[y]=np.roll(gm[y],shift)
path &= ~rockmask;distance=nd.distance_transform_edt(path);sand=load(REF/'metano_sable_24.png');sa=np.tile(np.array(sand),(math.ceil(H/24),math.ceil(W/24),1))[:H,:W].copy();sa[:,:,3]=np.where(path,np.where(distance>=2,255,190),0).astype('uint8');sa[sa[:,:,3]==0]=0
static=[('01_herbe_vast_steppe',grass),('02_chemin_sable_metano',Image.fromarray(sa))];Image.fromarray((path*255).astype('uint8')).save(O/'MASQUE_CHEMIN.png')
# Light-brown stone palette; preserve original rock shading, outlines, and component geometry.
stone=a.copy();lum=a[:,:,:3]@np.array([.2126,.7152,.0722]);palette=np.array([[47,38,28],[99,77,52],[139,110,74],[183,149,106],[212,181,136],[232,204,162],[247,228,194]])
for j in range(3):stone[:,:,j]=np.rint(np.interp(lum,[0,60,95,135,170,200,255],palette[:,j])).astype('uint8')
rocks=[]
for name,ids in [('04_falaises_brun_clair',cliffs),('05_rochers_brun_clair',blocks),('06_petits_rochers',pebbles)]:rocks.append((name,part(stone,np.isin(labels,ids))))
# Two existing PMD tree forms from Halcyon's reference layers. No AI-generated tree sprites or scaling.
canopy_atlas=load(REF/'vast_steppe_layer_4.png');objects=load(REF/'vast_steppe_layer_3.png');trees=[];tree_proof=[]
for k,(box,target) in enumerate([((16,96,160,216),(76,372)),((336,96,480,216),(341,276))]):
 foliage=canopy_atlas.crop(box);obj=objects.crop(box);oa=np.array(obj);rr,gg,bb=oa[:,:,:3].astype(float).transpose(2,0,1)
 wood=(rr>=gg*.85)&(bb<gg*.85)&(oa[:,:,3]>0);lab,num=nd.label(wood,np.ones((3,3)));counts=np.bincount(lab.ravel());counts[0]=0;mask=nd.binary_fill_holes(lab==counts.argmax());mask=nd.binary_dilation(mask,iterations=1)&(oa[:,:,3]>0);trunk=part(oa,mask)
 native=Image.alpha_composite(trunk,foliage);bbox=native.getbbox();native=native.crop(bbox);foliage=foliage.crop(bbox);trunk=trunk.crop(bbox)
 ny,nx=np.where(np.array(trunk)[:,:,3]>0);rootx=int(np.median(nx[ny>=ny.max()-3]));rooty=int(ny.max());origin=(target[0]-rootx,target[1]-rooty)
 native.save(D/f'arbre_pmd_{k:02}.png');trunk.save(D/f'arbre_pmd_{k:02}_tronc.png');foliage.save(D/f'arbre_pmd_{k:02}_feuillage.png')
 full=Image.new('RGBA',(W,H));full.alpha_composite(native,origin);leaf=Image.new('RGBA',(W,H));leaf.alpha_composite(foliage,origin)
 trees.append({'name':f'10_arbre_pmd_{k:02}','image':full,'leaf':leaf,'origin':origin,'size':native.size,'root':target})
 tree_proof.append({'source_box':list(box),'trim_box':list(bbox),'origin':list(origin),'size':list(native.size),'trunk_alpha_rebuilt':True,'native_rgb_no_recolor_no_resize':True})
# Reconstructed, independent tree contact shadows.
shadow=Image.new('L',(W,H));draw=ImageDraw.Draw(shadow)
for t in trees:
 x,y=t['root'];draw.ellipse((x-29,y-8,x+31,y+2),fill=58)
ar=np.zeros((H,W,4),dtype='uint8');ar[:,:,:3]=[52,81,40];ar[:,:,3]=np.array(shadow.filter(ImageFilter.GaussianBlur(.7)));ar[ar[:,:,3]==0]=0;static.append(('03_ombres_contact',Image.fromarray(ar)));static+=rocks;static +=[(t['name'],t['image']) for t in sorted(trees,key=lambda t:t['root'][1])]
# Actual Halcyon flower animation: native sequence 0,1,0,2, with three authored clocks.
atlas=load(REF/'Vast_Steppe_Flower_Animations.png');flower=[atlas.crop((pose*24,0,(pose+1)*24,24)) for pose in [0,1,0,2]];heads=[]
for i,im in enumerate(flower):
 im.save(D/f'fleur_vast_phase_{i:02}.png');fa=np.array(im);fr,fg,fb=fa[:,:,:3].astype(float).transpose(2,0,1)
 petals=((fr>=fg*.98)&(fr>100)&(fb>=fg*.75))|((fr>220)&(fg>190)&(fr>=fg));petals[14:]=False;fa[~petals]=0;head=Image.fromarray(fa).crop((0,0,12,16));head.save(D/f'petales_vast_phase_{i:02}.png');heads.append(head)
# Flower placements stay away from the path and solid scenery. Blooms on trees are a distinct adaptation layer.
treemask=np.maximum.reduce([np.array(t['image'])[:,:,3] for t in trees])>0;free=~(rockmask|treemask|nd.binary_dilation(path,iterations=3));clear=nd.distance_transform_edt(free);spots=np.argwhere((clear>=9)&(yy>126)&(yy<H-14)&(xx>13)&(xx<W-13));rng=np.random.default_rng(716);rng.shuffle(spots);sites=[];ticks=[8,10,14]
for y,x in spots:
 if any((x-s['center'][0])**2+(y-s['center'][1])**2<31**2 for s in sites):continue
 tx=int(x)-12;ty=int(y)-12
 if any(np.any((np.array(im)[:,:,3]>0)&~free[ty:ty+24,tx:tx+24]) for im in flower):continue
 sites.append({'kind':'ground','center':[int(x),int(y)],'origin':[tx,ty],'clock':ticks[len(sites)%3],'offset':len(sites)%4})
 if len(sites)>=19:break
assert len(sites)>=10,len(sites)
for ti,t in enumerate(trees):
 leaf=np.array(t['leaf'])[:,:,3]>0;inside=nd.distance_transform_edt(leaf);spots=np.argwhere((inside>=7)&(yy>4)&(yy<H-12)&(xx>8)&(xx<W-8));rng.shuffle(spots);chosen=[]
 for y,x in spots:
  if any((x-c[0])**2+(y-c[1])**2<18**2 for c in chosen):continue
  tx=int(x)-6;ty=int(y)-7
  if any(np.any((np.array(im)[:,:,3]>0)&~leaf[ty:ty+16,tx:tx+12]) for im in heads):continue
  chosen.append((int(x),int(y)));sites.append({'kind':'canopy','tree':ti,'center':[int(x),int(y)],'origin':[tx,ty],'clock':ticks[len(chosen)%3],'offset':len(chosen)%4})
  if len(chosen)>=10:break
 assert len(chosen)>=5
# Six animated groups: three clocks on the ground, three on the tree crowns.
groups=[]
for kind,sprite_set,prefix in [('ground',flower,'20_fleurs_sol'),('canopy',heads,'21_floraison_arbres')]:
 for tick in ticks:
  name=f'{prefix}_{tick}gf';ims=[]
  for phase in range(4):
   layer=Image.new('RGBA',(W,H))
   for site in sites:
    if site['kind']==kind and site['clock']==tick:layer.alpha_composite(sprite_set[(phase+site['offset'])%4],tuple(site['origin']))
   layer.save(P/f'amp_fleurie_{name}_{phase:03}.png');ims.append(layer)
  groups.append({'name':name,'tick':tick,'images':ims})
for name,im in static:im.save(P/f'amp_fleurie_{name}.png')
# Keep all three clocks exactly in game-frame units; deduplicate identical composed PNGs.
period=math.lcm(*(4*t for t in ticks));events=sorted(set(t for tick in ticks for t in range(0,period,tick)));timeline=[];frames=[];durations=[];unique={};comps=[]
for ei,t in enumerate(events):
 ls=static+[(g['name'],g['images'][(t//g['tick'])%4]) for g in groups];im=compose(ls);assert np.all(np.array(im)[:,:,3]==255);digest=hashlib.sha256(im.tobytes()).hexdigest()
 if digest not in unique:
  unique[digest]=len(comps);im.save(P/f'amp_fleurie_composition_{len(comps):03}.png');comps.append(im)
 stop=events[ei+1] if ei+1<len(events) else period;duration=round(stop*1000/60)-round(t*1000/60);timeline.append({'game_frame':t,'duration_game_frames':stop-t,'duration_ms':duration,'png':f'amp_fleurie_composition_{unique[digest]:03}.png'});frames.append(im);durations.append(duration)
 if ei==0:first=ls;im.save(P/'COMPOSITION.png')
frames[0].save(P/'ANIMATION_COMPLETE.webp',save_all=True,append_images=frames[1:],duration=durations,loop=0,lossless=True)
# Geometric access test, excluding scenery but not requiring every traversable pixel to be sand.
walk=Image.new('L',(W,H));ImageDraw.Draw(walk).line([(228,0),(228,H-1)],fill=255,width=24);wm=np.array(walk)>0;assert not np.any((rockmask|treemask)&wm);walk.save(O/'PASSAGE_CENTRAL_CONTROLE.png')
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(P/'amp_plains_fleurie.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(n,im) in reversed(list(enumerate(first))):
  fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(frames[0]))
with zipfile.ZipFile(P/'amp_plains_fleurie.ora') as z:
 st=ET.fromstring(z.read('stack.xml')).find('stack');im=compose([(n.get('name'),load(io.BytesIO(z.read(n.get('src'))))) for n in reversed(st)]);assert np.array_equal(np.array(im),np.array(frames[0]))
manifest={'size':[W,H],'static_layers':[n for n,_ in static],'animation_groups':[{'name':g['name'],'native_frame_length_game_frames':g['tick'],'files':[f'amp_fleurie_{g["name"]}_{i:03}.png' for i in range(4)]} for g in groups],'timeline':timeline,'loop_game_frames':period,'loop_ms':sum(durations),'unique_composed_pngs':len(comps),'frame_events':len(events),'flower_sites':sites,'tree_sources':tree_proof,'references_commit':'1522c7a8b7a34d70078e11ed605b21d563b0dc51','source_notes':{'layout':'Amp_Plains_entrance_TD.png; gray rock components recolored, two dead-tree components removed','grass':'Vast_Steppe_Base.png crop240,264–288,312 tiled, native colors','sand':'native Metano sample; generated magenta path used only as geometry guide','trees':'existing PMD sprites reused in Halcyon Vast Steppe; no AI generation, no RGB recoloring or resizing; trunk alpha isolated from grass','blossoms':'new placement of actual Vast Steppe petals on the existing canopies, not a claim that these flowering variants are untouched official sprites','flowers':'native 4-step sequence0,1,0,2 with8/10/14 game-frame clocks'},'tests':{'opaque_all_compositions':True,'ora_exact':True,'central_24px_access_clear':True},'runtime_pmdo_validated':False}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Tree/flower reference board, at native resolution plus nearest-neighbor enlargement.
board=Image.new('RGBA',(480,230),(35,55,36,255));dd=ImageDraw.Draw(board)
for k in range(2):
 im=load(D/f'arbre_pmd_{k:02}.png');board.alpha_composite(im,(20+k*180,18));dd.text((20+k*180,145),f'Arbre PMD {k+1}',fill=(242,228,178))
for k,im in enumerate(flower):board.alpha_composite(im,(30+k*42,178))
board.save(O/'PLANCHE_SPRITES.png')
def uri(data,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(data).decode()
items=[{'name':'Composition animée · trois cadences natives','src':uri((P/'ANIMATION_COMPLETE.webp').read_bytes(),'image/webp')}]
for g in groups:
 ds=[round((i+1)*g['tick']*1000/60)-round(i*g['tick']*1000/60) for i in range(4)];b=io.BytesIO();g['images'][0].save(b,format='WEBP',save_all=True,append_images=g['images'][1:],duration=ds,loop=0,lossless=True);items.append({'name':g['name'],'src':uri(b.getvalue(),'image/webp')})
for name,im in static:items.append({'name':name,'src':uri(png(im))})
# Scrub the deduplicated composition states; the full native-clock order remains in the timeline and WebP.
stills=[uri(png(im)) for im in comps]
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Amp Plains · plaine fleurie</title><style>body{background:#1b2a20;color:#edf0d9;font:16px system-ui;max-width:1050px;margin:30px auto;padding:0 22px}h1{color:#f0d69a}p{line-height:1.65;max-width:950px}img{image-rendering:pixelated;max-width:100%;background:repeating-conic-gradient(#2a4435 0 25%,#3c5942 0 50%) 0/16px 16px}button,select{padding:10px;margin:8px;background:#344c37;border:1px solid #80906b;color:#f4ecd1}input{width:180px}</style><h1>Amp Plains · plaine verdoyante et fleurie</h1><p>Reliefs d’Amp Plains brun clair, herbe de Vast Steppe, sable de Métano et arbres PMD existants sur leurs calques. Floraison ajoutée avec les pétales natifs de Halcyon. Trois cadences de fleurs conservées :8,10 et14 frames de jeu. Pas de test PMDO/collisions.</p><select id="sel"></select><button id="play">Pause</button><input id="scrub" type="range" min="0" max="'''+str(len(comps)-1)+'''" value="0"><span id="label">Animation complète · 18,667 s</span><br><img id="view" alt="Amp Plains transformée en prairie fleurie"><h2>Sprites source détourés</h2><img alt="Arbres PMD et fleurs Vast Steppe" src="'''+uri(png(board))+'''"><p>Le curseur montre les états PNG dédupliqués, pas l’ordre temporel : la chronologie complète est dans manifest.json et dans l’animation.</p><script>const items='''+json.dumps(items)+',frames='+json.dumps(stills)+''';items.forEach((x,i)=>sel.add(new Option(x.name,i)));view.src=items[0].src;sel.onchange=()=>{view.src=items[sel.value].src;play.textContent='Pause'};play.onclick=()=>{if(play.textContent==='Pause'){view.src=frames[+scrub.value];play.textContent='Reprendre'}else{view.src=items[sel.value].src;play.textContent='Pause'}};scrub.oninput=()=>{view.src=frames[+scrub.value];play.textContent='Reprendre';label.textContent='État PNG '+(+scrub.value+1)+' / '+frames.length};</script>'''
(R/'apercu_amp_plains_fleurie_v1.html').write_text(html)
print('Terrain',W,H,'trees',tree_proof,'flowers',len(sites),'states',len(comps),'events',len(events),'loop',sum(durations))
