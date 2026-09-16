# Carapagos V4 — reconstruction depuis les portraits validés

## Mandat utilisateur

Le choix explicite de l'utilisateur est de **reconstruire le sprite depuis les portraits approuvés** et de produire **toutes les animations**, scènes comprises. La V1 perdue n'est plus la base bloquante de cette reconstruction. Ce lot n'est pas présenté comme une récupération de V1.

Le profil complet effectivement défini par le contrat du projet compte32actions obligatoires. Le premier lot exporte **22 candidats**, les10autres restent dans le mandat. Il ne couvre pas les attaques facultatives spécifiques à d'autres espèces ni les placeholders Special0–31 du catalogue global.

## Sources et inspection

- `references/approved_portraits.png` : agrandissement nearest des portraits approuvés ; aucune modification de leurs fichiers source/export.
- `references/official_564.png` : art officiel Tirtouga récupéré depuis PokeAPI/sprites, référence d'anatomie du corps : quatre palettes natatoires, masque sombre angulaire, carapace ardoise avec anneaux/plaque sombres. Pas une tortue terrestre à pieds ni une carapace à grosses taches blanches.
- Caméra/échelle : Idle Torkoal0324, SpriteCollab `3609a86be2a4c8ad7cf255bd2255f044daafe24f`, crédits natifs conservés dans `references/torkoal_credits.txt`.
- Index XML : noms/indices du vrai `sprite/0001/AnimData.xml` à la même révision. Ne pas utiliser les positions dans la liste des actions comme indices moteur.
-10générations effectuées : Idle + Walk/Attack/Sleep/Hurt/Charge/Swing/Hop + Scenes_A/Scenes_B. Les deux générations Scenes_C/Scenes_D demandées ont été refusées par la limite de10du tour ; **aucun fichier imaginaire n'est exporté pour elles**.

Les sources ne respectaient pas toutes les grilles demandées : Idle avait7rangées inégales au lieu de8 ; Swing6colonnes au lieu de4 ; Scenes_B des titres, quadrillages et un fond magenta clair. Le découpage suit leurs dimensions réelles, pas les seules instructions du prompt. Les propositions originales sont conservées.

## Dessins invalides écartés / adaptations explicites

Voir `review/validation.json` pour la liste complète.
- Idle : cinq vues inspectées, trois autres par miroir anatomique. Clignement court sur les trois vues de face/profil et leurs miroirs ; vues arrière statiques. Pas32dessins uniques.
- Walk D : deux poses de la génération tournaient vers DR ; elles sont écartées, remplacées par les poses de contact D valides et leur symétrie. Les autres directions utilisent leurs poses articulées.
- Sleep D : le générateur n'avait fait que des profils. Remplacement par la pose frontale basse de Charge, yeux fermés. Les autres directions utilisent les dessins Sleep.
- Hurt D : récupération de profil rejetée, anticipation frontale utilisée pour le retour.
- Hop : les apex inventaient un ventre beige et changeaient de direction. Ils sont rejetés ; les deux phases en l'air réutilisent le bon dessin de décollage à des hauteurs différentes, entre les poses distinctes de compression et d'atterrissage. Ce n'est pas quatre dessins indépendants.
- Double : **deux frappes Attack successives** avec un rythme propre, pas une copie d'Idle. Artwork d'attaque partagé et déclaré.
- Rotate : rotation via les huit vues dessinées, pas une rotation arbitraire du PNG.
- Scenes_A : plusieurs rangées sont des illustrations lisses malgré le prompt pixel art. La palette et la reconstruction à l'échelle native ont été effectuées, mais elles ne prouvent pas une finition artistique PMD parfaite. EventSleep déjà orientéDR préservé ; les autres poses SW sont inversées, à l'exception des poses LookUp déjà dirigées correctement.
- Scenes_B : textes/fond/grille retirés ; la première pose Faint touchait le texte et est remplacée par la pose Hurt. HitGround et Faint déjàDR ne sont pas inversés.
- Revue à l'échelle native : liserés magenta détectés sur les nageoires, puis corrigés par une clé chromatique renforcée avant palette. Les véritables couleurs chaudes des bouches sont conservées.

**Statut artistique : candidat de revue, pas terminé/approuvé.** Des différences de proportions entre les familles d'actions, la continuité de contacts au sol, et l'anatomie des poses basculées demandent encore une revue/retouche. L'utilisateur a validé les PORTRAITS, pas encore cette reconstruction du corps ni les nouvelles animations. Ne pas transformer un PASS technique en revendication de qualité artistique ou d'approbation SpriteCollab.

## Actions présentes

### Dix actions de donjon — huit rangées de directions
Idle, Walk, Sleep, Hurt, Attack, Charge, Swing, Double, Rotate, Hop.
Ordre : D, DR, R, UR, U, UL, L, DL. Les trois directions miroirs échangent aussi les repères de nageoires droite/gauche.

### Douze actions de scène — une vue DR dessinée
EventSleep, Wake, Eat, DeepBreath, Nod, LookUp, Tumble, Trip, LostBalance, TumbleBack, HitGround, Faint.
Une rangée n'est pas huit directions couvertes. Les chutes/roulades inclinent et retournent le corps ; le cadrage de scène et les repères lors de ces bascules restent à revoir.

### Dix actions encore absentes
**Pose, Pull, Pain, Float, Sit, Sink, Laying, LeapForth, Head, Cringe.** Plan suivi dans `production_plan.json`. Aucune de ces actions n'est déclarée dans l'XML, aucun faux alias Idle.

## Format et contrôles

- Exports : `exports/pokemon_custom/tirtouga_v4/sprite_multisheet/`.
- Cellules64×64 transparentes (le personnage lui-même reste autour de30–40pixels, ce n'est pas un sprite géant agrandi). Dimensions des trois feuilles identiques,1ou8rangées.
- Palette globale choisie15couleurs pour TOUTES les actions, alpha0/255. Offsets/Shadow exclus du compte artistique.
- Marqueurs techniques binaires : noir tête, vert corps, rouge/bleu nageoires avant, blanc ombre. Ancre de sol constante **(32,44)**. Les positions anatomiques sont des guides ajustés au pixel opaque le plus proche : le test « dans la silhouette » ne prouve pas qu'une marque est sur le bon membre. Inspection humaine/éditeur encore requise.
- Durées positives en ticks1/60s. GIF à palette commune ; chronologie arrondie cumulativement au centième de seconde, erreur de durée totale≤5ms.
- Précontrôle local **minimumPASS, donjonPASS, completFAIL attendu (10actions manquantes)**.
- Contrôles indépendants PASS : palette15, alpha binaire, marqueurs dans la silhouette, ancre d'ombre fixe, aucune coupe sur les bords des cellules, contenus des exports limités à l'XML et aux triplets attendus, GIF décodés et durées contrôlées.
-19tests unitaires du profil PASS. **Aucun test SpriteBot officiel, import PMDO, réexport, gameplay ou rendu GPU.** Le ZIP n'est pas un `.chara` compilé, ne pas le renommer.

## Livrables

- `apercu_carapagos_v4_animations.html` : galerie autonome,22GIF et GIF Méga sur Dracaufeu.
- `carapagos_v4_22_actions_candidate.zip` : XML et66PNG directement à la racine, sans documentation parasite.
- `carapagos_v4_22_gifs.zip` : un GIF par action.
- `review/validation.json`, `review/independent_checks.json`, `review/landmarks.json` : mesures et limites.

Reconstruire :
```
.venv/bin/python source/pokemon_custom/tirtouga_v4/build.py
.venv/bin/python source/pokemon_custom/tirtouga_v4/verify_and_gallery.py
```
Dépendances : Pillow, NumPy, SciPy. La reconstruction est déterministe, les générations sont des sources conservées, pas réexécutées par le script.

## Crédits et portraits validés

Les cinq portraits générés V3 sont désormais **approuvés par l'utilisateur**, sur leurs fonds canoniques déjà composés. Empreintes immuables dans `source/pokemon_custom/tirtouga_portraits_v3/approval.json`. Ne pas régénérer les portraits ni substituer une autre palette/fond sans demande explicite.

Normal/référence faciale : SpriteCollab, MUCRUSH (historique), `<@!217899432652308480>` (crédit courant, CC_BY-NC_4) ; crédits source conservés dans `tirtouga_v2/references/credits.txt`. Le Normal et les dessins natifs Torkoal ne sont pas notre création. Cette reconstruction corporelle est AI-assisted, guidée par des œuvres existantes ; conserver attribution et restrictions non commerciales. Pokémon appartient à ses ayants droit. Aucune soumission publique annoncée ni admissibilité IA présumée.
