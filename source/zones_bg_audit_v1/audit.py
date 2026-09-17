"""Inspect every image in user upload 9ec9a081 and both maps in 3d801c76; no source edits."""
from pathlib import Path
import json,hashlib,subprocess,collections,base64,html
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'exports/zones_bg_audit_v1'
# Manual visual inspection of all 23 images, not inferred playability from filenames.
NOTES=[
('terrain','Arène côtière','Aplat sombre extérieur : hors terrain ; mer latérale et ouverture nord derrière les rochers.','Sable, falaises rouges, mer, écume, rochers isolés.','Élargir la zone de combat, déplacer les massifs ; conserver une arrivée sud et la perspective nord.'),
('BG','Aurore polaire','Image de fond complète : ciel étoilé et aurores ; pics de glace au premier plan, aucun sol praticable représenté.','Ciel, étoiles, aurores, frise de glace.','Réserver au fond d’une future map jouable ; sol à fournir séparément, pas de collision sur le BG.'),
('mixed','Clairière / bassin','Bande de ciel et nuages à l’horizon ; clairière centrale et approche sud au premier plan.','Ciel, canopée lointaine, sol, pierres du bassin, arbres devant.','Recomposer le contour rocheux et la clairière sans repeindre leur matériau ; ne pas ajouter d’eau sans décision explicite.'),
('BG','Mer nocturne et lune','Panorama complet : ciel, lune, étoiles, nuages, mer et reflet ; falaise à droite. Aucun sol de marche représenté.','Ciel, étoiles, lune, nuages, mer, reflet lunaire, falaise.','BG pour map jouable indépendante ; lune/reflet/nuages séparés, pas d’étirement de la lune.'),
('terrain','Entrée aride','Fond rocheux fermé, pas de ciel indépendant visible.','Sol sableux, falaise, bouche de grotte, arbres morts, petits cailloux.','Déplacer l’entrée et recomposer les parois avec les textures originales ; maintenir une approche dégagée.'),
('terrain','Forêt / grotte claire','Canopée arrière ; masse sombre de premier plan en bas, pas un ciel.','Sol clair, canopée arrière, falaise blanche, grotte, pierres, canopée avant.','Changer le tracé de clairière et la position de la grotte ; conserver la continuité des arbres.'),
('mixed','Route glacée','Ciel bleu et montagnes lointaines à séparer du corridor neigeux.','Ciel, montagnes, falaise arrière, neige praticable, rochers et glace avant.','Créer un autre coude de route ; ne pas transformer le BG montagneux en obstacles de terrain.'),
('interior','Chambre','Marge brune hors pièce ; aucun BG de paysage.','Vide extérieur, sol, murs arrière, murs avant, mobilier, tapis, cheminée.','Modifier le plan de pièce ; meubles et accès séparés, conserver les textures canoniques du bois.'),
('terrain','Jungle aux cascades','Grande paroi arrière verticale ; marges noires hors map.','Paroi, eau verticale, bassin/eau au sol, écume, herbe, chemin, végétation.','Recomposer la paroi et l’arrivée en plusieurs layers ; ne pas fabriquer des phases d’eau à partir de cette image fixe.'),
('terrain','Lac / sanctuaire cristallin','Eau périphérique derrière la plateforme ; pas de ciel.','Eau, plateforme cristalline, cristaux, piliers, lumières/reflets.','Changer la silhouette de plateforme et les placements ; vérifier la frontière eau/sol avant collision.'),
('duplicate','Forêt / grotte claire — copie','Même image que forêtglomypmdsky.png, vérification SHA-256.','Réutiliser la même source, pas un deuxième biome.','Un seul chantier de relayout, conserver les deux originaux.'),
('terrain','Caverne rocheuse sombre','Paroi sombre en haut et aux côtés ; pas de ciel.','Fond sombre, paroi, sol, blocs et végétation rare.','Nouvelle chambre/entrée en conservant roche et sol natifs.'),
('terrain','Clairière tropicale et rive','Canopée arrière et rivière au sud ; la rivière n’est pas un ciel/BG.','Herbe, chemin, arbres, fleurs, rive, eau, ponton, panneau.','Replacer clairière et arrivée de rive ; garder les fleurs/arbres/ponton indépendants.'),
('terrain','Couloir rocheux violet','Marges sombres et murs latéraux, pas de panorama.','Vide, parois arrière, sol du couloir, parois avant, blocs.','Modifier les courbes et embranchements ; largeur de marche constante à contrôler.'),
('interior','Salle dorée / ancien château','Mur et sol de salle, pas de panorama.','Dallage, motif central, colonnes, coffres, ombres.','Recomposer salle et rangées ; motif central conservé, coffres objets indépendants.'),
('mixed','Arène de glace','Bande de ciel bleu supérieure ; murs de glace arrière et avant entourent le sol.','Ciel, glace arrière, neige/sol, glace avant.','Changer forme de l’arène et accès, conserver la frise et les matériaux de glace.'),
('terrain','Grotte violette à deux issues','Marge sombre hors grotte, pas de BG de ciel.','Vide, paroi violette, sol, deux bouches, pierres.','Replacer les deux issues et le contour de chambre, sans recoloration.'),
('terrain','Terrain de roches / évents','Texture de terrain vue de dessus, aucun panorama.','Sol ocre, blocs, évents/creux clairs, ombres.','Nouvelle répartition des blocs/évents ; leur animation éventuelle exige des phases natives, non fournies ici.'),
('terrain','Passage rocheux bleu','Murs sombres arrière et premier plan ; pas de ciel.','Fond, paroi arrière, sol du passage, paroi avant, cailloux.','Changer courbe et largeur du passage, garder les textures bleutées originales.'),
('terrain','Jardin secret / puits lumineux','Marge verte vide hors plateforme ; faisceau lumineux au fond.','Vide, sol herbeux, chemin, arbres, fleurs, rochers, puits, faisceau.','Recomposer clairière et position du puits ; faisceau indépendant, sans repeindre le sol.'),
('multi_panel','Grotte étoilée — deux panneaux','Deux vues côte à côte, pas un seul panorama continu.','Fond sombre, sol bleu, parois, cristaux ; séparer les panneaux avant extraction.','Comparer les deux panneaux pour identifier leurs différences ; ne pas déclarer deux frames d’animation sur cette seule base.'),
('multi_panel','Souterrain dallé — deux panneaux','Deux vues côte à côte, pas un fond continu.','Vide, paroi, dallage, passage ; panneaux distincts.','Comparer et extraire séparément ; garder le motif du dallage, pas de duplication arbitraire en map longue.'),
('UI','Affiche de recherche','Affiche avec portrait et texte décoratif, pas une zone ni un BG jouable.','Papier / cadre UI ; portrait à traiter séparément si demandé.','Hors lot de terrains ; conserver comme référence de panneau/affiche.')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(parents=True,exist_ok=True)
 names=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r','-z','9ec9a081'],cwd=R).decode().strip('\0').split('\0');assert len(names)==len(NOTES)==23
 entries=[]
 for name,note in zip(names,NOTES):
  p=R/name;im=Image.open(p);kind,title,bg,layers,plan=note
  # Exact bytes must still match the user upload, not merely visual similarity.
  original=subprocess.check_output(['git','show',f'9ec9a081:{name}'],cwd=R);assert p.read_bytes()==original
  entries.append(dict(file=name,sha256=sha(p),dimensions_px=im.size,kind=kind,title=title,bg_identification=bg,layers=layers,layout_plan=plan,inspection='Manual visual review; source game/scene name not independently confirmed',status='Inventoried, not relaid out or runtime tested'))
 assert entries[5]['sha256']==entries[10]['sha256']
 maps=[]
 for name in ['cliffdaytest.rsground','cliffnordouesttest1.rsground']:
  p=R/name;assert p.read_bytes()==subprocess.check_output(['git','show',f'3d801c76:{name}'],cwd=R)
  obj=json.loads(p.read_text(encoding='utf-8-sig'))['Object'];ls=[]
  for l in obj['Layers']:
   c=collections.Counter(f['Sheet'] for col in l['Tiles'] for cell in col for seq in cell['Layers'] for f in seq['Frames'])
   ls.append({'name':l['Name'],'visible':l['Visible'],'render_layer':l['Layer'],'sheet_frame_references':dict(c)})
  maps.append({'file':name,'sha256':sha(p),'name':obj['Name']['DefaultText'],'texsize':obj['TexSize'],'obstacle_grid':[len(obj['obstacles']),len(obj['obstacles'][0])],'background':obj['Background'],'layers':ls,'finding':'BGAnim.AnimIndex is empty; sky actually referenced as 00_ciel within tile layers, not an assigned MapBG animation. Layer names are not trustworthy material labels. Cloud/nuage in cliffdaytest contains mixed prop/terrain sheets, not proof of animated clouds.','runtime':'NOT TESTED'})
 result={'scope':'All 23 PNGs from user commit 9ec9a081 and both .rsground files from 3d801c76. Older root references are not a new completed audit here.','entries':entries,'maps':maps,'counts':dict(collections.Counter(e['kind'] for e in entries)),'workflow':['Keep source originals immutable and hash recorded.','Confirm canonical texture source per map; uploaded reference is not automatically a license/provenance proof.','Extract canonical terrain/walls/objects without recoloring, mirroring or scaling texture pixels.','Use generated guide only for requested new layout, not final material pixels.','Build separate BG, ground, paths, walls, water, foreground, shadows and FX layers as applicable, all sharing origin and 8px grid.','For animations find real native phases, keep motion independent; do not claim a still screenshot provides a cycle.','Prepare entrances, collision and occlusion separately, then test in PMDO before calling playable.'],'relayouts_produced':0}
 (O/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 text='# Zones et BG — audit des derniers ajouts\n\n'+result['scope']+'\n\n**Aucun relayout encore produit dans ce lot.** Les images sont des références, pas une preuve de collision ou de jouabilité.\n\n'
 for e in entries:text+=f"## {e['title']} — {e['kind']}\n`{e['file']}` — {e['dimensions_px']}\n\nBG : {e['bg_identification']}\n\nLayers : {e['layers']}\n\nLayout : {e['layout_plan']}\n\n"
 for m in maps:text+=f"## {m['file']}\n\n{m['finding']}\n\n"
 (O/'AUDIT.md').write_text(text.rstrip()+'\n')
 page='<!doctype html><html lang="fr"><meta charset="utf-8"><title>Zones · BG et terrains</title><style>body{background:#15212b;color:#e3e6df;font:16px system-ui;margin:35px auto;max-width:1400px;padding:20px}p{line-height:1.55}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px}article{background:#24333d;border-radius:12px;padding:20px}img{max-width:100%;height:260px;object-fit:contain;image-rendering:pixelated}code{overflow-wrap:anywhere;color:#b9c5c7}b{color:#e1c281}</style><h1>Derniers ajouts · identifier les BG avant les relayouts</h1><p>23 images inspectées ; le décompte exact par catégorie est indiqué ci-dessous. Aucune map reconstruite ou déclarée jouable ici.</p><p>Textures canoniques conservées : seul le layout sera changé. Sol, BG, eau, murs, objets et FX resteront indépendants. Les noms de zones ci-dessous sont descriptifs ; identité officielle non certifiée.</p><p>'+html.escape(str(result['counts']))+'</p><section>'
 for e in entries:
  data=base64.b64encode((R/e['file']).read_bytes()).decode();page+=f'<article><b>{html.escape(e["kind"])}</b><h2>{html.escape(e["title"])}</h2><img src="data:image/png;base64,{data}"><p><code>{html.escape(e["file"])}</code></p><p><b>BG :</b> {html.escape(e["bg_identification"])}</p><p><b>Layers :</b> {html.escape(e["layers"])}</p><p><b>Relayout prévu :</b> {html.escape(e["layout_plan"])}</p></article>'
 page+='</section><h2>Les deux maps .rsground</h2><p>Le champ MapBG existe mais son AnimIndex est vide dans les deux fichiers. Le ciel est actuellement posé en tiles via <code>00_ciel</code>. Le nom « Cloud/nuage » ne prouve pas un calque de nuages : son contenu référence plusieurs feuilles de terrain et d’objets.</p>'
 for m in maps:page+='<h3>'+m['file']+'</h3><pre style="white-space:pre-wrap">'+html.escape(json.dumps(m['layers'],ensure_ascii=False,indent=2))+'</pre>'
 (R/'apercu_zones_bg_audit_v1.html').write_text(page+'</html>');print(result['counts'])
if __name__=='__main__':main()
