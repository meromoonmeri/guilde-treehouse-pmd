# Patch conservateur des nuages — mer en attente

```sh
.venv/bin/python source/cliffnordouesttest1_animation_v1/build.py
# Tester dans la copie jetable PMDO déjà installée sous .cache :
.venv/bin/python source/cliffnordouesttest1_animation_v1/runtime_test.py
# Appliquer seulement après validation ; refuse des edits indépendants :
.venv/bin/python source/cliffnordouesttest1_animation_v1/build.py --apply
.venv/bin/python source/cliffnordouesttest1_animation_v1/verify.py
```

Le constructeur lit l’original `aac14ae4:cliffnordouesttest1.rsground` avec `git show`, conserve les octets et remplace uniquement le littéral `"Status": {}`. Pas de resérialisation globale, pas de changement de frames, couches ou collisions. L’original reste accessible dans Git. Le `.rsground` contient un BOM UTF-8 et des fins de ligneCRLF : ne pas le normaliser. Pour le contrôle whitespace, employer `git -c core.whitespace=cr-at-eol diff --check`.

## Natif plutôt que faux fond animé

`GroundScene.InitGround` démarre les émetteurs des statuts existants. `OverlayEmitter` crée un `OverlayAnim` sur `DrawLayer.Top`. Ce mécanisme dessine réellement au-dessus des calques ; un `MapBG` serait masqué par les tuiles opaques du ciel.

Six familles de nuages issues de `source/ciels_valides.py`, commit de référencec16efe12. TextureBG1440×784, placement du bandeau ày208, déplacement−4px/s, alpha natif. L’émetteur répète les deux axes ; la hauteur de texture est exactement celle du Ground pour ne pas répéter les nuages à l’intérieur de son emprise.

Le squelette `MapStatusData` est conservé dans [`references/clouds_overhead.json`](references/clouds_overhead.json), provenance `meromoonmeri/town02` commit `1efd098f92a0abcc892f40410db8249ecc9c9bb1`, blob `7fb61b656d396ccb775219fc202d4c9fb7fcf364`. Ce n’est **pas** son ancienne textureSteam qui est utilisée : nouvelle ressourceBG de nuages natifs, statut dédié, masqué, sans état météo ni événement de gameplay.

CodeRogueEssence inspecté au commit `8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b` : `GSceneZone.cs`, `OverlayEmitter.cs`, `OverlayAnim.cs`, `Sprites.cs`. Validation de désérialisation ensuite exécutée avec le **vrai binaire PMDO0.8.12**, téléchargé via la méthode documentée dans [pmdo_runtime](../pmdo_runtime/README.md). Le cache d’installation n’est pas versionné.

## Résultats

- [`verification.json`](verification.json) : **14contrôles de préservation PASS**.
- [`runtime_results.tsv`](runtime_results.tsv) / [`runtime_verification.json`](runtime_verification.json) : **13contrôles de chargement natif PASS**, Ground et MapStatusData. StartupLua et ressources installées temporairement sont restaurés même sur échec.
- Premier essai de test : comparaison Lua `tostring(enum)=='Top'` incorrecte à cause de la représentation NLua. Corrigée en comparaison avec l’énumération native `DrawLayer.Top`, puis suite entièrement relancée.
- **Pas de GPU, d’éditeur ou de lecture de l’animation testés.** Aucun chargement de textures manquantes certifié.

## Blocage mer

Le constructeur **n’anime pas la mer** et n’écrit aucune tuile. Il faut obtenir les banques personnalisées exactes, particulièrement `v2_promontoire_jour_03.tile` et `terrain*.tile`, avant d’identifier l’eau et ses limites.

Recherche effectuée : checkout et archives locales ; arbres GitHub `town02`, `mypmdproject`, `zone-pmd`, `new-era-abyss-to-ascension-V4`, `PMD-5`, `New-Era-Abyss-to-Ascension-V5`. Des dépôts candidats étaient vides. Les banques canoniques connues de `town02` ont été décodées pour inspection ; elles ne fournissent pas les banques personnalisées manquantes. Ne pas transformer un nom de banque ou une case de cascade en preuve de mer.

[Installation, état partiel et fichiers](../../exports/cliffnordouesttest1_animation_v1/README.md).
