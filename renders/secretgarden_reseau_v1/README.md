# Jardin secret — réseau connectable style Ledian (V5)

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

Les 7 salles sont en **V4 layouts séparés** : sol/chemin/fleurs/rochers générés chacun sur magenta (texte seul quand la ref copiait trop), assemblés par règles scriptées (`build_v4.py` : partitions salvage, rock-rules, shift L latérale, transplant buissons du T ; précédent ns/carrefour figé). Terrains et bordures restent des **images générées guidées par les références**, pas des cartes natives pixel-identiques. Bruts conservés dans `bruts/` et `bordures_jungle/` (anciennes bordures jardin en `bordures/`, archives). Journal : `source/secretgarden_reseau_v1/GENERATION_LOG.md`.

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

Puis `composition.png`, `composition_animee.gif`, `terrain_detoure.png`, `schema.png` et le projet OpenRaster `<piece>.ora`. Sémantique V4 : chemin ⊆ sol, végétation hors-sol, rochers/fleurs sur sol|végétation ; couloir_ew et salle_traversee sans rochers (générations éjectées par les règles), couloir_t sans arbres (buissons transplantés). **68 calques alignés**, tous en 512×512 placés en (0,0).

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

## V4 — layouts séparés (en cours : 2/7 zones)

`couloir_ns` et `salle_carrefour` sont reconstruits depuis **4 layouts générés séparément** (`layouts/<zone>/{sol,chemin,fleurs,rochers}.png`) au lieu d'une partition d'un seul terrain. Règles d'assemblage : chemin strictement sur sol, végétation V3 rognée hors nouveau sol, rochers/fleurs uniquement sur sol ou végétation (rien dans le vide). Bordure jungle et accès inchangés. Les 5 autres zones gardent leurs couches V3 (mêmes noms de fichiers) en attendant leurs layouts.

## V5 — versions nues, tilesheets, végétation animée

Par zone, sans nouvelle génération (pixels existants uniquement) :
- `composition_nue.png` + `composition_nue_animee.gif` : **sol + chemin + fleurs + accès**, sans arbres, buissons, rochers ni bordure.
- `composition_full_animee.gif` : fleurs + végétation animées (4×200ms).
- `rochers_tilesheet.png` + `rochers_manifest.json` : sprites de rochers individuels (composantes ≥60px, cases uniformes, 8 colonnes). Total réseau : 88 sprites + planche `rochers_TOUTES_ZONES.png`.
- `vegetation/veg_f0..3.png` : arbres+buissons fusionnés, balancement ±1px et pulsation (200ms, synchronisés avec les fleurs) ; `vegetation_frames.png` (bande 4 phases) ; `buissons_spritesheet.png` + manifeste (lignes = buissons isolés ≤128px, colonnes = 4 phases ; 127 sprites ; les nappes connectées restent dans les phases).
- La galerie propose la végétation animée (remplace 03+04 quand activée), le bouton « vue nue » et les liens de téléchargement par zone.

## Packs (non suivis, reproductibles)

8 zips en workspace : `jardin_secret_SALLE_<piece>_v5.zip` (×7) + `jardin_secret_COMMUN_v5.zip` (galerie + manifeste + planche + matériaux + nappes globales + `layouts/` sources). Contenu byte-exact des fichiers suivis ; rebuild : `zip -qr jardin_secret_SALLE_<slug>_v5.zip renders/secretgarden_reseau_v1/<slug>`.
