# SPEC — Plage « Beach Cave », grande (lot `plage_beach_cave_v1`)

Fiche de composition écrite avant l'assemblage, conformément à la méthode du
dépôt (Étape 2 de `METHODE_PRODUCTION_MAPS.md`). Aucune image n'est générée
pour ce lot : la composition est un plan de cellules de 24 px.

## 1. Fonction

Zone extérieure de transition, jouable en Ground PMDO 0.8.12 :

- le joueur **arrive par la droite** (marqueur `Entrance`, bord est, orienté
  vers l'ouest) ;
- il traverse une **plage de sable large et profonde** (zone libre, sans
  obstacle imposé) ;
- le **seuil de donjon** est la bouche de **Beach Cave**, à **gauche**
  (déclencheur `Beach_Cave_Entrance`) ;
- la **sortie** est le bord droit (déclencheur `Exit`).

Deux destinations à raccorder dans le projet cible (le squelette Lua laisse
les appels en commentaire) ; référence de comportement : le `init.lua` de la
plage EoSO (`Exit` → `crossroads_south`, grotte → zone `beach_cave`).

## 2. Matière

Uniquement les cellules canoniques de la plage PMD Explorers of Sky
(fond `D01P11A`), prises telles que livrées par Explorers of Sky Origins :

| Calque PMDO | Feuille source | Feuille livrée | Contenu |
|---|---|---|---|
| `Back` | `D01P11A_layer1` | `PLAGE_BC1_LAYER1` | sable, sable mouillé, remplissage sous les rochers, ombres cuites des détails |
| `Anim` | `beach_animation` | `PLAGE_BC1_ANIM` | mer : 17 frames par cellule, `FrameLength` 16 (≈ 267 ms, cycle ≈ 4,5 s) |
| `Front` | `D01P11A_layer2` | `PLAGE_BC1_LAYER2` | falaises, grotte, rampe de gravier, chemin de sortie, rochers, palmiers, herbe, détails |

Les feuilles livrées sont des **copies octet pour octet** des feuilles EoSO
(renommées pour éviter toute collision de nom dans PMDO). Aucune cellule
n'est recolorée, tournée, redimensionnée ni redessinée.

## 3. Ordre de profondeur (du fond vers l'avant, du haut vers le bas)

1. **Mer lointaine** (rangées 0–2, statiques dans l'animation d'origine).
2. **Mer animée** (rangées 3–5 : vagues, 17 phases) puis **écume / sable
   mouillé** (rangée 6, animée).
3. **Sable sec** (rangées 7–13) : rangée 7 = transition claire, puis six
   rangées de sable libre.
4. **Bande du bas** (rangées 14–19) : rochers, palmiers, buissons, herbe,
   cellules de remplissage hors champ.
5. **Falaises latérales** (rangées 3–7) : massif gauche avec la grotte,
   massif droit avec le chemin de sortie.

## 4. Bords de carte

- **Nord** : mer jusqu'au bord (la caméra ne montre pas de vide : rangées 0–2
  de mer statique).
- **Ouest** : falaise pleine, sauf la bouche de la grotte (rangées 6–7,
  colonnes 2–3) et la rampe de gravier qui en descend (colonnes 2–4).
- **Est** : falaise en haut, **couloir libre** rangées 7–13 (chemin clair) qui
  sort de la carte ; `Exit` couvre tout le couloir.
- **Sud** : bande de rochers/palmiers/herbe fermée.

## 5. Dimensions et cibles

| | Original EoSO | Nouveau layout |
|---|---|---|
| Cellules (24 px) | 33 × 16 | **45 × 20** |
| Pixels | 792 × 384 | **1080 × 480** |
| Sable libre (cellules) | ≈ 24 × 3 (+ marges) | ≈ 36 × 6 (+ marges) — **≈ 3× la surface** |
| Grille d'obstacles 8 px | 99 × 48 | 135 × 60 |

Méthode d'agrandissement (mesures dans `ANALYSE.md`) :

- **Largeur** : insertion, une fois, du bloc de colonnes d'origine `[11, 23)`
  (mer et sable sans rocher côtier) après la colonne 22. Raccord mesuré
  22 → 11 = 203,7 (MSE sur les 17 frames), meilleur que le raccord médian des
  colonnes d'origine (318). Le module de rochers coupé à la colonne 22 se
  termine par la colonne 11, sa suite naturelle (« 0,4,2 | 3 »).
- **Hauteur** : quatre rangées de sable insérées entre les rangées 9 et 10
  d'origine. Calque `Back` : séquence 8, 9, 9, 9, 9, 9 (raccords ≤ 92, tous
  sous le raccord 7 → 8 d'origine = 107). Calque `Front` sur les colonnes
  latérales : rangée 8 répétée (mur, rampe, chemin rectilignes), rangée 9 en
  dernier. Calque `Front` sur le sable : vide, détails replacés à la main.
- Les massifs gauche et droit, la grotte et la bande du bas sont conservés
  d'un bloc (aucune cellule de rocher n'est isolée).

## 6. Détails du sable

Chaque détail du calque `Front` porte une **ombre cuite dans `Back`** ; il se
déplace avec ses cellules d'ombre, sur une cellule de **même phase** (même
rangée d'origine, même colonne modulo 8 : période du motif de sable).

- Conservés : paire de cailloux (12–13, 7), caillou (18, 9), buisson (35, 7),
  rocher (38, 7), massif 2 × 2 (37–38, 14–15), buisson (35, 15).
- Copies mécaniques retirées (avec remplacement de l'ombre par le sable propre
  de même phase) : paire (24–25, 7), caillou (30, 9), ombres des rangées
  répétées (18–19 et 30–31, rangées 10–13).
- Ajoutés (avec ombre) : cailloux isolés en (10, 12), (30, 12), (38, 10).

## 7. Entités

| Entité | Type | Collider (px) | Rôle |
|---|---|---|---|
| `Entrance` | marqueur, direction 2 (ouest) | 1036, 208, 16 × 16 | arrivée depuis la droite |
| `Exit` | GroundObject, `triggerType` 2 (contact) | 1070, 172, 16 × 164 | sortie bord droit, couloir rangées 7–13 |
| `Beach_Cave_Entrance` | GroundObject, `triggerType` 2 | 8, 144, 64 × 64 | seuil du donjon, bouche de la grotte |

Pas de PNJ ni de spawner de scénario (les spawners EoSO servaient à une
cinématique du chapitre 1).

## 8. Hors périmètre

- Variante crépuscule (`dusk_beach`) : son animation est un flipbook de toute
  la carte (27 frames avec les bulles de Krabby cuites dans les cellules) ;
  l'insertion de colonnes/rangées dupliquerait les bulles. Non produite.
- Bulles/étincelles (`BeachBubble_*`, `BeachSparkle`) : objets et particules
  EoSO, pas des cellules ; à ajouter dans l'éditeur si souhaité.
- Musique et son d'ambiance : champ `Music` vide ; `Ambient/AMB_Ocean`
  appartient au contenu EoSO, non présumé présent.
