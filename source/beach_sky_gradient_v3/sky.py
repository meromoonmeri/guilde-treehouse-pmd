"""Three sky treatments. Native pixels for day/night; documented JPEG adaptation at dusk."""
from pathlib import Path
from collections import Counter
import sys,json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'source/cote_v5_expeditions'))
from audit_references import tiles,straight

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def native_rows(bank,limit):
 size,cells,_=tiles(S/'references'/bank);atlas=Image.new('RGBA',((max(x for x,y in cells)+1)*size,(max(y for x,y in cells)+1)*size))
 for (x,y),tile in cells.items():atlas.paste(straight(tile),(x*size,y*size))
 a=np.array(atlas);out=np.empty((112,512,4),np.uint8);rows=[]
 for y in range(112):
  sy=min(y,108) if limit==180 else y
  candidates=[x for x in range(a.shape[1]-7) if np.all(a[sy,x:x+8,3]==255) and np.all(a[sy,x:x+8,0]<limit)]
  assert candidates,(bank,y)
  patterns=Counter(a[sy,x:x+8].tobytes() for x in candidates);pattern=patterns.most_common(1)[0][0];x=next(x for x in candidates if a[sy,x:x+8].tobytes()==pattern)
  out[y]=np.tile(a[sy,x:x+8],(64,1));rows.append([x,sy,8])
 return Image.fromarray(out),rows,a

def build(O):
 (O/'fonds').mkdir(parents=True,exist_ok=True);provenance={'moon':False,'native_resampling':False,'dusk_native_certified':False,'modes':{}};assets={}
 skyD,rowsD,day=native_rows('Habitat_SharpedoBluff_Day_Rock_and_Sky.tile',180)
 skyN,rowsN,night=native_rows('GuildOutsideNight.tile',30)
 # The supplied night GIF and decoded bank match exactly over the unobstructed top 70 rows.
 assert np.array_equal(np.array(Image.open(R/'IMG_4900.gif').convert('RGBA'))[:70],night[:70])
 jpeg=Image.open(R/'IMG_4888.jpeg').convert('RGB').resize((384,240),Image.Resampling.NEAREST);j=np.array(jpeg);ys=[0,16,32,48,64,80,96,109];anchors=[]
 for y in ys:
  row=j[y,240:] if y>=80 else j[y];q=(row//4)*4;winner=np.array(Counter(map(tuple,q)).most_common(1)[0][0]);anchors.append(np.median(row[np.all(q==winner,axis=1)],axis=0).astype(int).tolist())
 ramp=np.stack([np.interp(np.arange(112),ys,np.array(anchors)[:,c]) for c in range(3)],axis=1).round().astype('uint8');skyC=Image.fromarray(np.concatenate([np.tile(ramp[:,None,:],(1,512,1)),np.full((112,512,1),255,np.uint8)],axis=2))
 for mode,sky,rows,bank in [('jour',skyD,rowsD,'Habitat_SharpedoBluff_Day_Rock_and_Sky.tile'),('crepuscule',skyC,None,None),('nuit',skyN,rowsN,'GuildOutsideNight.tile')]:
  file='fonds/BeachSkyV3_ciel_'+mode+'.png';sky.save(O/file)
  stars=np.zeros((112,512,4),np.uint8)
  if mode=='nuit':
   src=night[:112];mask=(src[:,:,0]>140)&(src[:,:,1]>150)&(src[:,:,2]>185)
   mask[68:,128:352]=False # statue/flames excluded, not mistaken for stars
   stars[:,16:496][mask]=src[mask]
  elif mode=='crepuscule':
   src=j[:32];mask=(src[:,:,0]>215)&(src[:,:,1]>200)&(src[:,:,2]>215)
   rgba=np.dstack([src,np.full(src.shape[:2],255,np.uint8)]);stars[:32,64:448][mask]=rgba[mask]
  star='fonds/BeachSkyV3_etoiles_'+mode+'.png';Image.fromarray(stars).save(O/star)
  if mode=='crepuscule':
   a=np.array(Image.open(R/'renders/beach_network_v1/fonds/BeachNetwork_nuages_jour_wrap.png').convert('RGBA'));lum=a[:,:,:3].mean(axis=2)/255;pal=np.array([[166,92,154],[225,139,176],[255,228,158]])
   for c in range(3):a[:,:,c]=np.interp(lum,[.25,.7,1],pal[:,c]).round().clip(0,255).astype('uint8')
   a[a[:,:,3]==0]=0;cloud='fonds/BeachSkyV3_nuages_crepuscule_wrap.png';Image.fromarray(a).save(O/cloud)
  else:cloud='../beach_network_v1/fonds/BeachNetwork_nuages_'+mode+'_wrap.png'
  assets[mode]={'sky':file,'cloud':cloud,'stars':star,'horizon':'#'+''.join(f'{v:02x}' for v in np.array(sky)[-1,0,:3]),'size':[512,112],'cloud_period_ms':64000}
  provenance['modes'][mode]={'sky':file,'sky_sha256':sha(O/file),'method':'native 8-pixel row motifs repeated horizontally, no colour change or scaling' if bank else 'lavender/coral gradient reconstructed from the supplied JPEG; not a certified native sprite','row_sources':rows,'native_bank':bank,'native_bank_sha256':sha(S/'references'/bank) if bank else None}
 provenance['native_repository']={'repo':'Minemaker0430/ExplorersOfSkyOrigins','commit':'4e7422acc263886198113a8256677766e4244228','paths':['Content/Tile/Habitat_SharpedoBluff_Day_Rock_and_Sky.tile','Content/Tile/GuildOutsideNight.tile']}
 provenance['night_reference']={'file':'IMG_4900.gif','sha256':sha(R/'IMG_4900.gif'),'top_70_rows_equal_native_bank':True}
 provenance['dusk_reference']={'file':'IMG_4888.jpeg','sha256':sha(R/'IMG_4888.jpeg'),'sample_size':[384,240],'sampling':'nearest, JPEG reference adaptation only','anchor_rows':ys,'anchor_rgb':anchors}
 provenance['clouds']='Existing generated small cloud silhouettes retained; dusk recoloured only. No claim of native cloud pixels. 512 px / 8 px per second = 64 s exact cyclic translation.'
 (O/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return assets
