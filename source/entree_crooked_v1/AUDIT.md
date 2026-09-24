# Audit — méthode « map ⇒ layers de génération » + entrée grotte Crooked/Halcyon/Sky Peak

## 1. La méthode existe déjà (pas de création ex nihilo)

| Étape | Document de référence | Principe |
|---|---|---|
| Référence → générateur sur magenta → détourage → calques → assemblage | `source/layouts_magenta_v1/WORKFLOW.md` (+ `palette.py` : détourage partagé) | Chaque calque généré séparément sur fond #FF00FF, inondation depuis les bords, frange retirée |
| Maquette puis extraction par calque | `source/crooked_verdoyant_v1/AUDIT.md` §3–§6, `renders/crooked_verdoyant_v2_magenta/` | V1 = maquette d'entrée ; V2 = 9 calques magenta ; V3 = même pipeline sans downscale (928×1152) |
| Petits éléments → feuille de sprites | V2, leçon (1) | Les extractions directes de petites plantes échouent → feuille sur magenta, posée aux emplacements de la maquette |
| Compléments natifs certifiés | V1 `complement_natif/` | Rochers Crooked Objects+Shadows, arbres Vast Steppe, translation seule, provenance tuile par tuile |
| Fleurs natives animées | `renders/amp_plains_fleurie_v1/` (poses 0,1,0,2 ; 8/10/14 gf), `renders/applewoods_skygrass_v1/sprites/fleur_sky_*` (10 sprites × 4 phases Sky Peak @200 ms) | Poses natives replacées, jamais redessinées |

**« map ⇒ layer » dans ce lot** : entrée = plan de layout dessiné (`plan_zones.png` : paroi nord, bouche,
chemin sud→nord, emplacements arbres/fleurs) + références canoniques → sortie = calques générés détourés
+ compléments natifs. Le plan est passé au générateur avec les refs de style ; il ne fournit aucun pixel final.

## 2. Audit des textures demandées

- **Crooked Cavern** (`banque_canonique/cartes_natives/Halcyon__crooked_cavern_entrance.png`, 320×240) :
  roche ocre stratifiée, bouche sombre centrée, sol sableux. Feuille Base = scène unique non modulaire
  (audit V1 §2) → **la paroi 928 px de large DOIT être générée** (redessinée palette ocre, pas de pixels
  natifs). Rochers natifs réutilisables : `atlas/Halcyon__Crooked_Cavern_Objects` + `_Shadows`.
- **Arbres canoniques Halcyon** (`source/amp_plains_fleurie_v1/references/vast_steppe_layer_3/4.png`,
  Halcyon working-copy 1522c7a8) : arbres ronds, troncs (L3) et canopées (L4) déjà séparés nativement.
  Couple V3 : canopée (16,96,160,216) + tronc (72,160,120,216). **Natifs, translation seule.**
- **Herbe Sky Peak** (`source/sky_peak_v1/gif_0.png`, 504×504, sommet PMD2) : prairie verte native.
  Patches 24×16 extraits des zones sans fleurs (dominante verte, std bornée) → sol quilté natif.
- **Fleurs Sky Peak** (`renders/applewoods_skygrass_v1/sprites/fleur_sky_00..09_phase_00..03.png`) :
  10 sprites natifs × 4 phases @200 ms, réutilisés tels quels (provenance applewoods).
- **Chemin** : aucun chemin de terre natif dans ces trois sources → **généré** (sable Crooked, assorti
  au parvis de la bouche), calque séparé sur magenta.

## 3. Décision de production — `entree_crooked_v1`, 928×1152, sud→nord

Générations (économe) : **G1** paroi Crooked + bouche sur magenta (guide : plan + ref Crooked) ;
**G2** chemin sable + parvis sur magenta (guide : plan + sable Crooked). Le reste est natif.
Calques : 01_sol_herbe (natif), 02_chemin (généré), 03_paroi (généré), 04_bouche (généré, masqué),
05_rochers (natif), 06_fleurs (natif animé 4 phases), 07_troncs (natif), 08_canopées (natif).
Nuit Abyss exacte. Tout pixel généré est documenté « redessiné d'après refs », jamais « natif ».

## 4. Bruts (24/09/2026)

- **G1 rejetée** (`bruts/rejetes/`, 848×1264) : double paroi — un bandeau falaise bas
  barre le chemin vers la bouche. Le magenta était présent mais la composition est
  injouable (parvis surélevé sans escalier).
- **G1b retenue** (848×1264, 0 px magenta) : paroi unique + bouche centrée + sable
  plein cadre. Pas de détourage magenta : partition par masques matière (sable
  lum>175, bouche lum<110, entonnoir ombragé lum>85, éventail smoothstep + oscillation).
  Le générateur sort en 848×1264 : canevas adopté tel quel (divisible par 8,
  > caméras 640×360 et 848×480), au lieu du 928×1152 du plan. Aucun G2 (chemin) :
  le sable de G1b suffit, mis en forme par le masque d'éventail.
- Leçons : (1) interdire explicitement « second cliff / bandeau horizontal » dans le
  prompt ; (2) éventail linéaire = diagonale visible → smoothstep + oscillation ;
  (3) l'ombre portée de la gorge coupe le chemin (bande 85–175) → règle d'entonnoir
  documentée + priorité bouche ; (4) espacer les sites de fleurs (pas de chevauchement).
