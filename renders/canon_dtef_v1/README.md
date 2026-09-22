# CANON1 — quatre maps composées uniquement de cellules natives DTEF

Lot `source/canon_dtef_v1/` → `renders/canon_dtef_v1/`. Réponse à la demande
« poursuivre les maps avec les **textures canoniques** » : route pixels natifs
exactes, pas la route « rendu généré référencé ».

## Ce qui est livré

| Carte | Identité native | Plan |
|---|---|---|
| `JC1_entree` | `SouthernJungle` (donjon Jungle PMDO) | parvis sud → hall central → passée nord |
| `JC1_finale` | `SouthernJungle` | arène à fosses d’eau, pont central, plate-forme réservée |
| `TC1_entree` | `TreeshroudForest1` (forêt claire, Halcyon Relic Forest) | clairière large, deux miroirs d’eau, bosquets |
| `TC1_finale` | `TreeshroudForest1` | allée centrale bordée de deux lacs, zones réservées latérales |

Canevas 27 × 21 cases de 24 px = **648 × 504 px**, la dimension exacte de
l’entrée de Brine Cave auditée dans le manuel. Par carte : quatre groupes sémantiques
(`01` sol continu, `02` murs/relief, `03` secondaire statique, `04` secondaire animé),
un `.ora` éditable, la composition 1×, jour et nuit, plus les feuilles DTEF et un
Ground 8 px (voir `README_import.md`). Le mouvement est la cadence native elle‑même :
`SouthernJungle` expose un groupe de 16 frames à 19 ticks pour ses 47 masques
secondaires, `TreeshroudForest1` deux groupes de 12 frames à 18 et 6 ticks. Aucune
frame intermédiaire n'a été inventée.

## Pourquoi « canonique » veut quelque chose ici

1. **Une seule source de pixels.** `native.py` décode le `.tile` épinglé (SHA-256
   contrôlé contre `source/donjons_dtef_v2/references/provenance.json`) et ne connaît
   que ses cellules entières. Pas d’agrandissement, de rotation, de miroir, de
   recoloration, pas de « bombing » de pixels d’une variante à l’autre (contrairement
   à `renders/donjons_dtef_v2`, dont les feuilles modifiées restent inchangées).
2. **Les règles viennent du moteur, pas d’un goût.** `autotile.py` transcrit
   `AutoTileAdjacent.cs` (bits Dir4 = Bas, Gauche, Haut, Droite ; les bits de quadra
   seulement si les deux cardinaux et la diagonale continuent la masse ; 0xFF =
   intérieur) et `SelectTileVariant` (zéros de poids faible). Le `FieldDtefMapping`
   des feuilles est relu depuis `DtefImportHelper.cs`. Les 47 masques attendus sont
   recalculés et comparés.
3. **Le vérificateur recalcule tout.** `verify.py` rejoue le placement depuis les
   plans texte + les règles du moteur, puis compare **octet à octet** chaque cellule
   exportée à la cellule native, vérifie que aucun RGBA du rendu de jour n’existe
   hors des tuiles de la banque, que la nuit est le filtre Abyss appliqué **une**
   fois (alpha intact, non cumulable), que la composition en `t` égale celle en
   `t + cycle`, que les neuf cellules 8 px du Ground reconstituent la tuile native,
   et qu’une banque étrangère survit à la fusion d’index. 12 contrôles, niveaux A–D et aperçus.
4. **Ce qui n’est pas canonique est dit tel quel.** Le jour est natif ; la nuit est
   le filtre Abyss existant appliqué aux mêmes tuiles (adaptation demandée, pas une
   banque nocturne native) ; le découpage 24 px → 9 × 8 px est une conversion
   d’échelle sans perte, pas un rééchantillonnage ; les `obstacles`, marqueurs et
   liaisons sont une dérivation du layout, pas une validation moteur ; aucun rendu
   PMDO ni session de jeu n’a été exécuté dans cette reprise.

## Limites assumées de la matière

La banque d’autotile d’un donjon ne contient **que** les trois types Wall / Secondary
/ Floor : 905 cellules pour `SouthernJungle`, 1 234 pour `TreeshroudForest1`, aucune
tuile d’objet, d’escalier, de coffre ou de porte (vérifié : zéro coordonnée hors des
références des autotiles). Donc pas de props « canoniques » à poser : les
architectures sont exprimées par le layout, et les emplacements futurs (pieu,
escaliers, PNJ, scripts) restent des zones `R` vides, documentées. Inventer ces
props aurait été du dessin généré, ce que la demande écarte.

Le sol des donjons PMD est très uni par construction : le seul levier natif contre la
répétition est le choix de variante (0 ≈ ½, 1 et 2 ≈ ¼ chacun, distribution du
moteur). Les masses compactes (≥ 3 × 3) sont privilegiées pour que les raccords
pleins et les bords apparaissent ; un îlot de une ou deux cases rend mal — d’où les
remaniements de silhouette visibles dans l’historique des `layouts/*.txt`.

## Reproduire

```sh
.venv/bin/python source/canon_dtef_v1/build.py           # 4 cartes, jour+nuit, Ground, aperçus
.venv/bin/python source/canon_dtef_v1/verify.py          # 12 controles A-D + apercus, echoue au premier ecart
.venv/bin/python source/canon_dtef_v1/package.py         # archive autonome + SHA-256 + controle CRC
.venv/bin/python source/canon_dtef_v1/serve.py --port 8013   # PNG/WebP directs
```

Dépendances : Pillow, NumPy (le venv du dépôt suffit). `layouts/<carte>.txt` est
l’autorité géométrique : supprimer un fichier le régénère depuis les primitives,
l’éditer à la main change la map sans toucher au code. Le cache de build est
`.cache/canon_dtef_v1_pmdo/` (hors Git) ; `renders/canon_dtef_v1/PMDO/` en est la
copie livrée.

## Suite logique (non fait ici)

* deux duos de plus par banque (`marais`, `cristal`, `glace`, `desert`… sont déjà
  épinglés et décodables par le même outillage) ;
* reprise des cartes `dungeon_biomes_v2` restées à l’état d’étude, sur cette méthode
  native au lieu du generateur ;
* seuils de donjon réels : destinations, callbacks Lua, collisions et test en jeu —
  niveau E du manuel, jamais déduit des contrôles d’images.
