from pathlib import Path
import sys,json,math,base64,io
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/northern_calques_v1';C=R/'renders/crooked_statique_v2';L=R/'renders/spring_pulsation_v2';N=Image.Resampling.NEAREST
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night

def load(p):return Image.open(p).convert('RGBA')
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def blank(size):return Image.new('RGBA',size)
def key(im):
 a=np.array(im);r,g,b=[a[:,:,i].astype(int) for i in range(3)];a[(r>35)&(b>35)&(g<120)&(r>g*1.8)&(b>g*1.8)]=0;return Image.fromarray(a)
def shift(im,xy,size=None):
 out=blank(size or im.size);out.alpha_composite(im,xy);return out
# 1. A clean analytic beam. Its RGB field never moves; only alpha pulses.
V=R/'renders/soleil_spring_v1/spring';T=R/'renders/spring_escalier_v1/calques';base=load(V/'01_decor.png');relief=load(T/'02_petit_relief.png');stairs=load(T/'03_escalier.png');static=Image.alpha_composite(Image.alpha_composite(base,relief),stairs);save(static,L/'01_decor_escalier.png')
y,x=np.mgrid[:600,:600];t=np.clip((x-275)/49,0,1);spectrum=np.stack([.5+.5*np.cos(2*math.pi*(t-j/3)) for j in range(3)],2);colors=(255*(.35+.65*spectrum)).astype('uint8');shape=np.minimum(np.clip((x-274)/3,0,1),np.clip((325-x)/3,0,1))*np.clip((201-y)/15,0,1);shape[(x<275)|(x>=325)|(y>=201)]=0
# Separate clean foundation removes the old textured splash pixels INSIDE the beam only.
foundation=np.zeros((600,600,4),dtype='uint8');v=np.clip(y/190,0,1)
foundation[:,:,:3]=(np.array([42,119,110])[None,None,:]*(1-v[:,:,None])+np.array([91,236,220])[None,None,:]*v[:,:,None]).astype('uint8');foundation[:,:,3]=np.round(shape*255).astype('uint8');foundation[foundation[:,:,3]==0]=0;cleanbeam=Image.fromarray(foundation);save(cleanbeam,L/'02_colonne_nettoyee.png')
lightframes=[];scene_frames=[]
for f in range(78):
 power=.18+.48*(1-math.cos(2*math.pi*f/78))/2;a=np.zeros((600,600,4),dtype='uint8');a[:,:,:3]=colors;a[:,:,3]=np.round(255*power*shape).astype('uint8');a[a[:,:,3]==0]=0;beam=Image.fromarray(a);lightframes.append(beam);save(beam,L/'colonne'/f'{f:02}.png')
 original=static.copy();nf=f//2
 for n,k in [('02_cycle_3',3),('03_cycle_13',13)]:original.alpha_composite(load(V/n/f'{nf%k:02}.png'))
 im=original.copy();im.alpha_composite(cleanbeam);im.alpha_composite(beam);scene_frames.append(im)
 assert np.array_equal(np.array(im)[shape==0],np.array(original)[shape==0])
save(scene_frames[39],L/'composition.png');scene_frames[0].save(L/'animation.webp',save_all=True,append_images=scene_frames[1:],duration=[83,83,84]*26,loop=0,lossless=True)
sheet=blank((1000,1680))
for f,im in enumerate(lightframes):sheet.alpha_composite(im.crop((250,0,350,210)),(f%10*100,f//10*210))
save(sheet,L/'planche_pulsation_78.png')
# 2. Crooked Cavern is STATIC, 3 layouts, no particles, no animation files.
CV=R/'renders/crooked_verdure_v1/calques';old=[load(CV/n) for n in ['01_sol_herbe_chemin.png','02_paroi_grise.png','03_rochers_gris.png','04_vegetation.png']];caves=[]
for idx,(title,dx,ox) in enumerate([('Entree centrale',0,0),('Entree a gauche',-24,12),('Entree a droite',24,-12)],1):
 layers={};floor=old[0].copy();floor.alpha_composite(old[0],(dx,0));layers['01_sol']=floor
 wall=shift(old[1],(dx,0))
 if dx<0:wall.alpha_composite(old[1].crop((296,0,320,240)),(296,0))
 elif dx>0:wall.alpha_composite(old[1].crop((0,0,24,240)),(0,0))
 layers['02_paroi']=wall;layers['03_rochers']=shift(old[2],(ox,-4 if idx==2 else 0));layers['04_vegetation']=shift(old[3],(-ox,0));comp=blank((320,240))
 for n,im in layers.items():save(im,C/f'{idx:02}'/(n+'.png'));comp.alpha_composite(im)
 save(comp,C/f'{idx:02}'/'composition.png');caves.append({'id':f'{idx:02}','title':title,'layers':[n+'.png' for n in layers],'entrance_shift_x':dx})
(C/'manifest.json').write_text(json.dumps({'animated':False,'layouts':caves,'note':'Paroi canonique grise du pack precedent, disposition modifiee sans particules.'},indent=2))
# 3. Northern: split the regenerated terrain into disjoint semantic depth regions.
S=(456,432);raw=key(load(O/'bruts/terrain_northern.png')).resize(S,N);a=np.array(raw);h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w]
def polygon(points):
 m=Image.new('L',S);ImageDraw.Draw(m).polygon([(round(px*w),round(py*h)) for px,py in points],fill=255);return np.array(m)>0
floor_mask=polygon([(.327,.337),(.652,.337),(.692,.38),(.747,.438),(.743,.608),(.675,.668),(.333,.668),(.263,.615),(.245,.442),(.287,.387)])
front_mask=polygon([(0,.18),(.09,.27),(.245,.44),(.37,1),(0,1)])|polygon([(1,.17),(.9,.27),(.75,.44),(.63,1),(1,1)])
front_mask&=~floor_mask
socle=(yy>=int(.668*h))&(~front_mask)&(~floor_mask)
rear=~(floor_mask|front_mask|socle)
masks={'05_rochers_arriere':rear,'06_arene_centrale':floor_mask,'07_socle_arene':socle,'08_falaises_avant':front_mask}
# Alpha strata are disjoint and recompose the original keyed terrain exactly.
terrain={}
for n,m in masks.items():
 aa=a.copy();aa[~m]=0;terrain[n]=Image.fromarray(aa)
check=blank(S)
for im in terrain.values():check.alpha_composite(im)
assert np.array_equal(np.array(check),a)
save(raw,O/'terrain_detoure.png');save(Image.fromarray((floor_mask*255).astype('uint8')),O/'masque_arene.png')
# Terrain floor must include the exact canvas center, not sit in a corner.
assert floor_mask[h//2,w//2] and a[h//2,w//2,3]==255
moon=load(R/'renders/references_calques_v1/nuit/04_lune_halo.png').crop((650,65,850,265)).resize((76,76),N)
mist=key(load(O/'bruts/brume.png'));mist=mist.crop(mist.getbbox()).resize((456,100),N);ma=np.array(mist);ma[:,:,3]=(ma[:,:,3]*.18).astype('uint8');mist=Image.fromarray(ma)
scenes=[]
for mode in ['jour','nuit']:
 # Fine gradient without embedded stars or sun.
 top=np.array([70,140,204] if mode=='jour' else [10,20,57]);bottom=np.array([205,229,232] if mode=='jour' else [42,62,109]);sky=np.zeros((h,w,4),dtype='uint8');u=np.linspace(0,1,h)[:,None,None];sky[:,:,:3]=(top[None,None,:]*(1-u)+bottom[None,None,:]*u);sky[:,:,3]=255;layers={'01_ciel':Image.fromarray(sky)}
 stars=blank(S);d=ImageDraw.Draw(stars)
 if mode=='nuit':
  rng=np.random.default_rng(75116)
  for sx,sy in zip(rng.integers(3,w-3,100),rng.integers(3,140,100)):d.point((int(sx),int(sy)),fill=(218,231,255,210))
 layers['02_etoiles']=stars;astro=blank(S)
 if mode=='nuit':astro.alpha_composite(moon,(197,34))
 layers['03_lune_halo']=astro
 abyss=blank(S);ar=np.zeros((h,w,4),dtype='uint8');ar[:,:,:3]=[7,12,24] if mode=='nuit' else [21,29,37];ar[:,:,3]=np.clip((yy-150)/180*255,0,255).astype('uint8');layers['04_profondeur']=Image.fromarray(ar)
 for n,im in terrain.items():layers[n]=night(im) if mode=='nuit' else im
 overlay=blank(S);overlay.alpha_composite(mist,(0,265));overlay.alpha_composite(mist.resize((370,60),N),(45,110));layers['09_brume_overlay']=overlay
 comp=blank(S)
 for n,im in layers.items():save(im,O/mode/(n+'.png'));comp.alpha_composite(im)
 save(comp,O/mode/'composition.png');scenes.append({'id':mode,'layers':[n+'.png' for n in layers]})
(O/'manifest.json').write_text(json.dumps({'canvas':list(S),'reference_commit':'00cb874','reference_file':'Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Dungeon Boss Rooms - Northern Range.png','terrain':'Nouvelle generation guidee par la reference, pas des tuiles natives identiques','arena_center':[w//2,h//2],'scenes':scenes,'overlay':'Brume statique tres legere separee du ciel et du terrain','night':'Filtre Abyss exact sur terrain','animated':False},indent=2))
print('Spring pulse78; 3 STATIC caves; Northern day/night in 9 layers')
