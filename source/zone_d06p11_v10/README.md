# Zone D06P11 V10 — falaise en tuiles ROM canoniques
Dérivé V9, même cadrage (544×640), même mer/ciel/astres.
## Terrain (`canon_terrain.py` → `generation/terrain_canonique.png`)
- **Pixels de roche, sable et grotte = tuiles 8×8 exactes de la ROM d06p11a** (rendu `source/zone_d06p11_v1/source_rom/d06p11a_f0.png`) : aucune recoloration, rotation, miroir ni redimensionnement en mode jour. Provenance case par case : `generation/provenance_tuiles.json`.
- Mur : périodes ROM mesurées (120 px vertical, 80 px horizontal) → pavage **sans couture et continu jusqu'au bord haut** (plus de bout de sommet visible).
- Lèvres sous les terrasses et pieds de mur au-dessus du sable : vraies rangées ROM, ancre commune par série de colonnes voisines.
- Grotte : bloc ROM d'origine (bouche + sol), raccordé au mur par couture d'erreur minimale (image quilting) ; chaque pixel reste ROM.
- Non canonique : silhouette extérieure (reprise du guide généré V9) + liseré 1 px de la couleur la plus sombre de la roche ROM. Bords du sable lissés (médiane) → collisions recalculées : 1353 cases, zone unique ; sol de la bouche = warp à poser.
- Limites : raccords sable/roche en marches de 8 px, légère couture à gauche du bloc grotte, transition lèvre→mur visible sur les falaises basses.
## Berge animée contre la falaise
Principe repris de la rivière de Métano Town (Halcyon, 4 planches, FrameLength 10) : liseré sombre collé à la roche, bande claire à largeur ondulante, reflets courts qui glissent. 4 phases × 10 f (167 ms), procédural dans la palette de la mer — pas des pixels Métano.
## Crépuscule/nuit : étalonnage couleur du terrain (non canonique par nature). Non testé en jeu.
