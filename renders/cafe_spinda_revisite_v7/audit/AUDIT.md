# Audit de taille — Spinda Café / Halcyon

## Périmètre et provenance
Huit banques `.tile` réellement décodées : EoSO `SpindaCafe1/2` ; Halcyon objets du Café Metano, objets Over du café, objets/Over de l’auberge, objets/Over du réfectoire. **Pas un inventaire exhaustif de tout Halcyon.** Sources, commits figés, SHA Git et SHA256 dans `native_sizes.json`. Les compteurs de tuiles reposent sur la grille8px de ces banques.

La composition du Ground Spinda reconstituée depuis les deux banques est vérifiée RGBA contre la référence existante. Les comptoirs ne sont pas redessinés : masque de silhouette appliqué aux pixels de cette composition, avec partie arrière/étagère et plinthe avant. Tous les pixels opaques exportés égalent ceux de la référence à la même position. Les zones cachées par le décor ne sont pas reconstituées. Les contours du détourage sont manuels, conservés dans le JSON.

## Mesures utiles (pixels 1×)
| Objet | Visible / module | Canevas d’import |
|---|---:|---:|
| Comptoir Spinda complet | 120×96 (module source) | 120×96 |
| Comptoir Qulbutoké complet | 120×96 (module source) | 120×96 |
| Table Spinda, vide ou tasses | 43×43 | 48×48 |
| Table café Halcyon, vide | 46×44 | 48×48 |
| Table café Halcyon, tasses | 46×44 | 48×48 |
| Chevalet de menu | 35×45 | 40×48 |
| Paire de tonneaux | 42×45 | 48×48 |
| Caisses empilées | 50×56 | 56×56 |
| Plante haute café | 40×54 | 40×56 |
| Tonneau auberge | 24×29 | 24×32 |
| Petit tabouret auberge | 14×16 | 16×16 |
| Table de banquet réfectoire | 167×51 | 168×56 |
| Bannière réfectoire | 28×89 | 32×96 |

**30 objets/modules natifs** : détail de chacun en CSV/JSON. Les cadres visibles et canevas ne sont pas des masques de collision ; ne pas confondre une AABB visuelle avec une emprise de gameplay.

## Fenêtres : correction d’échelle
Ancien dessin généré :64px visibles dans72×72. Nouveau :28px visibles dans32×32, soit **−56,25% en diamètre**. Le diamètre est désormais environ65% de la largeur d’une table native Spinda, contre149% auparavant. Aucun mobilier natif n’a été agrandi pour compenser les fenêtres. Les fenêtres de réfectoire Halcyon mesurent52×59 à titre de comparaison ; elles ne sont **pas utilisées** comme dessin du café.

## Créations thématiques
Comptoirs Kirlia/Charmilly normalisés dans une enveloppe visible maximale120×96 ; banquette Kirlia56×40 max ; desserte Charmilly40×48 max. Aspect conservé, réduction nearest seulement sur le généré. Les dimensions réellement obtenues et les empreintes des bruts figurent dans `generated_provenance.json`. Les premiers comptoirs isométriques ne sont pas retenus ; variantes frontales employées.

## Garanties / non-garanties
- Aucun resampling, miroir, rotation ou changement de palette des natifs.
- Découpage et réassemblage à1× ; transparence de padding uniquement.
- Tilesheets : dimensions et positions divisibles par8, comparaison RGBA de chaque case avec son PNG individuel.
- PNG du pack complet recomposés contre les couches de l’atelier ; corrections hors zone contrôlées.
- Pas de NPC, mobilier ou feu préplacé dans les nouvelles salles.
- Aucune exécution PMDO, collision ou validation artistique utilisateur revendiquée.
