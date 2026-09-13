# Six calques de falaise — proches de la caméra, face à la mer

[Planche des six compositions](PLANCHE_FACE_MER.png) · [Aperçu autonome animé](../../apercu_caps_terrasses_v3.html)

Même principe que **Cap V2 / Terrasse V2** : masses de terrain au premier plan, sur un côté, avec une vue dégagée sur la mer. Générateur guidé par les références de roche et d’herbe Métano, sur fond magenta.

**Six plans de terrain complets**, chacun regroupant herbe, roche et bordures. L’océan, le ciel et les nuages restent sur des plans distincts ; le terrain ne contient pas de mer. PNG **1640 × 656**, aucun redimensionnement du terrain.

| Variante | Terrain transparent | Nuit Abyss | Magenta | Scène |
|---|---|---|---|---|
| Cap gauche | [PNG](01_cap_gauche_terrain.png) | [PNG](01_cap_gauche_terrain_nuit.png) | [PNG](01_cap_gauche_fond_uniforme.png) | [Jour](01_cap_gauche_scene.png) · [Nuit](01_cap_gauche_scene_nuit.png) |
| Cap droit | [PNG](02_cap_droit_terrain.png) | [PNG](02_cap_droit_terrain_nuit.png) | [PNG](02_cap_droit_fond_uniforme.png) | [Jour](02_cap_droit_scene.png) · [Nuit](02_cap_droit_scene_nuit.png) |
| Terrasse droite | [PNG](03_terrasse_droite_terrain.png) | [PNG](03_terrasse_droite_terrain_nuit.png) | [PNG](03_terrasse_droite_fond_uniforme.png) | [Jour](03_terrasse_droite_scene.png) · [Nuit](03_terrasse_droite_scene_nuit.png) |
| Terrasse gauche | [PNG](04_terrasse_gauche_terrain.png) | [PNG](04_terrasse_gauche_terrain_nuit.png) | [PNG](04_terrasse_gauche_fond_uniforme.png) | [Jour](04_terrasse_gauche_scene.png) · [Nuit](04_terrasse_gauche_scene_nuit.png) |
| Corniche gauche | [PNG](05_corniche_gauche_terrain.png) | [PNG](05_corniche_gauche_terrain_nuit.png) | [PNG](05_corniche_gauche_fond_uniforme.png) | [Jour](05_corniche_gauche_scene.png) · [Nuit](05_corniche_gauche_scene_nuit.png) |
| Balcon droit | [PNG](06_balcon_droit_terrain.png) | [PNG](06_balcon_droit_terrain_nuit.png) | [PNG](06_balcon_droit_fond_uniforme.png) | [Jour](06_balcon_droit_scene.png) · [Nuit](06_balcon_droit_scene_nuit.png) |

Les sorties brutes du générateur sont aussi conservées sous `*_magenta.png`. Pour la variante 04, le terrain exporté est décalé de 256 px vers la gauche avec recadrage, afin d’ouvrir la vue mer à droite ; aucun pixel conservé n’est repeint. Le PNG `_fond_uniforme` correspond exactement à ce cadrage exporté.

## Fonds séparés et cycle océan

[Océan : 64 phases jour/nuit et cadence](ocean/README.md) · [Paramètres JSON](ocean/animation.json)

[Ciel](fonds/ciel.png) · [Ciel nuit](fonds/ciel_nuit.png) · [Nuages](fonds/nuages.png) · [Nuages nuit](fonds/nuages_nuit.png)

Les fonds V2 restent à leur résolution source. Les compositions de démonstration les ajustent au canevas du terrain en nearest-neighbor. Nuages fixes dans cet aperçu ; le pack précédent n’est pas modifié.

**Limites :** créations générées d’après Métano, pas copies certifiées pixel à pixel de ses tuiles. Aucun nouveau Ground, collision ou test GPU livré. Ce lot ajoute des calques PNG et un aperçu, pas une mise à jour du mod natif.
