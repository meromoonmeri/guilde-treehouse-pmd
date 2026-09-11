# Vérification du test de personnalité de référence

## Périmètre consulté

- Dépôt : [meromoonmeri/mypmdproject](https://github.com/meromoonmeri/mypmdproject).
- Code de la branche fournie, figé pour cette lecture : [`e3fa166525d08202503200c77482a2c1cc9cabad`](https://github.com/meromoonmeri/mypmdproject/tree/e3fa166525d08202503200c77482a2c1cc9cabad).
- Référence artistique et multiframe : [`319d10f69605331a07c817227c85ec8d0aba3dab`](https://github.com/meromoonmeri/mypmdproject/commit/319d10f69605331a07c817227c85ec8d0aba3dab).
- Image de portail fournie : `IMG_4861.jpeg`, également récupérée depuis la branche liée. Les références d’art `IMG_4871.jpeg` et `IMG_4877.jpeg` ont servi au travail de texture.

Le commit artistique contient des références d’images, pas le code du test. Les mesures du quiz proviennent donc de la branche indiquée, et non d’une supposition à partir de la seule image du halo.

## Dimensions exactes dans le code

| Élément | Source | Dimensions |
|---|---|---|
| Écran logique du quiz | `soulhalo/dxui.py`, `SCREEN_W`, `SCREEN_H` | **320 × 240**, ratio 4:3 |
| Sortie par défaut du quiz | `soulhalo/quizscreen.py`, `scale=3`, `frame_image()` | **960 × 720**, agrandissement entier |
| Halo circulaire d’introduction | `personality_intro/build_halo_loop.py` | **1280 × 720**, ratio 16:9 |
| Boucle du halo source | même script | **36 images à 12 fps**, soit 3 s |

Le quiz source est un rendu à dimensions fixes. Il n’existe pas, dans ces fichiers, de gestion de taille de fenêtre HTML en plein viewport. La boîte de question coupe le texte après trois lignes ; cette limitation a été identifiée dans le code, sans prétendre qu’une question fournie est nécessairement tronquée.

## Progression et caméra

`QuizScreen.step()` pilote le regard avec la souris/le stick. `valider()` enregistre la réponse puis remet le choix à zéro. Cette méthode ne déclenche pas de déplacement de caméra propre à chaque nouvelle question.

Le quiz source tire huit questions dans une banque de dix-huit, possède treize natures, garde ses poids privés, n’avance pas sur un timer et annule les poids lors d’un retour. Ces règles sont conservées dans la version web.

## Réponse implémentée dans ce dépôt

- Canevas à la taille réelle de la zone disponible, ratio de caméra recalculé à chaque redimensionnement.
- Perspective 3D, sphère en profondeur, orbite gauche/droite et avancée à chaque réponse.
- Nébuleuse colorée derrière les anneaux : pas de fond noir uniforme.
- Atlas de 36 phases, interpolé dans le rendu. Le cycle de cette nouvelle version dure six secondes pour une animation plus douce.
- Interface souple sans la limite de trois lignes ; défilement interne si nécessaire sur un très petit écran.
- API plein écran avec gestion du refus en iframe, et préférence de mouvement réduit.

Les contrôles du nouveau module ont été exécutés sur des viewports 320 × 568, 390 × 844, 768 × 1024, 1280 × 720, 1920 × 1080 et 844 × 390. Le rapport machine indique les résultats du navigateur. La lecture du projet source ne vaut pas une validation de son exécution dans PMDO : aucun changement ni test moteur n’a été fait dans l’autre dépôt.
