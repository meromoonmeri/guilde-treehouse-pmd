# Intérieur du café Spinda

Quatre calques, combinant **déco / sans déco** et **jour / nuit**.

| Fichier | Déco | Moment |
|---|---|---|
| `interieur_sans_deco_jour.png` | non | jour |
| `interieur_avec_deco_jour.png` | oui | jour |
| `interieur_sans_deco_nuit.png` | non | nuit |
| `interieur_avec_deco_nuit.png` | oui | nuit |

Chaque calque est un PNG à fond transparent, bords nets (0 pixel
semi-transparent), généré en cascade à partir du précédent pour que le décor et
l'éclairage se superposent sans décalage.

## Échelle PMDO

Les quatre calques font **456 × 320 px**, soit **57 × 40 cellules** de 8 px.

Cette taille n'est pas arbitraire : c'est celle de l'intérieur du café de
Metano Town dans `Palikadude/Halcyon` (`Data/Ground/metano_cafe.rsground`),
relevée sur les assets réels. Le viewport correspond donc exactement à celui
d'une salle intérieure PMDO.

Le générateur rend en ~1180 × 910 : `../tileset_pmd/mettre_interieur_echelle_pmdo.py`
détoure le magenta, réduit par **couleur dominante** de chaque bloc — un filtre
classique moyennerait les pixels et rendrait les bords flous — puis centre la
salle dans le cadre 456 × 320.

```bash
python3 ../tileset_pmd/mettre_interieur_echelle_pmdo.py interieur_*.png
```

### Version calée sur la grille 8 px

Dans le cadre 456 × 320, la salle tombe à l'offset x=20 pour une largeur de
415 px : ni l'un ni l'autre n'est un multiple de 8, donc ses bords tomberaient
au milieu des tuiles et le découpage en `.tile` serait décalé.

`../tileset_pmd/caler_grille8_interieur.py` la recadre sur des frontières de
cellules : **52 × 40 cellules** pleines (416 × 320 px), à l'offset (16, 0).

| Fichier | Contenu |
|---|---|
| `interieur_sans_deco_jour_grille8.png` | jour, sans déco, calé grille |
| `interieur_sans_deco_nuit_grille8.png` | nuit, sans déco, calé grille |
| `interieur_avec_deco_jour_grille8.png` | jour, décoré, calé grille |
| `interieur_avec_deco_nuit_grille8.png` | nuit, décoré, calé grille |
| `*_grille8_apercu.png` | la grille en surimpression, pour vérifier le calage |

```bash
python3 ../tileset_pmd/caler_grille8_interieur.py interieur_*.png
```

## Calques séparés

Comme le café de Metano dans Halcyon, qui est découpé en `_Base`, `_Objects`,
`_Objects_Fringe`, `_Objects_Over` et `_Objects_Under`, le décor est livré en
calques indépendants. Tous partagent le **même cadre 456 × 320 et le même
offset** : ils se superposent au pixel près, sans le moindre recalage.

| Fichier | Contenu |
|---|---|
| `interieur_deco_seule_jour.png` | les meubles seuls **et leurs ombres portées**, le reste transparent |
| `interieur_deco_seule_nuit.png` | idem, en éclairage nocturne |
| `interieur_fenetres_jour.png` | le vitrage seul des quatre fenêtres, ciel de jour |
| `interieur_fenetres_nuit.png` | le vitrage seul, ciel nocturne étoilé |

Le calque de décoration se pose sur la salle vide pour retrouver la salle
décorée :

```python
fond = Image.open("interieur_sans_deco_jour_grille8.png").convert("RGBA")
fond.alpha_composite(Image.open("interieur_deco_seule_jour.png").convert("RGBA"))
```

Le **calque de fenêtres** sert d'éclairage : on le pose sur la salle pour
changer l'heure sans retoucher le reste, ou on le remplace pour changer le ciel.

Ces calques ne sont pas extraits par différence entre deux images : deux
générations successives reteintent légèrement tout le bois, et la soustraction
trouait les meubles (97 % de la salle marquée comme « modifiée »). Le calque de
déco est donc généré directement sur fond magenta, puis remis dans le cadre par
`../tileset_pmd/caler_calque_deco.py`, qui lui applique le décalage exact subi
par la salle — décalage mesuré sur les fichiers, jamais supposé.

## Contrôle qualité

Étalon : l'intérieur du café de Metano dans `Palikadude/Halcyon`, dont les
**920 tuiles de 8 × 8** ont été extraites et mesurées (0 pixel semi-transparent).

| Mesure | Résultat |
|---|---|
| Pixels semi-transparents | **0** sur les douze fichiers |
| Alpha strictement 0 ou 255 | **100 %** — masque binaire, comme un vrai sprite |
| Liseré orange/cuivré sur le contour | **0 %** (86 % avant correction) |
| Fenêtres : pixels blancs | quelques dizaines de reflets, plus d'aplat blanc |
| Salle | **52 × 40 cellules** pleines, offset (16, 0) |

L'alpha binaire est le point clé : aucun pixel fantôme sur les bords, donc le
moteur ne recompose rien au rendu.

### Le liseré cuivré

Le contour extérieur de la bordure était bordé d'un halo orange-cuivré sur
**86 % de son périmètre** en version jour, comme un rétroéclairage. Il a été
supprimé à la régénération : le bord extérieur est maintenant un trait brun
foncé net, mesuré à **0 %** de pixels cuivrés.

### Les fenêtres

Les quatre fenêtres étaient des **disques blancs** — refusés. Le vitrage est
désormais un **bleu ciel** franc de jour et un **bleu nuit étoilé** de nuit,
avec croisillon simple en bois et cadre rond cerné d'un trait sombre.

Le passage à la grille 8 px ne touche pas un pixel de l'image : mesures
identiques avant et après, seul le cadrage change. La salle de jour, large de
415 px, a été portée à 416 en dupliquant sa dernière colonne de pixels — aucun
pixel existant n'est modifié.

## Import dans l'éditeur PMDO

### Pourquoi « Load PNG to Tileset » écrasait la netteté

L'éditeur découpe le PNG en tuiles de 8 × 8, puis **déduplique** : deux tuiles
identiques ne sont stockées qu'une fois. Deux défauts faisaient s'effondrer ce
mécanisme. Mesures faites contre l'intérieur du café de Metano, reconstitué
tuile par tuile depuis `Palikadude/Halcyon`.

| | notre café (avant) | Metano (Halcyon) |
|---|---|---|
| Couleurs | **60 299** | **396** |
| Couleurs présentes sur 1 seul pixel | 46 123 — **76 %** de la palette | 153 |
| Pixels altérés si l'éditeur indexe en 256 couleurs | **65,5 %** | 0,2 % |
| Offset horizontal | x=20 → **4 px hors grille** | x=0 |
| Largeur | 415 px → **7 px hors grille** | 456 px = 57 cellules |
| Tuiles uniques générées | **1 602** | 1 118 |

**Le dégradé.** Le générateur d'image produit des dégradés lisses : 76 % de la
palette n'apparaît qu'une seule fois, du bruit invisible à l'œil. Quand
l'éditeur indexe la palette, deux tiers des pixels sont modifiés — c'est la
bouillie constatée à l'import. Un tileset ripé du jeu tient en 396 couleurs.

**La grille.** La salle commençait à x=20 pour 415 px de large : ni l'un ni
l'autre multiple de 8. Chaque tuile découpée tombait **à cheval** sur deux
motifs, donc aucune ne se répétait et le tileset explosait.

### La correction

`../tileset_pmd/assainir_pour_pmdo.py` fait les deux :

1. **Calage sur la grille** — offset et largeur ramenés à des multiples de 8.
   La largeur est complétée en dupliquant la dernière colonne : aucun pixel
   existant n'est modifié.
2. **Regroupement de palette** — chaque teinte rare est remplacée par la teinte
   fréquente la plus proche, dans la limite d'un écart de 16/255, imperceptible.
   Aucun pixel n'est moyenné, aucune couleur n'est inventée : on supprime des
   doublons quasi identiques, ce qu'est déjà un tileset du jeu.

| Fichier | Couleurs | Grille |
|---|---|---|
| `interieur_sans_deco_jour.png` | 60 299 → **3 162** | x=16, 416 px = 52 cellules |
| `interieur_sans_deco_nuit.png` | → **6 610** | idem |
| `interieur_avec_deco_jour.png` | → **20 038** | idem |
| `interieur_avec_deco_nuit.png` | → **15 558** | idem |

Dégât mesuré sur le dessin : écart **max 16/255**, moyen 2,70, et **0 %** de
pixels au-delà de 16. Le layout est strictement inchangé.

```bash
python3 ../tileset_pmd/assainir_pour_pmdo.py interieur_*.png
```

## La lumière de sortie

Comme dans Metano, la lumière du jour entre par l'escalier et s'ouvre en
éventail sur le plancher. Halcyon ne l'apporte pas en dégradé mais en **aplats
francs de la palette** — vérifié en relevant les pixels de l'asset original.

Elle est donc appliquée en **trois paliers nets**, uniquement sur les pixels du
sol, sans toucher aux meubles ni aux murs : doré chaud de jour, bleu lunaire de
nuit. Aucun pixel semi-transparent, aucun flou.

## Parti pris

Le vrai café Spinda d'*Explorers of Sky* est une **salle souterraine** : anneau
de roche brute, sol doré à spirales, escalier en bas. La référence est
conservée dans `reference/spinda_cafe_officiel_pmd_sky.png` (Spriters Resource).

Notre café n'étant pas en sous-sol, on garde **le layout exact** de la salle du
jeu — forme ovale, bordure épaisse à silhouette irrégulière, mur intérieur
octogonal, sol à spirales, escalier encastré au centre bas — mais la **roche est
remplacée par des rondins de bois miel**, et des **fenêtres rondes à croisillons**
sont percées dans le mur pour éclairer la pièce depuis l'extérieur. La salle est
ainsi cohérente avec la façade du kiosque tout en gardant la direction
artistique du jeu.

## La décoration

Elle est reprise du café Spinda officiel (`reference/spinda_cafe_pdmc_deco.png`)
et adaptée à notre layout ovale, pas réinventée.

Les deux stands sont bâtis comme dans le jeu : un long comptoir bas en planches
vert olive, et **derrière, un vrai meuble** — une étagère ouverte à deux niveaux
en bois sombre garnie de baies et de fruits, qui soutient l'enseigne. À gauche,
le stand à boissons, avec sa pancarte crème à volutes rouges, ses jarres-tonneaux
et ses quatre bocaux de boisson colorée. À droite, le stand de nourriture, avec
sa sculpture de glace bleue en éventail et ses buissons.

S'y ajoutent les guirlandes de fanions orange à nœuds rouges drapées le long des
murs, les tables en rondins de tailles variées, les tabourets-souches, les
plantes en pot, les caisses et les panneaux d'affichage.

**Ombres portées** : chaque objet pose une ombre douce sur le plancher, comme
dans la référence, ce qui l'ancre au sol.

Les fenêtres rondes ont un **croisillon simple** : une barre verticale et une
barre horizontale, quatre carreaux. Les diagonales en X du premier jet ont été
retirées, trop chargées à cette échelle.

La salle a été **élargie** : la bordure de rondins a été affinée pour dégager le
plancher, qui occupe désormais bien plus de surface et laisse de larges
circulations entre les meubles. Le plancher lui-même a été redessiné en planches
franches — lattes séparées par un trait sombre d'1 px, joints visibles — après
qu'un premier rendu l'eut laissé flou et constellé de halos lumineux diffus.

De nuit, la palette bascule vers un bleu-violet froid, les fenêtres montrent un
ciel nocturne et quelques flaques de lumière chaude subsistent au sol.

## Variante souterraine

`variante_caverne/` contient les quatre mêmes calques en version **grotte**,
fidèles au jeu d'origine, si tu préfères ce parti pris.
