# Guilde — premier lot de scènes

## Livré

| Dossier | Base préservée | Ajouts |
|---|---|---|
| `gardevoir_candidate` |14actions natives, tous les PNGs originaux inchangés |7actions Cutscene authentiques + Nod candidat de face |
| `weavile_canonical` |13actions natives, tous les PNGs originaux inchangés |Special0 et Special1 Cutscene authentiques |

Gardevoir : **StandingUp, Special0, Special1, Special2, Special3, Pose, Jump**. Les triples et timings proviennent de0282/0002. Attention : Special1 était un alias vers **Appeal Cutscene**, dont les trois PNGs diffèrent de la base ; cet alias est matérialisé sous Special1 avec ses vrais dessins/timings. Ne pas le réorienter vers l’Appeal de base.

Dimoret : deux actions spéciales de0461/0001, sans substitution de forme/genré et sans les renommer arbitrairement Nod/Pose. Les dossiers sont des packs sources complets base+ajouts au format XML/triples, **pas des fichiers compilés/importés dans PMDO**. Ils restent isolés des ressources actives.

Les noms Cutscene sont conservés sans réinterprétation : StandingUp est une posture native à1image par direction ; Special0/Special2 incluent des images entièrement transparentes, et Special3 alterne apparition/absence. Ce sont des états/effets de scène authentiques, pas nécessairement des gestes de dialogue. Les aperçus peuvent donc être fixes ou clignoter ; aucune image vide native n’a été supprimée.

## Nouvelle animation Nod

**Un candidat de face**, 32×40, 5étapes, 3dessins distincts, durées10/5/9/5/12ticks à60Hz. Les têtes de la première ligne générée sont détourées, ramenées à l’échelle/palette native et raccordées au corps natif stationnaire. Corps, repères et ombre restent identiques ; pas de rebond global ni de robe qui change.

La planche générée entière échouait : directions incohérentes sur les autres lignes et la planche arrière. **Sept directions restent à produire**, ces études ne sont pas acceptées comme Nod8vues. La première ligne de face seulement fournit les têtes du candidat. Ce montage n’est pas présenté comme entièrement dessiné par le générateur.

## Contrôles / limites

- Deux précontrôles `dungeon` PASS : XML, alias, indices, durées, dimensions, triples, repères et palette globale (voir `verification.json`).
- PNGs natifs préservés et actions XML de base inchangées sémantiquement ; pas de fichiers incomplets référencés.
- `review/` : GIF par ajout, planche Nod. GIFs d’aperçu à résolution agrandie nearest, délais arrondis aux10ms du GIF ; le XML garde les ticks exacts.
- **PMDO : non testé. Art du Nod : candidat non approuvé.** La présence d’un GIF ne certifie ni import, ni comportement Ground/Dungeon.
- Les9actions Cutscene étaient déjà disponibles dans des variantes : **pas9nouvelles créations**. Seule Pose comble un manque du profil32 audité ; les Specials et autres noms ne sont pas maquillés en actions génériques manquantes. Nod de face n’achève pas8directions. Les autres membres et le catalogue global restent à traiter.

## Sources / attribution

SpriteCollab épinglé à `3609a86be2a4c8ad7cf255bd2255f044daafe24f` : `sprite/0282`, `sprite/0282/0002`, `sprite/0461`, `sprite/0461/0001`. Téléchargements vérifiés contre les SHA Git des blobs. Crédits natifs exacts dans les quatre fichiers `*_credits.txt` voisins ; conserver chaque attribution/licence lors d’une redistribution. Base et Cutscene ont des fichiers de crédit distincts, aucun auteur n’est effacé. Nod dérive du corps/palette/repères Gardevoir natifs et de têtes nouvellement générées puis nettoyées ; ce n’est pas un ajout upstream et aucune licence des originaux n’est remplacée.

Reconstruction : `.venv/bin/python source/guild_scene_animations_v1/build.py`. Galerie : `apercu_guilde_scenes_v1.html` à la racine.

Validation de ce lot :48tests automatisés PASS (dont10nouveaux), `git diff --check` propre.
