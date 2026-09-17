"""Publish generated entrance PNGs, their Abyss variants, and a browsing catalogue.
No claim of canonical pixels, editable native layers, or PMDO integration.
"""
from pathlib import Path
import sys,json,hashlib,html
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/entrees_pmd_collection'
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'))
from night import night
TITLES=['Antre encaissé','Grotte sur corniche','Défilé du donjon','Forêt des racines','Caverne des cristaux','Antre du volcan','Grotte du givre','Ruines ensablées','Caverne de la cascade','Passage du marais','Gouffre du plateau','Sanctuaire lunaire']
BRANCH='arena/01a095e8-guilde-treehouse-pmd'
BASE='https://github.com/meromoonmeri/guilde-treehouse-pmd/blob/'+BRANCH+'/renders/entrees_pmd_collection/'

def main():
 files=sorted(f for f in OUT.glob('[0-9][0-9]_*.png') if '_nuit_' not in f.stem);assert len(files)==12
 board=Image.new('RGB',(1440,1400),'#132230');d=ImageDraw.Draw(board);records=[];cards=[]
 for i,(f,title) in enumerate(zip(files,TITLES)):
  im=Image.open(f).convert('RGBA');n=f.with_name(f.stem+'_nuit_abyss.png');night(im).save(n,optimize=True)
  preview=im.copy();preview.thumbnail((472,306),Image.Resampling.NEAREST);x=i%3*480;y=i//3*350
  d.text((x+12,y+10),f'{i+1:02d} - '+title,fill='white');board.paste(preview,(x+(480-preview.width)//2,y+36),preview)
  records.append({'id':f.stem,'title':title,'original':f.name,'night':n.name,'size':list(im.size),'origin':'AI-generated PMD-style image, not canonical tiles','integrated_in_pmdo':False,'layers':'flattened generated image','sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
  cards.append(f'<article><a class="picture" href="{f.name}"><img loading="lazy" src="{f.name}" data-original="{f.name}" data-night="{n.name}" alt="{html.escape(title)}"></a><h2>{i+1:02d} · {html.escape(title)}</h2><p>{im.width} × {im.height} px · <a href="{f.name}" download>PNG original</a> · <a href="{n.name}" download>Nuit Abyss</a> · <a href="{BASE+f.name}">GitHub</a></p></article>')
 board.save(OUT/'PLANCHE_12_ENTREES.png',optimize=True)
 (OUT/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
 page='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>12 entrées de donjon · collection PMD</title><style>body{margin:0;background:#10202d;color:#edf0e7;font:16px/1.55 system-ui}header{padding:28px 5%;border-bottom:1px solid #36505c}h1{margin:4px 0}header p{max-width:950px;color:#bccbd0}a{color:#bcdfa0}main{padding:24px 3%;display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px}article{background:#172d3b;padding:12px;border:1px solid #304956;border-radius:8px}img{width:100%;height:300px;object-fit:contain;image-rendering:pixelated;background:#0c1720}h2{font-size:18px}article p{font-size:13px}label{display:inline-block;padding:10px;background:#284050;border-radius:6px}footer{padding:20px 5%;color:#b3c3cc}</style><header><small>CRÉATIONS GÉNÉRÉES · TEXTURES PMD LIBRES</small><h1>Douze entrées, douze compositions</h1><p>Halcyon / Explorers of Sky comme direction artistique, sans contrainte de matière Métano pour ces nouvelles entrées. Images aplaties générées : ni tuiles canoniques, ni calques natifs, ni nouvelles cartes intégrées au mod.</p><label><input type="checkbox" id="night"> Afficher la variante filtrée Abyss</label><p><a href="PLANCHE_12_ENTREES.png">Planche PNG</a> · <a href="../metano_expeditions_actuel/README.md">Rendus PNG du mod existant</a></p></header><main>'''+''.join(cards)+'''</main><footer>Les images originales peuvent avoir une ambiance déjà sombre. La variante Abyss applique une fois le filtre à l’original ; aucune animation de cascade ou d’eau n’est créée. Les dimensions ne sont pas toutes multiples de 8 : préparation requise avant intégration PMDO. Ouvrir chaque PNG pour voir sa résolution complète.</footer><script>document.getElementById('night').addEventListener('change',e=>{document.querySelectorAll('img').forEach(im=>{im.src=e.target.checked?im.dataset.night:im.dataset.original;im.parentElement.href=im.src})});</script></html>'''
 (OUT/'index.html').write_text(page)
 lines=['# 12 entrées de donjon générées — collection PMD','', '**Nouvelles textures autorisées dans la DA PMD. Métano reste imposé seulement pour une extension explicitement Métano.**','', '[Planche PNG](PLANCHE_12_ENTREES.png) · [Galerie HTML](index.html)','', 'Ces PNG sont des créations du générateur, pas des prélèvements canoniques. Ils ne remplacent pas les entrées du mod Expéditions. Les images sont aplaties, sans calques éditables reconstruits à ce stade ; eau et cascades sont statiques. Certaines dimensions ne sont pas multiples de 8. Le filtre Abyss est appliqué une seule fois pour les variantes nocturnes.','', '| Entrée | Original | Nuit |','|---|---|---|']
 for r in records:lines.append(f'| {r["title"]} | [PNG]({r["original"]}) | [PNG]({r["night"]}) |')
 lines+=['','Les trois premières images prolongent la demande Halcyon initiale. Les neuf suivantes explorent librement forêt, minéraux, volcan, glace, désert, cascade, marais, gouffre et ruines. Le n°03 a produit un passage vers une grotte, et non le corridor ouvert initialement demandé au générateur : le résultat est conservé comme une proposition distincte.','', 'Références : compositions Halcyon/Crooked Cavern et EoSO/Drenched Bluff réellement décodées. Le Ground `aegis_cave_entrance` de PMD-SKY-PMDO-PORT a également été examiné ; son aperçu montre des couloirs intérieurs, pas une façade extérieure à recopier. Voir `source/entrees_pmd_collection/references.json`.','', 'Les rendus véritables du mod livré sont séparés dans [`../metano_expeditions_actuel/`](../metano_expeditions_actuel/README.md).']
 (OUT/'README.md').write_text('\n'.join(lines)+'\n')
 print('12 originals + 12 Abyss variants + board + gallery published.')
if __name__=='__main__':main()
