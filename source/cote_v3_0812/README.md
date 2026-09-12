# Dix côtes V2 — atelier PMDO 0.8.12

**20 Ground natifs : 10 formes organiques approuvées × jour / nuit.**
Ce lot est distinct des anciens packs et du lot 2 modulaire.

## Ouvrir les cartes — projet séparé

1. Fermer PMDO et extraire **tout** `cotes_v2_0812_pmdo.zip`.
2. Copier le dossier `cotes_v2_0812` dans `PMDO/MODS/`, sans remplacer un dossier existant.
3. En mode développeur de PMDO **0.8.12**, sélectionner ce projet d’édition : **Cotes V2 - Atelier 0.8.12**. Son `Mod.xml` le déclare comme Quest pour que les sauvegardes d’édition restent dans ce projet. Ce n’est pas une aventure jouable.
4. Dans l’éditeur **Ground**, ouvrir une carte `v30812_…_jour` ou `v30812_…_nuit`, présente dans `Data/Ground/`.

Le dossier contient les `.rsground`, les quatre banques `.tile`, les six fonds `.dir`, son **index complet**, et les scripts dans son namespace. **Aucune réimportation PNG, aucun redimensionnement** n’est nécessaire. Grille : `TexSize=1`, soit **8 px**.

**Attention :** ne fusionner manuellement ni ce dossier `Content/Tile/index.idx`, ni son `Mod.xml` avec ceux de ton projet existant. Cet index complet ne décrit que les quatre banques de ce projet séparé.

## Installer dans ton projet existant — option

Fermer PMDO. Avec Python 3, depuis le dossier extrait contenant `INSTALLER.py` :

```sh
python INSTALLER.py "CHEMIN/PMDO/MODS/TON_PROJET" --dry-run
python INSTALLER.py "CHEMIN/PMDO/MODS/TON_PROJET"
```

L’installateur ne copie **pas** l’index livré : il fusionne les en-têtes des banques avec l’index de destination, sauvegarde cet index avant modification, conserve les autres tilesets et refuse les conflits avec des cartes déjà éditées. Il ajoute les scripts au namespace du projet cible, sans remplacer son `Mod.xml`.

## Calques et animation

- Mer : huit phases de palette, 10 frames moteur par phase, boucle d’environ 1,33 seconde à 60 Hz.
- Herbe, roche Métano, lisière protégée, ombres de volume : quatre calques séparés.
- Trois calques vides pour tes structures, dont un devant les personnages (`Top=4`).
- Ciel et astres séparés ; nuages en wrap horizontal à −4 px/s.
- Un marqueur `entrance` placé sur l’herbe. Aucun arbre, bâtiment ou personnage posé.
- **Collisions volontairement libres** : dessiner les obstacles et les limites de marche avant de jouer. Un contact graphique avec le bord ne constitue pas une sortie scriptée.

## Formes, bords et fidélité

Les bandes extérieures vides à gauche, à droite et en bas ont été retirées par recadrage intérieur sur la grille 8 px, sans étirer les silhouettes. Le recadrage peut couper jusqu’à sept pixels supplémentaires au bord pour respecter la grille. Le haut conserve le ciel. Les dix terrains touchent les bords W/E/S ; cela ne signifie pas que toute la longueur de chaque bord est pleine : les baies et courbes restent ouvertes sur la mer.

La roche brute de jour vient réellement de `Metano_Town_Cliffs.tile`, rectangle `(912,464)-(976,512)`, répété à **1×**, sans recoloration. Le témoin 64×48 et le SHA-256 source sont dans `provenance/`. Les volumes proviennent d’un calque d’ombres translucides séparé, calculé depuis les propositions approuvées. **Le rendu ombré n’a donc pas les mêmes RGB que la matière brute.** Désactiver « Ombres » pour inspecter celle-ci. La nuit est une variante recolorée.

L’herbe et la lisière sont issues des images générées approuvées, non de tuiles canoniques. Les trois traces de parcelles du cap éventail ont été atténuées sur l’herbe uniquement. Les essais de retouche générée dans `source/cote_v3_0812/corrections/` ne sont pas les roches finales ; seul le n°09 sert à cette correction d’herbe.

Les nuages, le ciel et les astres reprennent les ressources Guilde / Sharpedo de l’autre agent au commit `c16efe12`. Les nuages ne sont ni agrandis ni redessinés. La nuit applique sa formule exacte. La mer reprend l’animation côtière V2 : ce n’est pas la rivière canonique Métano.

## Contrôles et limites

`verification.json` : reconstruction des pixels depuis les fichiers binaires natifs, alpha prémultiplié inclus ; 20 cartes, 80 calques de terrain, 16 phases de mer, six fonds, index complet, contacts aux bords, formule de nuit et tests d’installation/fusion/protection des cartes éditées.

Format ciblé : **PMDO 0.8.12**, sérialisation `0.8.12.0`, RogueEssence `4961b2271bb0cace74f40f6a85e799e8e4848ace`. Dix-huit sources moteur épinglées ont été auditées ; dix-sept sont identiques à la base déjà examinée. La différence Lua concerne des initialisations de règles de zones, pas ce format Ground. Rapport dans `provenance/engine_compatibility.json`.

**Aucune ouverture dans PMDO / aucun test moteur réel n’a été effectué ici.** Les tests par code ne remplacent pas cette validation, ni la revue des collisions. L’arrondi GPU des transparences peut différer légèrement de l’aperçu PNG.

`apercu_cotes_v2_0812.html` fonctionne hors ligne : jour/nuit, calques, grille, animation, zoom 1×, exports PNG natifs. Les planches réduites servent uniquement à voir les formes, pas à importer.

## Reproduire depuis le dépôt

Python avec Pillow et NumPy :

```sh
.venv/bin/python source/cote_v3_0812/prepare.py
.venv/bin/python source/cote_v3_0812/build.py
.venv/bin/python source/cote_v3_0812/make_project.py
.venv/bin/python source/cote_v3_0812/verify.py
.venv/bin/python source/cote_v3_0812/package.py
node source/cote_dix_zones/test_viewer.cjs apercu_cotes_v2_0812.html
```

Les fichiers natifs non compressés sont construits dans `~/.cache/cote_v3_0812_pack/`. Les ressources Métano sont créditées à Palika / Halcyon et leurs contributeurs ; leur disponibilité publique ne constitue pas une autorisation de réutilisation sans restrictions. Consulter les conditions des sources avant redistribution hors du projet.

Les copies PNG intermédiaires `AVANT_ROCHE`, `jour_*` et `nuit_*` ne sont pas versionnées pour éviter les doublons volumineux. Les commandes ci-dessus les régénèrent ; les exports finaux sont également accessibles depuis l’aperçu autonome sans perte.
