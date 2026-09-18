from pathlib import Path
import json, subprocess, hashlib, struct, io, copy
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;O=R/'exports/cliffnordouesttest1_animation_v1'
def main():
 checks=[]
 def check(name,ok):assert ok,name;checks.append(name)
 audit=json.loads((O/'audit.json').read_text());name=audit['target'];old=subprocess.check_output(['git','show',audit['original_commit']+':'+name],cwd=R);new=(R/name).read_bytes()
 check('Original pinned to aac14ae4 and SHA256',hashlib.sha256(old).hexdigest()==audit['original_sha256'])
 check('Root and distributable Ground byte-identical',new==(O/'a_copier/Data/Ground'/name).read_bytes() and hashlib.sha256(new).hexdigest()==audit['patched_sha256'])
 before=json.loads(old.decode('utf-8-sig'));after=json.loads(new.decode('utf-8-sig'));o=after['Object'];status=o['Status'];assert len(status)==1
 restored=copy.deepcopy(after);restored['Object']['Status']={}
 check('Only Object.Status differs structurally',restored==before)
 prefix,suffix=old.split(b'"Status": {}',1)
 check('All bytes outside Status untouched (BOM, CRLF, formatting included)',new.startswith(prefix+b'"Status": {') and new.endswith(suffix) and new.count(b'\n')==new.count(b'\r\n'))
 check('All tile placements AND animation frame lists unchanged',o['Layers']==before['Object']['Layers'])
 check('Collision geometry and tags unchanged',o['obstacles']==before['Object']['obstacles'])
 check('Sea and waterfall not guessed or altered',audit['sea']['modified'] is False and o['Layers']==before['Object']['Layers'])
 s=status['cliffnw_native_cloud_overlay'];em=s['Emitter']
 check('Visual-only hidden status, no gameplay state',s['Hidden'] and s['StatusStates']==[])
 check('Native Top overlay, horizontal -4px/s wrap',em['Layer']==4 and em['Movement']=={'X':-4,'Y':0} and em['$type']=='RogueEssence.Content.OverlayEmitter, RogueEssence')
 bank=O/'a_copier/Content/BG/CLIFFNW_NATIVE_CLOUD_OVERLAY.dir';raw=bank.read_bytes();length=struct.unpack('<q',raw[:8])[0]
 actual=np.array(Image.open(io.BytesIO(raw[8:8+length])).convert('RGBA'));src=np.array(Image.open(O/'png/CLIFFNW_NATIVE_CLOUD_OVERLAY.png').convert('RGBA'),dtype='uint16');src[:,:,:3]=src[:,:,:3]*src[:,:,3:4]//255
 check('Native BG binary contains exact premultiplied PNG and static frame metadata',np.array_equal(actual,src.astype('uint8')) and struct.unpack('<4i',raw[8+length:])==(1440,784,0,1))
 check('Clouds restricted to original sky band, map-height vertical period',not actual[:208,:,3].any() and not actual[416:,:,3].any() and actual[208:416,:,3].any())
 resource=json.loads((O/'a_copier/Data/MapStatus/cliffnw_native_cloud_overlay.json').read_text())['Object']
 check('Matching visual MapStatusData, no carryover or gameplay hooks',resource['Emitter']==em and resource['CarryOver'] is False and resource['StatusStates']==[] and all(v==[] for k,v in resource.items() if k.startswith(('On','Before','After','Modify','Restore','UserElement','TargetElement'))))
 with Image.open(O/'png/NUAGES_overlay_extrait_8s.webp') as im:
  check('One-play8s effect-only preview, not a fake short wrap',im.n_frames==32 and im.info['loop']==1)
  for f in range(im.n_frames):im.seek(f);im.load();assert im.info['duration']==250
 native=json.loads((HERE/'runtime_verification.json').read_text());check('Real PMDO deserialization passed13 checks; no GPU claim',native['status']=='PASS' and len(native['assertions'])==13 and not native['GPU_tested'])
 (HERE/'verification.json').write_text(json.dumps({'status':'PASS_CLOUDS_ONLY','count':len(checks),'checks':checks,'sea_status':'BLOCKED_MISSING_BANKS'},ensure_ascii=False,indent=2)+'\n')
 print(len(checks),'cloud-patch preservation checks PASS; sea still blocked.')
if __name__=='__main__':main()
