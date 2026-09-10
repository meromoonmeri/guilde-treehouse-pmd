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
| `interieur_sans_deco_jour_grille8.png` | jour, calé grille, prêt à découper |
| `interieur_sans_deco_nuit_grille8.png` | nuit, calé grille |
| `*_grille8_apercu.png` | la grille en surimpression, pour vérifier le calage |

```bash
python3 ../tileset_pmd/caler_grille8_interieur.py interieur_sans_deco_*.png
```

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

La déco reprend celle du café officiel : deux comptoirs en rondins sous auvents
rayés rouge et bleu, boissons colorées, tables et tabourets en rondins, plantes
en pot, caisses, tableau d'affichage et guirlandes de rubans rouges.

Les fenêtres rondes ont un **croisillon simple** : une barre verticale et une
barre horizontale, quatre carreaux. Les diagonales en X du premier jet ont été
retirées, trop chargées à cette échelle.

De nuit, la palette bascule vers un bleu-violet froid, les fenêtres montrent un
ciel nocturne et quelques flaques de lumière chaude subsistent au sol.

## Variante souterraine

`variante_caverne/` contient les quatre mêmes calques en version **grotte**,
fidèles au jeu d'origine, si tu préfères ce parti pris.
