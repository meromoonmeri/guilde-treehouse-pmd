# Aride générée V1 — statut

Demande : reprendre les textures et les différents layers au générateur,
assembler une map finale. Entrée aride (sud → bouche au nord), une seule map
soignée, avec animation subtile proposée.

## Bruts (5 générations, 1224×864)

`bruts/` : terrain_complet (composition de direction), sol_seul, parois_seules,
props_seuls (4 arbres + 2 blocs isolés), fx_poussiere (3 voiles + grains).
Référence : `entrancearidedungeonpmdsky.png`. Normalisation /3 NEAREST → 408×288.

## Leçons de nettoyage (à réutiliser)

- Le générateur laisse du magenta en **speckles intérieurs** + large AA rose :
  inondation depuis les bords + despill itératif (R>140&B>140&G<170 adjacent).
- Smear du sol : ne copier que du sable **vrai (G-B > 15)** comme source,
  sinon liseré rose recopié sur tout le cadre. Dilatation ~500 itérations max
  (bandeau haut épais).
- Props : kill rose total (pas de rose légitime), bouche par seuil strict
  lum<150 (les fissures sont claires, le réseau sombre large est un piège).
- RGB zéro sous alpha 0 partout (leçon V10) pour GIF/WebP propres.

## Sorties

`renders/aride_generee_v1/` : 4 calques + 12 frames FX + composite + GIF/WebP +
ORA + manifest + verification. Galerie racine `apercu_aride_generee_v1.html`.
Pack `renders/aride_generee_v1_pack.zip`. 10 tests PASS.

## Limites

Généré guidé, pas natif. FX proposés. Pas de runtime PMDO. Les autres zones du
programme restent ouvertes (voir FULL_PROGRAMME_STATUS.json mis à jour).
