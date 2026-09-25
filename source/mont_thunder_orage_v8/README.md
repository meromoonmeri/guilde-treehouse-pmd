# Mont Thunder V8 — chemin sans bordure, brume physique au rebord rocheux

- **Terrain** : le guide V7 est édité au générateur (`generation/falaise_guide_sans_bordure.png`) : les pierres de bordure du chemin sont retirées et le gravier se fond dans la roche. Le reste ne change pas.
- **Brume du contrebas** : même bande opaque que la V7 (dérive −4 px/s), avec les étincelles électrostatiques.
- **Nouveau calque `06_brume_rebord`** (24 frames × 120 ms, boucle exacte). C'est un ressac de vapeur contre les parois : la brume monte au pied des faces rocheuses sombres puis retombe. La hauteur de la langue suit deux ondes qui avancent le long du contour de la falaise. Le bord est tramé en Bayer 4×4, donc l'alpha reste binaire. Le calque couvre seulement les parois, jamais le sol praticable, et il est placé devant le terrain.
- Le ciel, les nuages et les éclairs bleus sont repris de la V7.
- **Limites** : les ondes sont une approximation (le contour est estimé par x + y), ce n'est pas une simulation de fluide. Rien n'a été testé en jeu.
