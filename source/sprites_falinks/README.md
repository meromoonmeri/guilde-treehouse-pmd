# Falinks #0870 — PMD / SpriteCollab

Ce lot ajoute les animations Starter manquantes à la variante SpriteCollab
`0870/0002` de Falinks. Le sprite canonique existant est conservé tel quel
pour les indices 0–3 et 5–12 ; le générateur ajoute `RearUp` (indice 4) puis
les indices 13–34.

## Méthode frame par frame

`build_sprites.py` est le générateur déterministe du pack :

1. chaque frame part d'une pose Falinks canonique (`Idle`, `Walk`, `Attack`,
   `Hurt`, `Sleep`, `Hop`) ;
2. les transformations sont nearest-neighbor et entières ;
3. les animations sont écrites selon leur action PMD : manger au sol, tirer,
   respirer, hocher la tête, s'asseoir, regarder vers le haut, tomber,
   s'enfoncer et bondir ;
4. les corrections draw manuelles (`_open_face`, `_effort_marks`,
   `_impact_marks`, `_head_only`, `_clip_below`) utilisent exclusivement la
   palette Falinks canonique ;
5. les offsets et ombres sont reconstruits dans leurs feuilles PMD dédiées.

Il n'y a pas de génération IA brute importée comme frame finale. Le générateur
travaille frame par frame pour qu'aucune animation ne change de silhouette, de
palette ou d'espèce par rapport au sprite de base.

La construction suit aussi le guide [How to Make PMD Sprites for
SkyTemple](https://docs.google.com/presentation/d/1SH2onT2yttVuznohr4yi3Uh07y4lNLcLlHGT_YWNGmo/edit?usp=drivesdk) :
poses natives de la même espèce, huit directions PMD, transformations
nearest-neighbor entières, feuilles d'offsets et d'ombres séparées, puis
contrôle à taille native. Les corrections manuelles servent uniquement à
rendre les actions lisibles (`Eat`, `Pull`, `DeepBreath`, chutes, impacts,
formation et tête) sans introduire une autre silhouette.

## Format livré

- `sprite/0870/0002/` : dossier multi-sheet SpriteCollab ;
- `sprite-0870-0002.zip` : archive correspondante ;
- `sprite-0870.zip` : alias de compatibilité, byte-for-byte identique ;
- `gifs/0870/0002/` : 35 aperçus GIF direction 0, avec `timing.json` ;
- `gifs-0870-0002.zip` et `gifs-0870.zip` : archives des aperçus ;
- `AnimData.xml` : indices 0–34, directions, dimensions et durées ;
- `Name-Anim.png`, `Name-Offsets.png`, `Name-Shadow.png` : feuilles PMD.

La variante utilisée est le dossier canonique SpriteCollab
`PMDCollab/SpriteCollab/sprite/0870/0002`, état
`f273fb951f3931503a1c5533e9ff00a19ddd373b`. Les pixels des animations
existantes, les crédits et la licence upstream restent inchangés.

## Contrôle

```bash
python source/sprites_falinks/build_sprites.py
python source/sprites_falinks/verify_sprites.py
python source/sprites_falinks/make_gifs.py
python source/sprites_falinks/verify_gifs.py
```

Le vérificateur contrôle les 35 indices, la copie byte-for-byte des feuilles
canoniques, la palette maximale de 15 couleurs, l'alpha binaire, les offsets,
les ombres et l'archive SpriteCollab. Les GIFs reprennent les durées de
`AnimData.xml` à 60 ticks/seconde ; les poses consécutives identiques sont
coalescées sans changer la durée totale de la boucle.
