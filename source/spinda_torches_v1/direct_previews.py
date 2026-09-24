"""Direct, lossless animated WebP + PNG sheet: no HTML or script needed to view."""
from pathlib import Path
import json,io,zipfile,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];O=R/'renders/spinda_torches_v1'
def resource(file):
 p=O/file
 if p.exists():return p.read_bytes()
 with zipfile.ZipFile(O/'Spinda_torches_8angles_animees.zip') as z:return z.read(file)
def image(file):return Image.open(io.BytesIO(resource(file))).convert('RGBA')
def build():
 m=json.loads((O/'manifest.json').read_text());dest=O/'apercus_directs';dest.mkdir(exist_ok=True);frames=[]
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',10)
 supports=[image(o['support']['jour']) for o in m['objects']];lights=[image(o['light_strip']) for o in m['objects']];fire=[image(f['file']) for f in m['flame']['frames']]
 for n in range(16):
  out=Image.new('RGBA',(416,224),'#211b23');d=ImageDraw.Draw(out)
  for j,o in enumerate(m['objects']):
   x=(j%4)*104+4;y=(j//4)*112+16
   out.alpha_composite(lights[j].crop((n*96,0,(n+1)*96,96)),(x,y));out.alpha_composite(supports[j],(x+16,y+4));out.alpha_composite(fire[n%4],(x+32,y+8))
   d.text((x+4,y-13),{'NW':'NO','SW':'SO','W':'O'}.get(o['id'],o['id']),font=font,fill='#eac795')
  frames.append(out.resize((832,448),Image.Resampling.NEAREST))
 png=dest/'Torches_8_angles.png';webp=dest/'Torches_8_angles_animees.webp';frames[0].save(png,optimize=True);frames[0].save(webp,save_all=True,append_images=frames[1:],lossless=True,duration=100,loop=0,minimize_size=True)
 im=Image.open(webp);assert im.n_frames==16 and im.info['loop']==0;durations=[];hashes=[]
 for i,f in enumerate(frames):
  im.seek(i);decoded=im.convert('RGBA');assert decoded.tobytes()==f.tobytes();durations.append(im.info['duration']);hashes.append(hashlib.sha256(decoded.tobytes()).hexdigest())
 assert durations==[100]*16 and len(set(hashes))==16;assert Image.open(png).convert('RGBA').tobytes()==frames[0].tobytes()
 report={'pass':True,'orientations':8,'size':[832,448],'webp_frames':16,'durations_ms':durations,'period_ms':1600,'loop':0,'lossless_all_frames_verified':True,'png_equals_first_frame':True,'preview_scale':2,'transparent_import_layers':'Original ZIP, unchanged; these previews use a dark background.'}
 (dest/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS direct previews: 8 angles,16 lossless frames,100ms each,loop,PNG exact first frame')
if __name__=='__main__':build()
