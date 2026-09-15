# Mont Horn V2 — ciel séparé et haute altitude

Correction de la V1, conservée intacte. Même canevas 648 × 504, même entrée nord, chemin et roches grises.

## Changements
- **Ciel opaque indépendant** : fond complet reconstitué en bleu, progressivement plus pâle vers le bas, sans montagnes intégrées.
- **Montagnes lointaines indépendantes** : ciel détouré du panorama V1, seules les chaînes supérieures conservées. Contraste atténué, couleurs éclaircies vers le bleu atmosphérique, disparition progressive avant y=245. Aucun relief de panorama dans la moitié inférieure.
- **Brume d’horizon indépendante** : fond inférieur léger, sans grandes montagnes au premier plan.
- **Brume d’altitude devant les falaises** : dissimule la terminaison inférieure du massif, en laissant le chemin et la grotte dégagés. Le massif semble se prolonger sous la brume plutôt que reposer sur un socle visible.
- Les deux animations de nuages wrap sont conservées, aux mêmes vitesses et sur leurs calques respectifs.

## Dix calques, ordre arrière → avant
1. `01a_ciel`
2. `01b_montagnes_lointaines`
3. `01c_brume_horizon`
4. `02_nuages_lointains` (324 phases)
5. `03_falaises_gauches`
6. `04_falaises_droites`
7. `05_chemin_pierre_grise`
8. `06_entree_nord_et_marches`
9. `06b_brume_altitude_pied_masque`
10. `07_nuages_overlay` (324 phases)

Les brumes sont des calques atmosphériques statiques à alpha progressif. Les nuages, eux, défilent horizontalement : 6,25 et 12,5 px/s, translations modulo 648 px, boucle commune de 103,68 s. Le second plan effectue deux tours pendant un tour du premier. Pas de fondu de retour ni de saut au raccord.

## Ouvrir
- `../../apercu_mont_horn_altitude_v2.html` : galerie autonome animée, sélection de chaque calque, pause et curseur.
- `mont_horn/COMPOSITION.png` et `ANIMATION_WRAP.webp` : rendu et animation.
- `mont_horn/mont_horn_panorama.ora` : dix calques, état initial.
- `mont_horn/horn_*.png` : calques plein cadre et neuf compositions clés ; les clés ne constituent pas toute la chronologie.
- `mont_horn_altitude_v2.zip` : paquet avec scripts, galerie et références nécessaires.

## Provenance / limites
Révision locale des images générées pour la V1 à partir de `Mt_Horn_entrance_Sky.png`. Pas de nouvelle génération ni de revendication de sprites officiels récupérés. Les quatre calques du relief sont identiques pixel pour pixel à la V1 : le pied est masqué par la brume, pas retaillé. Le ciel est reconstitué, les montagnes sont détourées et atténuées, les brumes calculées. Le panorama V1 reste archivé avec ses bruts.

Les contrôles vérifient toutes les phases wrap, l’opacité, l’ORA, les PNG clés, la séparation ciel/montagnes, l’absence de montagnes sous y=245, la conservation du relief, le masquage opaque des zones latérales basses et l’absence de brume/overlay sur le guide d’approche. Ce guide n’est pas une carte de collisions. **Aucun test PMDO effectué.**

Depuis la racine, avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/mont_horn_altitude_v2/build.py
.venv/bin/python source/mont_horn_altitude_v2/verify.py
.venv/bin/python source/mont_horn_altitude_v2/package.py
```
Le builder lit les trois bruts de `renders/mont_horn_panorama_v1/bruts/` et l’utilitaire `source/layouts_magenta_v1/palette.py`. Le vérificateur compare les quatre calques de relief V1 fournis dans le paquet. Aucune modification des anciens livrables.
