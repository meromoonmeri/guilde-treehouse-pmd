# EMF1 — Entrée Mystifying Forest sud → nord, format 4:3 vaste

Demande : « passe à la suite ! », après la version EWC2 de Waterfall Cave. C'est la map suivante de la série des entrées de donjon sud → nord. Le biome **Mystifying Forest a été choisi par l'agent : à confirmer**. Taille : **768 × 576 px = 96 × 72 cases de 8 px**.

- Aperçu : `apercu_entree_mystifying_forest_sud_nord_v1.html` (racine) ou `review/EMF1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EMF1_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `EMF1_`) : `EMF1_calques_png_8px.zip`.
- Source : `source/entree_mystifying_forest_sud_nord_v1/`, 13 tests.
- Base : branche de session (après EWC2). Rien n'est repris des branches sœurs.

## Méthode : textures canoniques par rendu généré référencé

La référence est `Mystifying_Forest_entrance_TDS.png`, la capture de l'entrée de Mystifying Forest (PMD Explorers). On y voit une herbe vive à brins fins, un chemin rose-brun, d'énormes arbres à houppiers en boules et racines pâles, des rochers moussus et des herbes hautes sombres. Cette capture a été **passée au générateur comme image de référence**. Les prompts complets sont dans `manifest.json` → `generation`.

1. `bruts/decor_magenta.png` (1200 × 896) : décor complet et **nouveau** en 4:3.
   - Le chemin part du sud et serpente dans une grande clairière jusqu'à une ouverture sombre entre les arbres, au nord.
   - La mare plate est peinte en magenta.
2. `bruts/sol_complet.png` : herbe complète, obtenue par édition du décor. Elle sert de sous-couche.
   - Elle est issue du **4ᵉ essai** : les trois premiers ont rendu une réponse sans image.
   - Le brut contient deux zones sombres parasites, recouvertes dans le build par de l'herbe recopiée du même brut, sans retournement :
     - une bande en haut (58 rangées, 76 avec le dégradé) ;
     - un rectangle en bas (x 480-720, y 834-896).
   - Ces coordonnées sont dans `manifest.json` → `sol_complet_reparation`.
3. `bruts/feuilles_lucioles_poses.png` : planche sur magenta.
   - La rangée 1 donne 6 feuilles qui tournoient.
   - La planche compte trois rangées au lieu des deux demandées. Seule la rangée 2 (6 lucioles, de sombre à brillante puis sombre) est utilisée.
   - Les poses sont repérées par composantes connexes.

### Fidélité au rip, mesurée par test

Les distances sont celles entre couleurs moyennes RGB, avec le même classifieur de pixels des deux côtés.

| Matière | Rip | Brut généré | Distance brut | Calque final | Distance finale |
|---|---|---|---|---|---|
| herbe | 80,156,87 | 79,151,85 | 5,3 | herbe | 4,1 |
| chemin | 168,153,137 | 165,151,133 | 5,8 | chemin | 6,4 |
| feuillage sombre | 37,78,64 | 39,78,64 | 1,6 | arbres | 2,9 |
| roche et racines | 138,152,133 | 131,148,123 | 12,9 | rochers | 3,9 |

Le test impose une distance inférieure à 20 pour chaque matière, sur le brut comme sur les calques finaux.

## Normalisation, segmentation et palettes

**Réduction.** Le décor est réduit d'un facteur **uniforme** 576/896 → 771 × 576, puis recadré au centre à 768. La réduction se fait par moyenne **par classe** (`down_class` du gabarit Jungle), et chaque pixel revient à la classe de poids maximal.

**Segmentation** (en pleine résolution) :

- **Eau** : le magenta, dilaté de 2 px.
- **Profondeur** : les pixels sombres (lum < 42) reliés au bord nord, dans la zone centrale.
- **Chemin** : les pixels rose-brun, puis la grande composante.
- **Herbe praticable** : critère régional (luminance lissée > 92, rapport b/g lissé < 0,64), composante reliée au chemin.
  - Les coutures de 2-3 px entre chemin et herbe, ainsi que les petits trous, sont comblés. Sans cela, des lignes de cases bloquées coupaient le chemin de la clairière.
- **Houppiers** : dessous vert sombre bleuté (b/g lissé > 0,74), ou forte densité de reflets clairs, hors clairière.
- **Rochers** : blobs pâles épais, de teinte gris-vert (r − b moyen < 10). Les blobs beiges (r − b de 13 à 24 : troncs, racines) restent avec les arbres.
- **Berge** : aucune. La mare du décor n'a pas de rive distincte.

**Palettes séparées :**

| Groupe | Couleurs |
|---|---|
| Terrain (sol complet, herbe, chemin, herbes hautes) | 96 |
| Arbres | 40 |
| Rochers | 16 |
| Profondeur | 12 |

## Calques (bas → haut)

| # | Calque | Origine | Animation |
|---|---|---|---|
| 00 | eau (mare) | structure rivière Métano, **couleurs Métano exactes**, sans liseré clair contre la rive | 4 × 10 ticks |
| 01 | scintillements | pixels Métano natifs (6 groupes) | 4 × 10 ticks |
| 02 | sol complet | herbe générée séparément, zones sombres réparées | — |
| 03 | herbe | clairière praticable | — |
| 04 | chemin | chemin rose-brun du sud au nord | — |
| 05 | herbes hautes | touffes sombres et sous-bois | — |
| 06 | rochers | rochers moussus isolés | — |
| 07 | arbres | houppiers, troncs, racines et rochers pris dans les racines | — |
| 08 | profondeur | ouverture sombre au nord (l'entrée du donjon) | — |
| 09 | feuilles | 6 poses générées, 8 feuilles | 48 × 5 ticks |
| 10 | lucioles | 6 poses générées, 14 lucioles | 48 × 5 ticks |
| 11 | Top vide (`Layer=4`) | pour vos éléments | — |

La scène boucle en 240 ticks, soit 4 s (PPCM de 40 et 240). Il n'y a **pas de calque d'ombres** : les zones sombres du rendu sont des houppiers ou des herbes hautes, sans ombre portée séparable, et aucune n'a été inventée.

### Feuilles et lucioles

- **Feuilles** :
  - La fenêtre de 120 px est ramenée à 10 px (×1/12), dans la palette du calque arbres.
  - Chaque feuille part du bord bas d'un houppier qui domine l'herbe ou le chemin. Elle tombe d'environ 37 px pendant 30 phases, avec un balancement de ± 6 px et une pose qui change toutes les 2 phases, puis se repose 18 phases.
  - Les 8 feuilles sont décalées de 8 phases.
- **Lucioles** :
  - La fenêtre de 72 px est ramenée à 6 px, avec 8 couleurs tirées des lucioles générées.
  - Elles sont placées dans les zones sombres qui bordent la clairière : herbes hautes, orée, ouverture.
  - Chacune suit une petite boucle de Lissajous fermée sur 48 phases et clignote selon une pulsation de 12 phases (allumage, éclat, extinction, repos).
- **Contrôles (testés)** :
  - Les images sont recalculées à partir du manifeste.
  - La phase 48 est égale à la phase 0.
  - Aucune feuille ne saute d'une phase à l'autre, phase 47 → 0 comprise.
  - Il y a des feuilles et des lucioles visibles à chaque phase.

## Collisions et marqueurs

- `entrance` (384, 560) est au sud, sur le chemin. `donjon_seuil` (368, 144) est au bout nord du chemin, au pied de l'ouverture sombre. **Aucun warp.**
- 1 881 cases sur 6 912 sont praticables (l'herbe de la clairière et le chemin). Une case est bloquée si plus de 25 % de sa surface est hors de ces deux zones.
- Un chemin libre de 16 × 16 px a été vérifié (656 cases explorées). **À contrôler en jeu.**

## Honnêteté

- Le terrain, les feuilles et les lucioles sont **générés** à partir de la capture : ce ne sont pas des tuiles natives.
- Les trajectoires, les boucles et la chronologie sont créées par nous ; ce ne sont pas des animations officielles.
- L'eau est façon Métano (pixels recalculés, couleurs Métano exactes). Seuls les scintillements sont des pixels Métano natifs.
- Le biome a été choisi par l'agent : **à confirmer**.
- Aucun test fait dans PMDO ; art non approuvé (`art_approved: false`, `runtime_tested: false`).
