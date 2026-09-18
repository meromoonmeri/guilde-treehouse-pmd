"""Galeries et kit PNG/ORA ; exclut les bruts et scènes redondantes du ZIP."""
from pathlib import Path
import json,zipfile,html
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/cliffs_metano_v1'

def main():
 manifest=(OUT/'manifest.json').read_text();m=json.loads(manifest)
 template=(HERE/'viewer.html').read_text().replace('__MANIFEST__',manifest.replace('</','<\\/'))
 (OUT/'index.html').write_text(template.replace('<!--BASE-->',''))
 (ROOT/'apercu_cliffs_metano_v1.html').write_text(template.replace('<!--BASE-->','<base href="renders/cliffs_metano_v1/">'))
 cards=[]
 for z in m['zones']:
  links=' '.join(f'<a href="{z["files"]["terrain_"+mode]}" download>PNG {mode}</a> · <a href="{z["files"]["ora_"+mode]}" download>ORA {mode}</a>' for mode in ['jour','nuit'])
  cards.append(f'<article><h2>{html.escape(z["title"])}</h2><img src="{z["files"]["terrain_jour"]}" alt="{html.escape(z["title"])}"><p>{links}</p><p>{html.escape(z["visual_review"])}</p></article>')
 catalog='<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kit falaises Métano</title><style>body{background:#13242e;color:#e4ecdb;font:16px/1.5 system-ui;max-width:1400px;margin:30px auto;padding:20px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px}article{background:#233640;padding:20px;border-radius:12px}img{width:100%;image-rendering:pixelated}a{color:#d5e790}</style><h1>Falaises Métano — kit PNG / ORA</h1><p>Créations générées référencées Métano, pas tuiles natives certifiées. Lire <a href="LIRE_AVANT_IMPORT.txt">la notice</a> avant import. Les ORA contiennent cinq calques : ciel validé, astres, nuages natifs, océan phase 0 et terrain complet.</p><main>'+''.join(cards)+'</main></html>'
 notice='''FALAISES METANO — LOT 01 — 18 septembre 2026

4 compositions ; 8 terrains PNG jour/nuit ; 8 projets ORA.
PNG : 1264 x 848, RGBA. Import PNG to Tileset : grille 8 px,
158 x 106 cellules, marge 0, espacement 0, pas de lissage.
Choisir les fichiers *_terrain_jour.png / *_terrain_nuit.png.
Vérifier l’échelle à côté d’une falaise native avant intégration.

Dessins générés à partir des références Métano du dépôt, couleurs
ramenées à 328 RGB natifs. Aucune identité aux motifs natifs garantie.
Pas de nouvelle extraction spécifique de Bourg-Trésor.
Pas de Ground, de collisions, d’autotiles ou de test moteur.

Chaque ORA : ciel validé, astres, nuages natifs, océan phase 0, terrain.
Herbe, roche, bordures et escaliers restent réunis dans le terrain.
Pas de sol caché ni de morceaux indépendants reconstitués.
Les projets ORA sont statiques. Les 64 phases d’océan jour/nuit sont
fournies séparément (50 ms chacune, 3,2 s), reprises du lot V3.
Ciel/astres/nuages : sources validées c16efe12, sans resampling.
Nuages : 6 familles, bande 1440x208, wrap -4px/s, boucle 360s.
La mer seule est adaptée en nearest ; pas le terrain.

Ouvrir CATALOGUE.html pour les 4 images et leurs liens PNG/ORA.
Les bruts, scènes et l’atelier interactif restent dans le dépôt :
renders/cliffs_metano_v1/index.html
Le manifest référence aussi ces fichiers absents du kit compact.

Les deux sprites sont complets, isolés sur transparence.
Les deux zones atteignent les bords aux accès prévus.
Pas de garantie de raccord entre les compositions.
Candidats visuels à valider par l’utilisateur dans son jeu.
'''
 selected=[OUT/'manifest.json',OUT/'PLANCHE_FALAISES_METANO.png']+sorted((OUT/'contexte').glob('*.png'))
 for z in m['zones']:
  selected.extend(OUT/z['files'][key] for key in ['terrain_jour','terrain_nuit','ora_jour','ora_nuit'])
 with zipfile.ZipFile(OUT/'METANO_CLIFFS_V1_pack.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for p in selected:archive.write(p,str(p.relative_to(OUT)))
  archive.writestr('CATALOGUE.html',catalog)
  archive.writestr('LIRE_AVANT_IMPORT.txt',notice)
  archive.write(HERE/'verification.json','controles/verification.json')
  archive.write(HERE/'audit_couleurs.json','controles/audit_couleurs.json')
 print('Galeries générées ; ZIP',round((OUT/'METANO_CLIFFS_V1_pack.zip').stat().st_size/1024**2,1),'MiB')
if __name__=='__main__':main()
