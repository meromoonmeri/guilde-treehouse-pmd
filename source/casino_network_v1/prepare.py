"""Generated casino assets + exact reconstruction of the native Ledian fire cycle."""
from pathlib import Path
import sys,json,hashlib,math,io,importlib.util
import numpy as np
from scipy import ndimage as nd
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/casino_network_v1';SRC=ROOT/'source/ledian_dojo_v1/references'
sys.path.insert(0,str(ROOT/'source/cote_v5_expeditions'))
from audit_references import tiles,straight

_spec=importlib.util.spec_from_file_location('casino_raw_archive',Path(__file__).parent/'archive.py');_arc=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_arc)
def sha(p):return hashlib.sha256(_arc.data(p)).hexdigest()
def rgba(p):return np.array(Image.open(io.BytesIO(_arc.data(p))).convert('RGBA'))
def save(a,p):
 p.parent.mkdir(parents=True,exist_ok=True);im=Image.fromarray(a) if isinstance(a,np.ndarray) else a
 im.save(p,optimize=True)
def keyed(a):
 a=a.copy();r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0);key=(r>g*1.4+25)&(b>g*1.4+25)&(b>r*.65)&(r>70)&(b>70);a[key]=0
 return a

def raw_path(name):
 p=OUT/'bruts'/f'{name}.webp'
 return p if p.exists() or any(r['path']==str(p.relative_to(ROOT)) for r in _arc.entries()) else OUT/'bruts'/f'{name}.png'

def archive_raws():
 p=OUT/'bruts';records=json.loads((p/'provenance.json').read_text()) if (p/'provenance.json').exists() else []
 for path in sorted(p.glob('*.png')):
  im=Image.open(path).convert('RGBA');target=path.with_suffix('.webp');im.save(target,lossless=True,method=6,exact=True)
  assert im.tobytes()==Image.open(target).convert('RGBA').tobytes()
  records.append({'file':target.name,'original_png_sha256':sha(path),'webp_sha256':sha(target),'rgba_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'size':list(im.size),'lossless_pixels':True});path.unlink()
 (p/'provenance.json').write_text(json.dumps(records,indent=2)+'\n')

def native_fire():
 o=json.loads((SRC/'ledian_dojo.rsground').read_text(encoding='utf-8-sig'))['Object'];ts,bank,_=tiles(SRC/'Ledian_Dojo_Animated.tile');assert ts==8
 grid=o['Layers'][1]['Tiles'];frames=[];lengths=set();source_tracks=[]
 for k in range(4):
  im=Image.new('RGBA',(32,64))
  for x in range(14,18):
   for y in range(11,19):
    for track in grid[x][y]['Layers']:
     if len(track['Frames'])==4:
      lengths.add(track['FrameLength'])
      if k==0:source_tracks.append({'map_tile':[x,y],'track':track})
      f=track['Frames'][k]
      if f['Sheet']:
       assert f['Sheet']=='Ledian_Dojo_Animated';v=f['TexLoc'];im.alpha_composite(straight(bank[v['X'],v['Y']]),((x-14)*8,(y-11)*8))
  frames.append(np.array(im));save(im,OUT/'animations'/f'Casino_brasero_natif_{k:02d}.png')
 assert lengths=={6};assert all(np.array_equal(frames[0][40:],f[40:]) for f in frames)
 body=frames[0].copy();body[:40]=0;save(body,OUT/'objets/brasero_support.png')
 for k,a in enumerate(frames):save(a[:40],OUT/'animations'/f'Casino_flamme_native_{k:02d}.png')
 report={'source_commit':(SRC/'halcyon_commit.txt').read_text().strip(),'source_map':'source/ledian_dojo_v1/references/ledian_dojo.rsground','source_map_sha256':sha(SRC/'ledian_dojo.rsground'),'source_bank':'source/ledian_dojo_v1/references/Ledian_Dojo_Animated.tile','source_bank_sha256':sha(SRC/'Ledian_Dojo_Animated.tile'),'layer':1,'instance_tile_rect':[14,11,18,19],'sprite_size':[32,64],'flame_size':[32,40],'support_split_row':40,'frames':4,'frame_length_ticks':6,'viewer_tick_rate':60,'frame_ms':100,'period_ms':400,'source_tracks':source_tracks,'native_pixel_unscaled':True}
 (OUT/'flammes_provenance.json').write_text(json.dumps(report,indent=2)+'\n')
 return report

def objects():
 meta={}
 for name,width in [('estrade',208),('rideaux',208),('kiosque',112),('table_jeu',112),('fourneau',104)]:
  a=keyed(rgba(raw_path(name)));mask=a[:,:,3]>0
  if name=='fourneau':
   # Model emitted three bodies despite requesting one: keep the complete middle one.
   labels,_=nd.label(mask);boxes=nd.find_objects(labels);candidates=[]
   for i,box in enumerate(boxes,1):
    if box is None:continue
    ys,xs=box;area=int((labels[box]==i).sum())
    if area>20000 and xs.start>5 and xs.stop<a.shape[1]-5:candidates.append((abs((xs.start+xs.stop)/2-a.shape[1]/2),i,box))
   _,ident,box=min(candidates);keep=labels==ident;a[~keep]=0
  im=Image.fromarray(a);box=im.getbbox();assert box;im=im.crop(box);scale=width/im.width;size=(width,round(im.height*scale));im=im.resize(size,Image.Resampling.NEAREST)
  canvas=Image.new('RGBA',(math.ceil(size[0]/8)*8,math.ceil(size[1]/8)*8));canvas.alpha_composite(im);save(canvas,OUT/'objets'/f'{name}.png')
  meta[name]={'file':f'objets/{name}.png','generated':True,'raw':raw_path(name).name,'crop':list(box),'uniform_scale':scale,'content_size':list(size),'size':list(canvas.size)}
 # Exact complete Metano object, no recolouring/rescaling.
 p=ROOT/'source/ledian_casino_v1/references/KrowBank_structure_native.png';save(Image.open(p).convert('RGBA'),OUT/'objets/krow_bank_natif.png');meta['krow_bank_natif']={'file':'objets/krow_bank_natif.png','generated':False,'source':str(p.relative_to(ROOT)),'sha256':sha(p),'size':[104,96]}
 rug=Image.open(SRC/'Ledian_Dojo_Objects.png').convert('RGBA').crop((176,136,232,176));save(rug,OUT/'objets/tapis_source_natif.png')
 meta['tapis_source']={'file':'objets/tapis_source_natif.png','source':'source/ledian_dojo_v1/references/Ledian_Dojo_Objects.png','crop':[176,136,232,176],'size':[56,40],'usage':'Native 8px patches repeated in a nine-slice rug; never stretched.'}
 (OUT/'objets/manifest.json').write_text(json.dumps(meta,indent=2)+'\n');return meta

def main():
 OUT.mkdir(parents=True,exist_ok=True);archive_raws();native_fire();objects()
 terrain=Image.fromarray(keyed(rgba(raw_path('terrain_corrige'))));assert terrain.size==(1024,1024)
 terrain.save(OUT/'terrain_vide.webp',lossless=True,method=6,exact=True)
 print('Prepared generated furniture, native Krow Bank, native rug, exact four-frame Ledian fire and unchanged 1024px generated terrain.')
if __name__=='__main__':main()
