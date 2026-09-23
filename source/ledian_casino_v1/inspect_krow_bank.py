"""Inspect Krow Bank's actual Halcyon object banks, without restyling native pixels."""
from pathlib import Path
import json,sys,hashlib,subprocess
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];P=Path(__file__).parent/'references'
sys.path.insert(0,str(ROOT/'source/cote_v5_expeditions'))
from audit_references import tiles,straight
PIN='da6c2130d641507447e6386a5e47a296e8cb4c71'
BANKS={
 'Metano_Town_Objects':ROOT/'source/amp_plains_fleurie_v1/references/Metano_Town_Objects.tile',
 'Metano_Town_Objects_Over':P/'Metano_Town_Objects_Over.tile',
 'Metano_Town_Objects_Under':P/'Metano_Town_Objects_Under.tile'}

def main():
 P.mkdir(parents=True,exist_ok=True)
 tree=json.loads(subprocess.check_output(['gh','api',f'repos/Palikadude/Halcyon/git/trees/{PIN}?recursive=1']))
 indexed={x['path']:x for x in tree['tree']};sources={};exports={}
 for name,path in BANKS.items():
  remote=f'Content/Tile/{name}.tile'
  if not path.exists():path.write_bytes(subprocess.check_output(['gh','api',f'repos/Palikadude/Halcyon/contents/{remote}?ref={PIN}','-H','Accept: application/vnd.github.raw+json']))
  raw=path.read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert blob==indexed[remote]['sha']
  ts,bank,_=tiles(path);assert ts==8
  sources[name]={'local':str(path.relative_to(ROOT)),'remote':remote,'git_blob':blob,'sha256':hashlib.sha256(raw).hexdigest(),'cell_px':ts}
  if name.endswith('_Under'):continue
  crop=Image.new('RGBA',(104,96))
  for y in range(928,1024,8):
   for x in range(976,1080,8):
    tile=bank.get((x//8,y//8))
    if tile is not None:crop.alpha_composite(straight(tile),(x-976,y-928))
  ident='toiture' if name=='Metano_Town_Objects' else 'guichet'
  if ident=='toiture':
   a=np.array(crop);a[48:]=0;crop=Image.fromarray(a)
  out=P/f'KrowBank_{ident}_native.png';crop.save(out,optimize=True)
  exports[ident]={'file':out.name,'sheet':name,'source_rect':[976,928,1080,1024],'kept_rows':[0,48] if ident=='toiture' else [0,96],'size':[104,96],'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
 roof=Image.open(P/exports['toiture']['file']).convert('RGBA');roof.alpha_composite(Image.open(P/exports['guichet']['file']).convert('RGBA'));roof.save(P/'KrowBank_structure_native.png',optimize=True)
 report={'repository':'https://github.com/Palikadude/Halcyon','commit':PIN,'identified_as':'Krow Bank, Bank_Owner = Murkrow','identity_evidence':[{'path':'Data/Script/ground/metano_town/init.lua','lines':[2837,2849]},{'path':'Data/Script/ground/metano_town/metano_town_ch_2.lua','lines':[460,466]}],'sources':sources,'exports':exports,'scope':'Native reference study and extracted object layers, NOT a finished casino map.','checks':['Git blob identity against pinned Halcyon tree','native 8 px grid','no resize, recolour, mirroring or generated redraw in these extracts','roof and front furnishing on separate aligned canvases'],'runtime_PMDO':'NOT TESTED'}
 (P/'provenance_krow_bank.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('PASS: pinned native banks; Krow Bank roof and front furnishing exported independently at 104×96.')

if __name__=='__main__':main()
