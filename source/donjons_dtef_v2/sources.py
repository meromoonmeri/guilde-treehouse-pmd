from pathlib import Path
import json,subprocess,concurrent.futures,hashlib
P=Path(__file__).parent/'references';PIN='3e767571f9dd94270b848b3a73de9bec2553a2eb0'
SOURCES={'foret':'treeshroud_forest_1','jungle':'southern_jungle','marais':'murky_forest','roche':'southern_cavern_1','cristal':'crystal_cave_1','glace':'vast_ice_mountain','volcan':'dark_crater','desert':'quicksand_cave','ruines':'sealed_ruin','vapeur':'steam_cave','illuminant_reference':'sky_peak_4th_pass'}
def get(path):
 p=P/'DumpAsset'/path;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():p.write_bytes(subprocess.check_output(['gh','api',f'repos/audinowho/DumpAsset/contents/{path}?ref={PIN}','-H','Accept: application/vnd.github.raw+json']))
 return p
if __name__=='__main__':
 paths=[f'Data/AutoTile/{s}_{t}.json' for s in SOURCES.values() for t in ['wall','secondary','floor']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:files=list(ex.map(get,paths))
 sheets=set()
 def walk(o):
  if isinstance(o,dict):
   if o.get('Sheet'):sheets.add(o['Sheet'])
   for v in o.values():walk(v)
  elif isinstance(o,list):
   for v in o:walk(v)
 for p in files:walk(json.loads(p.read_text(encoding='utf-8-sig')))
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:files+=list(ex.map(get,[f'Content/Tile/{s}.tile' for s in sorted(sheets)]))
 (P/'provenance.json').write_text(json.dumps([dict(repo='audinowho/DumpAsset',commit=PIN,path=str(p.relative_to(P/'DumpAsset')),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],indent=2));print('Fetched',len(files),'files;',sheets)
