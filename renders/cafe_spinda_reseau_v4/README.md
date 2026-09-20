# Café & Casino Spinda — cinq zones générées, trois niveaux

[Ouvrir l’atelier](index.html). Aperçus magenta supplémentaires dans le dépôt : `SpindaV4_accueil_magenta.webp` et `SpindaV4_cafe_croisillons_magenta.webp`.

## La bonne direction : le café de Spinda

Cette version remplace la méthode d’agrandissement par bandes pour la demande actuelle. L’utilisateur a précisé : **génération guidée par les textures canoniques, bordures immersives, pièces séparées, plusieurs étages et fenêtres rondes à croisillons**, puis a montré le véritable café de Spinda.

L’**accueil `accueil_spinda_fidele` a été choisi parmi deux propositions**. Les quatre autres pièces ont ensuite été générées séparément à partir de cette direction et de la référence native Spinda. Elles ne sont pas encore approuvées artistiquement par l’utilisateur. Les premières études aux grosses façades et deux essais d’étage corrigés sont archivés, pas utilisés par la livraison.

On retrouve la salle ovale, les boiseries tournées vers l’intérieur, le plancher doré horizontal, les lumières en spirales, le rebord rocheux bas et l’entrée sud de Spinda. **Pas de grande façade extérieure en roche ou en troncs.** Les matières de la génération sont des interprétations référencées ; elles ne deviennent pas des pixels canoniques simplement parce qu’une référence native a été fournie.

## Réseau proposé

| Niveau | Zones |
|---|---|
| +1 | **Café à l’étage ↔ Salon des croisillons** |
| RDC | **Accueil de Spinda**, sortie sud, départs vers −1 et +1 |
| −1 | **Casino souterrain ↔ Salon des jeux** |

Cinq maps indépendantes, **600×448px chacune**, grille d’import8px. Quatre liaisons bidirectionnelles :

1. accueil / descente ↔ casino / retour ;
2. casino / E ↔ salon des jeux / W ;
3. accueil / montée ↔ café / retour ;
4. café / E ↔ salon des croisillons / W.

`manifest.json` donne les points et destinations réciproques. Les marqueurs latéraux sont relevés sur les véritables ouvertures générées. Il s’agit de **transitions entre cartes distinctes**, pas d’une mosaïque dont les bords seraient garantis raccordables pixel par pixel. Le salon inférieur a notamment une entrée décalée en hauteur.

**Ce réseau est un plan d’intégration, pas un réseau de warps PMDO déjà programmé.** Collisions, points de spawn, scripts et interactions restent à configurer et tester dans votre éditeur.

## Calques et aménagement

**25 calques alignés**, origine0,0, sur cinq cartes :
- plancher, avec fond reconstitué seulement sous les lumières extraites ;
- spirales et lumières **statiques**, pas une animation prétendument native ;
- boiseries et rebord arrière ;
- bordures latérales/avant et seuil ;
- fenêtres natives aux deux salles de l’étage ;
- propositions d’escaliers natifs sur un calque **désactivé par défaut** à l’accueil, au casino et au café.

Le recomposé éclairé est exactement égal à la génération détourée et normalisée, hors retouche locale du petit avis mural indésirable de l’accueil. Aucun plan n’est refait par bandes. Les sous-couches des lumières sont complétées par le pixel non éclairé le plus proche sur la même rangée de planches : ce fond caché est une reconstruction, pas une matière native récupérée.

Les partitions de murs et de bordures sont des surfaces visibles, **pas des volumes mobiles avec intérieur caché reconstruit**. L’escalier du seuil sud fait partie de l’architecture générée de l’accueil choisi ; les autres escaliers sont des propositions natives indépendantes.

**Aucun meuble, marchand, brasero ou fourneau n’est placé dans les cinq scènes.** Le catalogue séparé contient :
- vraie planche de décoration Spinda (`SpindaCafe2`) : rubans, éléments de comptoirs, plantes, tables… ;
- vraie planche de matières/base Spinda (`SpindaCafe1`), pour les bois/roches et les façades des comptoirs qui font partie de cette banque. Cette planche de référence avec empreintes d’objets n’est PAS une nouvelle salle à importer telle quelle ;
- kiosque vide généré, en plans arrière et avant : placer le Pokémon entre les deux dans l’éditeur (repère visuel de pieds56,80 dans le canevas112×128, à adapter au sprite) ;
- corps de fourneau **généré, non natif**, sans feu (flamme native à l’offset32,32) ;
- support de brasero natif sans flamme.

Les motifs Pokémon des comptoirs de référence font partie de leur architecture. Aucun personnage NPC n’est dessiné dans les nouvelles maps. Les guides/grilles du viewer ne sont jamais imprimés dans les exports.

## Vraies fenêtres circulaires à croisillons

Sprite extrait de **`Guild_Heros_Room_Objects.tile`**, Palikadude/Halcyon, commit `da6c2130d641507447e6386a5e47a296e8cb4c71`. Crop natif `(176,56)–(240,120)`, canevas64×64, silhouette52×59 avec son arrondi en perspective. **Aucun agrandissement, recoloration, cadre redessiné ni disque de paysage collé.** Le verre et la croix viennent du sprite original.

Deux fenêtres au café, trois au salon supérieur, aucune dans les pièces souterraines ou l’accueil. Elles peuvent être masquées/exportées séparément. Banque, crop et empreintes : `fenetre_provenance.json` et références du script.

Escalier de proposition : `Guild_Second_Floor_Objects.tile`, crop natif208,128–304,200 (96×72), importé sans redimensionnement. Ses positions et directions de liaison sont des aides d’aménagement ; il faut régler les marqueurs, les collisions et les conditions d’accès dans le moteur.

## Vraies flammes séparées

Quatre poses Ledian/Halcyon, sans resampling, conservées dans l’ordre source. **6ticks par pose** ; aperçu100ms/pose sous hypothèse60Hz, boucle400ms. Le viewer n’anime que le brasero du catalogue, pas les lumières statiques des salles.

- atlas `SpindaV4_flamme_4poses.png` :128×40, quatre poses32×40 ;
- atlas `SpindaV4_brasero_4poses.png` :128×64, quatre poses32×64 ;
- huit PNG individuels et support séparé ; provenance dans `flammes_provenance.json`.

## Import et fichiers

**Le ZIP contient les25calques directement en PNG**, les assets natifs/générés séparés et un viewer autonome après extraction. Importer avec **PNG to Tileset, taille8px pour ces Ground**. Les basenames `SpindaV4_<salle>_<calque>` sont uniques. Garder l’origine0,0 des calques600×448 et ne pas les redimensionner. Les sprites natifs du catalogue gardent leur propre échelle1×.

Dans le dépôt, ces calques sont conservés en **WebP lossless** pour éviter plusieurs copies lourdes. Le packaging les convertit enPNG en comparant tous les octets RGBA. Le viewer permet aussi de télécharger chaque calque ou la composition enPNG. Les bruts et anciennes études sont conservés dans le dépôt, **exclus du ZIP**.

Les cinq générations actives font1200×896 ; seules les images générées sont normalisées à600×448 en nearest-neighbour. Les fenêtres, escaliers et flammes natifs ne subissent pas cette réduction. Le détourage supprime le magenta et les petits pixels isolés. Le petit avis mural généré malgré la consigne à l’accueil est remplacé localement par le bois adjacent, avec raccord adouci ; le brut choisi est conservé. Zone exacte dans `manifest.json`.

En modefile://, certains navigateurs bloquent les exports canvas. Les PNG du ZIP restent directement utilisables. Sinon servir le dossier par HTTP : `python -m http.server 8005 --bind 0.0.0.0`.

Aucun `.rsground` neuf, NPC, collision ou warp installé. Pas de validation en jeu. Les contrôles techniques ne valent pas approbation artistique des nouvelles salles.

## Reproduction et sources

Depuis le dépôt (Pillow, NumPy, SciPy) :

```sh
python source/cafe_spinda_reseau_v4/build.py
python source/cafe_spinda_reseau_v4/verify.py
python source/cafe_spinda_reseau_v4/package.py
node source/cafe_spinda_reseau_v4/test_viewer.cjs
python source/cafe_spinda_reseau_v4/package.py
```

Référence Spinda : `Minemaker0430/ExplorersOfSkyOrigins`, commit `4e7422acc263886198113a8256677766e4244228`, banques `SpindaCafe1/2` et `spinda_cafe.rsground`, conservées dans `source/cafe_multietage_v1/references/`. Références bois/fenêtre/escalier et feu : Palikadude/Halcyon au pin précité. La référence du café utilisée pour la génération est un crop sans redimensionnement de la reconstruction native EoSO, correspondant au design montré par l’utilisateur ; ce n’est pas une extraction revendiquée du fichier joint inaccessible sur disque.

Ancien café agrandi par bandes, anciens cafés V1–V3, casino et Beach conservés. Pour le budget, les grands bruts Beach ont été archivés losslessly avec leurs empreintes et le viewer Beach utilise ses PNG existants plutôt que leurs doublons embarqués ; aucun rendu ou ZIP Beach n’a été modifié.

Attribution : créateurs/contributeurs PMD, Minemaker0430/EoSO et Palikadude/Halcyon. Leur disponibilité publique ne constitue pas une licence générale de redistribution.

### Stockage des études supplantées
Les sept études non retenues sont maintenant conservées **à l’identique dans l’historique Git**, avec commit et SHA256 dans `bruts/archived_studies.json`. Les cinq bruts actifs, rendus, calques et ZIP restent en place. Le vérificateur lit ces archives directement ; restauration facultative : `python source/cafe_spinda_reseau_v4/archive_studies.py --restore`. Aucune livraison approuvée n’est supprimée.
