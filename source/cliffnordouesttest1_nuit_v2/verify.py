from pathlib import Path
import importlib.util, copy, io, json, struct
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('cliffnw_night_build',HERE/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
 checks=[]
 def check(name,ok):assert ok,name;checks.append(name)
 audit=json.loads((b.O/'audit.json').read_text());before=b.original();day=b.original(b.DAY_PIN);after=(R/b.TARGET).read_bytes()
 check('Original and daytime files pinned by SHA256',b.sha(before)==audit['original_sha256'] and b.sha(day)==audit['day_cloud_sha256'])
 check('Root matches distributed night Ground and manifest',after==(b.O/'a_copier/Data/Ground'/b.TARGET).read_bytes() and b.sha(after)==audit['patched_sha256'])
 original=json.loads(before.decode('utf-8-sig'));night=json.loads(after.decode('utf-8-sig'));restored=copy.deepcopy(night);restored['Object']['Status']={}
 check('Only Object.Status differs from the user original',restored==original)
 prefix,suffix=before.split(b'"Status": {}',1)
 check('Every byte outside Status preserved, including BOM and CRLF',after.startswith(prefix+b'"Status": {') and after.endswith(suffix) and after.count(b'\n')==after.count(b'\r\n'))
 check('All four tile layers and all frame lists unchanged',night['Object']['Layers']==original['Object']['Layers'])
 check('Collisions, entities and decorations unchanged',all(night['Object'][k]==original['Object'][k] for k in ['obstacles','Entities','Decorations']))
 status=night['Object']['Status'];check('Only night status, no stacked daytime lighting',list(status)==[b.ID] and status[b.ID]['Hidden'] and status[b.ID]['StatusStates']==[])
 em=status[b.ID]['Emitter'];veil,clouds=em['Emitters']
 check('Ordered native MultiSwitchEmitter: lighting before clouds',em['$type']=='RogueEssence.Content.MultiSwitchEmitter, RogueEssence' and veil['Anim']['AnimIndex']==b.NIGHT and clouds['Anim']['AnimIndex']==b.CLOUD)
 check('Both overlays use Top',veil['Layer']==clouds['Layer']==4)
 check('Lighting stays still at opacity176',veil['Anim']['Alpha']==176 and veil['Movement']=={'X':0,'Y':0})
 check('Clouds drift at minus4px/s independently',clouds['Movement']=={'X':-4,'Y':0} and clouds['Anim']['Alpha']==255)
 for name,size in [(b.NIGHT,(1,1)),(b.CLOUD,(1440,784))]:
  raw=(b.O/'a_copier/Content/BG'/f'{name}.dir').read_bytes();n=struct.unpack('<q',raw[:8])[0]
  im=Image.open(io.BytesIO(raw[8:8+n])).convert('RGBA');src=Image.open(b.O/'png'/f'{name}.png').convert('RGBA')
  a=np.array(src,dtype='uint16');a[:,:,:3]=a[:,:,:3]*a[:,:,3:4]//255
  assert im.size==size and np.array_equal(np.array(im),a.astype('uint8')) and struct.unpack('<4i',raw[8+n:])==(*size,0,1)
 check('Both BG files match premultiplied PNG and native static metadata',True)
 n=np.array(Image.open(b.O/'png'/f'{b.CLOUD}.png'));d=np.array(Image.open(R/'exports/cliffnordouesttest1_animation_v1/png/CLIFFNW_NATIVE_CLOUD_OVERLAY.png'))
 expected=Image.new('RGBA',(1440,784));expected.paste(b.climate.clouds('nuit'),(0,208))
 check('Night cloud RGB follows approved Guilde/Sharpedo recipe exactly',np.array_equal(n,np.array(expected)))
 check('Cloud alpha, scale, placement and six-family geometry preserved',np.array_equal(n[:,:,3],d[:,:,3]) and not np.array_equal(n,d))
 check('Clouds remain in sky band only',not n[:208,:,3].any() and not n[416:,:,3].any())
 check('Full-screen1px texture has exact navy RGB',Image.open(b.O/'png'/f'{b.NIGHT}.png').getpixel((0,0))==(*b.COLOR,255))
 resource=json.loads((b.O/'a_copier/Data/MapStatus'/f'{b.ID}.json').read_text())['Object']
 check('Resource matches status; no carryover or gameplay hooks',resource['Emitter']==em and not resource['CarryOver'] and resource['StatusStates']==[] and all(v==[] for k,v in resource.items() if k.startswith(('On','Before','After','Modify','Restore','UserElement','TargetElement'))))
 with Image.open(b.O/'png/NUAGES_NUIT_extrait_8s.webp') as im:
  assert im.n_frames==32 and im.info['loop']==1
  for f in range(32):
   im.seek(f);a=np.array(im.convert('RGBA'));ref=np.array(b.climate.wrap(expected,(1104,784),f));visible=ref[:,:,3]>0
   assert np.array_equal(a[:,:,3],ref[:,:,3]) and np.array_equal(a[visible],ref[visible]) and im.info['duration']==250
 check('8-second cloud-only preview exact; one play, not a fake short cycle',True)
 check('Sea still unmodified, missing banks explicitly reported',audit['sea']['modified'] is False and len(audit['sea']['required_custom_banks'])==5)
 native=json.loads((HERE/'runtime_verification.json').read_text())
 check('Real PMDO21 load/lifecycle tests pass; no GPU claim',native['status']=='PASS' and len(native['assertions'])==21 and not native['GPU_tested'])
 report={'status':'PASS_NIGHT_CLOUDS_SEA_BLOCKED','count':len(checks),'checks':checks,'GPU_tested':False,'sea_animated':False}
 (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(checks),'night/preservation checks PASS')
if __name__=='__main__':main()
