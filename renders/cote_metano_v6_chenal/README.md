# Les Terrasses du Chenal — Métano V6

## Statut

Première nouvelle map construite après la synthèse de `METHODE_COMPOSITION_MAPS_PMD.md`. C'est une **extension de matière Métano canonique** : le layout est nouveau, mais les pixels de terrain de jour sont prélevés dans les feuilles natives vérifiées. Les zones validées des lots V4/V5 restent inchangées.

- Canvas : **1024 × 768 px**
- Grille : **8 × 8 px**, `TexSize = 1`
- Direction : arrivée au sud, progression par le col central vers les terrasses nord
- Ambiances : jour et nuit Abyss
- Eau : 4 phases de rivière Métano, cadence de référence `FrameLength = 10` documentée dans `sprites/eau_metano/README.md`
- Statut : composition PNG multicouche vérifiée ; **pas encore une Ground PMDO, pas de collision/runtime validé, revue artistique 1× à poursuivre**

## 1. Références canoniques utilisées

### Matière

- `source/cote_v4_abyss/natifs/Metano_Town_Base.tile` — herbe native, rectangle `(0,640)-(128,768)`.
- `source/cote_v4_abyss/natifs/Metano_Town_Cliffs.tile` — face, retour, couronne et pied natifs :
  - face `(912,464)-(976,512)` ;
  - retour `(680,464)-(744,512)` ;
  - couronne `(912,448)-(976,464)` ;
  - pied `(912,528)-(976,544)`.
- Feuilles `_Night.tile` correspondantes d'Abyss V4, utilisées directement pour la variante nuit.

### Eau

- `sprites/eau_metano/Riviere_Metano_Compacte.png`, extrait sans redimensionnement des planches originales `Metano_Town_River_Animation_1..4.png`.
- Les 4 phases et le `FrameLength = 10` sont décrits et vérifiés dans `sprites/eau_metano/README.md` et `verification.json`.

### Composition PMD

- `source/cote_v5_expeditions/README.md` et `sprites/cote_v5_expeditions/layouts.json` pour la logique des silhouettes organiques, des plateaux et des bords hors-cadre.
- `renders/metano_expeditions_actuel/README.md` comme référence de continuité des dernières côtes Métano livrées ; aucun de ses pixels n'est collé dans cette nouvelle scène.
- Les études d'entrées Crooked Cavern / Brine Cave / Drenched Bluff ne sont pas utilisées comme textures : elles ne concernent pas cette composition ouverte.

La provenance et les hashes de la map sont dans `manifest.json`.

## 2. Structure générale de la map

La scène est composée de trois niveaux de lecture :

1. **Grande terrasse sud** : sol d'arrivée large, continu, touchant les bords ouest/est et le bord sud.
2. **Deux corniches hautes décalées** : une à l'ouest et une à l'est, avec un chenal sinueux entre elles.
3. **Cap nord et col central** : une masse plus haute reliée au sol par une continuité herbeuse de 8 px ; le col devient le chemin visuel sud → nord.

Le chenal n'est pas un rectangle : il contourne les plateaux et s'ouvre hors cadre. La route reste en herbe Métano parce qu'aucune texture de chemin inventée n'est introduite dans cette extension canonique. `masques/route.png` documente sa largeur et son dégagement, sans prétendre être une couche de pixels distincte.

## 3. Layers et fonctions

Tous les PNG ont le même canvas et commencent en `(0,0)`. Les calques 00–04 sont répliqués pour jour/nuit depuis les feuilles correspondantes ; les calques 05–09 contiennent le lit et les phases de la rivière.

| Ordre | Fichier | Fonction | Provenance |
|---:|---|---|---|
| 00 | `00_sol_herbe.png` | sol praticable de base | `Metano_Town_Base.tile` |
| 01 | `01_faces_falaise.png` | volumes verticaux des parois | `Metano_Town_Cliffs.tile` |
| 02 | `02_retours.png` | retours latéraux des masses | `Metano_Town_Cliffs.tile` |
| 03 | `03_couronnes.png` | rebords/sommets au contact de l'herbe | `Metano_Town_Cliffs.tile` |
| 04 | `04_pieds.png` | pieds et retours bas des falaises | `Metano_Town_Cliffs.tile` |
| 05 | `05_eau_fond.png` | substrat opaque du chenal sous les pixels de rivière | RGB dominant opaque de la source canonique, adaptation explicitement documentée |
| 06–09 | `06_eau_phase_01.png` … `09_eau_phase_04.png` | surface et motifs de rivière animés | quatre phases natives de `Riviere_Metano_Compacte.png` |

Il n'y a pas d'ombre noire générée ni de couche de décor ajoutée artificiellement : les ombres et modelés des faces restent ceux des modules natifs. Le ciel n'est pas peint dans le terrain ; il devra rester un `LayeredBG` indépendant lors de l'intégration PMDO.

## 4. Superposition volontaire

L'ordre est : sol → faces → retours → couronnes → pieds → lit de l'eau → phase de rivière. Les surfaces d'eau sont découpées par `masques/water.png` ; elles ne recouvrent ni le sol ni le col praticable. La phase de contrôle est la phase 01 ; les trois autres réutilisent exactement les mêmes coordonnées de modules et ne déplacent pas le chenal.

La nuit applique une seule fois la transformation Abyss V4 aux calques terrain et eau, avec alpha conservé. Elle ne reçoit pas le filtre de fond Guilde/Sharpedo et aucun calque déjà nocturne n'est refiltré.

## 5. Réutilisation des zones validées

Réutilisé :

- l'échelle de grille 8 px et le principe de couches séparées des zones Métano ;
- les familles de modules herbe/face/retour/couronne/pied déjà vérifiées ;
- la recette nocturne Abyss V4 ;
- les phases de rivière canoniques déjà extraites et vérifiées ;
- la logique de composition organique et de contact avec les bords.

Non réutilisé comme pixels : les compositions finales des côtes V4/V5, leurs masques de terrain et leurs layouts approuvés. Il s'agit donc d'une nouvelle silhouette, pas d'un relayout silencieux d'une zone existante.

## 6. Créations et adaptations nouvelles

- Le contour des trois terrasses, du col et du chenal est nouveau et défini sur la grille native.
- Les modules canoniques sont posés par passes cohérentes et clipped par les masques ; aucun pixel de jour n'est recoloré, tourné, miroiré ou agrandi.
- Le lit opaque du chenal est une adaptation minimale et déclarée : il reprend la couleur opaque la plus fréquente de la banque d'eau canonique pour éviter des trous transparents entre ses berges. Les motifs et pixels visibles de surface restent les 4 phases natives.
- Les masques `terrain`, `grass`, `water` et `route` sont nouveaux ; ils portent la géométrie et non une palette improvisée.
- Les fichiers de travail sont reconstruisibles par `source/cote_metano_v6_chenal/build.py`.

## 7. Cohérence et contrôles

`source/cote_metano_v6_chenal/verify.py` confirme :

- canvas identique 1024×768 et grille 8 px ;
- terrain, eau et route disjoints conformément aux masques ;
- contacts ouest/est/sud présents ;
- dix layers alignés par ambiance ;
- quatre phases de rivière présentes ;
- recomposition jour/nuit identique à la composition à l'arrondi près ;
- zéro pixel généré dans le terrain de jour, aucune mise à l'échelle des modules.

Niveaux de validation : A provenance enregistrée, B images PASS, C couches/recomposition PASS, D format PNG et manifest PASS, **E PMDO/runtime non effectué**. Une prochaine passe devra créer le Ground, dessiner les collisions, configurer le `LayeredBG`, vérifier l'échelle dans PMDO et contrôler le rendu/les transitions en jeu.

## Fichiers

- `apercu_cote_metano_v6_chenal.html` à la racine : aperçu avec calques activables, grille 8 px, jour/nuit, phase par phase et lecture de l'eau.
- `jour/` et `nuit/` : 10 couches PNG et `COMPOSITION.png` par ambiance.
- `jour/PREVIEW.png` et `nuit/PREVIEW.png` : compositions lisibles sur les fonds de référence ; **ne pas importer ces aperçus**.
- `bg_*.png` dans chaque ambiance : fonds séparés réutilisés uniquement pour l'aperçu, à remplacer/configurer comme `LayeredBG` dans PMDO.
- `masques/` : géométrie du terrain, de l'herbe, de l'eau et du chemin logique.
- `manifest.json` : sources, rectangles natifs, ordre des couches, placements et hashes.
- `verification.json` : résultat des contrôles reproductibles.

Reconstruction :

```sh
.venv/bin/python source/cote_metano_v6_chenal/build.py
.venv/bin/python source/cote_metano_v6_chenal/verify.py
```
