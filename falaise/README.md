# Prairie de la guilde

Scène indépendante de **480 × 408 px**, grille **8 px**, avec la disposition générale de GuildOutside et son escalier sud.

La direction finale est une **prairie avec un chemin de terre**, sans arbre, bâtiment, mobilier ni rocher ajouté sur le plateau. La falaise entière — sommet, bordures et paroi — a été repassée au **générateur d’images** avec la référence EoS, et non assemblée avec des fragments de sol. La bordure raccorde l’herbe, la terre et la paroi rocheuse. L’escalier de référence reste identique en palette jour ; le contour alpha reste celui de la référence. La paroi est désormais dans la reprise générée complète.

## Aperçu commun

Ouvrir [`../apercu_falaise.html`](../apercu_falaise.html). Choisir **Prairie de la guilde** ou **Falaise côtière**, puis **Jour / Nuit**. L’aperçu est autonome et hors ligne : calques, pause, vitesse, curseur temporel, grille, zoom, fond magenta et capture PNG. Le mouvement réduit du système démarre les animations en pause.

## Six calques, du fond vers l’avant

| Calque | Contenu | Mouvement |
|---|---|---|
| `00_ciel` | Ciel dédié jour/nuit, autres palettes | Fixe |
| `01_astres` | Lune et étoiles, ou soleil selon la lumière | **Étoiles scintillantes en nuit**, lune fixe |
| `02_nuages` | Six familles de silhouettes | Défilement horizontal |
| `03_reliefs` | Mesas et forêt lointaine | Fixe |
| `04_falaise` | Prairie, chemin, bordure, paroi et marches | Fixe |
| `05_vegetation` | Emplacement de décor additionnel | Vide |

Les six familles de nuages sont : cumulus vertical, nuage effilé, banc horizontal, cirrus, fragments séparés et nuage déchiqueté. La prairie est dans le terrain, pas dans le calque de décor vide.

Ambiances : jour, nuit, crépuscule, aube, soir, orageux. Le scintillement concerne la nuit ; les astres du crépuscule restent fixes.

## Animation et formats

- **480 images de 250 ms**, boucle globale de **120 s**. Les nuages avancent de 1 px par image, soit 4 px/s.
- Les étoiles ont **24 phases**, cycle global de **6 s**, avec des variations douces et différentes par groupes. La composante de la lune est exclue des variations.
- `calques/` : 36 PNG RGBA, image 0 de chaque plan. `compositions/` : six rendus complets à l’image 0.
- `bases/` : six bases transparentes et six contrôles magenta, sans paysage ni astres.
- `aseprite/` : six fichiers réellement animés. Cels liés pour les plans fixes et les phases qui se répètent ; aucune duplication inutile des 24 phases stellaires sur toute la boucle.
- `tiled/` : six cartes avec des image layers fixes et des objets-tuiles **réellement animés** pour les nuages et les étoiles de nuit.
- `animations/` : atlas de nuages et d’étoiles, plus une carte technique de groupes stellaires en niveaux de gris. Cette dernière n’est pas un calque à afficher.
- `kit.json` : dimensions, ordre, ambiances, opérations et chemins. **Conserver les dossiers d’images avec les cartes Tiled.**

L’aperçu utilise les phases stellaires exportées. Les nuages sont déplacés directement depuis leur PNG. Les repères du plateau et de l’accès sud ne sont ni des collisions complètes ni des transitions fonctionnelles. Aucun export moteur PMDO `.rsground`/`.tile` n’est fourni.

## Reconstruction

Avec les dépendances de `source/requirements.txt`, depuis la racine :

```bash
# Facultatif : réassembler les natives retenues, sans rappeler le générateur.
python source/prepare_falaise_reference.py
python source/prepare_sharpedo.py
python source/prepare_mer_reference.py
python source/prepare_nuages.py
# Exports et aperçu des deux scènes.
python source/rebuild_falaise.py
python source/rebuild_sharpedo.py
python source/build_preview_falaise.py
python source/verify_falaise.py
# Nécessite Playwright + Chromium :
python source/verify_falaise_browser.py
```

La préparation utilise désormais `falaise_eos_generee.png` pour la falaise complète et rétablit le rectangle des marches depuis `reference_escalier.png`. La direction artistique est contrôlée visuellement ; une génération ne constitue pas une garantie de copie pixel pour pixel du jeu hors de cette zone protégée.

Les contrôles relisent toutes les frames Aseprite, les phases Tiled et leurs compositions ; ils protègent l’escalier, le contour, la prairie et la lune fixe. Le navigateur est testé hors ligne, en iframe et sur mobile. Il s’agit d’une lecture/recomposition des formats, pas d’une validation dans les interfaces d’Aseprite ou de Tiled.

Les régions de marches/paroi reprises de GuildOutside restent des graphismes tiers : voir [`../source/falaise/PROVENANCE.md`](../source/falaise/PROVENANCE.md). Les douze salles et la terrasse antérieure sont inchangées.
