# Expressions animales sur fonds canoniques — lot partiel

- **Méga-Raichu X** : Normal conservé, Happy/Angry/Sad/Surprised/Pain proposés (5 nouveaux candidats).
- **Méga-Raichu Y** : Normal conservé, Happy/Sad/Pain proposés (3 nouveaux candidats). Angry/Surprised sont visibles en revue mais **bloqués à 16 couleurs**, pas exportés comme portraits individuels conformes.
- **Carapagos** : 6 originaux approuvés préservés octet pour octet, nouvelles propositions Pain/Worried depuis le Normal (2 candidats).

Les nouvelles expressions sont posées sur la case exacte de leur émotion dans `template.png`. Le fond n'est ni recréé ni quantifié ; les pixels visibles sont contrôlés identiques. Les Normal et portraits Carapagos déjà approuvés ne sont pas recomposés.

Raichu : bouche sans dents ni lèvres humaines, pas de mordillement, pas de grimace humaine. La palette de bouche est restreinte aux couleurs du museau et contours. Carapagos : seul l'œil est modifié, bec et narine restent intacts. Les propositions du générateur ne sont prélevées que dans des zones explicitement bornées. Tout pixel du sujet hors de ces zones reste celui du Normal.

**10 nouveaux portraits passent les contrôles mécaniques** (40×40, alpha opaque, maximum15couleurs, fonds canoniques exacts), mais ne sont pas déclarés approuvés artistiquement. Deux autres sont retenus en revue pour le budget de palette ; aucune recoloration silencieuse des traits fixes n'est utilisée pour les faire passer.

`portraits_partial.png` est une planche partielle200×160 avec cases absentes transparentes, pas un pack complet de16expressions. Les vues inversées ne sont pas produites. `editable/` sépare sujet et fond, `verification.json` détaille les sources et limites. Galerie à la racine : `apercu_expressions_canoniques_v1.html`. Aucun test PMDO en jeu.

Reconstruction : `.venv/bin/python source/pokemon_custom/next_species/build_canonical_expressions.py`.
