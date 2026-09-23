"""Portable PNG package; source repo stores lossless WebP layers to avoid duplicates."""
from pathlib import Path
import json,io,zipfile,hashlib,copy
from PIL import Image
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;O=R/'renders/cafe_spinda_reseau_v4'
def main():
 m=json.loads((O/'manifest.json').read_text());portable=copy.deepcopy(m);files={}
 for room in portable['rooms']:
  room['raw_in_repository']=room.pop('raw')
  for layer in room['layers']:
   im=Image.open(O/layer['file']).convert('RGBA');stream=io.BytesIO();im.save(stream,format='PNG',optimize=True);payload=stream.getvalue();assert Image.open(io.BytesIO(payload)).convert('RGBA').tobytes()==im.tobytes();files[layer['png']]=payload;layer['file']=layer['png']
 for p in (O/'assets').glob('*.png'):files[str(p.relative_to(O))]=p.read_bytes()
 files['manifest.json']=(json.dumps(portable,ensure_ascii=False,indent=2)+'\n').encode()
 page=(S/'viewer.html').read_text().replace('__DATA__',json.dumps(portable,ensure_ascii=False)).replace('id="pack" href=','hidden id="pack" href=');files['index.html']=page.encode()
 for name in ['README.md','fenetre_provenance.json','flammes_provenance.json','verification.json','verification_viewer.json']:
  if (O/name).exists():files[name]=(O/name).read_bytes()
 target=O/'SpindaV4_pack.zip'
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,payload in sorted(files.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,9,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,payload)
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  for name,payload in files.items():assert z.read(name)==payload
  for room in portable['rooms']:
   for l in room['layers']:assert l['file'] in z.namelist()
  for a in portable['assets']:assert a['file'] in z.namelist()
  for anim in portable['animations'].values():
   for f in anim['frames']+[anim['sheet']]:assert f in z.namelist()
 report={'pass':True,'file':target.name,'files':len(files),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'checks':['all CRCs','PNG decoding identical to repo WebP RGBA','all file payloads exact','all portable viewer terrain dependencies present'],'runtime_PMDO':'NOT TESTED'}
 (O/'verification_package.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
