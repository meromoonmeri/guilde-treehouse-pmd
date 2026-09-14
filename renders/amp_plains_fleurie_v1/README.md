# Amp Plains — plaine verdoyante et fleurie

## Ouvrir
- `../../apercu_amp_plains_fleurie_v1.html` : galerie autonome, animation et sélection des calques.
- `amp_plains_fleurie/COMPOSITION.png` : composition 456 × 408, taille de la référence originale.
- `amp_plains_fleurie/ANIMATION_COMPLETE.webp` : boucle complète des trois cadences.
- `amp_plains_fleurie/amp_plains_fleurie.ora` : calques alignés, état initial.
- `amp_plains_fleurie_v1.zip` : livraison avec galerie, calques, sprites, sources et références.

## Contenu
8 calques statiques : herbe, chemin, ombres de contact, falaises, rochers, petits rochers et deux arbres indépendants. Six groupes animés, chacun décliné en quatre PNG plein cadre : fleurs au sol et floraison des arbres, chacun aux cadences natives de 8, 10 et 14 frames de jeu. Toutes les images de scène sont alignées à 456 × 408.

19 emplacements de fleurs au sol ; 18 sur les deux couronnes. Les trois poses natives de 24 × 24 suivent les quatre clés **0, 1, 0, 2**. Les groupes ont des déphasages locaux ; les trois horloges bouclent ensemble après **1120 frames de jeu**, soit **18,6667 s à 60 Hz**. Le WebP arrondit les horodatages cumulés à la milliseconde (18 667 ms). Les 272 intervalles sont décrits dans `manifest.json`, avec 64 compositions PNG dédupliquées. Ne pas lire simplement les PNG numérotés comme une suite à cadence constante.

## Provenance et adaptations
- Géologie : `Amp_Plains_entrance_TD.png`, silhouettes et positions exactes des composantes grises conservées, hormis les deux arbres morts retirés. Les rochers sont recolorés avec une gamme brun clair, en conservant leurs valeurs de relief.
- Herbe : échantillon natif 48 × 48 de `Vast_Steppe_Base`, répété sans agrandissement ni recoloration.
- Sable : échantillon natif 24 × 24 de `Metano_Town_Base`, coordonnées archivées. Le générateur fournit **uniquement le guide de silhouette** du chemin sur magenta ; ses pixels de sable sont remplacés par le matériau natif, avec une bordure translucide d’un pixel. Le guide est ramené au vrai canevas 456 × 408, puis légèrement infléchi. La répétition du matériau n'est pas un autotile validé.
- Arbres : deux arbres PMD existants des calques Objects/Fringe de l’entrée Vast Steppe de Halcyon, extraits sans génération, recoloration ni changement d’échelle. L’alpha du tronc est isolé des touffes environnantes ; les pixels visibles restent aux coordonnées et couleurs des sprites source. Leur origine ROM officielle n’a pas été vérifiée indépendamment.
- Floraison des couronnes : **adaptation**, faite de pétales des fleurs natives de Vast Steppe sur un calque séparé. Ce ne sont pas des variantes fleuries officielles certifiées ni des arbres fleuris natifs intacts.
- Ombres de contact : reconstruction indépendante.

Références Halcyon : branche `working-copy`, commit `1522c7a8b7a34d70078e11ed605b21d563b0dc51`. Les neuf fichiers téléchargés et leurs identifiants/hachages sont dans `source/amp_plains_fleurie_v1/references/provenance.json`. Les ressources réutilisées restent soumises aux droits de leurs ayants droit ; aucune licence nouvelle n’est conférée.

## Vérifications et limites
`source/amp_plains_fleurie_v1/verify.py` vérifie indépendamment : pixels/couleurs/coordonnées des arbres par rapport aux couches natives, poses des fleurs, silhouettes exactes des roches restantes, reconstruction des 272 états temporels, opacité des compositions, correspondance ORA/PNG et corridor central libre de 24 px. Il ne s’agit **pas** d’un test de collisions, d’import ou de fonctionnement dans PMDO. Le chemin, les positions végétales et les ombres constituent une nouvelle composition, pas une récupération du décor Amp Plains original en couches.

Reconstruction depuis la racine :
```sh
.venv/bin/python source/amp_plains_fleurie_v1/build.py
.venv/bin/python source/amp_plains_fleurie_v1/verify.py
```
Dépendances : Pillow, NumPy, SciPy et l’utilitaire de détourage existant `source/layouts_magenta_v1/palette.py`. Les références décodées et le guide généré sont déjà fournis. `inspect_references.py` permet de réexporter les atlas natifs depuis les fichiers Halcyon.
