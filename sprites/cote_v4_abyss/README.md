# Dix côtes Métano — filtre nuit Abyss — PMDO 0.8.12

**Correction complète des dix terrains : 20 Ground jour/nuit.** Ce nouveau pack ne remplace ni les anciennes cartes, ni le ZIP V3.

- Aperçu autonome : `apercu_cotes_metano_abyss.html`.
- Pack : `cotes_metano_abyss_0812_pmdo.zip`.
- Projet : `cotes_metano_abyss_0812`.
- Cartes : `v40812_01_cap_large_jour` à `v40812_10_esplanade_arrondie_nuit`.

## Installation sans import PNG

1. Fermer PMDO et extraire **tout** le ZIP.
2. Copier le dossier `cotes_metano_abyss_0812` dans `PMDO/MODS/`, sans remplacer un dossier existant.
3. En mode développeur de **PMDO 0.8.12**, sélectionner le projet **Cotes Metano Abyss - Atelier 0.8.12**.
4. Dans l’éditeur **Ground**, ouvrir une carte `v40812_…_jour` ou `v40812_…_nuit`, située dans `Data/Ground/`.

Le projet contient son `Mod.xml` de type Quest, ses 20 `.rsground`, quatre banques `.tile`, six fonds `.dir`, son index complet et les scripts namespacés. Il s’agit d’un **projet d’édition**, pas d’une aventure jouable. Aucun PNG à réimporter : `TexSize=1`, grille native **8 px**.

### Ajouter les cartes à ton projet existant

Ne pas copier directement le `Mod.xml` ni l’`index.idx` du pack par-dessus les tiens. Utiliser l’installateur Python 3 depuis le dossier extrait :

```sh
python INSTALLER.py "CHEMIN/PMDO/MODS/TON_PROJET" --dry-run
python INSTALLER.py "CHEMIN/PMDO/MODS/TON_PROJET"
```

Il ignore l’index livré, fusionne les en-têtes des banques, sauvegarde l’index de destination et refuse d’écraser des cartes/ressources modifiées. Les scripts sont également ajoutés au namespace cible. Tests de simulation, double installation, conservation d’un autre tileset et refus d’une carte éditée : PASS.

## Ce qui a changé

### Roche et herbe

Le générateur ne fournit plus que les **masques de composition approuvés**. Aucun de ses pixels colorés, de ses pierres, de ses lisières ou de ses ombres n’est repris dans les nouveaux terrains.

Les couleurs de jour sont reconstruites depuis les véritables feuilles Métano :

| Partie | Source | Rectangle natif, en pixels |
|---|---|---|
| Herbe | Metano_Town_Base | 0,640 → 128,768 |
| Faces | Metano_Town_Cliffs | 912,464 → 976,512 |
| Retours arrondis | Metano_Town_Cliffs | 680,464 → 744,512 |
| Couronnes | Metano_Town_Cliffs | 912,448 → 976,464 |
| Pieds | Metano_Town_Cliffs | 912,528 → 976,544 |

Les grandes faces prolongent des panneaux cohérents de 64×48 px. Les retours suivent les bords des parois, au lieu d’ajouter des piliers à intervalles réguliers. Couronnes et pieds suivent les terrasses. Les pixels d’herbe contenus dans la source des couronnes sont exclus pour ne pas créer de marches vertes rectangulaires sur les parois.

**Aucune rotation, aucun étirement ni redessin des pixels sources.** Les modules sont translatés sur la grille 8 px, puis découpés par les masques approuvés. Cela reste un assemblage nouveau : ce n’est pas une falaise géante préexistante dans Métano. Les motifs se répètent pour couvrir les grandes hauteurs ; la fidélité des pixels ne garantit pas à elle seule des raccords artistiques parfaits.

### Le filtre nuit demandé, exactement

Source : `meromoonmeri/new-era-abyss-to-ascension-V4`, commit `55860b9a5eb48697a3cea3a8bdfce5f0529d6141`, fichier `tools/tile_night.py`, blob `438383f479e2d80a6a0b3be4cced4087470d9835`.

La version vectorisée conserve les calculs, l’ordre des opérations et la troncature entière du script original : luminance `(0.299, 0.587, 0.114)`, facteur `0.20 + 0.30 × luminance`, saturation `0.95`, multiplicateurs `(0.52, 0.70, 1.60)`, ajout bleu `6 × luminance`.

Le filtre est appliqué **une seule fois** aux cinq calques de terrain, aux nuages et aux huit phases de mer. Pas de filtre Guilde/Sharpedo supplémentaire, pas d’ancienne ombre générée ajoutée par-dessus. Les dessins distincts du ciel nocturne et des astres restent ceux de Guilde/Sharpedo ; ils ne sont pas filtrés une seconde fois.

Validation : égalité avec le script original sur toutes les couleurs des sources, et égalité pixel à pixel avec les **trois feuilles complètes** `Base_Night`, `Cliffs_Night`, `Fringe_Night` d’Abyss. La feuille Fringe est une référence de validation du filtre, pas un module posé sur les terrains.

## Calques et géométrie

1. Mer : huit phases, 10 frames moteur par phase, boucle ≈1,33 seconde à 60 Hz.
2. Herbe native.
3. Faces natives.
4. Retours natifs.
5. Couronnes natives.
6. Pieds natifs.
7. Vos sols et chemins — vide.
8. Vos structures, base — vide.
9. Vos structures, avant-plan — vide, `Top=4`.

Ciel, astres et nuages sont des fonds séparés ; les nuages gardent leurs formes Guilde/Sharpedo et leur wrap à −4 px/s. Un marqueur `entrance` est posé sur l’herbe. Pas de bâtiments, arbres ou personnages.

La transparence des dix terrains est identique à celle du pack V3 recadré : mêmes dimensions, mêmes silhouettes et mêmes contacts W/E/S. Les baies restent ouvertes sur la mer ; « contact au bord » ne signifie pas que tout le bord est rempli. Le haut conserve le ciel. Aucun nouvel étirement/recadrage n’a été appliqué.

**Collisions libres : dessiner les obstacles avant de jouer.** Les contacts graphiques ne créent pas automatiquement des sorties scriptées.

## Contrôles et limites

`verification.json` vérifie les sources, les placements de modules, les 100 calques de terrain natifs, les 16 phases de mer, les six fonds prémultipliés, les dimensions, les calques vides, les marqueurs, l’index complet et l’installation sûre.

Format ciblé : PMDO **0.8.12**, sérialisation `0.8.12.0`. L’audit du moteur figure dans `provenance/engine_compatibility.json` du pack.

**Aucune ouverture réelle dans PMDO n’a été testée ici.** Les contrôles de fichiers ne remplacent pas la vérification visuelle dans ton éditeur, des raccords, des collisions et du comportement en jeu. Le navigateur sert d’aperçu, pas d’émulation du moteur.

## Sources et reproduction

Les sources jour/nuit d’Abyss sont conservées dans `natifs/` avec hashes dans `provenance.json`. `tile_night_reference.py` est le script exact récupéré, utilisé comme oracle de comparaison, sans exécuter ses commandes d’écriture. La documentation historique d’Abyss est conservée dans `metano_nuit_reference.md` ; ses affirmations de tests concernent ce dépôt, pas nos tests.

```sh
.venv/bin/python source/cote_v4_abyss/prepare.py
.venv/bin/python source/cote_v4_abyss/build.py
.venv/bin/python source/cote_v4_abyss/make_project.py
.venv/bin/python source/cote_v4_abyss/package.py
node source/cote_dix_zones/test_viewer.cjs apercu_cotes_metano_abyss.html
```

Les fichiers natifs non compressés sont construits dans `~/.cache/cote_v4_abyss_pack/`. Les PNG intermédiaires/composites de chaque carte et les fonds sont régénérables et non versionnés ; l’aperçu autonome permet d’exporter les PNG sans perte. Le premier échantillon reste conservé dans `sprites/cote_v4_abyss_echantillon/`, mais n’est pas le nouveau pack final.

Attributions : Métano / Palika / Halcyon et contributeurs, variantes nocturnes d’Abyss to Ascension, fonds Guilde/Sharpedo du commit `c16efe12`. La disponibilité publique des sources n’est pas une licence sans restrictions ; consulter leurs conditions avant redistribution hors du projet.
