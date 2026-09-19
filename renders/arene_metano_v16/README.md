# Arène V16 — layout V15, matière Métano Town

## Correction appliquée

La map ne reprend pas la méthode de la précédente Côte Métano V6 : celle-ci assemblait des modules sur des polygones procéduraux et ne correspondait pas au workflow du dernier agent.

Cette V16 reprend précisément la méthode demandée :

1. le **layout de la zone du dernier commit** `renders/arene_halcyon_v15/couches/terrain_fixe.png` sert de référence de géométrie ;
2. son alpha et sa lecture des surfaces servent uniquement à produire les masques de layout ;
3. tous les pixels générés de glace, de sol ou de cliff de V15 sont exclus du résultat final ;
4. les cellules finales sont sélectionnées dans les tilesets canoniques Métano Town en grille 8 px ;
5. l'herbe, les faces, les couronnes et les pieds de cliff sont exportés en couches séparées ;
6. ciel, étoiles et nuages sont séparés du terrain ;
7. aucune structure ni mer n'est ajoutée.

Il ne s'agit donc pas d'une greffe d'une ancienne map ou d'un collage de fragments : **référence de layout → sélection de tuiles canoniques → composition multicouche**.

## Référence de layout

- Référence : `renders/arene_halcyon_v15/couches/terrain_fixe.png`.
- Dimensions conservées : **928 × 1152 px**.
- Grille : **8 × 8 px**, soit 116 × 144 cellules.
- Le grand bassin central, l'ouverture de l'arène, les masses de cliff latérales et les pointes périphériques servent de vocabulaire de forme.
- La glace, les cristaux, les fissures et les couleurs de la référence ne sont pas utilisées comme matière finale.

Le fichier de référence est conservé dans `layout_reference/` ainsi que les masques 8 px utilisés pour la sélection.

## Matière canonique Métano Town

- Herbe : `source/falaises_metano/natifs/Metano_Town_Base.tile`.
- Cliff : `source/falaises_metano/natifs/Metano_Town_Cliffs.tile`.
- Variante nuit : filtre Abyss V4 appliqué une seule fois aux layers, sans repeindre les pixels de jour.

La sélection est effectuée cellule par cellule à partir de la géométrie alpha du layout. Les RGB de la référence générée ne sont jamais copiés. Les exports jour contiennent **zéro pixel de texture générée**.

## Layers livrés

### Terrain

- `00_sol_herbe_metano.png` : remplissage du sol par tuiles natives Base Métano.
- `01_cliffs_faces_metano.png` : faces verticales, tuiles natives Cliffs Métano.
- `02_cliffs_couronnes_metano.png` : couronnes et bords supérieurs, tuiles natives Cliffs Métano.
- `03_cliffs_pieds_metano.png` : pieds et retours bas, tuiles natives Cliffs Métano.
- `TERRAIN_METANO.png` : recomposition transparente de ces quatre couches.

### Background et overlay

- `bg_00_ciel_fixe.png` : ciel séparé, issu de la référence de fond validée V15.
- `bg_01_etoiles_fixes.png` : étoiles séparées, non fusionnées au terrain.
- `overlay_nuages/NuagesWrap_00..54.png` : overlay de nuages indépendant, 55 phases.

Aucune couche `structure` et aucune couche `mer` n'est ajoutée dans cette version.

## Wrap de nuages

La bande validée `sprites/cote_v2/COTEV2_NUAGES_WRAP.png` mesure **2200 px** de large. Les 55 phases avancent de **40 px** :

- période spatiale : 2200 px ;
- période temporelle : 55 phases ;
- cadence : 100 ms par phase, soit 5,5 secondes ;
- le passage suivant la phase 54 revient exactement à la phase 00 ;
- la phase 55 n'est pas exportée comme doublon.

Deux copies jointives de la bande sont utilisées dans chaque frame. Le terrain ne bouge jamais. L'overlay est indépendant du ciel et des étoiles.

## Aperçu et limites

`jour/PREVIEW.png` et `nuit/PREVIEW.png` composent uniquement l'aperçu. Le terrain reste exporté séparément pour conserver l'architecture d'une vraie composition PMD.

Contrôles exécutés par `source/arene_metano_v16/verify.py` :

- alpha du layout V15 utilisé comme référence et non comme texture ;
- terrain final contenu dans le masque de layout ;
- recomposition exacte des quatre couches terrain Métano ;
- quatre couches Métano non vides ;
- 55 frames de nuages sur canvas uniforme ;
- wrap spatial et retour temporel exact ;
- absence de structure et de mer ;
- ciel/étoiles/nuages indépendants du terrain.

La map n'est pas encore un Ground PMDO : collisions, import, rendu moteur et transitions ne sont pas validés.

Reconstruction :

```sh
.venv/bin/python source/arene_metano_v16/build.py
.venv/bin/python source/arene_metano_v16/verify.py
```
