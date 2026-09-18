"""Night lighting + canonical-family night clouds, only Object.Status edited.
No missing textures invented. The requested sea animation remains blocked.
"""
from pathlib import Path
import copy, hashlib, json, subprocess, sys
from PIL import Image
R=Path(__file__).resolve().parents[2]; HERE=Path(__file__).parent
O=R/'exports/cliffnordouesttest1_nuit_v2'; TARGET='cliffnordouesttest1.rsground'
PIN='aac14ae4'; DAY_PIN='34d40dc0'; ID='cliffnw_night_overlay'
CLOUD='CLIFFNW_NIGHT_CLOUDS'; NIGHT='CLIFFNW_NIGHT_VEIL'
COLOR=(8,14,36); ALPHA=176
sys.path.insert(0,str(R/'source'))
import ciels_valides as climate
from pmdo_cote.build import write_dir

def original(pin=PIN): return subprocess.check_output(['git','show',pin+':'+TARGET],cwd=R)
def sha(b): return hashlib.sha256(b).hexdigest()
def dump(p,obj): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def overlay(name,alpha=255,speed=0):
 return {'$type':'RogueEssence.Content.OverlayEmitter, RogueEssence','LocHeight':0,'finished':False,'Offset':0,'Anim':{'AnimIndex':name,'FrameTime':1,'StartFrame':-1,'EndFrame':-1,'AnimDir':-1,'Alpha':alpha,'AnimFlip':0},'Movement':{'X':speed,'Y':0},'FadeIn':0,'FadeOut':0,'Layer':4,'Color':'255, 255, 255, 255'}
def main(apply=False):
 before=original();day=original(DAY_PIN);doc=json.loads(before.decode('utf-8-sig'));assert doc['Object']['Status']=={}
 cloud=Image.new('RGBA',(1440,784));cloud.paste(climate.clouds('nuit'),(0,208))
 png=O/'png';png.mkdir(parents=True,exist_ok=True);cloud.save(png/(CLOUD+'.png'))
 veil=Image.new('RGBA',(1,1),COLOR+(255,));veil.save(png/(NIGHT+'.png'))
 pack=O/'a_copier'
 write_dir(pack/'Content/BG'/f'{CLOUD}.dir',cloud);write_dir(pack/'Content/BG'/f'{NIGHT}.dir',veil)
 # One composite emitter guarantees veil first, clouds second in Top draw list.
 emitter={'$type':'RogueEssence.Content.MultiSwitchEmitter, RogueEssence','LocHeight':0,'finished':False,'Emitters':[overlay(NIGHT,ALPHA),overlay(CLOUD,speed=-4)]}
 status={'$type':'RogueEssence.Dungeon.MapStatus, RogueEssence','ID':ID,'StatusStates':[],'Emitter':emitter,'Hidden':True}
 resource=json.loads((R/'source/cliffnordouesttest1_animation_v1/references/clouds_overhead.json').read_text(encoding='utf-8-sig'))
 resource['Version']='0.8.12.0';resource['Object'].update(Name={'DefaultText':'Cliff nord-ouest — nuit','LocalTexts':{}},Desc={'DefaultText':'Éclairage nocturne non destructif et nuages Guilde/Sharpedo nuit.','LocalTexts':{}},Comment='Visuel uniquement. Voile bleu nuit puis nuages nocturnes, aucun événement de gameplay.',DefaultHidden=True,Emitter=copy.deepcopy(emitter))
 dump(pack/'Data/MapStatus'/f'{ID}.json',resource)
 old=b'"Status": {}';replacement=('"Status": '+json.dumps({ID:status},ensure_ascii=False,indent=2).replace('\n','\r\n')).encode()
 assert before.count(old)==1;after=before.replace(old,replacement,1)
 assert after.replace(replacement,old,1)==before
 restored=json.loads(after.decode('utf-8-sig'));restored['Object']['Status']={};assert restored==doc
 dest=pack/'Data/Ground'/TARGET;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(after)
 frames=[climate.wrap(cloud,(1104,784),i) for i in range(32)]
 frames[0].save(png/'NUAGES_NUIT_extrait_8s.webp',save_all=True,append_images=frames[1:],duration=250,loop=1,lossless=True,method=4)
 # Full-size transparent veil for editing; .dir uses the native 1×1 fullscreen path.
 Image.new('RGBA',(1104,784),COLOR+(ALPHA,)).save(png/'VOILE_NUIT_overlay.png')
 prior=json.loads((R/'exports/cliffnordouesttest1_animation_v1/audit.json').read_text())
 if apply:
  assert (R/TARGET).read_bytes() in [before,day,after], 'Refusing to overwrite independent user edits'
  (R/TARGET).write_bytes(after)
 report={'status':'NIGHT_AND_CLOUDS_READY_SEA_BLOCKED','target':TARGET,'original_commit':PIN,'day_cloud_commit':DAY_PIN,'original_sha256':sha(before),'day_cloud_sha256':sha(day),'patched_sha256':sha(after),'root_applied':apply,'only_changed_json_path':'Object.Status','all_bytes_outside_status_unchanged':True,'all_tiles_collisions_entities_metadata_unchanged':True,
 'night':{'method':'Native full-screen translucent navy overlay; NOT recolored tile banks or a new canonical night sky. Characters and decorations receive the same scene lighting.','rgb':COLOR,'alpha':ALPHA,'native_bg_size':[1,1],'order':['night_veil','night_clouds'],'draw_layer':'Top','reference_formula':'out = original * (1 - 176/255) + (8,14,36) * 176/255; night clouds drawn afterward'},
 'clouds':{'mode':'nuit','recipe':'source/ciels_valides.py / Guilde-Sharpedo c16efe12','texture_size':[1440,784],'y':208,'speed_px_s':-4,'cycle_seconds':360,'native_families':6,'alpha_and_geometry_unchanged':True},
 'sea':prior['sea'],'limits':['Missing custom banks prevent full-map preview and sea identification.','No stars, moon, new terrain, sky replacement, collisions or script changes.','Native headless emitter tests are reported separately; no GPU or actual game playback validation.','Night is non-destructive global lighting, not an exact canonical per-material night-palette conversion.'],'engine_source':'RogueCollab/RogueEssence 8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b: SingleEmitter.cs, OverlayEmitter.cs, OverlayAnim.cs, BaseGroundScene.cs'}
 dump(O/'audit.json',report);print('Night lighting and night clouds built. Sea unchanged. Root applied:',apply)
if __name__=='__main__':main('--apply' in sys.argv)
