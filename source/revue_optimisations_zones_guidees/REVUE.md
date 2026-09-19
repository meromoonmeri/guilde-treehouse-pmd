# Revue des optimisations proposées pour `build_zones_guidees.py`

**19 septembre 2026 · lecture du code + mesures reproductibles · rien n’a été appliqué.**

Objet : la note « Partie 1 — comment les textures PMD sont réutilisées / Partie 2 — propositions d’optimisation du rendu ». Chaque affirmation a été confrontée au code `source/build_zones_guidees.py` (152 lignes) et aux feuilles natives ; chaque proposition a été **mesurée** sur les deux zones réelles (`01_cirque`, `02_terrasses`) avec une réplique en mémoire de la boucle de sélection. Aucun fichier de `sprites/` n’a été modifié.

Reproduction (≈ 12 s) :

```bash
.venv/bin/python source/revue_optimisations_zones_guidees/mesure_optimisations.py
```

Sorties dans `resultats/` : `report.json`, `comparaison_crops.png` (quatre variantes au zoom ×3 sur la fenêtre la plus dense de la zone 01), `plage_93_113_escaliers_grotte.png`, `colonnes_interieur_85_92_114_121.png`.

La réplique reproduit exactement l’indice de l’audit antérieur (`audits/metano_import/RAPPORT.md`) : paires horizontales absentes du modèle natif **54,7 % / 43,0 %** (audit : 54,65 % / 42,98 %). Elle est donc fidèle au script d’origine.

---

## 1. Partie 1 — corrections de fait

| Affirmation de la note | Réalité vérifiée |
|---|---|
| « Les textures des cartes de référence PMDO (Crooked Cavern, Brine Cave, Drenched Bluff) … ce qui est réutilisé, c’est leur vocabulaire de tuiles » | **Faux.** Le vocabulaire vient de **Métano** (`Metano_Town_Cliffs` / `Metano_Town_Base`, Palika/Halcyon, `source/zones_guidees/native_tools.py` l. 6). Les trois cartes PMD Sky ne servent qu’à l’étude de layout du lot Expéditions (`source/cote_v5_expeditions/audit_references.py`) ; aucune de leurs tuiles n’entre dans un vocabulaire. |
| « Seules certaines colonnes du tileset source sont éligibles » | Les plages `57–92`, `114–121`, `162–188` ne sont pas des colonnes d’un tileset classé par type : la feuille `Cliffs` est **la carte de la ville elle-même** (189 × 189 cellules, coordonnées source = coordonnées carte, cf. `audit_zones_metano.py`). Ce sont donc des **positions x dans la ville**. Le filtre de lignes `y < 26 / 38 / 54` (l. 31) est omis dans la note. |
| « Résultat : un vocabulaire de N tuiles distinctes » | N = **148** (après `by_pixels`), sur 381 motifs distincts de la feuille complète. |
| « Le générateur produit une composition à la bonne résolution (ex. 2048 × 1536) » | Les guides font **1200 × 896** ; ils sont rééchantillonnés ×1,71 (NEAREST) uniquement pour la mesure des formes (l. 46). |
| « score = couleur (×0.5) + masque (×1.4) + raccord (×0.10) » | Exact (l. 72–76), mais **le reclassement n’opère que sur ≤ 22 candidats** : les 20 plus proches du k-d tree (features `rgb×.45` + `masque×1.2`) plus au plus deux continuations suggérées (l. 53, 64–71). Aucun poids ne peut faire entrer une tuile hors de cette présélection. |
| « Intérieurs > 95 % : une tuile de motif cohérent 64 × 48 px » | Seulement pour `ratio ≤ .64` (bloc `114–121 × 59–64`). Pour les trois autres classes de ton, c’est **une seule colonne** (`85`, `86` ou `92`) **répétée horizontalement**, soit un motif de **8 × 48 px** (l. 61). Ces colonnes sont des tranches du module **retour** de Métano (`source/cote_v5_expeditions/terrain.py` : `retour = Cliffs (680,464,744,512)` = x 85–92). C’est précisément le défaut confirmé par l’audit (« colonnes d’ombre répétées »). |
| Directions de voisinage : gauche + haut | Exact (l. 65). |

Le fond de la Partie 1 (les pixels du guide n’entrent jamais dans le résultat ; pas de rotation/recoloration/agrandissement ; sélection de vraies tuiles 8 px) est **juste**.

---

## 2. Partie 2 — mesures

Métrique principale : MSE RGB des coutures entre cellules de falaise adjacentes (colonne droite de A vs colonne gauche de B ; ligne basse vs ligne haute), toutes cellules placées. « Intérieur » = les deux cellules à ≥ 95 % de roche ; « bordure » = le reste. « Absent natif » = part des paires adjacentes qui n’existent nulle part côte à côte dans la falaise native (indice de l’audit). « Erreur masque » = désaccord roche/non-roche avec le guide sur les cellules de bordure (fidélité à la silhouette).

### Zone 01 — Le cirque des sources (17 549 cellules de falaise, **80 % d’intérieur**)

| Variante | Couture H moy. | dont intérieur | dont bordure | Couture V moy. | Absent natif H | Erreur masque | Cellules changées |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Baseline** (w = .10, G+H) | 941 | 851 | 1 226 | 841 | 54,7 % | 0,116 | — |
| P1a — w = .25 (G+H) | 936 | 851 | 1 204 | 835 | 54,6 % | 0,116 | 190 (1 %) |
| P1b — 4 directions, ICM × 3, w = .25 | 926 | 851 | 1 163 | 825 | 54,5 % | 0,116 | 391 (2 %) |
| P1c — 4 directions, w = 1.0 | 906 | 851 | 1 078 | 794 | 54,3 % | 0,118 | — |
| P1c — 4 directions, w = 3.0 | 870 | 851 | 932 | 742 | 53,7 % | **0,128** | — |
| P3 — hash sur [85, 86, 87, 92] | **1 063** | **1 013** | 1 221 | **1 010** | **90,0 %** | 0,116 | 12 801 |
| ALT — run contigu 85…91 dans l’ordre source | 820 | **691** | 1 224 | 829 | **39,0 %** | 0,116 | 4 257 |
| ALT + 4 directions ICM w = .25 | **805** | 691 | 1 164 | 813 | 38,8 % | 0,116 | 4 588 |

### Zone 02 — Les trois gradins (13 804 cellules, **87 % d’intérieur**)

| Variante | Couture H moy. | intérieur | bordure | Couture V moy. | Absent natif H | Erreur masque |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 867 | 825 | 1 142 | 783 | 43,0 % | 0,110 |
| P1a — w = .25 | 866 | 825 | 1 132 | 782 | 43,0 % | 0,110 |
| P1b — 4 dir. ICM w = .25 | 863 | 825 | 1 107 | 780 | 42,9 % | 0,110 |
| P1c — w = 3.0 | 828 | 825 | 848 | 737 | 42,7 % | 0,121 |
| P3 — hash | **1 027** | **1 011** | 1 129 | **957** | **88,4 %** | 0,110 |
| ALT — run 85…91 | 776 | **721** | 1 139 | 772 | **31,4 %** | 0,110 |

Termes du score pour la tuile gagnante (zone 01, cellules de bordure, médiane / p90) : couleur **0,011 / 0,036**, masque **0,153 / 0,306**, raccord **0,0028 / 0,0059**. Le terme de raccord est ~50 × plus petit que le terme de masque : passer son poids de 0,10 à 0,25 le laisse négligeable.

---

## 3. Verdict par proposition

### Problème 1 — poids de raccord 0,10 → 0,25 et voisinage à 4 directions

- **Effet mesuré : ≈ nul.** −0,6 % de couture moyenne pour le poids seul, −1,6 % avec les quatre directions ; 1–2 % des cellules changent. Cause : (a) le terme de raccord est deux ordres de grandeur sous le terme de masque, (b) le reclassement ne voit que ≤ 22 candidats, (c) **80–87 % des cellules de falaise sont des intérieurs choisis hors score** : aucun poids ne les touche.
- Le snippet proposé est **inopérant tel quel** : en balayage ligne par ligne, `chosen[i+1]` et `chosen[i+GW]` valent encore −1 quand la cellule `i` est traitée, donc les voisins droite/bas sont filtrés par `if ci >= 0`. Il faut au minimum : une seconde passe (la mesure ci-dessus utilise 3 passes ICM, convergence 3 429 → 341 → 11 changements), des suggestions symétriques `(sx−1, sy)` / `(sx, sy−1)`, et des comparaisons de bords orientées (`a[:, :, −1]` contre `C[ci][:, 0]` pour le voisin droit, `a[:, −1]` contre `C[ci][0]` pour le voisin bas).
- Monter le poids jusqu’à 3,0 (30 ×) réduit les coutures de bordure de 24 % mais **dégrade la silhouette** (erreur masque 0,116 → 0,128) et laisse les intérieurs intacts.
- **Conclusion : ne pas retenir comme levier principal.** Le voisinage à 4 directions est une amélioration correcte mais marginale, à intégrer seulement si le reste de la méthode est conservé.

### Problème 2 — tuiles de « lisière » dans la plage 93–113

- **Prémisse fausse.** Les x 93–113 de la feuille `Cliffs` contiennent **l’escalier (≈ 93–100) et la porte de grotte (≈ 108–113)** de la ville — c’est exactement ce que le commentaire de la l. 27 exclut. Voir `resultats/plage_93_113_escaliers_grotte.png`.
- **Le code proposé est un no-op** : `by_coord` n’est rempli que pour les x de `allowed` (l. 31), donc `[by_coord[x,y] … if 93 <= x <= 113]` est toujours vide. S’il était rempli, il poserait des marches d’escalier et des montants de porte en lisière d’herbe, avec un simple critère de couleur, sans terme de masque ni de raccord.
- La vraie lisière de Métano est ailleurs : (1) les **rangs de couronne** au sommet des faces (déjà dans le vocabulaire, cf. `couronne = Cliffs (912,448,976,464)` dans `terrain.py`) ; (2) la feuille **`Metano_Town_Fringe.tile`** (135 cellules, présente dans `source/cote_v4_abyss/natifs/`, **pas chargée** par `native_tools.py`, aucune cellule commune avec `Cliffs`). Une transition herbe/roche crédible se règle par la **grammaire couronne → face → pied** des modules, pas par une substitution colorimétrique cellule par cellule.
- **Conclusion : à rejeter sous cette forme.**

### Problème 3 — variation pseudo-aléatoire des intérieurs sur [85, 86, 87, 92]

- **Mesuré : nettement pire.** Coutures +13 % (H) et +20 % (V), intérieur 851 → 1 013, **90 % de paires non natives** (contre 55 %). Visuellement une mosaïque de bruit (`resultats/comparaison_crops.png`, panneau P3).
- Cause : 85 est le bord gauche ombré du module retour, 92 son rebord droit clair, 86–87 son corps. Coutures mesurées entre colonnes : 85→86 = 126, 86→87 = 284 (ordre source, faibles) mais 85→85 = 5 851, 92→86 = 1 471, 87→85 = 7 305. Tirer une colonne au hasard par cellule multiplie les mauvaises paires ; en outre cela **supprime la variation d’ombre guidée par le ton du guide**, que `AGENTS.md` demande de conserver.
- Le diagnostic (« intérieurs trop uniformes ») est réel mais la répétition actuelle est déjà une répétition de **8 px** de large (colonne unique) : le problème n’est pas le manque d’aléa, c’est l’unité d’assemblage. Le témoin **ALT** (colonnes 85…91 posées dans l’ordre source, 56 × 48 px) réduit à lui seul les coutures intérieures de 19 % et les paires non natives de 55 % → 39 %, sans toucher aux bordures ni au masque. Il reste pourtant une face sans sommet ni pied : la solution complète est celle des lots V4/V5 (modules **couronne / face 64 × 48 / pied / retours**, `source/cote_v4_abyss/build.py`, `source/cote_v5_expeditions/terrain.py`).
- **Conclusion : à rejeter tel quel ; la variation doit se faire au niveau du module (blocs entiers, ordre source respecté), pas de la cellule.**

### Problème 4 — nommage unique et contrôle des doublons

- **Diagnostic fondé.** Les sorties de `build_zones_guidees.py` sont `herbe.png`, `falaises.png`, `eau_1…4.png`, `berges.png`, `canonique_*.png` **dans chaque dossier de zone** : **24 basenames PNG en double** entre `01_cirque/` et `02_terrasses/` (12 du build sec/eau, 12 du découpage multicalques `01_sol.png` … `06_cascades_phase_4.png`). Le nommage « actuel » cité dans la note (`zone_{zone_id}.png`) n’existe pas dans le code, mais le risque est réel.
- **L’assertion proposée est vide** : `output_dir.glob('*.png')` ne liste qu’un dossier, où le système de fichiers interdit déjà les doublons. Il faut `rglob('*.png')` sur l’ensemble du lot (ou sur tout ce qui sera importé ensemble).
- Le préfixe `METANO_V5_` entre en collision de sens avec le lot V5 Expéditions (`v50812_*`). Convention déjà en place : `METANO_V3_*` (PNG d’import), `V40812_*` / `V50812_*` (tilesets du mod : 8 `.tile`, 8 basenames uniques vérifiés dans `mod_metano_expeditions_pmdo_0812.zip`). Proposition cohérente : `ZG_<zone>_<calque>.png` (`ZG01_FALAISES.png`, `ZG02_EAU_1.png`…) si ces PNG doivent un jour être importés directement.
- **Conclusion : à retenir (préfixe par zone + contrôle `rglob` global), en corrigeant le snippet.** Ne pas renommer rétroactivement les fichiers déjà livrés (viewer et ZIP y font référence) ; appliquer aux prochains lots.

### Problème 5 — validation en 3 niveaux

- Le protocole existe déjà en **5 niveaux** dans `MANUEL_METHODE_PMDO.md` § 20 : A provenance, B images, C formats, D installation, E moteur. Les niveaux 1–2 de la note correspondent à A–C et à E sans affichage (`source/pmdo_runtime/verify_ground_runtime.py`, `source/cote_v5_expeditions/runtime_test.py`).
- Le niveau 3 (rendu réel) **ne peut pas être exécuté ici** : `./PMDO -dev` plante avec le code 139 dans cet environnement. La mention « Rendu moteur garanti » du tableau récapitulatif est donc une **surdéclaration** : un protocole ne garantit rien tant que l’étape manuelle n’a pas été faite par l’utilisateur sur un échantillon.
- `verify_zones_guidees.py` vérifie provenance, alpha, atlas, animations et recomposition ; il **ne vérifie pas les doublons de noms** (voir Problème 4).
- **Conclusion : rien à ajouter au manuel ; corriger la formulation (« garanti » → « validé si l’échantillon passe en jeu »).**

---

## 4. Ce que ces mesures changent — et ne changent pas

- Les propositions 1–3 optimisent l’**assembleur cellule par cellule** de septembre 12, dont l’audit du retour en jeu a établi qu’il « ne préserve pas les volumes natifs ». `AGENTS.md` demande depuis des **modules natifs complets** ; les livraisons courantes (`cotes_metano_abyss_0812_pmdo.zip`, `mod_metano_expeditions_pmdo_0812.zip`) sont déjà construites ainsi. Améliorer le score de raccord de ce vieil assembleur ne rapprocherait pas les zones guidées du rendu Métano attendu.
- Si l’objectif est de **reprendre les deux zones guidées** (compositions approuvées), la voie compatible avec les règles est : conserver leurs masques de silhouette, et les reconstruire avec la grammaire de modules de V4/V5 — pas de retoucher les poids.
- Aucune de ces mesures n’est une validation artistique ni moteur ; ce sont des indices de continuité de pixels et de conformité à l’adjacence native.

## 5. Récapitulatif

| Proposition | Verdict | Motif principal |
|---|---|---|
| P1 poids .10 → .25 | ✗ inutile | −0,6 % ; terme 50 × sous le masque ; intérieurs hors score |
| P1 voisinage 4 directions | ~ marginal | −1,6 % avec ICM corrigé ; snippet fourni inopérant en une passe |
| P2 lisière via x 93–113 | ✗ faux | plage = escaliers + porte de grotte ; code no-op ; vraie lisière = couronnes + feuille Fringe |
| P3 hash sur [85,86,87,92] | ✗ nuisible | coutures +13/20 %, 90 % de paires non natives, perd l’ombre guidée |
| P4 noms uniques + contrôle | ✓ à retenir | doublons réels ; corriger `glob` → `rglob`, préfixe par zone |
| P5 validation 3 niveaux | = déjà couvert | protocole 5 niveaux existant ; « garanti » à retirer |
