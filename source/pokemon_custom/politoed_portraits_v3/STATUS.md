# Tarpaud — V1 préservée, deux changements ciblés

- **13 portraits V1 inchangés octet par octet**, dont les quatre originaux natifs.
- **Dizzy** : spirale continue dessinée au pixel sur le visage préféré, après étude générée sur magenta. Le générateur avait dessiné des anneaux, corrigés explicitement.
- **Special0** : mains réunies pour applaudir, œil fermé, bouche de grenouille ouverte sans dents. Sujet généré complet, magenta vers alpha, taille40×40 et palette sémantique nettoyée à11couleurs.
- Dizzy : fond exact `template.png`, case13. Special0 : fond festif exact `Extra_Backgrounds.png`, rectangle `[40,0,80,40]` ; ce choix explicite évite les cases spéciales de démonstration du template.
- **14/16 émotions de face +1 spéciale**. Sigh/Stunned et vues inversées restent absents. V2 écartée, pas utilisée pour compléter artificiellement.

V1 reste intacte dans son dossier. V3 est un jeu candidat distinct. Les ajouts ne sont pas encore approuvés artistiquement ni testés dans PMDO. PNGs opaques40², ≤15couleurs, fonds visibles exacts et hashes V1 contrôlés par le builder/tests.

Crédits natifs : `native_credits.txt`, conservé sans modification depuis SpriteCollab, révision3609a86be2a4c8ad7cf255bd2255f044daafe24f. Les 10 propositions V1 ont la provenance documentée dans `../politoed_portraits_v1/`; les deux ajouts V3 sont des adaptations assistées par génération, pas des ressources natives SpriteCollab. Respecter les crédits/licences des sources ; aucune acceptation upstream revendiquée.

Reconstruction : `.venv/bin/python source/pokemon_custom/politoed_portraits_v3/build.py`.
