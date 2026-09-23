"""Editor handoff: empty kiosk back/front planes, NPC markers, magenta review maps."""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/casino_network_v1';DEST=OUT/'editeur'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 DEST.mkdir(parents=True,exist_ok=True)
 data=json.loads((OUT/'manifest.json').read_text());specs={};checks=[]
 kiosk=Image.open(OUT/'objets/kiosque.png').convert('RGBA');back=Image.new('RGBA',kiosk.size);front=kiosk.copy()
 # Merchant window remains a background, while canopy/posts/counter occlude
 # a separately authored NPC. No character or replacement floor is drawn.
 window=(32,40,80,72);back.paste(kiosk.crop(window),(32,40));front.paste((0,0,0,0),window)
 back.save(DEST/'Casino_kiosque_arriere.png',optimize=True);front.save(DEST/'Casino_kiosque_avant.png',optimize=True)
 proof=back.copy();proof.alpha_composite(front);assert proof.tobytes()==kiosk.tobytes();checks.append('Generated kiosk back/front exactly recompose the unchanged original')
 specs['kiosque']={'size':list(kiosk.size),'background':'editeur/Casino_kiosque_arriere.png','foreground':'editeur/Casino_kiosque_avant.png','npc_feet_local_px':[56,80],'visible_window_local_px':[32,40,48,32],'customer_marker_local_px':[56,136],'customer_faces':'N','counter_collision_suggestion_local_px':[0,88,112,40]}
 refs=ROOT/'source/ledian_casino_v1/references'
 back=Image.open(refs/'KrowBank_toiture_native.png').convert('RGBA');front=Image.open(refs/'KrowBank_guichet_native.png').convert('RGBA')
 back.save(DEST/'Casino_KrowBank_arriere.png',optimize=True);front.save(DEST/'Casino_KrowBank_avant.png',optimize=True)
 proof=back.copy();proof.alpha_composite(front);assert proof.tobytes()==Image.open(OUT/'objets/krow_bank_natif.png').convert('RGBA').tobytes();checks.append('Native Krow Bank roof/counter exactly recompose the unchanged original')
 specs['krow_bank_natif']={'size':list(back.size),'background':'editeur/Casino_KrowBank_arriere.png','foreground':'editeur/Casino_KrowBank_avant.png','npc_feet_local_px':[52,88],'visible_window_local_px':[32,48,40,32],'customer_marker_local_px':[52,104],'customer_faces':'N','counter_collision_suggestion_local_px':[0,88,104,8]}
 # Synthetic 24x32 test marker only, never saved into an asset or a map.
 for spec in specs.values():
  rear=Image.open(OUT/spec['background']).convert('RGBA');fore=Image.open(OUT/spec['foreground']).convert('RGBA');x,y=spec['npc_feet_local_px']
  test=rear.copy();test.alpha_composite(Image.new('RGBA',(24,32),(0,255,255,255)),(x-12,y-32));test.alpha_composite(fore)
  assert test.getpixel((x,y-24))==(0,255,255,255)
  assert fore.getpixel((x,y-2))[3]==255 and test.getpixel((x,y-2))==fore.getpixel((x,y-2))
 checks.append('Synthetic merchant marker remains visible in window and is occluded by counter; no marker asset saved')
 slots=[]
 for layer in data['layers']:
  if layer.get('asset') not in specs:continue
  spec=specs[layer['asset']];x,y=layer['position'];px,py=spec['npc_feet_local_px'];cx,cy=spec['customer_marker_local_px']
  slots.append({'host':layer['id'],'asset':layer['asset'],'initial_host_position_px':[x,y],'initial_npc_feet_world_px':[x+px,y+py],'initial_customer_world_px':[x+cx,y+cy],'npc_species':None,'npc_entity_created':False})
 assert len(slots)==3
 meta={'status':'EDITOR GUIDES ONLY — no NPC entities, native Ground collisions or warps created','generation_background':'#FF00FF','import_layers':'transparent PNG','render_order':['terrain','kiosk background','NPC placed separately in editor','kiosk foreground'],'assets':specs,'instances':slots,'notes':['Do not stack the original fused kiosk over these split planes. Replace it with background + foreground.','Feet anchors are visual pixel guides, not serialized PMDO entity positions. Adjust for the chosen Pokemon sprite pivot/size.','Recompute world markers from host position plus local markers when moving a kiosk.','Reserve an empty merchant station behind the counter and keep customer access clear.','Collision rectangles are authoring suggestions only and must be configured and tested in PMDO.','Krow Banks bird-shaped roof is architecture, not a baked merchant Pokemon.']}
 (DEST/'placements_pnj.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 # Both key-colour previews are opaque; actual layer PNGs remain transparent.
 base=Image.new('RGBA',(1024,1024))
 for layer in data['layers']:
  if layer['group']=='terrain':base.alpha_composite(Image.open(OUT/layer['file']).convert('RGBA'),tuple(layer['position']))
 for name,im in [('terrain',base),('reseau',Image.open(OUT/'Casino_reseau_decore.webp').convert('RGBA'))]:
  result=Image.new('RGBA',im.size,(255,0,255,255));result.alpha_composite(im);path=OUT/f'Casino_{name}_magenta.webp';result.save(path,lossless=True,exact=True,method=6)
  decoded=Image.open(path).convert('RGBA');assert decoded.tobytes()==result.tobytes();assert decoded.getpixel((0,0))==(255,0,255,255)
  assert decoded.getchannel('A').getextrema()==(255,255)
  assert Image.composite(decoded,im,im.getchannel('A')).tobytes()==im.tobytes()
  checks.append(name+': exact opaque magenta background, visible pixels preserved')
 report={'pass':True,'checks':checks,'empty_npc_slots':len(slots),'npc_entities_created':0,'existing_composition_sha256':digest(OUT/'Casino_reseau_decore.webp'),'source_kiosk_sha256':digest(OUT/'objets/kiosque.png'),'runtime_PMDO':'NOT TESTED'}
 (DEST/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
