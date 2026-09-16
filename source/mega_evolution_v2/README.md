# Méga-Évolution V2 — reprise au générateur et GIF

Demande du 16 septembre 2026 : remplacer toute la matière visuelle V1 par une reprise au générateur, avec cycles, phases fluides et layouts multidirectionnels, fournir un GIF de chaque animation, retrouver Carapagos V1 et reprendre les portraits sur fonds canoniques.

## Ce qui a changé

**Aucun dessin procédural de la V1 n'est réutilisé comme énergie, sphère, éclat ou emblème.** Les quatre composants proviennent des planches conservées dans `generation/`. L'assemblage reste programmé : détourage, calage, masques, interpolation et enveloppes temporelles ne sont pas produits par le générateur.

| Composant | Source utilisée | Images clés | Phases |
|---|---|---:|---:|
| Colonnes / impacts / anneau | 01_energy_cycle.png | 8 | 48 en boucle |
| Sphère spiralée | 02_sphere_cycle.png | 8 | 48 en boucle |
| Fissures, fragments, particules | 03b_shell_break_matched.png | 8 | 43, non cyclique |
| Emblème de flammes | 04_emblem_cycle.png | 8 | 48 en boucle |

`03_shell_break.png` est la première proposition, **non utilisée** : la matière lisse ne correspondait pas à la sphère. Le deuxième passage a utilisé la planche de sphère comme référence. Les grilles noires indésirables de certaines générations sont retirées à l'extraction.

### Animation et cycling

- 32 images clés générées utilisées. Les intermédiaires sont calculés par flot optique bidirectionnel (Farneback), rééchantillonnage nearest-neighbor et mélange en alpha prémultiplié pour éviter des liserés de détourage.
- Les trois cycles passent aussi de la clé 8 à la clé 1 par six sous-phases. La forme et les couleurs évoluent dans les images générées : ce n'est **pas un export de LUT palette-cycling native PMDO**.
- GIF : palette commune de 256 couleurs pour chaque séquence, sans dithering. C'est un aperçu aplati ; le GIF ne préserve pas l'alpha progressif des PNG RGBA.
- Séquence complète : 192 phases, 2 ticks par phase, **6,4 secondes**. Les durées GIF suivent 30/30/40 ms pour représenter 30 images/seconde en moyenne malgré la précision de 10 ms du format.
- Colonne et anneau à l'ancre de sol (120,198), sphère centrée (120,186). La sphère devient opaque avant le switch réel Dracaufeu → MégaX à la phase 78. Coque fissurée dès la phase 96 ; séparation à partir de 108 ; particules et emblème disparaissent progressivement.

### Calques et directions

Six atlas dans `renders/mega_evolution_v2/atlases/`, noms uniques `MEGAGEN_V2_*`. **2880×4096**, cellules **240×256**, grille **12 colonnes ×16 lignes**, lecture ligne par ligne. Ordre : ground → rear_energy → personnage → sphere → front_energy → fracture → emblem.

Les masques `mask_energy_*.png` sont une partition de la même image générée : ils ne peignent pas de nouveaux pixels et leur recomposition est contrôlée. Ils sont une séparation sémantique approximative des colonnes proches/lointaines et du sol, pas des objets entièrement dessinés séparément.

Les atlas de composants dans `cycles/` utilisent des cellules 160×160 et 8 colonnes. 48 phases =6 lignes ; la rupture a43 phases suivies de5 cases transparentes de remplissage, **à ne pas lire comme phases utiles**.

La caméra PMD est fixe. Le GIF `mega_8_directions.gif` présente les huit orientations **natives du personnage** autour des mêmes coordonnées, avec le même VFX radial. Ne pas le décrire comme huit nouvelles caméras 3D générées. Les PNG de personnages viennent de SpriteCollab `3609a86be2a4c8ad7cf255bd2255f044daafe24f`, Dracaufeu0006 / MégaX0006/0001 ; crédits dans les références V1, jamais recolorés.

## Vérifications

- `build.py` teste la couverture complètement opaque des pixels des **2 formes ×8 directions ×4 Idle**, pour25 phases autour du switch : 1600 vérifications PASS.
- `finish.py` décode les15 GIF, contrôle les durées, six atlas RGBA, début/fin transparents et absence de pixels magenta pur opaques.
- Les diagnostics de raccord de boucle sont dans `manifest.json`. La différence du raccord final reste inférieure au plus grand changement interne mesuré. Cela ne prouve pas une animation artistiquement parfaite.
- Revue des planches, du storyboard et des portraits à taille native/agrandie effectuée. **Pas de validation utilisateur/SpriteCollab ni de test de lecture PMDO Ground/Dungeon.** Aucune certification pour toutes les tailles X/Y/Z-A : seule l'enveloppe Dracaufeu/X est mesurée ici.
- Les atlas sont des **sources VFX**, pas des tilesets de terrain. Ne pas employer PNG to Tileset pour les charger comme décor ni renommer en binaires moteur. Le raccordement à l'animation moteur reste à faire.

## Reconstruction

Depuis la racine avec Python/Pillow/NumPy/OpenCV :
```
.venv/bin/python source/mega_evolution_v2/build.py
.venv/bin/python source/pokemon_custom/tirtouga_portraits_v3/build.py
.venv/bin/python source/mega_evolution_v2/finish.py
```
`finish.py` construit `apercu_mega_generee_v2.html`, galerie autonome intégrant ses principales images et GIF. Les liens de téléchargement individuels pointent vers les fichiers du dépôt.

## Récupération Carapagos et provenance

Voir `recovery_carapagos.md` : la V1 n'a pas été retrouvée dans les fichiers/Git accessibles. Les deux GIF Idle/Walk inclus sous `gifs/carapagos_v2_archive/` sont **explicitement la V2 existante**, pas une récupération de V1. Leurs durées viennent du XML, corrigées par rapport aux anciens WebP de démonstration. Pas de nouvelle extension d'actions sur le sprite rejeté.

Emblème : génération guidée par la silhouette flamme/S d'une référence secondaire de logo fan déjà inspectée, crop conservé. Ce n'est pas une extraction de l'icône officielle. Les ressources générées sont AI-assisted/custom ; aucune soumission publique n'a été faite, aucun crédit officiel ou natif attribué à cette création.

Planche de revue supplémentaire : `MEGAGEN_V2_directional_layout.png`, **8 rangées de directions ×12 colonnes temporelles**, phases0,16,…176. Ce sont des captures de composition avec personnage, pas des frames de personnage à soumettre à SpriteCollab.

La transformation complète et l'éclatement sont des séquences à jouer une fois en jeu. Leurs GIF recommencent uniquement pour faciliter la revue : le retour Méga→forme de base au début du GIF n'est pas une animation inverse ni un raccord cyclique revendiqué. Les trois composants energy/sphere/emblem sont les vrais cycles.
