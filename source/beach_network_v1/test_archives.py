"""Regression for archived originals only; delivery renders/ZIPs are not rebuilt."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.beach_network_v1 import build
from source.beach_network_v1.archive_raws import verify_record
P=build.OUT;m=json.loads((P/'manifest.json').read_text());records=json.loads((P/'bruts/archive_lossless.json').read_text());n=0
assert build.sha(R/m['source']['file'])==m['source']['sha256']
for name,expected in m['sources'].items():
 path=R/name;assert verify_record(path,expected),name
 assert not verify_record(path,'deliberately incorrect hash'),name
for record in records:
 original=P/'bruts'/record['original'];assert verify_record(original,record['original_png_sha256'])
 decoded=build.load(original);assert hashlib.sha256(decoded.tobytes()).hexdigest()==record['rgba_sha256'];assert list(decoded.shape[:2][::-1])==record['size'];n+=1
assert n==7
for slug,_,_,_,raw in build.SPECS:
 im=Image.fromarray(build.load(build.BRUT/raw)).convert('RGB');assert im.width==im.height
 assert list(im.size)==next(r for r in m['rooms'] if r['id']==slug)['original_generated_size']
 assert im.tobytes()==Image.open((build.BRUT/raw).with_suffix('.webp')).convert('RGB').tobytes()
report={'pass':True,'source_entries':len(m['sources']),'archived_originals':n,'checks':['original PNG hashes in manifest match archive provenance','live WebP bytes and decoded RGBA hashes verified','old PNG paths decode identically through the loader','wrong expected hashes rejected','reference image hash unchanged','all six terrain build input images resolve as identical RGB'],'scope':'Archive/provenance/loader regression only; existing rendered maps, full animation exports and ZIP not rebuilt.'}
(P/'verification_archives.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',n,'archived originals,',len(m['sources']),'source hashes, lossless loader and wrong-hash rejection')
