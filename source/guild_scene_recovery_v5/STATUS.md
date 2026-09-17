# Reconstruction V5 — cycles de guilde sans nourriture intégrée

Les commits V3/V4 restés locaux n’étaient plus présents dans le checkout restauré ni sur GitHub. Ce lot est **une nouvelle reconstruction**, pas une récupération octet par octet des anciens fichiers. Premier checkpoint effectivement poussé : **adb28898**.

## Livrables

| Pokémon | Action | Étapes/vue | Vues | Méthode |
|---|---|---:|---:|---|
| Gardevoir | Eat |16|8|Bras fin articulé depuis les repères natifs, pause près du visage puis retour ; masquage par le casque en vue arrière |
| Gardevoir | Nod |16|8|Inclinaison/foreshortening de la tête autour du cou, corps et robe fixes |
| Balignon | Eat |16|8|Inclinaison directionnelle du corps, pieds ancrés ; aucun bras inventé |

Chaque cycle part et revient exactement au repos de sa vue native.16étapes comprennent des maintiens : voir les nombres de dessins uniques dans verification.json. Toutes les vues partent de leurs véritables images natives, pas de sprites de face pivotés ou de miroirs automatiques.

- `review/` :27GIFs de nos cycles (3planches8vues +24directions individuelles),3planches de phases clés.
- `gardevoir_candidate/`, `shroomish_candidate/` : packs source XML/triples complets avec bases natives conservées.
- `halcyon_review/` :3GIFs d’extraits natifs Eat, isolés des packs. Ce sont des références, pas nos créations.
- `verification.json` : contrôle technique, palette, ancrages et nombres de dessins.
- `production_progress.json` / `PROGRESS.md` : les128actions du profil encore sans cycle local. Le catalogue global et le reste de la guilde ne sont pas terminés.

## Provenance et correction Halcyon

Les études de geste V1/V2 encore disponibles ont servi de références, puis les gestes ont été reconstruits explicitement au pixel depuis les8anatomies natives. **Pas de nouvelle sortie de générateur revendiquée**, et pas de prétention à avoir retrouvé les sources perdues.

Aucune nourriture intégrée aux sprites Eat. Halcyon déclenche séparément le geste Eat, l’émote eating et les objets Food_*. Les véritables archives de Chapignon286, Kranidos408 et Nanméouïe531 ont été téléchargées à nouveau et vérifiées contre leurs SHA Git. Leurs premières séquences Eat de4frames ont été décodées pour inspection : pas de nourriture dessinée.

`source/guild_scene_recovery_v5/halcyon/` conserve scripts, archives, preuves et lecteur moteur. Eat est l’ID48 de GFXParams (None0/Idle1), pas la position47 dans un contrat sans None ni l’Index interne XML. Le décodeur vérifie dimensions, frames et fin du bloc binaire. Il ne remplace pas l’exécution de Halcyon.

Crédits de SpriteCollab conservés dans les fichiers voisins des packs. Références Halcyon attribuées à Palikadude et aux artistes originaux ; elles ne sont pas incorporées aux packs de Pokémon. Aucune nouvelle licence sur leurs œuvres n’est revendiquée.

## Contrôles / limites

Deux précontrôles `dungeon` PASS ; PNGs et actions XML natifs inchangés ; boucles fermées, repères équivalents pour dessins identiques, ombres/pieds fixes, masquage arrière et absence des couleurs de nos anciennes baies vérifiés. Agrandissement nearest ; délais GIF arrondis à10ms, ticks XML exacts.

**Cycles complets au sens phases +8vues. Approbation artistique et runtime PMDO non effectués.** Ce ne sont pas des animations importées/compilées en jeu ni des ajouts approuvés SpriteCollab.

Reconstruction hors ligne depuis les références conservées :
```
.venv/bin/python source/guild_scene_recovery_v5/build.py
.venv/bin/python source/guild_scene_recovery_v5/inspect_halcyon.py
.venv/bin/python source/guild_scene_recovery_v5/progress.py
```
Galerie principale : `apercu_guilde_reconstruction_v5.html`.
