# Relayouts V1 — deux candidats, onze calques

Ouvrir `apercu_zones_relayout_v1.html` à la racine du dépôt : calques activables, références originales et parcours indicatifs. Les guides générés sont conservés dans `source/zones_relayout_v1/generation/` et ne fournissent **aucun pixel final**.

## Contenu

- **Clairière forestière** :768×360,7layers. Sol, canopée arrière, falaise/entrée entière, traces de terre, pierres, buissons avant, couverture végétale du pied de falaise. Falaise déplacée168px à droite ; approche en courbe, espace élargi. Le pied caché dans l’original reste caché : aucune roche invisible inventée.
- **Passage rocheux bleu** :768×360,4layers. Vide gris, sol, paroi arrière et crête avant. La crête avance de72px vers le bas ; couloir élargi. Modules240px : la référence répète ce motif avec une seule différence au bord droit (623,160), sans correction de l’original. Le coude du guide **n’est pas réalisé**, faute de retours natifs adéquats.

PNG `RelayoutV1_*` : seules images de calques destinées au montage. TSX8px fournis à titre de descripteurs, non testés dans Tiled. Origine commune0,0, ordre des calques dans `manifest.json`. Aucun .tile/.rsground moteur fabriqué ici. PNG de comparaison, masques de parcours et fichiersNPZ ne sont pas des ressources de terrain à importer.

`*_provenance.npz` contient `source_xy[y,x] = [x_source,y_source]`, ou[-1,-1] pour transparence. Chaque pixel visible RGBA est identique au pixel source enregistré. Pas de recoloration, miroir, rotation, mise à l’échelle ou mélange alpha. Seuls les sols homogènes sont assemblés par patches natifs et coutures de moindre différence (sans fondu), pas les falaises. Cela ne garantit pas à lui seul la qualité visuelle des raccords.

Sources utilisateur : `forêtglomypmdsky.png` et `rockroadpmd.png`, commit9ec9a081. Originaux byte-identiques, hashes conservés. Crédits des références aux ayants droit et auteurs PMD d’origine ; aucun transfert de droits/licence déduit du dépôt utilisateur. Noms descriptifs, identification officielle des scènes non certifiée.

96 testsPASS, dont7 nouveaux. **Art à examiner ; aucune collision, entrée/warp, occlusion de personnages ou exécution PMDO validée.** La ligne orange est uniquement une proposition de parcours. Autres zones et panoramas encore à produire, suivi dans `production_progress.json`.
