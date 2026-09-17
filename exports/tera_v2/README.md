# Couronnes et verre prismatique — lot 02

**17 septembre 2026. Galerie : `apercu_tera_v2.html` à la racine.**

Ce lot répond à trois volets : régénération des accessoires, traitement de verre animé compatible avec les cellules SpriteCollab, et reprise de la file de ressources manquantes **du projet**, périmètre confirmé par l'utilisateur. Ce n'est pas une déclaration d'achèvement de tout SpriteCollab ni une validation PMDO.

## 1. Couronnes régénérées

Dix générations réussies ont produit des propositions pour **19 types** : Feu et Eau repris, plus les 17 types auparavant absents. Les premières versions Eau/Normal/Plante comportaient des anneaux pendants incorrects ; elles sont rejetées et remplacées par de nouvelles générations, pas simplement retouchées au pinceau.

- Feu : **4 vues cardinales**, diagonales absentes.
- Eau : **8 propositions de vues**, orientation non certifiée, notamment DL à revoir.
- Autres 17 types : **une proposition frontale chacun**, pas huit directions ni animation de couronne.
- **Vol doit être régénéré** : le remplacement n'a pas respecté le compte canonique de deux ballons rouges et deux verts.
- **Stellaire refusé pour utilisation** : statuette non fidèle, nombre exact des 18 pierres et 18 emblèmes non validé. Sa découpe se trouve dans `review/rejected_models`, pas dans les accessoires utilisables.
- Les autres modèles restent des candidats à revoir, pas une approbation artistique ou une reproduction canonique pixel-exacte.

Les accessoires n'incluent **aucun Pokémon porteur, tête ou corps sous la couronne**. Les joyaux frontaux sont sans yeux. Les emblèmes intrinsèques des types restent reconnaissables : crâne Poison, symbole d'œil Psy, masque Ténèbres, fantôme Spectre. Ce sont des motifs décoratifs, distincts du visage du porteur.

`crown_manifest.json` donne les sources, découpes, directions demandées et réserves. PNG de présentation : cellules 64×80, **pas** de fausse feuille `.Dir8` lorsque les directions manquent. Les nouveaux modèles ne remplacent pas les anciens profils d'attachement sans nouvelle calibration par type, espèce, pose et direction. La matérialisation animée de tous les types reste à faire.

Une revue supplémentaire `review/fire_attached_glass.gif` réunit le nouveau Feu et le verre sur quatre formes × quatre vues cardinales (16 placements proposés, pose Idle initiale). L’assise arrière de Carapagos a été abaissée de deux pixels natifs après revue du vide au-dessus de sa tête. Les occultations cornes/oreilles restent non validées.

## 2. Surface de verre animée

`source/tera_v2/prismatic.py` accepte une cellule RGBA sans identifiant d'espèce, sans repère de tête et sans couronne. Il combine :

- facettes triangulaires et orientation locale de la surface ;
- reflets blancs mobiles, dispersion spectrale et liseré de bord ;
- réfraction locale qui ne prélève jamais dans une autre cellule ou hors du Pokémon ;
- protection des pixels sombres pour conserver yeux et contours ;
- **alpha exactement conservé**, y compris les pixels partiellement transparents ; RGB des pixels totalement transparents également conservé.

Il s'agit d'une interprétation du verre prismatique inspirée de Téra, **pas du shader officiel extrait du jeu**. Les reflets sont calculés en pixels ; ils ne sont ni un simple halo extérieur ni un remplacement global du Pokémon par une couleur uniforme.

### Exports et horloges

**59 planches sources locales**, dans six dossiers, ont été traitées sur **24 phases**, soit **1 416 variantes PNG** et **25 728 contrôles cellule-phase**. Cela couvre toutes les planches localement disponibles, y compris les actions de chute/roulade : les restrictions des couronnes ne bloquent pas un traitement de surface fondé sur l'alpha. Les six dossiers comprennent quatre formes actives et deux archives Carapagos, pas six nouvelles espèces.

- `surface_banks/{profil}/phase_00…23/` : les variantes conservent les dimensions et le découpage de chaque planche native.
- `surface_manifest.json` : sources, tailles des cellules, variantes, horloges et actions déclarées dont les sources locales sont absentes.
- `AnimData.xml` conservé à l'identique : **aucune multiplication des durées des actions**.
- Horloge de lumière indépendante : une phase tous les 4 ticks, période 96 ticks / 1,6 seconde à 60 ticks/s. L'animation du corps garde sa propre horloge.
- Les GIF locaux utilisent un multiple commun des périodes pour montrer le corps animé et les reflets ensemble. Le GIF des douze silhouettes distantes montre la première pose figée avec la lumière animée ; leurs planches complètes sont néanmoins traitées et testées.

Ces banques sont une référence de rendu et des variantes de texture, **pas des sprites de remplacement à soumettre tels quels à SpriteBot**, ni un pack compilé directement jouable. Un contrôleur moteur doit sélectionner la frame d'action native et la phase de matériau indépendamment. Ce contrôleur n'est pas installé dans PMDO.

## 3. Périmètre de tout SpriteCollab

L'inventaire est complet à la révision `3609a86be2a4c8ad7cf255bd2255f044daafe24f` :

- **984 racines** interrogées séparément, sans erreurs ni troncature ;
- **3 337 fichiers AnimData.xml** de formes ;
- **55 953 planches `*-Anim.png`**, environ 853 Mo de sources avant variantes.

La première requête récursive globale était tronquée : elle n'a pas servi à annoncer une couverture complète. Les fichiers natifs récupérés restent dans `.cache/tera_v2`, non dans Git.

`catalogue_surface.py` peut traiter **à la demande toute planche de cet inventaire**, sans ajouter de règle par espèce. Il vérifie le SHA Git du PNG, charge les dimensions natives dans le XML, conserve les crédits et rend la phase demandée. La sortie est limitée à `exports/tera_v2` pour ne pas écraser les originaux.

```bash
.venv/bin/python source/tera_v2/catalogue_surface.py \
  --source 0025/Idle-Anim.png --phase 6 \
  --output exports/tera_v2/custom/pikachu_phase06.png
```

**Compatibilité de l'outil ≠ traitement réalisé de tout le catalogue.** Douze planches distantes ont été réellement récupérées et vérifiées sur les 24 phases : Pikachu, Magnéti, Fantominus, Onix, Ronflex, Zarbi, Wailord, Skelénox, Kyogre, Motisma, Majaspic et Statitik. Les 288 variantes sont dans `remote_banks/`, avec les crédits natifs. Les **55 941 autres planches** restent non rendues/non vérifiées. L'état exact par fichier est dans `spritecollab_catalogue.csv` ; il ne faut pas déduire la couverture de toutes les actions d'une espèce depuis son seul Idle.

## 4. Portraits et sprites manquants du projet

`project_queue.json` conserve la file choisie par l'utilisateur et les ressources à ne pas remplacer :

| Sujet | Existant à préserver | Reste |
|---|---|---|
| Carapagos personnalisé | 32 actions, 16 portraits déjà exportés ; six originaux inchangés | Revue artistique finale et PMDO ; galerie consolidée ajoutée ici |
| Zarude `0893` | 16 émotions natives | Sprites, notamment corriger l'ouest du premier modèle |
| Terapagos Stellaire `1024/0002` | Normal et Normal^ natifs | 15 émotions et sprite fidèle ; ancien généré rejeté |
| Méga-Raichu X `0026/0002` | Normal natif retrouvé et conservé | 15 émotions et sprites ; référence corporelle officielle à vérifier |
| Méga-Raichu Y `0026/0003` | Normal natif retrouvé et conservé | 15 émotions et sprites ; référence corporelle officielle à vérifier |

L'audit du projet comporte aussi **46 espèces de base sans sprites** et aucune sans portrait Normal. Les dictionnaires du tracker sont interprétés par leurs **clés** ; leurs booléens sont des verrouillages, pas des indicateurs d'absence.

**Aucun nouveau portrait ou sprite de ces espèces n'a été produit dans ce tour.** Les deux demandes de génération suivantes, Zarude ouest et Terapagos Stellaire fidèle, ont été bloquées après les dix générations de couronnes. Elles n'ont créé aucun fichier et ne sont pas comptées comme livrées. La galerie Carapagos est un regroupement d'existants, pas une nouvelle production.

## Vérifications et reprise

```bash
.venv/bin/python -W error -m unittest source.tera_v2.test_prismatic source.transformations_v1.crown_attachment.test_attachment -v
.venv/bin/python source/tera_v2/build.py
.venv/bin/python source/tera_v2/remote_review.py
.venv/bin/python source/tera_v2/project_queue.py
.venv/bin/python source/tera_v2/attached_review.py
.venv/bin/python source/tera_v2/gallery.py
.venv/bin/python source/tera_v2/verify.py
```

11 tests unitaires passent, y compris cellules totalement opaques, dimensions d'un pixel, pixels semi-transparents, absence de contamination entre cellules, périodicité et non-mutation. Rapports : `surface_verification.json`, `remote_verification.json`, `catalogue_report.json`. Les tests de pixels et de géométrie ne certifient ni fidélité artistique, ni palette de soumission SpriteBot, ni intégration.

**Ground/Dungeon PMDO : aucun test réel ni intégration de ce nouveau matériau effectués.** Couronnes adaptées à toutes les têtes, directions manquantes, motifs non fidèles, animations de tous les types, portraits/sprites de la file et tests moteur restent à poursuivre.

### Provenance

Designs de couronnes : descriptions des Tera Jewels de Scarlet/Violet consultées dans [Terastal phenomenon](https://bulbapedia.bulbagarden.net/wiki/Terastal_phenomenon), avec les références Feu/Eau conservées dans `source/transformations_v1/references`. Nouvelles images du générateur dans `source/tera_v2/generation`, dont essais rejetés. Les captures trouvées via recherche ne sont pas des sprites PMD approuvés. Le générateur a encore commis des erreurs détaillées ci-dessus.

Personnages et portraits : SpriteCollab à la révision indiquée. Crédits exacts des douze échantillons conservés dans chaque `remote_banks/{slot}/credits.txt`, références Méga-Raichu dans `source/pokemon_custom/next_species/references/mega_raichu_{x,y}`. Ne pas attribuer une licence unique inventée à l'ensemble ; respecter chaque fichier de crédits, y compris ses restrictions.
