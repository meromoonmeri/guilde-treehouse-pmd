# Antre V6 — écumes générées de face/profil et contours bleus natifs

## Ce qui change
- Nouvelle génération sur magenta : **3 orientations × 3 poses** d’écume. Première rangée frontale ; deuxième impact à gauche et écoulement vers la droite ; troisième impact à droite et écoulement vers la gauche. La planche a été inspectée puis détourée avec un rectangle commun par orientation, sans recentrage indépendant des poses.
- Les deux chutes gauches utilisent le profil gauche, les deux chutes centrales la vue frontale, les deux droites le profil droit. Les écumes s’étalent vers l’intérieur du bassin, plutôt que derrière les rochers.
- L’ancre de chaque effet est placée à `(x de la chute, foot_y − 2)` : **le plan d’impact au bas de la chute**, pas la dernière ligne de son sprite. La chute se prolonge jusqu’à `foot_y + 4` derrière l’écume. Un petit raccord local maintient leur continuité. Aucun fragment blanc détaché n’est conservé.
- Le liseré translucide approximatif de V5 est remplacé par les **pixels des quatre phases de rive d’Altere Pond**, extraits de la couche River de la carte native. Le profil bleu fluctuant est reporté selon la distance aux parois sur une bande de 6 px côté eau. Les couleurs et alphas proviennent de la pose native correspondante, pas d’une sinusoïde de transparence inventée.

Le bassin subtil, les parois Crooked, le petit disque natif, les trois pas japonais et leurs huit phases natives de reflets sont conservés. Les cascades adaptées de V4 restent identiques ; leurs pieds sont désormais recouverts par les nouvelles écumes orientées.

## Provenance et limites
Les écumes sont **générées puis adaptées** au layout, ramenées à la palette cascade/écume de la référence et ajustées à 38–42 px de large. Leurs trois poses utilisent la cadence de 10 frames de jeu, mais **ne sont pas les poses natives intactes**. Le cœur du raccord est reconstruit localement. « Pixel perfect » concerne ici l’alignement en pixels entiers et la continuité vérifiée du contact, pas une certification moteur ou une identité aux sprites source.

Les profils de rive proviennent d’un rectangle natif de 48 × 64 px, coordonnées carte (400,304)–(448,368), reconstitué dans les quatre phases à partir de `Altere_Pond_River` et `Altere_Pond_River_Animations`. Les premiers pixels aquatiques de chaque rangée fournissent un profil de couleur/alpha variant par phase. Ces pixels sont redistribués sur les nouveaux contours : **adaptation géométrique de phases natives**, pas copie du contour de la carte originale.

Référence Halcyon : Altere Pond, commit `1522c7a8b7a34d70078e11ed605b21d563b0dc51`. Les ressources natives restent soumises aux droits de leurs ayants droit.

## Livraison
**26 calques**, 480 × 312, 24 états alignés, boucle commune de **4 secondes**. Cycles : bassin/cascades/rives 4 poses ; écumes générées 3 poses ; reflets autour des pierres 8 poses. Chaque pose dure 10 frames de jeu ; arrondi des horodatages cumulés à la milliseconde pour le WebP.

- `../../apercu_antre_ecumes_v6.html` : galerie animée autonome, chaque calque sélectionnable.
- `antre/COMPOSITION.png` et `antre/ANIMATION.webp` : état initial et boucle.
- `antre/antre_ecumes_v6.ora` : tous les calques à la phase initiale.
- `antre/ecumes6_*.png` : calques plein cadre et compositions, noms distincts de V5.
- `bruts/ecumes_orientees_magenta.png` : nouvelle planche générée.
- `sprites/ecume_orientee_*` : orientations et poses détourées avant adaptation au décor.
- `sprites/rive_altere_native_*` : quatre rectangles de rive natifs utilisés.
- `antre_ecumes_v6.zip` : scripts, fichiers et dépendances nécessaires.

## Vérifications
Les 24 recompositions opaques passent les contrôles : murs et pierres inchangés, reflets des plateformes recomposés exactement, cycles 4/3/8, ORA identique au PNG, chaque composante d’écume attachée à sa chute et chevauchement effectif dans chaque état. Les six écumes possèdent chacune trois états distincts. Les quatre contours de rive sont distincts, uniquement côté eau ; chaque couleur/alpha visible provient de la pose native correspondante. Aucun effet ne repeint les surfaces sèches.

Pas de test de collisions, d’import, de mouvement ou de combat dans PMDO ; pas de simulation physique des fluides. Les versions précédentes restent intactes.

Depuis la racine, avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/antre_ecumes_v6/build.py
.venv/bin/python source/antre_ecumes_v6/verify.py
.venv/bin/python source/antre_ecumes_v6/package.py
```
