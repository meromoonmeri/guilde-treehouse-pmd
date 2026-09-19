# Méthode de production des maps PMD — générateur + pipeline natif

**Fiche de synthèse · 19 septembre 2026 · cible moteur : PMDO 0.8.12.**

Cette fiche condense la méthode documentée dans [`MANUEL_METHODE_PMDO.md`](MANUEL_METHODE_PMDO.md) (manuel exhaustif) et les règles approuvées par l’utilisateur dans [`AGENTS.md`](AGENTS.md). Elle ne les remplace pas : en cas de doute, ces deux documents font foi. Ce dépôt **alimente les imports** de PMDO ; il ne remplace pas le moteur.

Chaque chemin cité ci-dessous a été vérifié dans le dépôt à la date de la fiche (voir l’annexe « Vérifications »).

---

## 1. Ce que fait le générateur — et ce qu’il ne fait pas

**Rôle exact : guide de composition, pas source de tuiles.**

Le générateur d’images sert uniquement à proposer la composition :

- rythme des masses (falaises, terrasses, entrées de donjon) ;
- silhouettes organiques, profondeur, cadrages ;
- ambiances (jour, nuit Abyss, biomes différents).

Il **ne produit jamais** de tuiles certifiées pixel-perfect pour l’import du terrain Métano. Pixels générés ≠ tuiles canoniques. Cette distinction est absolue pour tout ce qui étend Métano.

Règles issues de l’expérience (`MANUEL_METHODE_PMDO.md`, § 2 et § 6) :

> « Une référence générée ne constitue jamais une preuve de fidélité des pixels natifs. »
> « Ne jamais tenter de réparer une roche non conforme par une succession de retouches générées présentées comme “pixel perfect”. »

> **Nuance importante (AGENTS.md).** Depuis le 13 septembre 2026 — et précisé par les corrections suivantes — les *nouvelles entrées indépendantes* et les *rendus générés demandés explicitement* suivent un régime différent : la composition générée complète **est** le livrable (détourée sur magenta, découpée en calques), et l’utilisateur a rejeté pour ces lots « l’assemblage de bouts de maps » même pixel-exact. Voir § 4.

---

## 2. Le pipeline complet (étapes dans l’ordre)

### Étape 1 — Références canoniques

Étudier les vraies cartes PMDO de référence (résultats réels de `audit_references.py`) :

| Référence | Dimensions | Grille | Calques graphiques |
|---|---:|---:|---|
| `Crooked Cavern` (Palika / Halcyon) | 320 × 240 px | 8 px | Base, Objects, Shadows |
| `Brine Cave` (Explorers of Sky Origins) | 648 × 504 px | **24 px** | un calque référant la feuille animée |
| `Drenched Bluff` (Explorers of Sky Origins) | 528 × 408 px | 8 px | Background, Details |

Pour chaque référence : résoudre un **commit précis**, télécharger le `.rsground`, lire toutes les références `Sheet` de ses frames, conserver le chemin distant, le hash de blob Git et le SHA-256 local. Registre : `source/cote_v5_expeditions/references/provenance.json`.

Ne pas généraliser une taille de cellule à partir d’un seul pack : lire les en-têtes (`TexSize`, `tileSize`).

### Étape 2 — Spécification de composition

Pour chaque carte, écrire **avant** de générer quoi que ce soit :

- sa fonction : espace libre, passage, belvédère, entrée de donjon ;
- le nombre de terrasses et leur ordre de profondeur ;
- les côtés où le terrain rejoint la limite de carte ;
- la position du point d’arrivée ;
- pour un donjon : seuil, largeur libre, direction d’entrée, zone de retour ;
- les zones réservées aux futures structures, le rôle des fonds, la présence de mer.

Une silhouette « nouvelle » doit l’être réellement : retourner, étirer ou recolorer une ancienne carte ne suffit pas.

### Étape 3 — Génération guidée

Fournir au générateur des références de **caméra, d’échelle et de composition**. Demander explicitement l’absence de structures et de détails non voulus. Produire plusieurs propositions, sélectionner la composition utile.

Contrôler systématiquement : nombre de panneaux, numérotation, objets parasites, continuité des terrasses, échelle de l’entrée. Exemple documenté : `source/cote_v5_expeditions/guide_compositions.png` a produit **douze panneaux à numéros répétés** pour une consigne de dix. Un tel guide **ne doit jamais être découpé automatiquement** en cartes ; les compositions retenues sont redéfinies dans une spécification explicite (`layouts.py`).

### Étape 4 — Reconstruction avec tuiles natives (régime Métano)

La composition générée sert de guide ; la carte réelle est construite avec :

- des tuiles natives de **8 px** extraites de Métano (terrain de référence du projet) ;
- des **modules complets** : sommet, face, pied, retours — pas des fragments 8 px choisis indépendamment (cause du rendu « désastreux » signalé en jeu, cf. `audits/metano_import/RAPPORT.md`) ;
- **aucune** recoloration, rotation, miroir, agrandissement ni interpolation des tuiles sources ; les transformations du guide servent uniquement à *choisir* des tuiles existantes ;
- des calques séparés : sol, parois, bordures, berges, surface de rivière, cascades ; versions sèches sans eau ni chemins ; quatre phases natives de l’eau.

Pipelines de référence : `source/build_zones_guidees.py`, `source/build_zones_multicalques.py`, `source/cote_v4_abyss/build.py`, `source/cote_v5_expeditions/{layouts,terrain,build}.py`. Format documenté dans `sprites/zones_guidees/README.md` et `README_multicalques.md`.

### Étape 5 — Filtre nuit Abyss (variante nocturne uniquement)

Source épinglée : dépôt `meromoonmeri/new-era-abyss-to-ascension-V4`, commit `55860b9a5eb48697a3cea3a8bdfce5f0529d6141`, script **`tools/tile_night.py`** (chemin *dans ce dépôt amont*), blob Git `438383f479e2d80a6a0b3be4cced4087470d9835`.

Dans le présent dépôt :

- copie de référence du script amont : `source/cote_v4_abyss/tile_night_reference.py` (même blob `438383f4…`) ;
- implémentation vectorisée utilisée par les builds : `source/cote_v4_abyss/night.py` ;
- vérifications : 1 421 couleurs des sources, puis les trois feuilles nocturnes complètes de New Era `Metano_Town_Base_Night.tile`, `Metano_Town_Cliffs_Night.tile`, `Metano_Town_Fringe_Night.tile` (`source/cote_v4_abyss/verification.json`).

Le filtre s’applique **une seule fois** aux variantes nuit (terrain, mer, nuages). Les pixels de jour restent natifs. Ne pas ajouter le filtre Guilde/Sharpedo par-dessus ; ne pas refiltrer une image déjà nocturne. Formule complète : `MANUEL_METHODE_PMDO.md`, § 12.

### Étape 6 — Audit avant livraison

```bash
# environnement (la .venv est ignorée par Git)
python3 -m venv .venv && .venv/bin/pip install -r source/requirements.txt

# provenance et lecture réelle des trois références (Ground + feuilles, 8 et 24 px)
.venv/bin/python source/cote_v5_expeditions/audit_references.py

# échelle et assemblage natif des zones guidées — passer la carte originale en argument
.venv/bin/python source/audit_zones_metano.py /chemin/vers/metano_town_palika.rsground

# contrôles propres à chaque lot : ils vérifient la sortie de leur propre chaîne
# (build.py → make_project.py → verify.py → package.py, dans .cache/), donc
# reconstruire le lot d'abord en suivant son README
.venv/bin/python source/cote_v5_expeditions/verify.py
.venv/bin/python source/cote_v5_expeditions/verify_access.py
.venv/bin/python source/cote_v4_abyss/verify.py

# désérialisation par le vrai chargeur PMDO (copie de cache, sans affichage ;
# nécessite l'installation décrite dans source/pmdo_runtime/README.md)
.venv/bin/python source/pmdo_runtime/verify_ground_runtime.py
```

> ⚠️ `source/audit_zones_metano.py` **réécrit** `audits/metano_import/mesures.json`. Lancé sans le `.rsground` original en argument, il remplace le rapport archivé par une version dégradée (`original_ground.available = false`). Toujours fournir l’argument, ou restaurer le fichier (`git checkout -- audits/metano_import/mesures.json`) après un essai à blanc.
>
> Les `verify.py` de lot échouent avec `FileNotFoundError` dans `.cache/` si le lot n’a pas été reconstruit dans la session : ce n’est pas un échec de contrôle, c’est l’absence de sortie à contrôler.

Contrôles attendus : dimensions divisibles par 8, pas de resampling, alpha propre (RGB à zéro sous alpha 0), absence d’objets parasites, continuité des terrasses, provenance de chaque tuile, hash des sources inchangés.

### Étape 7 — Import dans le moteur

L’utilisateur importe les PNG dans l’éditeur PMDO Dev via **PNG to Tileset**, taille d’import **8 px**.

Noms de fichiers **uniques** (`METANO_V3_*`, `v40812_*`, `v50812_*`) : l’importeur nomme les tilesets par *basename* ; deux fichiers homonymes venant de dossiers différents peuvent s’écraser.

---

## 3. Structure des livraisons

Livrables : des **zips PMDO** contenant des Ground complets jour + nuit (comptes vérifiés dans les archives) :

| Archive | Contenu | Préfixe |
|---|---|---|
| `cotes_metano_abyss_0812_pmdo.zip` | 10 terrains × 2 variantes = **20 Ground**, projet `cotes_metano_abyss_0812` | `v40812_*` |
| `mod_metano_expeditions_pmdo_0812.zip` | **40 Ground** = 20 nouveaux (7 falaises + 3 entrées, jour/nuit) + les 20 précédents, projet `metano_expeditions` | `v50812_*` + `v40812_*` |

Chaque zone a un identifiant unique. **Les anciennes livraisons sont toujours conservées — jamais écrasées.** Les archives antérieures (`cote_metano_v2_pmdo.zip`, `cote_metano_dix_zones*_pmdo.zip`, `cotes_v2_0812_pmdo.zip`, packs `sprites/…`) restent disponibles à la racine.

Les aperçus HTML (`apercu_*.html`) montrent le rendu visuel sans moteur, avec calques activables, zoom natif et exports PNG. Ils **ne valident pas** les raccords artistiques, les collisions ni l’intégration PMDO.

---

## 4. Deux régimes distincts : terrain Métano vs nouvelles entrées

### Terrain Métano (falaises de la ville, extensions)

Contrainte stricte : uniquement les tuiles natives de Métano ; aucune texture inventée par le générateur dans l’export final. Référence de nuit : les tilesets nocturnes de New Era déjà existants (Étape 5). Le générateur ne sert qu’à guider la composition ; les propositions approuvées sont conservées et ne sont pas régénérées lors d’un export en calques.

### Nouvelles entrées de donjon indépendantes et rendus générés

Autorisé depuis le **13 septembre 2026** (`AGENTS.md`) : textures **inventées dans la DA PMD** via le générateur, avec de nombreux layouts et biomes. La contrainte Métano exacte ne s’applique pas et ne doit pas être réimposée. Références de construction : les Ground PMD Sky (Crooked Cavern, Brine Cave, Drenched Bluff) — **layout et construction, pas copie de textures**.

Règles ajoutées ensuite par l’utilisateur pour ce régime :

- **Règle permanente des calques** : toute entrée est livrée en plusieurs calques (sol/chemin, végétation basse, arbres ou massif, ombres, profondeur du passage), jamais comme génération aplatie seule. Une image validée ne voit pas son layout régénéré pour la découpe.
- **Workflow magenta** : référence → générateur sur fond magenta → détourage alpha → calques → assemblage (`source/layouts_magenta_v1/WORKFLOW.md`). Toute eau ou aurore animée doit avoir plusieurs phases cohérentes ; ne pas livrer un fond statique en prétendant avoir conservé l’animation.
- **« Rendus générés, pas des bouts de maps »** : pour ces lots, l’utilisateur a rejeté la mosaïque de prélèvements natifs même vérifiée pixel-exacte. Ne pas la réintroduire sous prétexte de fidélité RGB.
- Un rendu généré n’est jamais présenté comme sprite canonique récupéré ni attribué à un artiste humain.

---

## 5. Limites documentées

- **Pas de test moteur avec affichage** : PMDO 0.8.12 installé depuis `RUNTIMEPMDO` (`source/pmdo_runtime/README.md`), mais `./PMDO -dev` plante avec le **code 139** dans cet environnement, y compris avec SDL offscreen. Les 40 Ground du mod Expéditions passent la **désérialisation par le vrai chargeur** (`DataManager.GetGround`, sans GPU) — dimensions, grille, calques, marqueurs — sans aucun rendu.
- **Approbation visuelle ≠ validation moteur** : l’import peut décevoir en jeu même si l’aperçu HTML est correct (retour utilisateur : qualité désastreuse et falaises trop petites lors de l’assemblage par fragments 8 px). Valider un échantillon au zoom natif 100 % puis en jeu avant de généraliser.
- **Un guide généré non conforme** (12 panneaux au lieu de 10, numéros répétés) n’est jamais découpé automatiquement ; sélection manuelle et spécification écrite.
- Les marqueurs `donjon_seuil` sont fournis mais **aucune destination de donjon n’est raccordée** ; `RACCORDEMENT_DONJONS.json` est une fiche, pas un téléporteur. Collisions à dessiner ou à vérifier en mouvement.
- Un test « 0 différence de pixel » prouve la provenance, pas l’échelle perçue, les raccords artistiques ni le motif.

---

## 6. Sources de référence du dépôt

| Chemin | Rôle |
|---|---|
| `MANUEL_METHODE_PMDO.md` | méthode complète (25 sections : références, échelle, calques, filtre Abyss, formats `.tile`/`.dir`/`.rsground`, installation, protocole de validation en cinq niveaux, erreurs connues) |
| `AGENTS.md` | journal des règles et corrections approuvées par l’utilisateur (fait foi) |
| `source/build_zones_guidees.py` · `source/build_zones_multicalques.py` | pipelines zones guidées / calques séparés |
| `sprites/zones_guidees/README.md` · `README_multicalques.md` | documentation du format des zones guidées |
| `source/cote_v4_abyss/` | pack Métano/Abyss : `night.py`, `tile_night_reference.py`, `build.py`, `verify.py`, `provenance.json` |
| `source/cote_v5_expeditions/` | mod Expéditions : `audit_references.py`, `layouts.py`, `terrain.py`, `build.py`, `verify.py`, `verify_access.py`, `runtime_test.py`, `README.md` |
| `source/audit_zones_metano.py` | audit lecture seule d’échelle et d’assemblage natif (écrit dans `audits/metano_import/`) |
| `source/pmdo_runtime/` | installation du vrai moteur et `verify_ground_runtime.py` |
| `source/layouts_magenta_v1/WORKFLOW.md` | workflow magenta pour les rendus générés en calques |
| `audits/` | rapports d’audit archivés (`metano_import/RAPPORT.md`) |
| `renders/` | aperçus et rendus générés, **non certifiés** |
| `exports/` | lots récents en calques (relayouts, arène, structures, végétation) et leurs ZIP |
| racine `*.zip` | packs PMDO prêts à importer, jamais écrasés |

---

## 7. À retenir pour toute nouvelle map

1. Générateur = guide de composition pour Métano, jamais source de tuiles ; livrable complet (en calques) uniquement pour les nouvelles entrées / rendus générés demandés.
2. Toujours spécifier la carte **avant** de générer : fonction, terrasses, bords, arrivée, seuil.
3. Terrain Métano : reconstruire avec des modules natifs 8 px complets, jamais des pixels générés, jamais de fragments isolés.
4. Calques séparés : sol / parois / détails / eau / ombres ; eau et effets animés en plusieurs phases.
5. Nuit = filtre Abyss exact appliqué une fois ; jour = pixels natifs.
6. Noms de fichiers uniques pour éviter l’écrasement à l’import (basename).
7. Auditer (provenance, alpha, grille 8 px, hash des sources) puis valider un échantillon au zoom natif et en jeu avant de généraliser.
8. Conserver toutes les anciennes livraisons ; ne jamais écraser ; identifiants nouveaux pour chaque lot.
9. Dire exactement ce qui a été validé (fichiers, chargeur natif) et ce qui ne l’a pas été (rendu, collisions, gameplay).

---

## Annexe — Vérifications faites pour cette fiche (19 septembre 2026)

- `source/cote_v5_expeditions/audit_references.py` exécuté : **PASS**, hashes des sources vérifiés, trois compositions reconstruites ; dimensions/grilles/calques du tableau de l’Étape 1 relevés en sortie.
- `source/audit_zones_metano.py` exécuté sans argument : sortie code 0 mais `audits/metano_import/mesures.json` modifié → restauré via Git ; d’où l’avertissement de l’Étape 6.
- Archives : `cotes_metano_abyss_0812_pmdo.zip` contient 20 `.rsground` (`v40812_*`) ; `mod_metano_expeditions_pmdo_0812.zip` en contient 40 (20 `v40812_*` + 20 `v50812_*`).
- Blob `438383f479e2d80a6a0b3be4cced4087470d9835` présent dans l’historique sous `source/cote_v4_abyss/tile_night_reference.py` ; **il n’existe pas de `tools/tile_night.py` dans ce dépôt** (c’est le chemin amont Abyss V4).
- **Il n’existe pas de `exports/audit_zones_metano.py`** ; le script est `source/audit_zones_metano.py`.
- Aucun asset, aperçu ni archive n’a été modifié pour produire cette fiche.
