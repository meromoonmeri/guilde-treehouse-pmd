"""Verify rendered GIFs, make legacy sprite GIFs, package a standalone review gallery."""
from pathlib import Path
import json,base64,math,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/mega_evolution_v2'
legacy=OUT/'gifs/car apagos_v2_archive'.replace(' ','');legacy.mkdir(exist_ok=True)
sp=ROOT/'exports/pokemon_custom/tirtouga_v2/sprite_multisheet'
for node in ET.parse(sp/'AnimData.xml').findall('.//Anim'):
 name=node.findtext('Name');w,h=int(node.findtext('FrameWidth')),int(node.findtext('FrameHeight'));dur=[int(t.text) for t in node.findall('./Durations/Duration')];im=Image.open(sp/f'{name}-Anim.png').convert('RGBA');frames=[]
 for f in range(len(dur)):
  c=Image.new('RGBA',(w*8,h),(235,223,199,255))
  for d in range(8):c.alpha_composite(im.crop((f*w,d*h,(f+1)*w,(d+1)*h)),(d*w,0))
  frames.append(c.convert('RGB').resize((w*8*2,h*2),Image.Resampling.NEAREST))
 frames[0].save(legacy/f'{name}.gif',save_all=True,append_images=frames[1:],duration=[round(t*1000/60/10)*10 for t in dur],loop=0,disposal=2)
checks={}
for path in sorted((OUT/'gifs').rglob('*.gif')):
 im=Image.open(path);duration=0
 for f in range(im.n_frames):
  im.seek(f);im.load();duration+=im.info.get('duration',0)
 if path.name.startswith('mega_'):assert duration==6400
 checks[str(path.relative_to(OUT))]={'size':im.size,'encoded_frames':im.n_frames,'duration_ms':duration,'loop':im.info.get('loop')}
for name in ['ground','rear_energy','sphere','front_energy','fracture','emblem']:
 im=Image.open(OUT/'atlases'/f'MEGAGEN_V2_{name}.png').convert('RGBA');assert im.size==(2880,4096)
 for i in [0,191]:
  cell=np.array(im.crop(((i%12)*240,(i//12)*256,(i%12+1)*240,(i//12+1)*256)))
  assert not cell[:,:,3].any()
 arr=np.array(im);assert not np.any(np.all(arr[:,:,:3]==[255,0,255],axis=2)&(arr[:,:,3]>0))
checks['atlas_validation']='6 RGBA atlases 2880x4096; first/last frame transparent; no opaque pure-magenta pixels'
checks['runtime']='NOT TESTED';(OUT/'verification.json').write_text(json.dumps(checks,indent=2)+'\n')

def uri(path):
 p=ROOT/path;ext=p.suffix[1:];return f'data:image/{ext};base64,'+base64.b64encode(p.read_bytes()).decode()
def embed(path,alt,cl=''):
 return f'<img class="{cl}" src="{uri(path)}" alt="{alt}">'
html='''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Méga — cycles générés & portraits</title><style>
:root{color-scheme:dark}body{margin:0;background:#0e1622;color:#e9f0f7;font:16px/1.6 system-ui}main{max-width:1100px;margin:auto;padding:40px 24px}h1{font-size:clamp(28px,5vw,48px);line-height:1.15;max-width:850px}h2{font-size:27px;margin:0 0 12px}h3{margin:8px 0}p{color:#bbcadb}a{color:#8ce1d7}section{margin:36px 0;padding:26px;border:1px solid #2a3d51;border-radius:18px;background:#121b29}img{max-width:100%;image-rendering:pixelated} .eyebrow{letter-spacing:.12em;font-size:12px;color:#8ce1d7}.badge{display:inline-block;border:1px solid #3c5766;border-radius:20px;padding:5px 12px;margin:4px;font-size:13px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:16px}.tile{background:#0d1521;border:1px solid #263d50;border-radius:12px;padding:15px}.tile img{width:100%}.hero{text-align:center;background:#121927;border-radius:12px}.hero img{width:480px;max-width:100%}.native{width:240px!important}.notice{border-left:3px solid #ecc573;padding-left:15px;color:#e3d2b3}.portraits{display:flex;flex-wrap:wrap;gap:12px}.portrait{text-align:center}.portrait img{width:120px;height:120px}button{font:inherit;cursor:pointer;background:#234152;color:#fff;border:1px solid #557e8f;padding:7px 14px;border-radius:8px}details{margin:16px 0}summary{cursor:pointer;color:#8ce1d7}footer{color:#8b9db1;font-size:13px}
</style></head><body><main><div class="eyebrow">ATELIER PMD · REPRISE AU GÉNÉRATEUR · V2</div><h1>Méga-Évolution : cycles d’énergie et nouvelle matière</h1><p>Les composants visuels de la V1 ont été remplacés par des planches générées. Les images clés sont détourées et calées, puis reliées par des intermédiaires au flot optique.</p><span class="badge">32 images clés utilisées</span><span class="badge">192 phases · 6,4 secondes</span><span class="badge">8 directions de personnage</span><span class="badge">6 calques RGBA</span><section><h2>Transformation complète</h2><p>Dracaufeu → Méga-Dracaufeu X. Le changement de forme a lieu à la phase 78, lorsque la sphère est entièrement opaque. L’emblème persiste après l’éclatement, puis s’efface.</p><button onclick="document.querySelector('#hero img').classList.toggle('native')">Échelle native / ×2</button><div class="hero" id="hero">'''
html+=embed(Path('renders/mega_evolution_v2/gifs/mega_0.gif'),'Méga-Évolution complète en GIF')
html+='</div><p><a href="renders/mega_evolution_v2/gifs/mega_0.gif">Fichier GIF — sud</a> · <a href="renders/mega_evolution_v2/manifest.json">Chronologie et calques</a></p></section><section><h2>Layout multidirectionnel</h2><p>D · DR · R · UR / U · UL · L · DL. La caméra PMD reste fixe : le même effet radial entoure les huit orientations natives du personnage. Ce ne sont pas huit caméras 3D différentes.</p>'
html+=embed(Path('renders/mega_evolution_v2/gifs/mega_8_directions.gif'),'GIF des huit directions simultanées')
html+='<p><a href="renders/mega_evolution_v2/MEGAGEN_V2_directional_layout.png">Planche : 8 rangées de directions × 12 étapes</a></p><p>GIF individuels : '+' · '.join(f'<a href="renders/mega_evolution_v2/gifs/mega_{i}.gif">{d}</a>' for i,d in enumerate(['D','DR','R','UR','U','UL','L','DL']))+'</p></section><section><h2>Un GIF par composant animé</h2><div class="grid">'
for name,title,note in [('energy','Colonnes d’énergie','48 phases en boucle : formes et couleurs évoluent.'),('sphere','Sphère opaque','48 phases en boucle, matière spiralée générée.'),('break','Fissures → fragments','Séquence non cyclique : 43 phases, puis pause de lecture.'),('emblem','Emblème en flammes','48 phases en boucle. Motif flamme/S issu de la référence secondaire.')]:
 html+=f'<article class="tile"><h3>{title}</h3>'+embed(Path(f'renders/mega_evolution_v2/gifs/cycle_{name}.gif'),title)+f'<p>{note}</p><a href="renders/mega_evolution_v2/gifs/cycle_{name}.gif">Ouvrir le GIF</a></article>'
html+='</div><details><summary>Storyboard de la nouvelle animation</summary>'+embed(Path('renders/mega_evolution_v2/storyboard.png'),'Huit étapes du nouvel effet')+'</details><p class="notice">Contrôles d’image effectués, mais pas d’import ni de lecture Ground/Dungeon dans PMDO. Le calage est mesuré sur Dracaufeu/X uniquement. Les interpolations et les masques avant/arrière restent à juger visuellement.</p></section><section><h2>Carapagos — nouveaux portraits</h2><p>Cinq expressions générées individuellement puis reprises à 40 × 40, avec palette choisie et retouches de sourcils. Les fonds des cellules canoniques sont conservés pixel pour pixel là où le sujet ne les recouvre pas. Normal est le fichier SpriteCollab original inchangé.</p><div class="portraits">'
for name in ['Normal','Happy','Angry','Sad','Shouting','Surprised']:
 html+='<div class="portrait">'+embed(Path(f'exports/pokemon_custom/tirtouga_portraits_v3/portraits_individual/{name}.png'),name)+f'<div>{name}</div></div>'
html+='</div><details><summary>Voir à l’échelle native 40 × 40</summary>'+embed(Path('exports/pokemon_custom/tirtouga_portraits_v3/review/portraits_native.png'),'Six portraits à leur taille native')+'</details><details><summary>Comparaison : adaptations V2 en haut, nouvelles expressions V3 en bas</summary>'+embed(Path('exports/pokemon_custom/tirtouga_portraits_v3/review/before_after_x4.png'),'Avant après des portraits')+'</details><p><a href="exports/pokemon_custom/tirtouga_portraits_v3/portrait_sheet/portraits.png">Planche SpriteCollab partielle 200 × 160</a> · <a href="exports/pokemon_custom/tirtouga_portraits_v3/review/validation.json">Contrôle palettes et fonds</a></p><p class="notice">Minimum technique PASS ; dix émotions obligatoires restent absentes. La qualité artistique et l’admissibilité SpriteCollab ne sont pas certifiées par ce contrôle.</p></section><section><h2>Première version du sprite Carapagos</h2><p class="notice">Non retrouvée dans le checkout, le stash ou les objets Git. Une copie de l’ancienne image est nécessaire pour reprendre exactement la version préférée. Aucune nouvelle génération n’est présentée comme cette récupération.</p><details><summary>GIF d’archive : Idle et Walk de la V2 (pas la V1 demandée)</summary>'
for name in ['Idle','Walk']:
 html+=f'<h3>{name} — archive V2</h3>'+embed(Path(f'renders/mega_evolution_v2/gifs/carapagos_v2_archive/{name}.gif'),f'{name} V2 archive')+f'<p><a href="renders/mega_evolution_v2/gifs/carapagos_v2_archive/{name}.gif">GIF {name}</a> · Durées lues dans l’XML.</p>'
html+='</details><p><a href="source/mega_evolution_v2/recovery_carapagos.md">Recherche de récupération effectuée</a></p></section><footer>Sources générées conservées. Personnages de démonstration et portrait Normal : SpriteCollab, crédits originaux préservés. Les nouvelles expressions utilisent ce portrait comme référence et ne sont pas attribuées à ses artistes comme s’ils les avaient dessinées. Aucun fichier natif existant écrasé. Voir les README pour provenance et limites.</footer></main></body></html>'
(ROOT/'apercu_mega_generee_v2.html').write_text(html)
print('GIFs verified:',len(checks)-2,'gallery bytes:',len(html))
