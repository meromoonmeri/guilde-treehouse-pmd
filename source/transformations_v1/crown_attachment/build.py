"""Export faceless crown assets, per-frame placement proposals and visible fit tests."""
from pathlib import Path
import sys,json,hashlib,base64
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import assets
from crown_attachment.attach import ROOT,load_profiles,inspect_profile,place,band_geometry,DIRECTIONS
OUT=ROOT/'exports/crown_attachment_v1'
for n in ['assets','placements','review']:(OUT/n).mkdir(parents=True,exist_ok=True)
profiles=load_profiles();crowns={kind:assets.crown_views(kind) for kind in ['fire','water']}
asset_info={}
for kind,views in crowns.items():
 sheet=Image.new('RGBA',(64,512));info=[]
 for d,c in enumerate(views):sheet.paste(c,(0,d*64));info.append(band_geometry(c,kind))
 sheet.save(OUT/'assets'/f'TERA_HEADLESS_{kind}.Dir8.png');asset_info[kind]=info
(OUT/'assets/anchors.json').write_text(json.dumps(asset_info,indent=2)+'\n')
# Verify that no local source/approved sprite has been touched by this attachment build.
source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for cfg in profiles.values() for p in (ROOT/cfg['sprite_dir']).glob('*.png')}
reports={};summary={};demos=[];placements_tested=0
for name,cfg in profiles.items():
 report=inspect_profile(name,cfg);reports[name]=report
 (OUT/'placements'/f'{name}.json').write_text(json.dumps(report,indent=2)+'\n')
 states={}
 for r in report['records']:states[r['state']]=states.get(r['state'],0)+1
 summary[name]={'active':cfg['active'],'local_frames':len(report['records']),'states':states,'missing_local_actions':len(report['skipped_actions'])}
 if not cfg['active']:continue
 for action in ['Idle','Walk','Hop']:
  records=[r for r in report['records'] if r['action']==action]
  if not records:continue
  count=max(r['frame'] for r in records)+1;rows=max(r['row'] for r in records)+1
  source=records[0]['source_action'];native=Image.open(ROOT/cfg['sprite_dir']/f'{source}-Anim.png').convert('RGBA');w,h=records[0]['frame_size']
  for kind,views in crowns.items():
   fs=[];details=[]
   for f in range(count):
    canvas=Image.new('RGB',(192*4,208*2),(23,33,47));dd=ImageDraw.Draw(canvas)
    for d in range(rows):
     r=next(x for x in records if x['row']==d and x['frame']==f)
     x0=d%4*192;y0=d//4*208;ground=(96+x0,166+y0)
     if r['state'].startswith('blocked'):
      dd.text((x0+8,y0+30),'NEEDS MANUAL FIT',fill='orange');continue
     sprite=native.crop((f*w,d*h,(f+1)*w,(d+1)*h));layer=Image.new('RGBA',canvas.size)
     c,pos,detail=place(views[r['direction']],kind,r,ground)
     # Rear of the accessory first; the face belongs only to this native sprite.
     rear=Image.new('RGBA',canvas.size);rear.alpha_composite(c,pos)
     seat_y=detail['seat_world'][1];a=np.array(rear);yy=np.arange(canvas.height)[:,None];band=(yy>seat_y)&(yy<=seat_y+r['front_overlap_px'])
     back_arr=a.copy();back_arr[~np.broadcast_to(band,a.shape[:2])]=0
     front_arr=a.copy();front_arr[np.broadcast_to(band,a.shape[:2])]=0
     layer.alpha_composite(Image.fromarray(back_arr))
     layer.alpha_composite(sprite,(ground[0]-r['shadow'][0],ground[1]-r['shadow'][1]))
     layer.alpha_composite(Image.fromarray(front_arr));canvas.paste(layer,(0,0),layer)
     dd=ImageDraw.Draw(canvas);dd.text((x0+8,y0+190),DIRECTIONS[d],fill=(190,210,225))
     details.append({'frame':f,'row':d,**detail});placements_tested+=1
     # World seat follows exact head-minus-shadow calculation, not sheet/body top.
     assert detail['seat_world']==[ground[i]+r['seat_relative_to_ground'][i] for i in range(2)]
    fs.append(canvas)
   ticks=[next(r['ticks'] for r in records if r['frame']==f) for f in range(count)];ends=[round(sum(ticks[:i+1])*100/60)*10 for i in range(count)];dur=[ends[i]-(ends[i-1] if i else 0) for i in range(count)]
   assets.gif(fs,OUT/'review'/f'{name}_{action}_{kind}.gif',dur)
   fs[0].save(OUT/'review'/f'{name}_{action}_{kind}.png')
   demos.append({'profile':name,'action':action,'kind':kind,'frames':count,'details':details})
for path,sha in source_hashes.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
# Inventory coverage is bounded to actual local multisheet directories, not the entire remote catalogue.
local=[str(p.parent.relative_to(ROOT)) for base in ['source','exports'] for p in (ROOT/base).rglob('AnimData.xml')]
known={p['sprite_dir'] for p in profiles.values()};unprofiled=sorted(set(local)-known)
verification={'source_sprite_hashes_preserved':source_hashes,'placements_rendered':placements_tested,'local_directories':local,'unprofiled_directories':unprofiled,'summary':summary,'unknown_profile_policy':'blocked until a head-width/seat profile is provided','runtime_PMDO':'NOT TESTED','visual_status':'initial fit proposals; crown angle geometry and complex poses not approved'}
(OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
(OUT/'review/rendered_placements.json').write_text(json.dumps(demos,indent=2)+'\n')
# Standalone review document: assets alone, then real sprites underneath the separate accessory.
def uri(path):
 p=OUT/path;return f'data:image/{p.suffix[1:]};base64,'+base64.b64encode(p.read_bytes()).decode()
standalone=Image.new('RGBA',(64*8,128),(23,33,47,255))
for y,(kind,views) in enumerate(crowns.items()):
 for d,c in enumerate(views):standalone.alpha_composite(c,(d*64,y*64))
standalone.resize((1024,256),Image.Resampling.NEAREST).save(OUT/'review/crowns_only.png')
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Couronnes séparées — adaptation aux têtes</title><style>body{background:#101927;color:#edf2f8;font:16px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:20px}h1{font-size:38px}section{padding:22px;border:1px solid #34495c;border-radius:14px;margin:24px 0}img{max-width:100%;image-rendering:pixelated}p{color:#bdccdc}a{color:#8fe1d4}.note{border-left:3px solid #e5bd70;padding-left:14px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}details{margin:16px 0}summary{cursor:pointer;color:#8fe1d4}</style><h1>Couronnes seules, sans visage intégré</h1><p>Les motifs de visage ont été remplacés par des facettes. Aucun crâne ou visage de Pokémon n’est inclus dans les assets ; les Pokémon visibles plus bas sont des sprites natifs séparés, inchangés.</p><section><h2>Assets Feu et Eau corrigés</h2>'''
html+=f'<img src="{uri(Path("review/crowns_only.png"))}" alt="Couronnes Feu et Eau seules, sans visage"><p>Variantes sans visage demandées pour le projet ; ce retrait est volontaire et ne doit pas être présenté comme une reproduction pixel-exacte de toutes les décorations canoniques.</p></section><section><h2>Placement anatomique, frame par frame</h2><p>Repère noir de tête − repère blanc d’ombre + réglage anatomique de la forme. L’échelle dépend de la largeur du bandeau par rapport à la tête, pas de la largeur totale des ailes ou de la queue. Rotate suit aussi la direction réelle de chaque phase.</p><p class="note">Les poses de chute et de roulade non calibrées sont bloquées. Une marque placée sur un pixel opaque ne garantit pas à elle seule que le repère de tête est anatomiquement correct.</p></section>'
for name,cfg in profiles.items():
 if not cfg['active']:continue
 html+=f'<section><h2>{name}</h2><div class="grid">'
 for kind in ['fire','water']:
  p=Path(f'review/{name}_Idle_{kind}.gif')
  if (OUT/p).exists():html+=f'<div><h3>{kind}</h3><img src="{uri(p)}" alt="{name} Idle {kind}"></div>'
 html+='</div>'
 for action in ['Walk','Hop']:
  p=Path(f'review/{name}_{action}_fire.gif')
  if (OUT/p).exists():html+=f'<details><summary>Suivi de tête pendant {action}</summary><img src="{uri(p)}" alt="Suivi {action}"></details>'
 html+='</section>'
html+='<section><h2>Portée réelle</h2><p>Six dossiers multi-sheet locaux recensés, dont quatre modèles actuels et deux archives Carapagos. Les actions absentes des références locales et les poses non calibrées sont listées, pas déclarées adaptées. Ce n’est pas encore tout le catalogue SpriteCollab.</p><p><a href="exports/crown_attachment_v1/verification.json">Rapport de couverture et contrôles</a> · <a href="source/transformations_v1/crown_attachment/profiles.json">Réglages par sprite</a></p><p class="note">Prévisualisation et données d’attachement uniquement : pas de test de rendu/import PMDO. Les couronnes des autres types et les trois transformations complètes restent en cours.</p></section></html>'
(ROOT/'apercu_couronnes_attachees.html').write_text(html)
print(json.dumps({'placements_rendered':placements_tested,'profiles':summary,'unprofiled':unprofiled},indent=2))
