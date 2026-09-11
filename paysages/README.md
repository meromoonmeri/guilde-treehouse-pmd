# Zones originales — texture Treasure Town et palette cycling

Cette version remplace la première tentative trop proche des captures nettoyées. Les références servent de **direction artistique** ; les quatre zones ont de nouveaux layouts et des **plans dessinés séparément**, comme la guilde et la falaise côtière.

[Ouvrir les zones](../apercu_falaise.html) · [Démonstration du vrai cycling](../previews/palette_cycling_tt.gif)

| Zone | Dimensions | Layout |
|---|---|---|
| [Cap des Alizés](littoral/README.md) | 504 × 384 | Cap en arc, arrivée sud-ouest, belvédère à l’est |
| [Prairies suspendues](plateaux/README.md) | 504 × 408 | Terrasses asymétriques, clairière et rampe naturelle |
| [Clairière des sources](etang/README.md) | 480 × 432 | Étang décalé, rive est, deux chutes dans une paroi boisée |
| [Ressauts célestes](cascades/README.md) | 576 × 432 | Deux hauteurs rocheuses, bassin central et berges au premier plan |

La roche suit la texture de **Treasure Town** : strates ocres, petits éclats et ombres rose-brun en pixel fin. Les grands blocs gris facettés de l’essai précédent ne sont plus utilisés. Les bâtiments, panneaux, clôtures et installations ne sont pas réintroduits.

## Dix plans

1. Ciel indépendant.
2. Lune fixe et étoiles scintillantes.
3. Nuages en défilement continu.
4. Fond du bassin ou de la mer, fixe.
5. **Surface de l’eau : palette cycling.**
6. Reliefs/forêt du fond.
7. **Cascades : palette cycling distinct.**
8. **Écume et rides : palette cycling distinct.**
9. Terrain/chemins du premier plan.
10. Végétation en overlay masquable.

Les plans inutiles à une zone restent vides. Ce ne sont pas neuf/dix découpes d’une seule capture : terrains, arrière-plans rocheux et banques de végétation/eau ont leurs propres dessins. Les ciels et nuages partagent les éléments déjà retenus dans le projet.

## Ce que signifie ici « palette cycling »

Une image d’**indices fixes** est associée à une table de couleurs. Les entrées réservées changent selon les frames, mais les pixels de la carte et sa silhouette ne se déplacent pas. Le fond de l’eau reste visible sous ce plan. Les cascades et l’écume ont leurs propres cartes et palettes.

- Surface : 24 images à 250 ms, soit 6 s ; huit états de palette tenus trois images.
- Cascades et écume : huit états à 250 ms, soit 2 s.
- Nuages : un pixel par image, boucle sur la largeur de la zone.
- Étoiles : cycle de 6 s, lune exclue du scintillement.
- Boucles globales : 126 s pour le cap et les prairies, 120 s pour l’étang, 144 s pour les ressauts.

Les surfaces terrestres et les éléments de végétation restent fixes. Le mode de mouvement réduit démarre l’aperçu en pause.

## Fichiers

- `calques/` : PNG RGBA des plans, dans les deux ambiances.
- `compositions/`, `bases/` : rendus et premier plan transparent/magenta.
- `animations/*_indices.png` : cartes d’indices, pas des images à afficher telles quelles.
- `animations/*_palettes_*.json` : palettes et entrées réservées au cycling.
- **`aseprite_indexe/`** : vrais Aseprite 8 bits ; carte fixe, cels liés, chunks de palette différents par frame.
- `aseprite/` : scènes complètes RGBA, avec les mêmes phases rendues. Le défilement des nuages utilise des cels liés déplacés plutôt que des centaines de duplications.
- `tiled/` : image layers et animations de tuiles correspondant aux mêmes phases.

L’aperçu reconstruit le cycling directement depuis les indices et les palettes ; il ne simule pas ce mouvement par un simple déplacement d’image. Le bouton **Cycling indexé Aseprite** télécharge l’animation indexée de l’eau ; les cascades et l’écume sont disponibles dans le même dossier.

Les bases isolent le premier plan. Conserver les atlas et les données d’animation avec les cartes. Ce sont des ressources graphiques éditables, pas des collisions ou des transitions PMDO intégrées.

## Reconstruction et contrôle

```bash
python source/prepare_zones_tt.py
python source/rebuild_zones_tt.py
python source/build_preview_falaise.py
python source/verify_zones_tt.py
python source/export_nouveaux_gifs.py
python source/export_palette_demo.py
```

Les anciennes commandes `prepare_paysages_nouveaux.py`, `rebuild_paysages_nouveaux.py` et `verify_paysages_nouveaux.py` redirigent désormais vers cette méthode. L’ancien détourage d’une composition complète est conservé seulement dans l’historique Git.

Les tests relisent les Aseprite indexés et RGBA, leurs palettes, les atlas Tiled, les compositions et les calques du navigateur. Ils vérifient que les indices, l’alpha et les entrées de palette fixes ne changent pas. Les dessins et la texture font aussi l’objet d’un contrôle visuel ; il n’y a pas de promesse d’identité pixel pour pixel avec le jeu original.
