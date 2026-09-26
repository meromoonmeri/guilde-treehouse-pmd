# EFF1 — Entrée Foggy Forest, camp de base sud → nord, format 4:3 vaste

Demande : « oui enchaîne avec Foggy Forest Base Camp mais n'oublie pas que la méthode doit être employée ». Taille : **768 × 576 px = 96 × 72 cases de 8 px**.

- Aperçu : `apercu_entree_foggy_forest_sud_nord_v1.html` (racine) ou `review/EFF1_scene_animee.webp`.
- Pack PMDO 0.8.12 : `EFF1_projet_pmdo_0812.zip`.
- Calques PNG 8 px (préfixe `EFF1_`) : `EFF1_calques_png_8px.zip`.
- Source : `source/entree_foggy_forest_sud_nord_v1/`, 12 tests. Les utilitaires viennent d'EMF1, sur la branche de session.

## Méthode : textures canoniques par rendu généré référencé

La référence est `Foggy_Forest_Base_Camp_TDS.png`, qui n'avait jamais servi de référence principale. On y voit une herbe pâle menthe, un sous-bois sombre rayé, un chemin beige, des arbres ronds à reflets jaune-vert, des tentes Grodoudou roses, des rochers rosés et de petits buissons. La capture a été **passée au générateur comme image de référence**. Les prompts complets sont dans `manifest.json` → `generation`.

1. `bruts/decor_magenta.png` (1200 × 896) : décor complet et **nouveau** en 4:3.
   - Le chemin part du sud et traverse un grand camp avec quatre tentes, puis mène à une grotte encadrée de pierre, au nord.
   - La mare, à l'est du camp, est peinte en magenta.
2. `bruts/sol_complet.png` : herbe pâle complète, obtenue par édition du décor au premier essai, sans réparation.
3. `bruts/brume_poses.png` : 8 nappes de brume sur magenta. La planche est rendue en 4 rangées × 2 colonnes au lieu de 2 × 4 ; les poses sont repérées par composantes connexes.

## Découpage et calques

Le décor est découpé en pleine résolution, puis chaque matière est réduite séparément (×576/896, recadrage centré). Palettes séparées : terrain 96 couleurs, arbres 40, tentes 32, rochers 16, grotte 16.

Calques : eau, scintillements, sol complet, herbe du camp, chemin, sous-bois, buissons et fleurs, rochers, tentes, arbres, grotte, brume. Le Ground ajoute un calque Top vide.

## Animations

| Animation | Cadence | Origine |
|---|---|---|
| Mare façon Métano, sans liseré clair | 4 × 10 ticks | couleurs Métano exactes, pixels recalculés |
| Scintillements | 4 × 10 ticks | pixels Métano natifs |
| Brume | 48 × 5 ticks | nappes générées, réduites ×1/4 en 6 couleurs ; 10 nappes, dérive sinusoïdale de ±20 px (créée par nous) |

La brume est **tramée en damier fixe sur la carte**. Elle n'utilise que l'alpha 0/255 : on obtient l'effet voilé sans translucidité à prémultiplier dans les `.tile`. Toutes les boucles sont fermées (testé : la phase 48 égale la phase 0). La scène complète boucle en 240 ticks, soit 4 s.

## Fidélité au rip, mesurée par test

Même classifieur de matière sur la capture et sur le brut, distance euclidienne des moyennes RGB :

| Matière | Brut | Calque final |
|---|---|---|
| Herbe du camp | 34,3 | 38,6 |
| Chemin | 27,3 | 37,8 |
| Sous-bois | 37,6 | 37,5 |
| Tentes | 27,1 | 25,5 |

**Réserve** : le générateur a rendu une scène plus claire et laiteuse que la capture, comme un voile de brume. Les écarts sont donc nettement plus grands que sur les lots précédents (3 à 15). Je ne les ai pas corrigés, pour ne pas recolorer. Le seuil du test est de 40 (20 pour EMF1).

## Accès et collisions

- Sont praticables l'herbe du camp et le chemin. Une case est bloquée si plus de 25 % de sa surface est hors de ces deux calques.
- Bilan : 1475 cases praticables sur 6912.
- `entrance` est en (384, 560), au sud du chemin. `donjon_seuil` est en (376, 96), devant la bouche de la grotte.
- Un chemin libre de 16 × 16 px a été vérifié. Il n'y a aucun warp.
- Une petite bande d'herbe au nord de la grotte est marquée praticable mais n'est pas atteignable.

## Tests

12 tests PASS : hashes des bruts, dimensions et alpha, couverture et exclusivité des calques, palettes, fidélité, eau Métano, scintillements natifs, boucle et trame de la brume, ORA et scène, accès, préfixes uniques, relecture du Ground depuis les `.tile`. **Pas de test PMDO en jeu. L'art n'est pas validé.**
