"""Non-destructive native cloud overlay. Sea patch is BLOCKED by missing custom banks.
The only edit is a new visual-only MapStatus in the existing Status object.
Preserves every other original byte, including BOM/CRLF and tile placements.
"""
from pathlib import Path
import json, sys, hashlib, subprocess, copy
from PIL import Image
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;O=R/'exports/cliffnordouesttest1_animation_v1'
PIN='aac14ae4'; TARGET='cliffnordouesttest1.rsground'; ID='cliffnw_native_cloud_overlay'; BG='CLIFFNW_NATIVE_CLOUD_OVERLAY'
sys.path.insert(0,str(R/'source'));import ciels_valides as climate
sys.path.insert(0,str(R/'source/pmdo_cote'));from build import write_dir

def sha(data):return hashlib.sha256(data).hexdigest()
def original():return subprocess.check_output(['git','show',PIN+':'+TARGET],cwd=R)
def dump(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def main(apply=False):
 before=original();doc=json.loads(before.decode('utf-8-sig'));obj=doc['Object'];assert obj['Status']=={}
 assert len(obj['obstacles'])==138 and len(obj['obstacles'][0])==98
 # Full-map-height transparent texture prevents vertical duplicates in this Ground.
 # Six native Guilde/Sharpedo cloud families, original pixels and scale.
 cloud=Image.new('RGBA',(1440,784));cloud.paste(climate.clouds('jour'),(0,208))
 preview=O/'png';preview.mkdir(parents=True,exist_ok=True);cloud.save(preview/(BG+'.png'))
 write_dir(O/'a_copier/Content/BG'/f'{BG}.dir',cloud)
 emitter={'$type':'RogueEssence.Content.OverlayEmitter, RogueEssence','LocHeight':0,'finished':False,'Offset':0,
          'Anim':{'AnimIndex':BG,'FrameTime':1,'StartFrame':-1,'EndFrame':-1,'AnimDir':-1,'Alpha':255,'AnimFlip':0},
          'Movement':{'X':-4,'Y':0},'FadeIn':0,'FadeOut':0,'Layer':4,'Color':'255, 255, 255, 255'}
 status={'$type':'RogueEssence.Dungeon.MapStatus, RogueEssence','ID':ID,'StatusStates':[],'Emitter':emitter,'Hidden':True}
 resource=json.loads((HERE/'references/clouds_overhead.json').read_text(encoding='utf-8-sig'));resource['Version']='0.8.12.0';data=resource['Object']
 data.update(Name={'DefaultText':'Nuages natifs — cliff nord-ouest','LocalTexts':{}},Desc={'DefaultText':'Overlay visuel uniquement. Aucun changement de terrain ou de météo de combat.','LocalTexts':{}},Comment='Six familles Guilde/Sharpedo c16efe12 ; -4 px/s ; boucle 360 s. Aucun événement gameplay.',DefaultHidden=True,Emitter=copy.deepcopy(emitter))
 dump(O/'a_copier/Data/MapStatus'/f'{ID}.json',resource)
 old=b'"Status": {}';new=('"Status": '+json.dumps({ID:status},ensure_ascii=False,indent=2).replace('\n','\r\n')).encode('utf-8')
 assert before.count(old)==1;after=before.replace(old,new,1)
 assert after.replace(new,old,1)==before
 parsed=json.loads(after.decode('utf-8-sig'));restored=copy.deepcopy(parsed);restored['Object']['Status']={};assert restored==doc
 dst=O/'a_copier/Data/Ground'/TARGET;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(after)
 # Short one-play preview of the EFFECT ONLY; not a fabricated render of missing art.
 frames=[climate.wrap(cloud,(1104,784),i) for i in range(32)]
 frames[0].save(preview/'NUAGES_overlay_extrait_8s.webp',save_all=True,append_images=frames[1:],duration=250,loop=1,lossless=True,method=4)
 banks=sorted({f['Sheet'] for l in obj['Layers'] for col in l['Tiles'] for cell in col for a in cell['Layers'] for f in a['Frames']})
 missing=['v2_promontoire_jour_03','terrain','terrain (2)','terrain (3)','terrain (4)']
 report={'status':'PARTIAL_CLOUDS_ONLY_SEA_BLOCKED','date':'2026-09-18','target':TARGET,'original_commit':PIN,'original_sha256':sha(before),'patched_sha256':sha(after),'root_applied':apply,
 'only_changed_json_path':'Object.Status.'+ID,'byte_reversible':True,'all_existing_fields_identical':True,'preserved':['All four tile layers and every Frames/FrameLength','obstacles','rand','Background','BlankBG','Decorations','Entities','AssetName','Music','EdgeView','NoSwitching','ViewCenter','ViewOffset','Name','Released','Comment','TexSize'],
 'clouds':{'texture':BG,'size':[1440,784],'cloud_y':208,'movement_px_s':[-4,0],'native_draw_layer':4,'draw_layer_name':'Top','cycle_seconds':360,'alpha':255,'native_families':6,'provenance':climate.provenance(),'preview':'8-second one-play effect-only excerpt, not full Ground render.'},
 'sea':{'modified':False,'reason':'Custom texture banks absent from this checkout and searched public repository trees. Material identity and original pixels cannot be verified. No assumed water tiles or palette animation applied.','required_custom_banks':missing},'all_ground_banks':banks,
 'engine_source':{'repo':'RogueCollab/RogueEssence','commit':'8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b','files':['RogueEssence/Ground/GSceneZone.cs','RogueEssence/Content/Animation/Emitters/OverlayEmitter.cs','RogueEssence/Content/Animation/OverlayAnim.cs','RogueEssence/Content/Animation/Sprites.cs']},
 'limits':['Only native headless validation, if separately reported. No GPU/animation playback claim.','Requires original custom tile banks already installed in the user project.','OverlayEmitter repeats X and Y; vertical period equals this Ground height. No visible duplicate inside its 784-pixel bounds.','MapStatus starts on entering the Ground; editor-only display is not guaranteed.','Sea remains entirely unchanged until exact bank assets are supplied.']}
 if apply:
  current=(R/TARGET).read_bytes();assert current in [before,after], 'Refuse to overwrite independent user edits'
  (R/TARGET).write_bytes(after)
 dump(O/'audit.json',report)
 print('Native cloud patch built; only Status changed. Sea UNMODIFIED (missing banks). Root applied:',apply)
if __name__=='__main__':main('--apply' in sys.argv)
