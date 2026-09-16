# Carapagos — portraits générés individuellement V3

**Nouvelles propositions : Happy, Angry, Sad, Shouting, Surprised.** Normal est conservé octet pour octet depuis SpriteCollab. Les cinq nouvelles images ne sont pas les petites retouches V2 ; chaque expression a sa génération propre, guidée par le portrait Normal agrandi sans interpolation.

## Format et fonds

- Portraits individuels40×40 RGBA entièrement opaques.
- Palette choisie explicitement par rôle : ombres du masque, blues, blanc d'œil, couleurs chaudes de la bouche lorsque nécessaire. Un premier essai median-cut a été rejeté parce qu'il transformait la langue rose en gris-bleu.
- Les fonds viennent des cellules **Happy1, Angry3, Sad5, Shouting7, Surprised12** de `template.png` fourni par l'utilisateur. Aucun de leurs pixels n'est recoloré, aucun fond n'est régénéré. Tous les pixels visibles du fond sont vérifiés égaux à ceux du template. Les quatre couleurs du fond Angry/Surprised sont prises en compte dans la limite totale15.
- Retouches pixel de sourcils Angry/Sad après inspection, définies dans le script. Les autres dessins gardent les expressions issues du générateur, la sélection de palette et le nettoyage ; ne pas prétendre qu'ils ont tous été redessinés entièrement à la main.
- Sujets transparents et fonds opaques séparés dans `exports/pokemon_custom/tirtouga_portraits_v3/editable/`, pour poursuivre la retouche sans écraser les fonds.
- Planche SpriteCollab **200×160** à emplacements standards ; toutes les cases manquantes sont entièrement transparentes. Pas de faux remplissage des émotions restantes.

Minimum technique PASS. Niveau complet FAIL attendu : **Pain, Worried, Crying, Teary-Eyed, Determined, Joyous, Inspired, Dizzy, Sigh, Stunned** manquent. Ce lot est une proposition visuelle partielle, pas une planche complète approuvée ou un personnage importé.

## Référence et crédits

Source de référence : SpriteCollab `3609a86be2a4c8ad7cf255bd2255f044daafe24f`, `portrait/0564/Normal.png`. Crédits natifs conservés dans `source/pokemon_custom/tirtouga_v2/references/credits.txt` : MUCRUSH (historique), `<@!217899432652308480>` (courant, CC_BY-NC_4). Le fichier Normal fourni n'est pas notre création. Les nouvelles expressions utilisent cette œuvre comme référence de génération ; préserver l'attribution de la référence et la restriction non commerciale, sans attribuer ces générations aux artistes originaux. Pokémon appartient à ses ayants droit.

Les guides et la configuration SpriteCollab sont documentés dans `source/pmd_character_pipeline/`. Le précontrôle ne vaut ni approbation artistique, ni admissibilité des contenus AI-assisted au dépôt public, ni test d'import PMDO. Pas de remplacement de ressources existantes.

Reconstruire : `.venv/bin/python source/pokemon_custom/tirtouga_portraits_v3/build.py`.
