# Guilde PMDO — audit prioritaire des neuf membres

**17 septembre 2026 · formes standard/base.** SpriteCollab HEAD revérifié : `3609a86be2a4c8ad7cf255bd2255f044daafe24f`. Portraits existants et crédits conservés ; aucune génération ni modification de sprite.

## Conclusion

- **Priorité portrait : Politoed / Tarpaud**, seul membre auquel il manque des émotions parmi les 16du contrat. Ne pas refaire ses quatre portraits existants ni ceux des huit autres membres.
- Les neuf membres ont les 10actions du profil donjon du projet. Aucun nouveau sprite de base/Idle/Walk n’est à créer simplement pour combler une absence.
- Pour un jeu de 32 actions incluant les scènes, Bagon, Happiny et Pachirisu (slot de base) sont complets. Les six autres ont des lacunes de scènes à comparer aux besoins réels de la quête.

| Membre | Portraits /16 | Actions XML disponibles | Donjon /10 | Manques du profil 32 |
|---|---:|---:|---:|---:|
| Gardevoir (Gardevoir) | 16/16 | 14 | 10/10 | 22 |
| Farfetch’d (Canarticho) | 16/16 | 13 | 10/10 | 22 |
| Pancham (Pandespiègle) | 16/16 | 13 | 10/10 | 22 |
| Bagon (Draby) | 16/16 | 36 | 10/10 | 0 |
| Shroomish (Balignon) | 16/16 | 14 | 10/10 | 22 |
| Happiny (Ptiravi) | 16/16 | 37 | 10/10 | 0 |
| Pachirisu (Pachirisu) | 16/16 | 35 | 10/10 | 0 |
| Weavile (Dimoret) | 16/16 | 13 | 10/10 | 22 |
| Politoed (Tarpaud) | 4/16 | 13 | 10/10 | 22 |

## P1 — Tarpaud : émotions à produire

**Déjà disponibles :** Inspired, Normal, Shouting, Surprised.

**Manquants :** Happy, Pain, Angry, Worried, Sad, Crying, Teary-Eyed, Determined, Joyous, Dizzy, Sigh, Stunned.

Partir du Normal natif, conserver son anatomie et produire des expressions animales naturelles sur les fonds canoniques correspondants. Les quatre portraits existants restent intacts. Les autres membres n’ont pas besoin de nouveaux portraits pour couvrir les 16émotions.

## P2 — Scènes de guilde à compléter selon le scénario

### Gardevoir / Gardevoir

EventSleep, Wake, Eat, Tumble, Pose, Pull, Pain, Float, DeepBreath, Nod, Sit, LookUp, Sink, Trip, Laying, LeapForth, Head, Cringe, LostBalance, TumbleBack, HitGround, Faint.

### Farfetch’d / Canarticho

EventSleep, Wake, Eat, Tumble, Pose, Pull, Pain, Float, DeepBreath, Nod, Sit, LookUp, Sink, Trip, Laying, LeapForth, Head, Cringe, LostBalance, TumbleBack, HitGround, Faint.

### Pancham / Pandespiègle

EventSleep, Wake, Eat, Tumble, Pose, Pull, Pain, Float, DeepBreath, Nod, Sit, LookUp, Sink, Trip, Laying, LeapForth, Head, Cringe, LostBalance, TumbleBack, HitGround, Faint.

### Shroomish / Balignon

EventSleep, Wake, Eat, Tumble, Pose, Pull, Pain, Float, DeepBreath, Nod, Sit, LookUp, Sink, Trip, Laying, LeapForth, Head, Cringe, LostBalance, TumbleBack, HitGround, Faint.

### Weavile / Dimoret

EventSleep, Wake, Eat, Tumble, Pose, Pull, Pain, Float, DeepBreath, Nod, Sit, LookUp, Sink, Trip, Laying, LeapForth, Head, Cringe, LostBalance, TumbleBack, HitGround, Faint.

### Politoed / Tarpaud

EventSleep, Wake, Eat, Tumble, Pose, Pull, Pain, Float, DeepBreath, Nod, Sit, LookUp, Sink, Trip, Laying, LeapForth, Head, Cringe, LostBalance, TumbleBack, HitGround, Faint.

Le total des manques des **slots de base** est 132 actions pour ce profil 32. Ce n’est pas une preuve que la quête utilise toutes ces actions ni qu’il faut toutes les générer : établir la correspondance avec les scènes avant production. Un `CopyOf` valide compte comme disponible, mais pas comme un dessin d’animation distinct. Les replis automatiques du moteur ne constituent pas une animation spécifique créée.

## Ressources à réutiliser avant de générer

- **Gardevoir / Cutscene (`0282/0002`)** : 21 actions déclarées ; ajouts par rapport à la base : StandingUp, Special0, Special1, Special2, Special3, Pose, Jump. Ne pas substituer silencieusement cette variante : comparer apparence, direction, repères et crédits.
- **Weavile / Cutscene (`0461/0001`)** : 15 actions déclarées ; ajouts par rapport à la base : Special0, Special1. Ne pas substituer silencieusement cette variante : comparer apparence, direction, repères et crédits.
- **Pachirisu / Female (`0417/0000/0000/0002`)** : 13 actions déclarées ; ajouts par rapport à la base : aucun. Cette variante femelle n’a pas nécessairement les mêmes scènes que la base ; vérifier le sexe voulu du membre. Ne pas substituer silencieusement cette variante : comparer apparence, direction, repères et crédits.

Gardevoir possède notamment un dossier Cutscene ; Weavile aussi. Farfetch’d est ici la forme standard, pas celle de Galar. Les variantes shiny, femelles, alternatives et Méga restent listées en annexe JSON, mais ne sont pas choisies à la place des membres sans indication.

## Vues inversées des portraits

- Gardevoir : 0/16 fichiers `^` présents.
- Farfetch’d : 16/16 fichiers `^` présents.
- Pancham : 16/16 fichiers `^` présents.
- Bagon : 0/16 fichiers `^` présents.
- Shroomish : 16/16 fichiers `^` présents.
- Happiny : 0/16 fichiers `^` présents.
- Pachirisu : 0/16 fichiers `^` présents.
- Weavile : 0/16 fichiers `^` présents.
- Politoed : 0/16 fichiers `^` présents.

Absence de fichier `^` ne signifie pas automatiquement portrait obligatoire manquant : vérifier l’asymétrie, les accessoires (poireau/feuille notamment) et le rendu côté dialogue. Ne pas fabriquer des miroirs automatiques présentés comme des dessins vérifiés. Les Special sont optionnels, hors total 16.

### Ordre conseillé pour les animations

Après vérification des variantes Cutscene, commencer par les gestes de dialogue **Nod, Pose, LookUp** et la posture **Sit** si les scènes de guilde les appellent. Ensuite seulement les repas/sommeil/chutes et autres actions spécifiques au scénario. Ne pas recréer ces ressources pour Draby, Ptiravi ou Pachirisu de base : elles existent déjà.

## P3 — Intégration dans la quête

Vérifier les IDs Pokémon/formes/genres, les noms de portraits et actions appelés par les scripts, puis les ancrages, directions, collisions et déclenchements Ground/Dungeon dans PMDO. **Aucun test en jeu n’a été effectué pour ces neuf membres.**

Cet audit contrôle les clés du tracker (les valeurs sont des verrous), les listings réels, les XML et leurs alias ainsi que la présence des triples de PNG déclarés. Seuls les triples Idle représentatifs ont été téléchargés et décodés : ce n’est pas une validation graphique image par image de toutes les animations. Les XML, crédits et Normal natifs sont conservés sous `source/guild_members_audit/references/`, avec hashes dans `audit.json`.

## Correction Carapagos conservée

Les portraits approuvés à bouche ouverte sont réussis car ils suivent une référence canonique **sans dents visibles** : ils restent inchangés. La règle est la fidélité anatomique, pas une interdiction générale d’ouvrir le bec. Les paupières seules convenaient au dernier lot fermé ; une ouverture naturelle du bec est autorisée lorsque l’émotion et la référence la justifient.
