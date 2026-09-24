# Jardin secret — réseau connectable style Ledian (V3)

Galerie autonome : **`apercu_jardin_secret_reseau_v1.html`** à la racine (fleurs animées, pause, pas à pas). [Planche des sept pièces](PLANCHE.png).

## Pièces livrées (512×512, vides : aucun donjon, personnage ni mobilier)

| Pièce | Accès |
|---|---|
| Couloir nord-sud fleuri | Nord, sud |
| Couloir est-ouest fleuri | Est, ouest |
| Jonction en T | Nord, est, ouest |
| Salle traversante | Nord, sud |
| Salle latérale | Ouest, sud |
| Salle carrefour | Nord, sud, est, ouest |
| Carrefour de la clairière | Nord, sud, est, ouest |

## Méthode

Référence `secretgarden.png` (408×408, SHA-256 dans `manifest.json`) → générations guidées sur magenta (7 terrains + 7 bordures jungle) → inspection des ouvertures → détourage → partitions matière et calques → vérification. Bordures guidées aussi par `Southern_Jungle_entrance_S.png` (SHA-256 dans le manifeste).

Les terrains et bordures sont des **images générées guidées par les références**, pas des cartes natives pixel-identiques. Bruts conservés dans `bruts/` et `bordures_jungle/` (anciennes bordures jardin en `bordures/`, archives). Journal : `source/secretgarden_reseau_v1/GENERATION_LOG.md`.

## Calques (par zone, au choix)

Chaque dossier de pièce contient :

1. `01_sol.png` — sol, rives du polygone de circulation
2. `02_chemin.png` — chemin, bande centrale (érosion géométrique 15px du polygone)
3. `03_arbres.png` — arbres : cimes claires et troncs, toutes profondeurs
4. `04_buissons.png` — buissons et sous-bois sombre
5. `05_rochers.png` — rochers et pierres
6. `06_fleurs.png` — fleurs (phase 0 ; voir `fleurs/06_fleurs_f0..3.png`)
7. `07_bordure_jungle.png` — végétation bordure feuillue style jungle PMD (lianes, grosses feuilles), fenêtres dégagées aux accès
8. Un `08_acces_N/S/E/W.png` **par accès**, indépendant.

Puis `composition.png`, `composition_animee.gif`, `terrain_detoure.png`, `schema.png` et le projet OpenRaster `<piece>.ora`. **68 calques alignés**, tous en 512×512 placés en (0,0).

Les couches 01 à 06 sont des partitions disjointes des surfaces visibles : leur recomposition redonne exactement le terrain détouré (seuils dans `build_v3.py`). Elles ne reconstruisent pas le dessous de la végétation. La bordure jungle est un avant-plan généré à part ; ses fenêtres (104×88) sont dégagées par script à chaque accès. La V2 (fond/cimes/premier plan/troncs séparés) reste dans l'historique git.

## Fleurs animées (cadence Sky Peak)

**4 phases × 200ms = 0,8s**, balancement ±1px et pulsation lumineuse. Animation **créée pour ce lot**, pas un cycle officiel récupéré. Boucle fermée vérifiée (f3→f0).

## Entrées / sorties

**19 ports de 64px**, centrés sur les bords. Coordonnées dans `manifest.json` et sur les schémas.

Leur bande de raccord utilise l'extrait natif `secretgarden.png` (190,240)-(222,272), agrandi ×2 sans lissage, opaque sur 24px au bord puis atténué (`materiaux/sol_raccord_natif.png`). Continuité et opacité vérifiées sur chaque port, fenêtres de bordure contrôlées transparentes.

**La bande commune ne garantit pas l'emboîtement de toute la silhouette végétale sans retouche.** Il ne s'agit pas de transitions PMDO codées ni d'un test de navigation/collision. Les coins extérieurs au terrain et à la bordure restent transparents (vide standard).

## Vérifications et reproduction

`verification.json` : références inchangées, 7 compositions recomposées, partitions exactes, 68 calques 512×512, fenêtres de bordure, 4 phases distinctes en boucle, 7 GIF 4×200ms, 7 ORA relus, patch natif identique, 19 bandes opaques. Scripts : `source/secretgarden_reseau_v1/{build_v3,gallery,verify}.py` (Pillow, numpy, scipy).

**Rendus statiques hors fleurs, pas de validation PMDO.** Aucun nouveau `.rsground` livré.
