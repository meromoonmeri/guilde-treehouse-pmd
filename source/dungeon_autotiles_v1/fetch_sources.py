from pathlib import Path
import subprocess,concurrent.futures,json,sys
from PIL import Image
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';pin=(P/'assets_commit.txt').read_text().strip();sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight
paths=['Content/Tile/AppleWoods.tile','Content/Tile/BeachCave.tile']+[f'Data/AutoTile/{s}_{t}.json' for s in ['apple_woods','beach_cave'] for t in ['wall','secondary','floor']]
def get(x):
 p=P/'assets'/Path(x).name
 if not p.exists():p.write_bytes(subprocess.check_output(['gh','api',f'repos/audinowho/DumpAsset/contents/{x}?ref={pin}','-H','Accept: application/vnd.github.raw+json']))
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(get,paths))
for name in ['AppleWoods','BeachCave']:
 size,b,_=tiles(P/'assets'/(name+'.tile'));o=Image.new('RGBA',((max(x for x,y in b)+1)*size,(max(y for x,y in b)+1)*size))
 for (x,y),im in b.items():o.alpha_composite(straight(im),(x*size,y*size))
 o.save(P/'assets'/(name+'.png'));print(name,size,o.size)
for s in ['apple_woods','beach_cave']:
 for t in ['wall','secondary','floor']:
  o=json.loads((P/'assets'/f'{s}_{t}.json').read_text(encoding='utf-8-sig'))['Object']['Tiles'];fields=[v for k,v in o.items() if k.startswith('Tilex')];print(s,t,len(fields),[(len(l['Frames']),l['FrameLength']) for l in fields[0][0]])
