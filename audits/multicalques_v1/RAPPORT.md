# Audit qualité des générations multicalques — 24 septembre 2026

Demande utilisateur : « audit tes propres générations multicalques, tu vois bien qu'il y a un souci de qualité ». **Constat confirmé.** Les anciens fichiers ne sont ni modifiés ni supprimés : ce rapport les déclasse sans les effacer.

## Verdict chiffré

Contrôle bloquant `source/controle_qualite_pixel/gate.py`, étalonné sur trois jeux de calques canoniques natifs du dépôt :

| Jeu audité | Zones | PASS |
|---|---:|---:|
| **Références canoniques** (Vast Steppe, Altere Pond, forêt sud–nord V3) | 3 | **3** |
| Froggy Forest multicalque | 1 | 0 |
| Maison intérieure (générateur V2, V3, finale) | 3 | 0 |
| Zones duo V1 | 3 | 0 |
| Réseau de zones multicalques V1 à V4 | 44 | 0 |
| **Total généré** | **51** | **0** |

Détail : `gate_sortie.txt`, `gate_resultats.json`, mesures brutes `mesures.json`. Planche visuelle au zoom ×4 : `PLANCHE_ZOOM_X4.png`.

| Mesure | Canon | Nos multicalques |
|---|---|---|
| Couleurs par calque | 5 à 805 (1 397 pour une map Altere entière) | **13 000 à 245 000** |
| Pixels de couleur rare (< 4 occurrences) | ≤ 0,3 % | **5 à 89 %** : flou, anticrénelage, faux pixels |
| Semi-transparence hors ombres | ≤ 0,14 % | jusqu'à **14 %**, voire des calques 100 % semi-transparents |
| Magenta de détourage restant | 0 | **jusqu'à 362 000 px** (végétation Froggy) |
| Calques vides ou dupliqués | 0 | **21 vides, 31 doublons** sur 249 calques |

## Défauts constatés et causes dans le code

1. **Faux pixel art.** La sortie du générateur (≈ 1024 px, pixels simulés d'environ 2,5 à 8 px non entiers, bords lissés) est livrée telle quelle comme pixels finaux. Le canon Vast Steppe a 82 couleurs ; la composition Froggy en a 245 674.
2. **Réductions floues.** Les builders `network_zones_multicalques_v2/v3/v4` et `generator_v3` utilisent `thumbnail(..., LANCZOS)` / `resize(..., LANCZOS)`, ce qui produit des halos, du flou et des dizaines de milliers de couleurs intermédiaires. La cascade Crooked réduit au contraire de 1024 à 320 en `NEAREST` : une décimation qui supprime des pixels et crée de l'aliasing.
3. **Détourage cassé.** `key()` (Froggy, cascade Crooked, generator_v3) prend la couleur du pixel (0,0) comme clé. Si ce coin n'est pas magenta (végétation Froggy : coin vert foncé), le fond magenta n'est pas retiré du tout. La rampe `(d-55)*6` crée en plus des bords semi-transparents mêlés de magenta, d'où des franges roses (bassin de la cascade, murs de la maison).
4. **Calques incohérents entre eux.** Froggy a été produit en six générations indépendantes de la scène entière, une par calque. Les géométries ne coïncident pas et 82 % de la surface est couverte par plusieurs calques. Le composite ne correspond pas à l'empilement : 82 881 px diffèrent, à cause d'un fond ajouté.
5. **Faux multicalques.** Dans les douze zones du réseau V4, `01_sol_terrain_existant` = `03_decor_existant` = `composite` à l'octet près, et `02_salle_vide` / `04_cadre_layout` sont vides. V1, V2 et la maison V3 contiennent des calques entièrement semi-transparents (voiles). Dans les zones duo, `00_fond` et `01_terrain` sont tous deux 100 % opaques (le terrain masque le fond) et `03_layout_ovale` est vide.
6. **Hors grille.** Tailles 1108×960, 1121×944 et 400×250 : pas multiples de 8, donc inimportables proprement via PNG to Tileset.
7. **Nom sans rapport avec le contenu.** Dans les réseaux V3 et V4, `lisiere_foret` et `route_ruines` ont un composite identique. `riviere_jungle` montre une cavité rocheuse sans rivière ni jungle.
8. **Cascade Crooked V2.** Filet d'eau rectiligne peint sur une roche recolorée, frange magenta autour du bassin (40 px dans la composition, 74 dans la frame d'eau), 4 378 couleurs. L'« animation » décale tout le calque de −2 à +2 px verticalement : ce n'est pas un écoulement.
9. **Guide généré pendant cette session** (`source/entree_steppe_v1/guide/guide_layout_genere.png`) : 330 144 couleurs, 34 % de couleurs rares. Il sert **uniquement de guide de layout** (méthode choisie : générateur puis tuiles natives) et ne doit jamais fournir de pixels.

## Règle désormais appliquée

- Aucune sortie du générateur n'est livrée comme pixels de map. Le générateur donne la composition ; les pixels finaux viennent des feuilles natives (8 px, sans rééchantillonnage, sans recoloration), ou bien d'une retouche pixel réelle ramenée à la grille et à la palette.
- Pas de `LANCZOS`/`BILINEAR`/`BICUBIC` sur des pixels de map. Pas de clé chroma lue sur le pixel (0,0) : clé magenta explicite et alpha binaire.
- Un calque = un contenu distinct, jamais vide, jamais une copie du composite. Le composite doit être exactement l'empilement des calques.
- `gate.py` doit afficher PASS sur chaque zone **avant** toute annonce de livraison. PASS ne veut dire ni validation artistique ni test PMDO.

## Suites proposées

- Les 51 zones restent en historique, déclassées « non conformes ». Il ne faut ni les corriger à la marge (un meilleur détourage ne rendrait pas des pixels réels) ni les présenter comme livrables.
- Reprises prioritaires, par assemblage natif et avec passage par le contrôle : Froggy Forest (entrée en cascade), puis la cascade Crooked.
- L'entrée Vast Steppe sud→nord, en cours, sera construite exclusivement depuis les feuilles natives Halcyon et contrôlée par `gate.py`.
