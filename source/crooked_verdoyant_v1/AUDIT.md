# Audit des références canoniques — zone « Crooked Cavern verdoyante » (sud → nord)

Audit réalisé AVANT toute génération (demande : « commence les générations une fois l'audit fait »).
Planche visuelle : `audit/planche_references.png` (tout à l'échelle 1×, sans recoloration).

## 1. Ce qui existe nativement dans la banque canonique

| Réf. | Fichier (banque_canonique/) | Taille | Contenu utile | Verdict |
|---|---|---|---|---|
| A | `cartes_natives/Halcyon__crooked_cavern_entrance.png` (+ `_L00_Base`, `_L01_Objects`, `_L02_Shadows`) | 320×240, 1 frame | **Seule scène Crooked Cavern native** : piliers de roche ocre/beige stratifiée, bouche de grotte sombre centrée en haut (≈ x 130–190, y 60–130), sol sableux clair, rochers en bas. | Référence maîtresse pour la roche et l'entrée. |
| A' | `atlas/Halcyon__Crooked_Cavern_Base.png` (1200 tuiles 8 px) | 320×240 | La feuille Base **est** la scène peinte entière (pas de modules répétables : chaque tuile n'existe qu'une fois). | Aucune paroi Crooked modulaire n'existe nativement → une paroi Crooked plus large que 320 px ne peut pas être assemblée sans répéter/miroiter des fragments (interdit par AGENTS.md). |
| A'' | `atlas/Halcyon__Crooked_Cavern_Objects.png` (116 tuiles, bbox 32,154 → 286,240) / `_Shadows.png` (83 tuiles) | 288×240 / 296×240 | 5 rochers ocre (2 gros, 3 petits) + cailloux, avec leurs ombres portées séparées. | Objets natifs réutilisables tels quels (translation seule). |
| B | `cartes_natives/vast_steppe_entrance.png` | 512×512 | Herbe claire (#8ac262 / #70bb56), arbres ronds complets (tronc dans `Vast_Steppe_Objects`, canopée dans `Vast_Steppe_Fringe`), fougères, fleurs, pierres brunes, sentier d'herbe rase. | Référence maîtresse pour le biome verdoyant (végétation, arbres). |
| B' | `atlas/Vast_Steppe_Objects.png` (689 t.), `Vast_Steppe_Objects_Under.png` (135 t.), `Vast_Steppe_Fringe.png` (959 t.) | 512×512 | Troncs + ombres d'herbe, rochers bruns, fougères, fleurs ; canopées dans Fringe. | Objets natifs réutilisables. |
| C | `atlas/Relic_Forest_Base.png` (5625 t.) | 600×600 | **Clairière sud → nord native** : lisière sombre (#275c3f), herbe claire (#729b68), chemin de terre beige-rosé (#b1a08f) qui monte du bord sud vers le nord. | Référence maîtresse pour la structure « chemin sud → nord dans une clairière » et pour la terre du chemin. |

Palettes dominantes mesurées (quantification 8 couleurs, `audit/planche_references.png`) :

- Crooked : `#f7d6a3 #a78e5e #8e7150 #615239 #c3a76e #735f42 #e0bf85 #4c3b2e` (ocre chaud, jamais gris).
- Vast Steppe : `#70bb56 #8ac262 #87d264 #314f24 #7c9856 #45883b #876c4d #b1e582`.
- Relic Forest : `#729b68 #275c3f #296c44 #267046 #277f4a #274f3f #1f463f #4a5d49`.

## 2. Ce qui n'existe PAS nativement (et qui justifie une génération)

- Aucune carte native ne combine roche Crooked et végétation : Crooked Cavern est un désert sableux.
- La roche Crooked n'est pas modulaire (1 scène unique de 320×240). Une bouche de grotte dans une paroi plus large, entourée d'herbe, ne peut donc être produite qu'en **redessinant** la paroi dans la palette et le style Crooked.
- Livraisons antérieures (`renders/crooked_verdure_v1`, `crooked_statique_v2`) avaient recoloré la roche en gris : refusé. Ici la palette ocre native est conservée (comme dans `antre_harmonie_v3`).

## 3. Décision de méthode (conforme à `renders/arene_glace_generee_v2` et `source/layouts_magenta_v1/WORKFLOW.md`)

1. Génération d'image guidée par les références A, B, C (images natives fournies au générateur), format portrait 4:5 → normalisé **512×640** (NEAREST), arrivée bord sud, bouche de grotte au nord.
2. Deux rendus : terrain complet sur fond magenta (#FF00FF) et sous-couche de sol complète (herbe + terre) pour que les calques hauts puissent être retirés sans trou.
3. Découpe en calques alignés (même origine 0,0) : sol complet, chemin, parois Crooked, entrée, arbres, rochers, végétation basse ; masques PNG ; ORA ; composition ; galerie HTML ; manifeste SHA-256 ; vérification de recomposition exacte.
4. Calque complémentaire **natif certifié** : rochers Crooked (feuille Objects + Shadows) et arbres Vast Steppe (tronc + canopée) posés par translation seule, avec provenance tuile par tuile.
5. Variante nuit = filtre Abyss exact (`source/cote_v4_abyss/night.py`) sur les calques.

Les pixels générés sont **redessinés d'après références PMD** ; ils ne sont pas des pixels natifs certifiés et sont documentés comme tels dans le README de rendu. Aucun test moteur PMDO n'est réalisé.

## 4. Fichiers de l'audit

- `audit/planche_references.png` — planche A/B/C/D/E + palettes (1×).
- `audit/ref_*_1x.png`, `audit/vue_*.png` — copies 1× des références et feuilles (fond magenta pour les feuilles à alpha).
- `audit/gen_ref_A_crooked_x2.png` (×2 NEAREST), `gen_ref_B_steppe_1x.png`, `gen_ref_C_relic_1x.png` — les trois images
  natives exactement fournies au générateur comme références (le ×2 n'est qu'une aide de lecture pour le générateur ;
  aucune de ces images n'entre dans les calques livrés).
- `audit/vue_arbre_natif_steppe.png`, `audit/vue_rochers_crooked_x3.png` — modules natifs retenus pour le complément.
