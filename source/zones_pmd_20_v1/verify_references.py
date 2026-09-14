from pathlib import Path
import json,hashlib,subprocess,zipfile,xml.etree.ElementTree as ET,io
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/references_fideles_v1';m=json.loads((O/'manifest.json').read_text());report=[]
for e in m['scenes']:
 p=O/e['id'];size=tuple(e['size']);src=Image.open(R/e['source']);base=Image.new('RGBA',size)
 for l in e['layers']:
  im=Image.open(p/l['file']).convert('RGBA');assert im.size==size;base.alpha_composite(im)
 raw=subprocess.check_output(['git','show',f'8eb46bc:{e["source"]}']);assert hashlib.sha256(raw).hexdigest()==e['source_sha256']
 for f in range(getattr(src,'n_frames',1)):
  src.seek(f);expected=src.convert('RGBA');c=base.copy()
  if e['animation']:
   layer=Image.open(p/e['animation']['files'][f]).convert('RGBA');assert layer.size==size;c.alpha_composite(layer);assert e['animation']['durations_ms'][f]==int(src.info.get('duration',100))
  assert np.array_equal(np.array(c),np.array(expected))
 original=Image.open(p/'REFERENCE_RECOMPOSEE.png').convert('RGBA');src.seek(0);assert np.array_equal(np.array(original),np.array(src.convert('RGBA')))
 if e['optional_subtle_variant']:
  patch=Image.open(p/'OPTION_reflet_discret.png').convert('RGBA');mask=np.array(patch)[:,:,3]>0;v=Image.open(p/'VARIANTE_SUBTILE.png').convert('RGBA');delta=np.any(np.array(v)!=np.array(original),axis=2);assert not np.any(delta&~mask);assert delta.sum()<size[0]*size[1]*.03
 with zipfile.ZipFile(p/(e['id']+'_calques.ora')) as z:
  tree=ET.fromstring(z.read('stack.xml'));c=Image.new('RGBA',size)
  for node in reversed(tree.find('stack').findall('layer')):c.alpha_composite(Image.open(io.BytesIO(z.read(node.attrib['src']))).convert('RGBA'))
  assert np.array_equal(np.array(c),np.array(original))
 report.append({'id':e['id'],'source_commit_hash_match':True,'verified_frames':getattr(src,'n_frames',1),'png_and_ora_recomposition_exact':True})
result={'scenes_including_background':len(report),'native_frames_verified':sum(r['verified_frames'] for r in report),'records':report,'runtime_validated':False};(O/'verification_independante.json').write_text(json.dumps(result,indent=2));print(result['scenes_including_background'], 'references;',result['native_frames_verified'],'frames exact; source commit hashes and ORA verified')
