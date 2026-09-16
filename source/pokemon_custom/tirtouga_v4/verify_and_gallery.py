from pathlib import Path
import json,math,hashlib,base64,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];SRC=Path(__file__).parent;OUT=ROOT/'exports/pokemon_custom/tirtouga_v4';SP=OUT/'sprite_multisheet'
report={};allcolors=set();root=ET.parse(SP/'AnimData.xml');expected={'AnimData.xml'}
for node in root.findall('.//Anim'):
 name=node.findtext('Name');dur=[int(d.text) for d in node.findall('./Durations/Duration')];ims=[]
 for kind in ['Anim','Offsets','Shadow']:
  p=SP/f'{name}-{kind}.png';expected.add(p.name);a=np.array(Image.open(p).convert('RGBA'));assert set(np.unique(a[:,:,3]))<={0,255};ims.append(a)
 a,o,s=ims;assert a.shape==o.shape==s.shape;assert a.shape[1]==64*len(dur);assert a.shape[0] in [64,512]
 for y in range(a.shape[0]//64):
  for x in range(len(dur)):
   aa=a[y*64:(y+1)*64,x*64:(x+1)*64];oo=o[y*64:(y+1)*64,x*64:(x+1)*64];ss=s[y*64:(y+1)*64,x*64:(x+1)*64]
   assert np.all(aa[:,:,3][oo[:,:,3]>0]==255)
   ys,xs=np.where(np.all(ss[:,:,:3]==255,axis=2)&(ss[:,:,3]>0));assert list(zip(xs,ys))==[(32,44)]
   assert not aa[0,:,3].any() and not aa[-1,:,3].any() and not aa[:,0,3].any() and not aa[:,-1,3].any()
 for c in np.unique(a[:,:,:3][a[:,:,3]>0],axis=0):allcolors.add(tuple(int(v) for v in c))
 gif=Image.open(OUT/'review/gifs'/f'{name}.gif');total=0
 for f in range(gif.n_frames):gif.seek(f);gif.load();total+=gif.info['duration']
 assert abs(total-sum(dur)*1000/60)<=5
 report[name]={'gif_frames_encoded':gif.n_frames,'gif_duration_ms':total,'xml_ticks':sum(dur),'markers_on_opaque_pixels':True,'shadow_anchor':[32,44],'unclipped':True}
assert len(allcolors)<=15;assert {p.name for p in SP.iterdir()}==expected
report['global_visible_colors']=len(allcolors);report['xml_mapping']='copied named IDs from pinned native Bulbasaur AnimData.xml, not guessed action-list indices';report['runtime']='NOT_TESTED';report['anatomy']='markers are nearest-pixel anatomical guides; actual limb semantics and rotated/falling poses still need human/editor review'
(OUT/'review/independent_checks.json').write_text(json.dumps(report,indent=2)+'\n')
# Flat source archive, not a PMDO binary and not a complete publicly approved submission.
with zipfile.ZipFile(OUT/'carapagos_v4_22_actions_candidate.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(SP.iterdir()):z.write(p,p.name)
with zipfile.ZipFile(OUT/'carapagos_v4_22_gifs.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((OUT/'review/gifs').glob('*.gif')):z.write(p,p.name)
# Preserve the user's explicit portrait approval without re-running the portrait generator.
portraitdir=ROOT/'exports/pokemon_custom/tirtouga_portraits_v3/portraits_individual';approval={'approved_by_user':True,'date':'2026-09-16','scope':'five proposed expressions Happy/Angry/Sad/Shouting/Surprised; Normal existing preserved','canonical_background_status':'already composed, exact visible template pixels verified by portrait build','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(portraitdir.glob('*.png'))}}
(ROOT/'source/pokemon_custom/tirtouga_portraits_v3/approval.json').write_text(json.dumps(approval,indent=2)+'\n')

def uri(path):
 p=ROOT/path;return f'data:image/{p.suffix[1:]};base64,'+base64.b64encode(p.read_bytes()).decode()
def image(path,alt,cls=''):
 return f'<img class="{cls}" src="{uri(path)}" alt="{alt}">'
r=json.load(open(OUT/'review/validation.json'));plan=json.load(open(SRC/'production_plan.json'))
html='''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Carapagos — animations V4 / GIF Dracaufeu</title><style>body{background:#101927;color:#edf2f7;font:16px/1.55 system-ui;margin:0}main{max-width:1180px;margin:auto;padding:34px 22px}h1{font-size:38px;line-height:1.15}h2{font-size:26px}p{color:#bfcdde}a{color:#8bded1}section{border:1px solid #33475b;border-radius:14px;padding:24px;margin:24px 0;background:#141f2e}img{image-rendering:pixelated;max-width:100%}.hero{text-align:center;background:#121927}.hero img{width:480px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}.card{border:1px solid #344d60;border-radius:12px;padding:16px;background:#142230}.card img{width:100%;background:#e9dec6;border-radius:6px}.scene img{width:128px;display:block;margin:auto}.meta{font-size:13px;color:#a9bacb}.notice{border-left:3px solid #ebc579;padding-left:16px}.portraits{display:flex;flex-wrap:wrap;gap:16px}.portraits img{width:120px;height:120px}.small{font-size:13px}.badge{display:inline-block;padding:5px 12px;border-radius:18px;border:1px solid #486a72;margin:4px}summary{cursor:pointer;color:#8bded1}footer{margin:28px 0;color:#a4b3c3}</style></head><body><main><p>PMD · CARAPAGOS · RECONSTRUCTION DEPUIS LES PORTRAITS VALIDÉS</p><h1>Animations et GIF — premier lot V4</h1><span class="badge">22 / 32 actions du profil complet</span><span class="badge">15 couleurs maximum</span><span class="badge">Alpha 0 / 255</span><p class="notice">Les portraits sont validés. Le nouveau sprite et ses animations sont des candidats à revoir, pas encore une finition artistique approuvée ni un import PMDO testé. La limite de10générations a empêché les10dernières actions ; elles ne sont pas remplacées par des copies d’Idle.</p><section><h2>Le GIF demandé : Méga-Évolution sur Dracaufeu</h2><div class="hero">'''
html+=image(Path('renders/mega_evolution_v2/gifs/mega_0.gif'),'Dracaufeu devient Méga-Dracaufeu X')
html+='</div><p><a href="renders/mega_evolution_v2/gifs/mega_0.gif">Ouvrir le fichier GIF directement</a> · 192 phases / 6,4 secondes. Ressource V2 inchangée.</p></section><section><h2>Nouvelle base : huit directions</h2><p>Forme de la tête guidée par les portraits approuvés, corps référencé sur Carapagos officiel, caméra comparée au Torkoal natif. Ce n’est pas la V1 récupérée, ni une nouvelle série sur la V2 rejetée.</p>'
html+=image(Path('exports/pokemon_custom/tirtouga_v4/review/model_x2.png'),'Nouveau modèle huit directions')
html+='<p>Trois directions latérales sont obtenues par symétrie des poses valides ; les marqueurs de nageoires droite/gauche sont inversés en conséquence.</p></section><section><h2>Animations de donjon</h2><p>Un GIF par action, avec les huit orientations. Les chronologies GIF proviennent des durées XML en ticks.</p><div class="grid">'
core=['Idle','Walk','Sleep','Hurt','Attack','Charge','Swing','Double','Rotate','Hop']
for name in core:
 m=r['actions'][name]
 html+=f'<article class="card"><h3>{name}</h3>'+image(Path(f'exports/pokemon_custom/tirtouga_v4/review/gifs/{name}.gif'),name)+f'<p class="meta">{m["columns"]} phases · 8 directions · {m["ticks"]} ticks</p><p class="small">{m["kind"]}</p><a href="exports/pokemon_custom/tirtouga_v4/review/gifs/{name}.gif">GIF {name}</a></article>'
html+='</div><details><summary>Corrections et limites des dessins</summary><ul>'
for note in r['manual_source_rejections_and_corrections']:html+=f'<li>{note}</li>'
html+='</ul><p>Le précontrôle minimum/donjon PASS ne certifie pas les proportions, les contacts des nageoires ou les marqueurs anatomiques. Les poses ont des maintiens/réutilisations déclarés ; une phase n’est pas forcément un dessin inédit.</p></details></section><section><h2>Animations de scène : douze premières séquences</h2><p>Une orientation DR de référence par action. Les chutes inclinent/retournent volontairement le corps. Ce ne sont pas des animations huit directions.</p><div class="grid">'
for name,m in r['actions'].items():
 if name in core:continue
 html+=f'<article class="card scene"><h3>{name}</h3>'+image(Path(f'exports/pokemon_custom/tirtouga_v4/review/gifs/{name}.gif'),name)+f'<p class="meta">4 phases · 1 vue de scène · {m["ticks"]} ticks</p><a href="exports/pokemon_custom/tirtouga_v4/review/gifs/{name}.gif">GIF {name}</a></article>'
html+='</div><h3>À dessiner ensuite — pas encore exporté</h3><p>'+', '.join(plan['actions_missing'])+'</p><p>Ces dix actions restent dans le mandat complet ; aucun fichier de substitution n’a été créé pour les faire passer pour terminées.</p></section><section><h2>Portraits approuvés : fonds déjà canoniques</h2><p>Images conservées sans régénération. Les fonds visibles correspondent exactement aux cellules du template fourni.</p><div class="portraits">'
for p in sorted(portraitdir.glob('*.png')):html+='<div>'+image(p.relative_to(ROOT),p.stem)+f'<p>{p.stem}</p></div>'
html+='</div></section><section><h2>Fichiers et contrôles</h2><p><a href="exports/pokemon_custom/tirtouga_v4/carapagos_v4_22_actions_candidate.zip">ZIP multi-sheet — 22 actions, XML + triplets PNG à la racine</a><br><a href="exports/pokemon_custom/tirtouga_v4/carapagos_v4_22_gifs.zip">ZIP des 22 GIF</a><br><a href="exports/pokemon_custom/tirtouga_v4/review/validation.json">Rapport technique et réutilisations de poses</a><br><a href="source/pokemon_custom/tirtouga_v4/README.md">Provenance et statut artistique</a></p><p class="notice">Minimum/donjon : PASS. Profil complet : FAIL attendu,10actions manquantes. Pas de test SpriteBot officiel, d’import ou de lecture PMDO. Les sources générées, notamment les scènes qui ont dérivé vers une illustration, nécessitent encore une revue artistique.</p></section><footer>Sources et portraits existants préservés. Portrait Normal/référence : SpriteCollab, crédits dans les dossiers source. Nouvelle production AI-assisted pour le mod ; pas de soumission publique annoncée.</footer></main></body></html>'
(ROOT/'apercu_carapagos_v4_animations.html').write_text(html)
print('actions checked',len(report)-4,'palette',len(allcolors),'gallery bytes',len(html))
