# CANON1 — import dans PMDO 0.8.12

Deux routes séparées, à ne pas confondre (elles ne prennent pas les mêmes fichiers).

## 1. Feuilles DTEF 24 px (génération de donjon)

`DTEF/<banque>_<jour|nuit>/`

* `tileset_0.png`, `tileset_1.png`, `tileset_2.png` : 432 × 192 px, trois blocs de
  6 × 8 cases de 24 px — Wall, Secondary, Floor ;
* `tileset_<v>_frame<groupe>_<indice>.<duree>.png` : bandes de frames animées, une
  par groupe natif et par variante qui le possède ;
* la durée est en **frames moteur**, pas en millisecondes.

Sur une **copie de test** du projet, après extraction de l’archive :

```sh
./PMDC -raw "<chemin>/DTEF/<banque>_jour/" -convert autotile
```

Préfixez ou déplacez les dossiers pour éviter d’écraser un tileset existant ; les
feuilles de nuit sont des adaptations filtrées, pas des natives distinctes.

## 2. Ground 8 px (éditeur de zones)

`PMDO/Data/Ground/*.rsground` + `PMDO/Content/Tile/*.tile` + `PMDO/Mod.xml`

Fermer PMDO, puis depuis le dossier extrait :

```sh
python PMDO/INSTALLER.py "CHEMIN/PMDO/MODS/ton_mod" --dry-run
python PMDO/INSTALLER.py "CHEMIN/PMDO/MODS/ton_mod"
```

L’installateur partagé refuse d’écraser une carte déjà modifiée, **fusionne**
`Content/Tile/index.idx` avec les tilesets du mod et sauvegarde l’ancien index.
Ne pas copier le `index.idx` livré par-dessus celui d’un mod existant : il ne
contient que les banques CANON1.

Chaque tuile native de 24 px a été découpée en **neuf cellules de 8 px**, sans
aucune interpolation (`TexSize=1`). Les calques du Ground sont `01 Sol`, `02 Murs`,
`03 Secondaire` ; le cycle animé du secondaire est porté par les frames de la tuile
elle-même, donc sans script Lua.

## 3. Ce que le pack ne fournit pas

* aucune collision validée en jeu : les `obstacles` sont dérivés du layout
  (mur et secondaire bloquants) et restent à contrôler dans l’éditeur ;
* aucun warp installé : `arrivee`, `sortie` et `zone_reservee_structures` sont des
  **marqueurs**, pas des déclencheurs ; la destination de donjon doit être créée ;
* aucun Pokémon, objet, décor ou texte ajouté dans les maps ; les zones `R` du plan
  sont laissées vides exprès ;
* aucune exécution de PMDO, de rendu GPU ni de session de jeu dans cette reprise :
  les contrôles fournis couvrent les niveaux A à D du manuel, pas le niveau E.

## 4. Contrôle rapide après import

Ouvrir `canon1_JC1_entree_jour` : le sol doit être continu sous l’eau, les bords de
mur doivent rester nets au zoom 1×, le cycle d’eau doit avancer sans saut à la
dernière frame, et la nuit doit être la même image, seulement filtrée. Comparer avec
`apercus/CANON1_<carte>_jour_1x.png`, qui est le même rendu, à la même échelle.
