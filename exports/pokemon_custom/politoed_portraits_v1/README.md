# Tarpaud — portraits sur magenta, puis fonds canoniques

**14 portraits de face disponibles dans ce lot partiel : 4 natifs conservés et10nouvelles propositions.**

- Natifs inchangés : Normal, Inspired, Shouting, Surprised. Hashes vérifiés ; crédits originaux dans `native_credits.txt`.
- Nouveaux candidats : Happy, Pain, Angry, Worried, Sad, Crying, Teary-Eyed, Determined, Joyous, Dizzy.
- **Manquants : Sigh, Stunned.** Limite de10générations atteinte ; aucun fichier créé pour ces deux demandes.

## Étapes séparées

1. Générateur : sujet sur magenta uniforme, anatomie du Normal de référence, expression animale.
2. `extracted/` : source réellement détourée en alpha ; les couleurs roses naturelles sont conservées.
3. `editable/*_subject.png` : nettoyage à40×40 et palette native ; seules régions œil/larmes prélevées, autres traits natifs préservés. Pas de lèvres humaines ni deuxième bouche dans la mâchoire jaune.
4. `editable/*_canonical_background.png` : case de l’émotion extraite de `template.png`, jamais redessinée ou recolorée.
5. `portraits_individual/` : composite opaque ; `portraits_partial.png` : grille200×160 avec cases manquantes transparentes.

Les nouveaux fichiers passent les contrôles40×40, alpha, maximum15couleurs fond compris, intégrité du sujet hors masque et fond visible pixel-exact. Aucun doublon exact parmi les dix sujets avant fond. Les quatre natifs restent identiques octet pour octet. **Ce n’est pas une approbation artistique, une planche complète, une validation des vues inverses, ni un testPMDO.**

Reconstruction : `.venv/bin/python source/pokemon_custom/politoed_portraits_v1/build.py`. Galerie : `apercu_tarpaud_portraits_v1.html`, montrant magenta → alpha → fond canonique.
