# Méthode spriter — assets PMD (Guilde Treehouse)

Pipeline professionnel reproduit depuis `source/rebuild_kit.py` et appliqué avec succès à
l'**entrée de donjon « forêt avec chemin »** (`sprites/entrees_donjon/`).
Le même pipeline sert pour tout nouveau sprite (entrée de grotte, panneau, pont, etc.).

## 1. Références

- Rips **Pokémon Mystery Dungeon: Explorers of Sky / Rescue Team** (Spriters Resource) :
  `source/_refs_pmd/` — entrées de donjons forêt (Murky Forest, Apple Woods, Tiny Woods…).
- Sprites existants du kit (`sprites/individuels/`) pour verrouiller la **palette** et le
  rendu du bois/feuillage.
- Règles du kit : grille **8 px**, images fixes, continuité du sol aux accès (le chemin
  **touche le bord bas**, pas de barre opaque).

## 2. Génération brute

Prompt structuré, avec les références passées en images au générateur. Le prompt impose :

| Contrainte | Pourquoi |
|---|---|
| perspective ¾ oblique légèrement surélevée | caméra PMD overworld |
| herbe en damier deux verts dithérés | texture signature PMD |
| chemin sable clair, bords dithérés, quelques cailloux | lisibilité du trajet |
| massif d'arbres à houppiers ronds, 3 verts + contour sombre | masse forestière PMD |
| ouverture quasi noire bleu-violet, trapèze plus étroit en haut | « gouffre » d'entrée de donjon |
| couleurs à plat, contour 1 px, pas d'anticrénelage, ~24 couleurs | look GBA |
| fond **magenta #FF00FF** uni | détourage automatique |
| chemin jusqu'au bord bas | règle de continuité du kit |
| aucun texte / personnage / UI | asset pur |

Sortie brute conservée dans `source/_gen/` (comme `source/natives/` pour les salles).

## 3. Traitement (script `source/rebuild_entree_foret.py`)

1. **Détourage magenta** + décontamination des franges (pixels opaques trop magenta
   neutralisés vers le neutre).
2. **Quantification palette** : découpe médiane, fusion des couleurs à distance < 14,
   plafond **28 couleurs** (résultat : 26).
3. **Réduction pixel art** : cible multiple de 8 px (160 × 88), réduite par **vote
   majoritaire par bloc** — chaque pixel final prend la couleur la plus fréquente du
   bloc, pas une moyenne ; les aplats et contours restent nets.
4. **Nettoyage** : 2 passes anti-parasites (pixel isolé remplacé par la majorité de ses
   8 voisins).
5. **Canevas** : centrage horizontal, **collé en bas** (le chemin touche le bord).
6. **Calques** (partition exacte, chaque pixel opaque dans un seul calque) :
   - `00_sol_chemin` — herbe + chemin, flood-fill depuis le bord bas ;
   - `01_ouverture_sombre` — cavité sombre connectée au haut ;
   - `02_massif_foret` — le reste (arbres, troncs, fougères).
7. **Nuit** : formule exacte du kit — `RGB × [0.36, 0.34, 0.43] + [9, 10, 19]`,
   transparents remis à (0,0,0,0).
8. **Exports** : PNG indexés (palette ≤ 256, transparence), **Aseprite** `.aseprite`
   avec les calques et la grille 8 px (écrivain binaire pur Python du kit),
   manifeste `entrees.json` (pivot bas-centre du chemin).

## 4. Contrôle qualité (automatique, `PASS` obligatoire)

- dimensions multiples de 8 ;
- chemin présent sur le bord bas (≥ 80 % — mesuré : 97 %) ;
- ouverture sombre présente dans le tiers haut ;
- **identité bit à bit** : composite des calques = PNG = relecture de l'Aseprite ;
- nuit = formule du kit, exacte ;
- palette ≤ 28 couleurs ;
- corrélation de luminance sprite / brute ≥ 0.75 (contrôle de fidélité de la
  réduction — mesuré : 0.815).

Résultat : `controle_entree_foret.json`.

## 5. Livrables type d'un sprite

```
sprites/entrees_donjon/
  entree_foret_chemin_jour.png / _nuit.png      sprite final (RGBA, indexé)
  entree_foret_chemin_jour.aseprite / _nuit     calques + grille 8, 1 image
  calques/00_sol_chemin_{jour,nuit}.png         3 calques × 2 modes
  entrees.json                                  manifeste (taille, pivot, fichiers)
apercus/apercu_entree_foret.html                aperçu autonome (zoom, calques, nuit)
apercus/planche_entree_foret.png                planche jour/nuit ×3
source/_gen/entree_foret_brut.png               génération brute (source)
source/rebuild_entree_foret.py                  pipeline reproductible
controle_entree_foret.json                      rapport de contrôle
```

## 6. Reproduire / créer un nouveau sprite

```bash
pip install -r source/requirements.txt
python3 source/rebuild_entree_foret.py    # retraite la brute et revalide tout
```

Nouveau sprite : générer la brute dans `source/_gen/`, dupliquer le script en changeant
les classes de couleurs (grotte = roches grises + cavité, plage = sable…), relancer,
vérifier `PASS`. Intégration moteur : collisions et déclencheur d'entrée de donjon à
configurer côté jeu (le sprite n'est qu'un décor posé).
