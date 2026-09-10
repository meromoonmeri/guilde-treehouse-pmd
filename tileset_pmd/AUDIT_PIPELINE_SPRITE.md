# Audit — pourquoi la façade passe et pas les intérieurs / le décor

Objectif : comprendre la perte de qualité en jeu sur les intérieurs et le décor,
alors que la façade extérieure passe bien, puis en tirer une pipeline qui rend
une génération d'image compatible pixel-art PMDO.

Toutes les mesures ci-dessous sont reproductibles avec
`tileset_pmd/pipeline_sprite_pmdo.py` (fonction `controler`).

## 1. État des lieux mesuré

| Calque | Couleurs | Coul./tuile | Tuiles ≤16 | Orphelins | Aplats |
|---|---|---|---|---|---|
| **Étalon officiel EOS** | 147 | 4,8 | 99,0 % | 8,3 % | 51,8 % |
| **Étalon Halcyon** | 396 | 5,3 | 99,4 % | 8,6 % | 38,5 % |
| Façade jour *(jugée OK)* | 782 | 6,9 | 94,1 % | 10,3 % | 41,8 % |
| Salle intérieure | 98 | 5,6 | 99,3 % | 4,8 % | 31,0 % |
| Décor généré | 494 | 9,5 | 100 % | **21,8 %** | 19,9 % |
| Meubles générés | 490 | 10,2 | 85,6 % | **25,1 %** | — |
| Meubles extraits | 373 | 6,1 | 99,2 % | 15,0-20,2 % | — |

Définitions : **orphelin** = pixel dont aucun des 4 voisins n'a exactement la
même couleur (bruit de rééchantillonnage) ; **aplat** = pixel dont les 4 voisins
sont identiques (surface franche, marque du pixel art).

## 2. Deux hypothèses testées — une seule tient

### Hypothèse A : « le facteur de réduction non entier casse la grille » — **RÉFUTÉE**

C'était l'explication intuitive : les pipelines historiques réduisaient de /2,54,
/2,60, /3,12, et l'agrandissement de la salle utilisait 5/4. Deux mesures la
démentent :

* **colonnes dupliquées** — signature d'un rééchantillonnage non entier :
  notre salle après ×1,25 en a 10,9 %… et **l'asset officiel EOS en a 11,4 %**.
  Le motif est donc normal dans un asset de jeu, pas un défaut.
* **ablation directe** sur la même génération, réduction /2,6 non entière contre
  /4 entière :

  | Méthode | Coul./tuile | Tuiles ≤16 | Orphelins |
  |---|---|---|---|
  | A. non entier seul | 38,7 | 21,5 % | 90,1 % |
  | B. entier seul | 38,7 | **21,4 %** | 90,1 % |

  Écart : 0,1 point. **Le facteur entier n'apporte rien à lui seul.**

### Hypothèse B : « la génération a une fréquence de détail supérieure au pixel cible » — **CONFIRMÉE**

Le vrai discriminant est le taux d'**orphelins**, qui sépare nettement les deux
familles : 8,3-10,3 % pour les assets réels et la façade, contre 21,8-25,1 %
pour tout ce qui sort du générateur. Un pixel sur quatre du décor généré n'a
aucun voisin de sa couleur : ce n'est pas du détail, c'est du bruit.

**Pourquoi la façade échappe au problème :** elle est livrée en 648 px de large
pour un sujet simple et frontal. Le décor, lui, entasse une quinzaine de petits
objets dans la même surface — chaque objet reçoit ~10× moins de pixels, donc le
détail peint par le modèle tombe sous la taille du pixel cible et se dégrade en
bruit. Ce n'est pas la façade qui est mieux traitée, c'est son sujet qui est
plus gros à l'écran.

**Le volet « taille » se règle donc en amont, à la génération** : générer les
objets sur une planche large et espacée, jamais un décor entier à réduire d'un
bloc.

## 3. Pipeline retenue

`tileset_pmd/pipeline_sprite_pmdo.py`, quatre étapes :

1. **Décontamination du fond** — la frange anti-aliasée sujet/magenta est
   rendue transparente *avant* le vote de blocs, sinon elle se propage.
2. **Cadrage entier** — réduction par vote de couleur dominante sur blocs K×K.
   Conservé pour la propreté de la grille, même si l'ablation montre que son
   apport propre est marginal.
3. **Projection sur palette d'asset** — chaque couleur est projetée sur la plus
   proche de la palette extraite des vrais tilesets, avec pondération
   perceptuelle (2, 4, 3). C'est l'étape qui fait l'essentiel du travail.
4. **Nettoyage des orphelins** — absorption par la couleur dominante du
   voisinage 3×3, deux passes.

### Résultat sur une génération neuve (1408×768 → 352×192)

| Étape | Couleurs | Coul./tuile | Tuiles ≤16 | Orphelins | Aplats |
|---|---|---|---|---|---|
| 0. source brute | 172 615 | 48,0 | 9,8 % | 85,8 % | 0,1 % |
| 1. cadrage entier | 16 338 | 38,7 | 21,4 % | 90,1 % | 0,1 % |
| 2. palette d'asset | 222 | 11,8 | 72,3 % | 30,4 % | 11,6 % |
| 3. nettoyage | **147** | **4,4** | **100 %** | **0 %** | **30,7 %** |

147 couleurs et 4,4 par tuile : exactement le profil de l'étalon officiel EOS
(147 couleurs, 4,8 par tuile).

## 4. Effet sur les livrables existants

La pipeline a été repassée sur le décor déjà produit, **sans rien regénérer** :

| Livrable | Avant | Après |
|---|---|---|
| `decor_cafe_genere.png` | 494 coul., 9,5/tuile, 21,8 % orphelins | **159 coul., 5,3/tuile, 0 % orphelins** |
| `meubles_cafe_tilesheet.png` | 863 coul., 8,1/tuile, 93,3 % conformes | **463 coul., 6,2/tuile, 99,4 % conformes** |
| `interieur_avec_deco_jour.png` | 412 coul. | **280 coul.** |

Les meubles extraits ne sont pas dégradés : ils étaient déjà dans la palette du
jeu, la projection les laisse donc inchangés. Seul le décor généré bouge, et il
converge vers le profil des assets réels.

## 5. Règles à suivre pour toute génération future

1. Générer **sur fond magenta pur** `#FF00FF`, objets bien espacés.
2. Générer **une planche d'objets détachés**, jamais une scène complète à
   réduire — c'est la cause racine de la perte de détail.
3. Viser au moins **~4× la taille cible** de chaque objet dans la génération.
4. Passer systématiquement par `pipeline_sprite_pmdo.py`.
5. Contrôler : viser **≥ 99 % de tuiles ≤16 couleurs**, **0 semi-transparent**,
   **< 10 % d'orphelins**.
