# Spinda V7 — corrections et mobilier à l’échelle

## Corrections demandées
- Fenêtres café/salon haut : canevas **32×32**, diamètre visible **28px** au lieu de64. Le centre de chaque fenêtre reste au même endroit. C’est toujours le dessin propre au café, pas une fenêtre de la guilde.
- Montées N accueil/casino : suppression du palier doré/de la vue sur l’étage supérieur. Les marches montent dans une ouverture sombre, occultée par le mur ; petites joues rocheuses sans les anciennes grosses volutes. Correction bornée au rectangle **[200,0,400,184]** ; tous les pixels d’architecture en dehors restent identiques. Les accès S, latéraux et le graphe N/S restent inchangés.
- Le module de correction contient le mur, les marches, leurs bordures et le raccord au sol. Ce n’est pas un escalier autonome à déplacer tel quel. Les anciennes images V6 et leur ZIP restent accessibles.

## Mobilier / tilesheets
**4 PNG transparents à importer à 1×** dans `tilesheets/` : Spinda/Qulbutoké natifs, Halcyon natif, Kirlia (créations), Charmilly (créations). Chaque objet est aussi disponible séparément. Index des rectangles, audit CSV/JSON et provenance fournis. Grille Ground8px ; les objets ne sont pas étirés pour remplir leurs cellules. Les sprites natifs restent intacts, seul un padding transparent est ajouté.

Les deux comptoirs natifs sont tirés du Ground EoSO et détourés manuellement : toutes leurs valeurs RGBA visibles correspondent exactement à la composition native. Étagère, bar/plinthe et accessoires d’origine conservés. Les parties cachées par les rubans de la référence ne sont pas inventées. Pas de génération IA pour ces comptoirs. Les silhouettes de détourage sont documentées : cette extraction n’est pas un sprite indépendant inédit trouvé dans le dépôt.

Kirlia : comptoir frontal + banquette. Charmilly : comptoir frontal + desserte à pâtisseries. **Créations générées**, normalisées à l’échelle mesurée, pas pixels natifs certifiés. Ni personnage ni vendeur placé. Les meubles ne sont pas préinstallés dans les salles.

## Ouvrir et exporter
- `.venv/bin/python source/cafe_spinda_revisite_v7/serve.py --port 8007` : serveur commun sur0.0.0.0, atelier V7 par défaut.
- `SpindaV7_objets_tilesheets.zip` : pack autonome des objets et tilesheets, stocké dans Git.
- `SpindaV7_complet.zip` : salles en PNG/calques + catalogue + atelier autonome, **autonome et stocké dans Git**. Le dépôt utilise les calques V6 avec des corrections explicites ; le pack complet matérialise tous les pixels et n’a pas besoin de V6 une fois extrait.
- Reconstruction manuelle : `.venv/bin/python source/cafe_spinda_revisite_v7/build.py` (Pillow, NumPy, SciPy).

Les bruts générés complets (y compris les deux premières perspectives non retenues) et les quatre bruts V6 restent bit-identiques dans l’historique Git, avec commits et SHA256 dans `source/cafe_spinda_revisite_v7/raws/archive.json`. Lecture automatique et restauration facultative par `archive.py --restore` ; conserver l’historique Git complet (clone non shallow). Cette archive évite de perdre les sources tout en respectant le budget des livrables.

## Limites
Audit de pixels, dimensions visibles et calques, pas de collision/warp/navigation PMDO. Le graphe approuvé est conservé mais ces nouvelles corrections/créations restent à valider artistiquement. Les feuilles de décoration n’appliquent pas automatiquement des rubans aux courbes des murs ; pas de bibliothèque nouvelle de tapis rouges revendiquée.
