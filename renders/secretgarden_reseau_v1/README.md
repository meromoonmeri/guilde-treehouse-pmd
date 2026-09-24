# Jardin secret — réseau connectable style Ledian (V2)

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

La jonction en T (barre à mi-hauteur, sud fermé par le mur d'arbres) a été régénérée et vérifiée : herbe aux trois ouvertures, arbres au sud. Journal des générations : `source/secretgarden_reseau_v1/GENERATION_LOG.md`.

## Méthode

Référence `secretgarden.png` (408×408, SHA-256 dans `manifest.json`) → générations guidées sur magenta (7 terrains + 7 bordures) → inspection des ouvertures → détourage → partitions matière et calques → vérification.

Les terrains et bordures sont des **images générées guidées par la référence**, pas des cartes natives pixel-identiques. Bruts conservés dans `bruts/` et `bordures/` (dont les essais T non retenus : voir le journal).

## Calques (par zone, au choix)

Chaque dossier de pièce contient :

1. `01_sol_chemin.png` — sol et chemins
2. `02_vegetation_fond.png` — masses arrière
3. `03_cimees_arbres.png` — canopées claires
4. `04_buissons_sous_bois.png` — sous-bois sombre
5. `05_vegetation_premier_plan.png` — masses avant
6. `06_troncs.png` — souches et troncs visibles (souvent clairsemé en vue de dessus)
7. `07_rochers.png` — rochers et pierres
8. `08_fleurs.png` — fleurs (phase 0 ; voir `fleurs/08_fleurs_f0..3.png`)
9. `09_bordure_feuillue.png` — cadre immersif de feuillage au premier plan, fenêtres dégagées aux accès
10. Un `10_acces_N/S/E/W.png` **par accès**, indépendant.

Puis `composition.png`, `composition_animee.gif`, `terrain_detoure.png`, `schema.png` et le projet OpenRaster `<piece>.ora`. **82 calques alignés au total**, tous en 512×512 placés en (0,0).

Les couches 01 à 08 sont des partitions par matériau des surfaces visibles : leur recomposition redonne exactement le terrain détouré (seuils documentés dans `build_v2.py`). Elles ne reconstruisent pas le dessous de la végétation. La bordure est un avant-plan généré à part ; ses fenêtres (104×88) sont dégagées par script à chaque accès.

## Fleurs animées (cadence Sky Peak)

**4 phases × 200ms = 0,8s**, balancement ±1px et pulsation lumineuse : `fleurs/08_fleurs_f0..3.png` par pièce, `composition_animee.gif` (seules les fleurs bougent). Animation **créée pour ce lot**, pas un cycle officiel récupéré. Boucle fermée vérifiée (f3→f0).

## Entrées / sorties

**19 ports de 64px**, centrés sur les bords. Coordonnées dans `manifest.json` et sur les schémas.

Leur bande de raccord utilise l'extrait natif `secretgarden.png` (190,240)-(222,272), agrandi ×2 sans lissage, opaque sur 24px au bord puis atténué vers l'intérieur (`materiaux/sol_raccord_natif.png`). Continuité et opacité vérifiées sur chaque port, fenêtres de bordure contrôlées transparentes.

**La bande commune ne garantit pas l'emboîtement de toute la silhouette végétale sans retouche.** Il ne s'agit pas de transitions PMDO codées ni d'un test de navigation/collision. Les coins extérieurs au terrain et à la bordure restent transparents (vide standard).

## Vérifications et reproduction

`verification.json` : référence inchangée, 7 compositions recomposées, partitions exactes, 82 calques 512×512, fenêtres de bordure, 4 phases distinctes en boucle, 7 GIF 4×200ms, 7 ORA relus, patch natif identique, 19 bandes opaques. Scripts : `source/secretgarden_reseau_v1/{build_v2,gallery,verify}.py` (Pillow, numpy, scipy).

**Rendus statiques hors fleurs, pas de validation PMDO.** Aucun nouveau `.rsground` livré.
