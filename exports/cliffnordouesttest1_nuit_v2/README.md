# cliffnordouesttest1 — nuit + nuages en overlay

**Version nocturne du Ground utilisateur. Mer toujours non animée : textures personnalisées manquantes.**

## Installer les quatre fichiers ensemble

Après sauvegarde de votre carte, PMDO fermé, fusionner [`a_copier/`](a_copier/) dans la racine de votre mod :

| Chemin dans le mod | Fichier |
|---|---|
| `Data/Ground/cliffnordouesttest1.rsground` | [Ground nocturne](a_copier/Data/Ground/cliffnordouesttest1.rsground) |
| `Data/MapStatus/cliffnw_night_overlay.json` | [Statut visuel](a_copier/Data/MapStatus/cliffnw_night_overlay.json) |
| `Content/BG/CLIFFNW_NIGHT_VEIL.dir` | [Éclairage nocturne](a_copier/Content/BG/CLIFFNW_NIGHT_VEIL.dir) |
| `Content/BG/CLIFFNW_NIGHT_CLOUDS.dir` | [Nuages nocturnes](a_copier/Content/BG/CLIFFNW_NIGHT_CLOUDS.dir) |

Le Ground livré est identique au [fichier racine](../../cliffnordouesttest1.rsground). **Ne pas copier uniquement le Ground**, ni remplacer les dossiers entiers : conserver vos autres ressources et scripts. Réindexer les MapStatus du mod si nécessaire, puis quitter/rentrer dans la carte en jeu. La lecture des effets dans la seule vue éditeur n’est pas garantie.

La version jour reste dans [le dossier V1](../cliffnordouesttest1_animation_v1/README.md). Ses anciennes ressources peuvent rester installées : le Ground nocturne ne les référence plus et ne cumule pas les deux versions.

## Ce qui change visuellement

1. **Éclairage de nuit** : voile bleu nuit RGB(8,14,36), opacité176/255, fixe et au-dessus de la scène. C’est un éclairage global non destructif — **pas une conversion canonique des palettes de chaque matériau**, ni un remplacement du ciel. Les personnages et décorations reçoivent également cet éclairage.
2. **Nuages de nuit** : les six familles validées Guilde/Sharpedo, avec la recette nocturne de `source/ciels_valides.py`. Alpha, échelle et placement inchangés ; déplacement−4px/s, wrap1440px, période360s. Ils sont dessinés après le voile pour ne pas être assombris deux fois.

Un seul statut `cliffnw_night_overlay` contient un `MultiSwitchEmitter` : voile d’abord, nuages ensuite, sur `DrawLayer.Top`. Aucun ajout de lune, d’étoiles, de nouveaux rochers ou de décor.

## Ce qui ne change pas

**Tous les octets hors `Object.Status` sont identiques à la carte d’origine** : quatre calques, tuiles et listes de frames, collisions, entités, décorations, fond, noms, musique, caméra et autres paramètres. BOMUTF-8 et fins de ligneCRLF conservés. Aucun script utilisateur modifié.

- [Original sans effets, commit aac14ae4](https://github.com/meromoonmeri/guilde-treehouse-pmd/blob/aac14ae4/cliffnordouesttest1.rsground).
- [Version nuages jour, commit34d40dc0](https://github.com/meromoonmeri/guilde-treehouse-pmd/blob/34d40dc0/cliffnordouesttest1.rsground).
- [Audit, paramètres et empreintesSHA-256](audit.json).

## PNG et extrait d’effet

- [Nuages nocturnes transparents](png/CLIFFNW_NIGHT_CLOUDS.png).
- [Voile nocturne transparent1104×784](png/VOILE_NUIT_overlay.png).
- [Nuages animés — extrait8s, une lecture](png/NUAGES_NUIT_extrait_8s.webp).

Le `.dir` du voile emploie le **cas natif1×1 plein écran** de `OverlayAnim`, pas un tileset à importer sur une grille8px. Le PNG1104×784 est fourni séparément pour composition/édition.

**Pas de faux aperçu de carte** : les PNG/WebP montrent uniquement les effets. Les textures manquantes empêchent de recomposer fidèlement votre Ground entier.

## Mer : fichiers nécessaires pour terminer

Merci de fournir, depuis votre `Content/Tile/` :

- **`v2_promontoire_jour_03.tile`** ;
- `terrain.tile`, `terrain (2).tile`, `terrain (3).tile`, `terrain (4).tile`.

Idéalement, fournir le dossier de textures complet. Le `.rsground` ne contient que les références, pas les images. Aucune zone d’eau n’a été devinée et aucune cascade animée à la place de la mer. **Le voile nocturne assombrit visuellement la mer déjà présente, mais ne l’anime pas.**

## Contrôles

- **20contrôles de préservation/ressources PASS**.
- **21contrôles natifs PMDO0.8.12 PASS** : chargement du Ground et du MapStatus, ordre des deux émetteurs, vitesse, coucheTop, création des animations, absence de doublons, horloge et arrêt.
- Tests d’émetteurs sans dessin dans un conteneur natif `BaseScene` ; **pas de validation GPU, d’aperçu éditeur ou de lecture effective en jeu**. Les banques absentes n’ont pas été chargées.

[Scripts et résultats](../../source/cliffnordouesttest1_nuit_v2/README.md).

L’arène V3 est un livrable distinct, déjà nocturne : [roche/glace référencées, montagnes à l’horizon et mer de sapins](../../renders/arene_glace_sky_peak_v3/README.md).
