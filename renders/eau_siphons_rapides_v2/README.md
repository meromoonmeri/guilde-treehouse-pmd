# Siphons V2 — aspiration rapide, palette cycling et approche praticable

Correction non destructive de `eau_integrale_rochers_gris` (74c4cd9). Les anciens fichiers restent disponibles.

## Changements
- Eau entraînée vers les centres : filets qui suivent des trajectoires spiralées **vers l’intérieur**, en sens horaire, avec accélération à l’approche du centre.
- Palette cycling bleu–cyan sur toute la surface : une table de 24 entrées, décalée de deux indices par phase. Le jeu de couleurs est fixe, leur attribution aux pixels change.
- Spirales visibles ajoutées aux cuvettes ; les six poses de la version précédente tournent désormais en 240 ms au lieu de 360 ms. Les bras lumineux se déplacent vers l’intérieur et tournent également en 240 ms.
- Bordure d’eau/écume animée autour des rochers et de la chaussée. Reflets mobiles sur leurs bords, en calque séparé.
- Rochers dans une palette ardoise bleutée, cohérente avec l’eau ; reliefs et positions conservés.
- Une **chaussée rocheuse continue depuis le sud jusqu’au bord du grand siphon**, terminée par un palier. Son intérieur reste sec et n’est pas traversé par les effets d’eau. Elle mène au siphon, pas sur une surface d’eau prétendument marchable.

## Livrables
Scène : `eau_siphons_rapides/`, 456×384.
- `COMPOSITION.png`, phase zéro.
- `ANIMATION_COMPLETE.webp` : 48 phases à 40 ms (25 images/s), boucle de 1,92 seconde.
- 48 compositions complètes PNG.
- 5 groupes animés de 48 PNG chacun : surface/palette cycling, filets d’aspiration, spirales, écume, reflets sur rochers.
- 6 calques statiques : ombres de contact, trois partitions de rochers, surface et rebords de chaussée.
- `eau_siphons_rapides.ora` : les 11 calques à la phase zéro. L’ORA n’anime pas les séquences ; importer les phases séparées selon le manifeste.
- `masque_approche_sud_palier.png` : masque de contrôle de continuité du passage, **pas un fichier de collision PMDO**.
- ZIP `SIPHONS_RAPIDES_V2_calques.zip` : PNG, calques, ORA, masque et documentation ; brut généré et galerie exclus.
- Galerie autonome à la racine : `apercu_eau_siphons_rapides_v2.html`, animation, inspection des groupes/calques, pause et curseur des phases.

## Ordre et origine des calques
Composer les quatre premiers groupes animés, puis les six calques statiques, puis les reflets sur les rochers. L’ordre exact et les cadences figurent dans `manifest.json`.

La chaussée est une nouvelle génération sur magenta, détourée puis ajustée à la scène et recolorée. Elle est partitionnée en surface/rebords visibles : ce ne sont pas des objets complets avec des faces cachées reconstruites. Le palier touche le bord sud du grand siphon, dont le centre visuel est (231,144).

Les anciennes poses de siphons étaient déjà des adaptations de six phases de sable ; elles ne deviennent pas des animations natives d’eau parce qu’elles sont accélérées. Les courants, spirales lumineuses, palette cycling, écume et reflets sont de nouveaux effets procéduraux. Aucune prétention à une simulation hydrodynamique : les trajectoires visuelles sont masquées par les rochers et le chemin, sans solveur de collisions de fluide. Les cycles des filets sont décalés entre 1920, 960 et 640 ms, tous divisant la boucle complète.

## Vérifications
Reconstruction : `source/eau_siphons_rapides_v2/build.py`, puis `verify.py` (Pillow, numpy, scipy).
- Opacité de toutes les compositions et recomposition ORA exacte.
- 48 compositions sauvegardées recomposées pixel à pixel depuis leurs PNG indépendants, toutes distinctes.
- Connexion sud → palier avec une marge intérieure de 12 px par rapport au contour de la chaussée.
- Intérieur du passage identique au terrain sec dans les 48 phases.
- Même palette de surface à chaque phase, indices cyclés.
- Rayon des trajectoires strictement décroissant pendant leur course, avant réapparition invisible au bord extérieur.

**Pas de test runtime PMDO/GPU, ni de collisions, dégâts, aspiration des personnages ou téléportation configurés.** Le chemin est prévu pour la marche ; sa jouabilité et le comportement au bord du siphon doivent encore être validés dans le moteur. Les générations ne sont pas présentées comme de nouveaux sprites officiels.
