# Spring — colonne nettoyée et vraie pulsation

Correction remplaçant l’ancien spectre défilant. Le layout avec petit relief et escalier est conservé. Bassin et halo restent turquoise.

- `animation.webp` : 78 images, 6,5 s, sans perte.
- `composition.png` : maximum de pulsation, phase 39.
- `01_decor_escalier.png` : décor fixe assemblé.
- `02_colonne_nettoyee.png` : fond propre de la colonne.
- `colonne/00.png`…`77.png` : couleurs fixes, opacité pulsante.
- `planche_pulsation_78.png` : 10×8 cellules, fenêtres de 100×210 px du canvas (250,0)–(350,210).

La nouvelle colonne est un champ de couleurs analytique, sans réutilisation de pixels de rochers/cascades dans le calque de lumière. Un fond uniforme remplace les anciens pixels texturés **à l’intérieur du faisceau uniquement** ; ceci supprime aussi la texture du jet central qui apparaissait dans la colonne. Les cascades latérales et le bassin hors colonne ne sont pas repeints.

Les RGB restent fixes d’une frame à l’autre. Une sinusoïde fait monter puis descendre l’alpha une fois sur 6,5 secondes : **pas de défilement horizontal/vertical ni de rotation des teintes**. Les RGB sont nuls lorsque l’alpha vaut zéro, et aucune lumière ne sort du rectangle (275,0)–(325,201).

Ordre : décor/escalier, cycles natifs 3 et 13 du pack `soleil_spring_v1/spring/`, colonne nettoyée, pulsation. À la frame f de 0 à 77, phase native floor(f/2), modulo 3 ou 13. WebP : 83/83/84 ms répétés 26 fois. Galerie : `apercu_northern_calques_v1.html`, vue Spring.

Vérifications dans `renders/northern_calques_v1/verification.json` : RGB fixes, opacité monotone vers le maximum puis vers le minimum, aucun RGB caché dans l’alpha nul, absence de pixels hors colonne. Pas de validation PMDO/GPU. Les versions précédentes restent archivées.
