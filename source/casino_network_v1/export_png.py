"""Export aligned PNG layers for the whole network or one 512px sector."""
from pathlib import Path
import argparse,json
from PIL import Image

def export(root,out,sector='all',frames=False):
 data=json.loads((root/'manifest.json').read_text());rect=[0,0,1024,1024] if sector=='all' else next(r['rect'] for r in data['rooms'] if r['id']==sector)
 x,y,w,h=rect;count=0;manifest=[];comp=Image.new('RGBA',(w,h))
 for i,l in enumerate(data['layers'],1):
  files=l.get('frames',[l.get('file')]);positions=l['position']
  for k,file in enumerate(files if frames else files[:1]):
   im=Image.new('RGBA',(w,h));im.alpha_composite(Image.open(root/file).convert('RGBA'),(positions[0]-x,positions[1]-y))
   if im.getbbox() is None:continue
   name=f"Casino_{sector}_{i:02d}_{l['id']}"+(f'_pose{k:02d}' if 'frames' in l else '')+'.png';out.mkdir(parents=True,exist_ok=True);im.save(out/name,optimize=True);count+=1
   manifest.append({'file':name,'layer':l['id'],'phase':k if 'frames' in l else None,'origin':[0,0]})
   if k==0:comp.alpha_composite(im)
 comp.save(out/f'Casino_{sector}_composition.png',optimize=True);count+=1
 (out/'calques.json').write_text(json.dumps({'sector':sector,'size':[w,h],'layers':manifest,'frame_ms':100,'frames':4,'runtime_PMDO':'NOT TESTED'},ensure_ascii=False,indent=2)+'\n')
 return count

if __name__=='__main__':
 here=Path(__file__).resolve().parent;default=here if (here/'manifest.json').exists() else here.parents[1]/'renders/casino_network_v1'
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=default);parser.add_argument('--out',type=Path);parser.add_argument('--sector',choices=['all','scene','salon','accueil','jeux'],default='all');parser.add_argument('--frames',action='store_true');args=parser.parse_args()
 print('Exported',export(args.root,args.out or args.root/'export_png'/args.sector,args.sector,args.frames),'PNG files')
