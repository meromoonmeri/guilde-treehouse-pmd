# Plage / arène côtière V1 — statut

Choix utilisateur : « Go la plage / arène côtière », même méthode que
l'entrée aride (rendu généré référencé PMD, statique, PNG + ORA).

## Livré

- `renders/plage_arene_generee_v1/` : 6 couches 456×480, scène, planche,
  ORA, manifeste. ZIP `renders/plage_arene_generee_v1_pack.zip`.
- Viewer racine `apercu_plage_arene_v1.html` (6 calques embarqués).
- 10 tests dédiés PASS. PMDO NON TESTÉ, art non approuvé.

## Points techniques

- Brut 1008×1061 au ratio exact de la cible : normalisation sans recadrage.
- Ouverture sud : le brut fermait l'arène par un monticule (~y400-445).
  Sculpture en entonnoir 16/20/24 px depuis y395/405/415, pavage cyclique de
  sable strict (même règle que la découpe), 3860 px, 100 % sable testé.
- Tri falaises/rochers : règle « touche les bords » puis « taille » puis
  « proximité roche » toutes insuffisantes (système central isolé de 27k px,
  pans de 800-3000 px, champ de 5 blocs proches). Retenu : murs par
  propagation depuis graines + rochers <1500 px loin des murs, sans vide
  proche, entourés de sable/mer/écume. 8 rochers (blocs + monticules ombrés).
- Correctif de teinte « sable → sable » essayé puis ABANDONNÉ : il mangeait
  les monticules ombrés (obstacles). Les speckles <12 px sont rendus aux
  voisins avant le tri ; poches bleues enfermées <600 px gardées en falaise.
- Corridor 48/48 colonnes sans falaise sur [420,480], bord sud sable.

## Registre

Le registre natif sud–nord (`FULL_PROGRAMME_STATUS.json`) est laissé inchangé :
ce lot généré ne prétend pas être un relayout pixel-natif de la référence.
Prochaine map à choisir (jungle aux cascades, lac cristallin, route glacée…).
