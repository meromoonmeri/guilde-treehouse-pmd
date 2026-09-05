# Sources validées — corrections des accès PMD, version 2

Cette passe suit **la construction des accès dans la référence fournie par l’utilisateur**, sans reprendre ses briques, sa roche, son herbe ni ses objets. Le bois ambré, les textures, les fenêtres, les dimensions et l’identité de la guilde sont conservés. Les neuf PNG de `source/natives/` restent intacts.

## Corrections retenues

- **01 et 09, nord :** remplacement de l’escalier dressé hors cadre par un passage de plain-pied en retrait dans le mur. Sol visible dans le renfoncement, ombre sous le linteau et sur les joues. Aucune porte ajoutée.
- **Les neuf accès latéraux :** raccord du mur arrière du petit couloir, tranche avant continue et sol jusqu’au bord de l’image. Aucun portique, poteau isolé ni porte. Les fines colonnes transparentes aux bords de la salle 03 sont remplies.
- **Les cinq accès sud :** continuité de sol jusqu’au bord inférieur, retours bas du contour et contacts latéraux. Les deux poteaux de 06 sont remplacés par les joues basses déjà présentes dans 01.
- **03 :** son échelle et son tronc continuent hors champ ; le sommet scié n’est plus dessiné.
- **12 :** suppression de l’échelle courte sans destination. Le tronc reste un élément architectural continu, sans nouveau passage au nord.
- **02 :** l’unique porte du maître est conservée ; ses fenêtres et tableaux ne sont pas déplacés.
- **08/10 :** retrait de 78 pixels roses par salle, et prise en compte des 55 petits pixels transparents auparavant exclus du paysage. Le masque passe de 951 à 1 084 pixels par salle. Les petits trous des fenêtres de 12 sont également couverts.
- Les îlots de plancher classés avec la structure et la continuité des masques de sol des nouveaux passages nord ont été corrigés.

## Fichiers faisant autorité

- `bases/NN.png` : intérieur de jour validé, transparent, sans paysage et sans les **nouveaux** effets de seuil. Le modelé ambiant du bois reste dans ces images.
- `masques/NN.png` : segmentation artistique figée, un code par pixel : `0` transparent, `1` sol, `2` structure, `3` cadres, `4` tableaux, `5` porte, `10` bordure avant. Les masques ne sont pas recalculés par GrabCut pendant l’export.
- `masques/NN_retouches.png` : zones autorisées lors de la correction des bases. En dehors, la base de jour du premier état est conservée pixel pour pixel. Ces masques ne comprennent pas les nouveaux effets d’éclairage, produits séparément.
- `definitions.json` : les **19 repères d’accès** et la géométrie utilisée par l’éclairage. Les rectangles de transition sont au format `[x, y, largeur, hauteur]`, en pixels natifs. Ce sont des propositions pour l’intégration, pas des triggers déjà installés dans un jeu.
- `conservation.json` : mesure des retouches sur la base artistique par rapport à la base transparente du commit initial. Les pourcentages portent sur **tout le canevas, transparence comprise**, avant les nouveaux effets de contact/lumière.
- `provenance.json` : empreintes des natifs, prompts exacts des deux retouches génératives retenues, fichiers d’entrée/sortie et description des traitements.

## Rôle du générateur et protection de la DA

Deux propositions sont conservées : le renfoncement nord issu de 01, réemployé dans 09, et la correction du tronc de 12. Les sorties complètes sont archivées dans `retouche_nord/` et `retouche_tronc/`, mais **seules leurs zones autorisées sont utilisées**. Elles ont été ramenées aux dimensions natives au plus proche voisin et rapprochées de la palette d’origine. Le raccord supérieur du passage nord réemploie le bois de la salle 05.

Les essais génératifs des côtés et du sud ajoutaient/conservaient des poteaux indésirables : ils ont été rejetés. Pour ces parties, les retours et les tranches réutilisent les propres textures de la guilde, notamment 03 et 05. Aucun pixel du décor PMD de référence n’a été collé dans la guilde.

Les nouvelles bases et leurs masques constituent désormais les sources artistiques de reconstruction. Les retouches créatives ne sont pas relancées par un build.

## Ombre et lumière

`source/pmd_lighting.py` dessine deux plans indépendants :

- **`08_ombres_acces`** : contacts localisés, brun sombre de jour et légèrement bleutés de nuit. Ils suivent les joues et les pieds d’échelle ; ils ne sont plus déduits des pixels foncés du veinage.
- **`09_eclairage_fixe`** : liserés et petits reflets locaux, ambrés de jour et très atténués de nuit. Pas de faisceau, halo, animation ou lampe ajoutée.

Les centres de passage restent dégagés. Les effets ne couvrent jamais les fenêtres ni la transparence extérieure. L’éclairage ambiant déjà peint dans les matériaux n’est **pas** transformé en un système physique complet de relighting.

## Reconstruction et contrôles

Depuis la racine du dépôt :

```bash
python source/rebuild_kit.py
python source/build_preview.py
python source/verify_pmd.py
python source/verify_passages.py
python source/verify_browser.py
```

`GUILDE_ROOMS=01,03` limite la reconstruction aux salles demandées sans recalculer les masques ni modifier les autres salles. L’aperçu doit ensuite être reconstruit, car il embarque les images.

`verify_passages.py` contrôle la connexion des 19 points de passage au sol principal, leur dégagement, la continuité du sol au bord pour les sorties latérales/sud, les petits trous de fenêtres, la conservation des silhouettes jour/nuit et le caractère local des effets. Il vérifie aussi les empreintes des neuf natifs inchangés.

L’aperçu utilise les PNG de base précalculés dans la vue complète : cela évite les écarts d’arrondi dus à la prémultiplication des petits alphas colorés par Canvas. Les calques peuvent toujours être affichés ou masqués séparément ; cette inspection utilise la composition native du navigateur.

**Limites conservées :** cartes fixes, pas d’animation de porte, pas de moteur ni de collisions intégrés, banque d’objets séparée. Il s’agit d’une adaptation des principes visibles dans la référence PMD, pas d’une certification officielle du jeu d’origine.
