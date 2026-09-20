"""Independent decoded-file checks, no renderer/game claim."""
from pathlib import Path
import sys, json, re, hashlib, io, zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/ice_arena_northern_sky_v5';P='NorthernSkyV5'
sys.path.insert(0,str(R/'source'));import ciels_valides as climate

def load(p):return Image.open(p).convert('RGBA')
def light(rgb):
 a=rgb.max(2).astype(np.uint16);out=np.zeros((*a.shape,4),np.uint8)
 out[:,:,:3]=np.minimum(255,np.rint(rgb.astype(float)*255/np.maximum(a[:,:,None],1))).astype(np.uint8);out[:,:,3]=a;out[a==0]=0;return out

def main():
 checks=[]
 def check(label,value):
  assert value,label
  checks.append({'check':label,'status':'PASS'})
 sky=load(O/'layers'/f'{P}_Sky.png');terrain=load(O/'layers'/f'{P}_Terrain.png');cloud=load(O/'layers'/f'{P}_Clouds_phase0.png')
 auroras=[load(O/'aurora_frames'/f'{P}_Aurora_{i:03}.png') for i in range(192)]
 stars=[load(O/'star_frames'/f'{P}_Stars_{i:02}.png') for i in range(64)]
 check('192 distinct aurora PNG samples',len({im.tobytes() for im in auroras})==192)
 def composition(f):
  im=sky.copy();im.alpha_composite(stars[f//3]);im.alpha_composite(auroras[f]);im.alpha_composite(cloud);im.alpha_composite(terrain);return im
 check('Initial composition matches layers',composition(0).tobytes()==load(O/'composition.png').tobytes())
 def compare(movie_name,expected,fps):
  movie=Image.open(O/movie_name);t=0;seen=[]
  for f in range(movie.n_frames):
   movie.seek(f);movie.load();idx=round(t*fps/1000);actual=np.array(movie.convert('RGBA'));wanted=np.array(expected(idx))
   mask=(wanted[:,:,3]>0)|(actual[:,:,3]>0)
   assert np.array_equal(actual[mask],wanted[mask]),(movie_name,f,idx)
   seen.append(idx);t+=movie.info['duration']
  check('All decoded frames equal PNG references: '+movie_name,seen==list(range(len(seen))) and t==6400 and movie.info['loop']==0)
  return len(seen)
 count=compare('composition_loop.webp',composition,30)+compare('aurora_loop.webp',lambda f:auroras[f],30)+compare('stars_loop.webp',lambda f:stars[f],10)
 check('All 448 encoded frames decoded and checked',count==448)
 # A warped midpoint must differ from a fixed-coordinate dissolve for EVERY pair.
 # Rebuild the premultiplied key light from the same quantization description.
 raw=Image.open(O/'bruts/aurora_six_poses.png').convert('RGB');manifest=json.loads((O/'manifest.json').read_text())
 poses=[raw.crop(box).resize((512,320),Image.Resampling.NEAREST) for box in manifest['aurora']['crops']]
 sheet=Image.new('RGB',(512,1920))
 for i,im in enumerate(poses):sheet.paste(im,(0,i*320))
 palette=sheet.quantize(colors=64,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);keys=[]
 for im in poses:
  a=np.array(im.quantize(palette=palette,dither=Image.Dither.NONE).convert('RGB'));a[a.max(2)<=10]=0;keys.append(a)
 for i in range(6):
  simple=light(np.rint((keys[i].astype(float)+keys[(i+1)%6])/2).astype(np.uint8))
  check(f'Pair {i} midpoint is spatially warped, not a mere dissolve',not np.array_equal(simple,np.array(auroras[i*32+16])))
 with zipfile.ZipFile(O/f'{P}_layers.ora') as z:
  root=ET.fromstring(z.read('stack.xml'));im=Image.new('RGBA',(512,864))
  for node in reversed(list(root.find('stack'))):im.alpha_composite(Image.open(io.BytesIO(z.read(node.attrib['src']))).convert('RGBA'),(int(node.attrib['x']),int(node.attrib['y'])))
  check('Actual ORA ZIP layers and merged image agree',im.tobytes()==load(O/'composition.png').tobytes()==Image.open(io.BytesIO(z.read('mergedimage.png'))).tobytes())
 html=(O/'index.html').read_text();data=json.loads(re.search(r'const D=(.+?);',html).group(1))
 paths=[data[k] for k in ['terrain','sky','clouds','aurora_movie','stars_movie']]+re.findall(r'(?:href|src)="([^"]+)"',html)
 check('All literal viewer image/download paths exist',all((O/p).is_file() for p in paths))
 check('No remote/localhost dependencies in browser code','localhost' not in html and '127.0.0.1' not in html and 'https://' not in html and '__DATA__' not in html)
 strip=load(O/'layers'/f'{P}_CloudStrip.png');source=np.array(climate.clouds('nuit'));source[:,:,3]=np.rint(source[:,:,3].astype(float)*.30).astype(np.uint8);source[source[:,:,3]==0]=0
 check('Six approved cloud families unscaled; only approved night grade and alpha',strip.crop((0,224,1440,432)).tobytes()==Image.fromarray(source).tobytes())
 # Existing versions are validated against their published inventory when present.
 for name in ['ice_arena_northern_sky_v4','ice_arena_aurora_coherent_v3']:
  changes=__import__('subprocess').check_output(['git','diff','68872140','--name-only','--',f'renders/{name}',f'source/{name}'],cwd=R,text=True)
  check('Published old delivery unchanged: '+name,not changes.strip())
 inventory=O/'files.sha256.json'
 if inventory.exists():
  entries=json.loads(inventory.read_text())
  check('Recorded source/export hashes unchanged',all(hashlib.sha256((R/p).read_bytes()).hexdigest()==digest for p,digest in entries.items()))
 report={'checks':checks,'count':len(checks),'decoded_frames':count,'status':'PASS','not_a_game_test':True}
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(f'{len(checks)} independent checks PASS; {count} decoded frames checked.')
if __name__=='__main__':main()
