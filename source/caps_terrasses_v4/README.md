# Dix créations supplémentaires — configuration Métano renforcée et audit

## Bilan honnête
**Dix créations générées, dix palettes corrigées, huit dessins retenus visuellement, deux refusés : 07 et 11.** Le travail de reprise de ces deux dessins reste à faire. La tentative de régénération de 07 a été refusée par l’outil après dix générations ; aucun fichier de reprise n’a été produit. Ne pas annoncer dix dessins certifiés conformes.

## Configuration plus stricte du générateur
Chaque appel recevait trois images :
1. un terrain du lot précédent pour la présentation latérale et proche de la caméra ;
2. `reference_matiere_stricte.png`, avec les vrais échantillons d’herbe, de roche, de rebord et de pied de Métano (agrandissements nearest-neighbor explicitement réservés à l’inspection) ;
3. `source/falaises_generees/reference_canonique.png`, pour la matière et ses raccords en contexte.

Les consignes interdisaient les galets génériques, les gros blocs réinventés, les bandes de grès lisse, les contours noirs épais et les nouveaux chemins/objets. Le dessin devait conserver la couronne rocheuse mince et irrégulière sous l’herbe Métano, une falaise proche caméra et un espace latéral pour l’océan, le tout sur fond magenta. Les originaux générés sont conservés dans `renders/caps_terrasses_v4/bruts/`.

Références de présentation : 07/10/13/15 prennent la terrasse gauche V3 ; 08/09/14 la terrasse droite ; 11 la corniche gauche ; 12/16 le balcon droit. Ce ne sont pas des imports de nouveaux motifs canoniques.

## Contrôle des vraies sources
`prepare.py` décode `Metano_Town_Base.tile` et `Metano_Town_Cliffs.tile` du dossier natif, reconstruit les rectangles indiqués dans la provenance et compare les quatre échantillons RGBA existants. Ces comparaisons passent. Les coordonnées, couleurs et empreintes des fichiers figurent dans `palette_canonique.json`.

Le petit échantillon plat ne contenait pas l’ombre mauve profonde nécessaire à certains retours. La couleur **96,56,88** a donc été ajoutée depuis un pixel opaque effectivement trouvé dans la banque Cliffs, avec ses coordonnées enregistrées et revérifiées. Aucun assombrissement inventé.

## Correction colorimétrique mesurée
La palette autorisée contient **328 couleurs RGB réellement issues de ces ressources natives**. Pour chaque pixel de terrain généré, le script choisit la couleur de cette palette la plus proche en CIELAB (distance ΔE76, conversion sRGB/D65). Aucune réduction des dimensions et aucun flou spatial. Contrairement au lot V3, les couleurs du terrain jour sont volontairement corrigées ; les sorties brutes restent disponibles pour comparaison.

Le détourage utilise le magenta pur et ses franges connectées au bord, sans effacer automatiquement toutes les ombres mauves. Les exports ont un alpha binaire et un RGB nul derrière l’alpha nul. Le terrain 10 a été décalé de 26 pixels vers le bas pour raccorder le premier plan au bas de son canevas ; ce décalage est enregistré et vérifié, sans mise à l’échelle.

**Résultat : zéro pixel opaque du terrain jour hors palette canonique.** Cela ne concerne ni les fonds de démonstration, ni les sorties brutes, ni les couleurs nocturnes dérivées par le filtre Abyss. La distribution des corrections ΔE est publiée par image dans `audit_couleurs.json` : ce n’est pas une mesure d’identité du dessin.

## Audit visuel — ne pas confondre palette et motif
`audit_visuel.json` décrit l’inspection des dix compositions et des coupes de couronne avant/après. Les zones 13 et 11 ont une coupe choisie manuellement sur la face avant, au lieu d’un simple bord arrière du plateau.

- **07 refusée** : roche en galets verticaux et couronne en chapelet, différentes de la texture demandée.
- **11 refusée** : gros blocs et rebord lisse à double bande, trop simplifiés par rapport à Métano.
- **08, 09, 10, 12, 13, 14, 15, 16 retenues visuellement**, avec observations individuelles conservées (grain, extrémités de couronne, profondeur et répétition). Cette appréciation ne certifie pas une identité aux tuiles natives, un autotiling ou des raccords seamless entre cartes.

Les deux refus sont visibles dans la galerie, la planche et le catalogue. Ils sont conservés pour inspection, pas présentés comme des résultats validés. **Prochaine action : régénérer 07 et 11 en gardant leurs layouts, remplacer leur mauvais motif et leur couronne, puis refaire les mêmes contrôles.**

## Fichiers et aperçu
- `renders/caps_terrasses_v4/` : terrain texturé transparent, fond magenta, nuit Abyss, composition de démonstration ; originaux dans `bruts/`.
- `AUDIT_BORDURES_AVANT_APRES.png` : comparatif avec la référence canonique et coupes à taille native.
- `audit/*_bande_reperage.png` : repérage heuristique pour l’inspection, **pas un calque de couronne canonique ni une collision**.
- `apercu_caps_terrasses_v4.html` : aperçu autonome, proportions des terrains conservées, affichage du statut d’audit, jour/nuit, visibilité des plans et océan V3 de 64 phases réutilisé sans modification.

Les fonds des scènes sont ajustés au canevas ; les PNG de terrain ne sont pas redimensionnés. Les six créations précédentes, le témoin, les tuiles canoniques et le mod PMDO restent inchangés. Aucune intégration native ni validation GPU revendiquée.

## Reproduction
Dépendances : Pillow, numpy, scipy.

```sh
python source/caps_terrasses_v4/prepare.py
python source/caps_terrasses_v4/build.py
python source/caps_terrasses_v4/audit_visuel.py
python source/caps_terrasses_v4/gallery.py
python source/caps_terrasses_v4/verify.py
node source/caps_terrasses_v4/test_viewer.cjs
```

Les scripts ne refont pas les appels du générateur. `build.py` réinitialise les statuts visuels : une nouvelle génération exige une nouvelle inspection, pas une validation automatique aveugle. `audit_visuel.py` consigne la revue de ces dix sorties ; mettre à jour ses observations si les PNG changent. Les tests de galerie utilisent un DOM simulé et ne sont pas un test dans un navigateur réel.

La revue visuelle est épinglée aux SHA des sorties brutes et des pixels RGBA corrigés (`visual_review_pins.json`). Le script refuse d’appliquer les anciennes appréciations à une nouvelle image ou à un export modifié : revoir les images et mettre à jour les observations/empreintes explicitement.
