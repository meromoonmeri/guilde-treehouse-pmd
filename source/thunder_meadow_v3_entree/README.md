# Thunder Meadow V3 — entrée de donjon (grotte nord, orage en contrebas)

Guides générés : `generation/entree_guide.png` (1er jet : la grotte en roche beige Crooked Cavern ne se fondait pas dans la falaise, rejeté) puis `entree_guide_b.png` (grotte creusée dans la même falaise brune, retenu). Références données au générateur : la carte 5394, la composition Crooked Cavern (Halcyon) et le guide V2.
Même traitement qu'en V2 : réduction BOX à 456×336, puis chaque pixel ramené à la couleur la plus proche de la palette 5394 (aucune couleur hors planche). Le dessin est généré, pas canonique.

Calques :
- `00_nuages` : mer de nuages en contrebas. Bande canonique des 112 premières lignes répétée verticalement, avec la palette flash sur 6 niveaux.
- `01_eclairs` : frames canoniques. Placement automatique dans le vide, là où l'éclair est le plus visible ; positions dans `manifest.json`.
- `02_montagne_grotte` : falaise nord et bouche de grotte.
- `03_terrain`
- `04_details` : rochers bleus.

`seuil_donjon` : (228, 128), direction nord. La destination n'est pas configurée.
Limites : collisions 8 px indicatives, raccords de la bande de nuages répétée (visibles seulement dans les gorges), rien n'a été testé en jeu.
