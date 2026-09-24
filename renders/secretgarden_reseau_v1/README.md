# Jardin secret — réseau connectable style Ledian (V1)

Galerie autonome : **`apercu_jardin_secret_reseau_v1.html`** à la racine. [Planche des six pièces](PLANCHE.png).

## Pièces livrées (512×512, vides : aucun donjon, personnage ni mobilier)

| Pièce | Accès |
|---|---|
| Couloir nord-sud fleuri | Nord, sud |
| Couloir est-ouest fleuri | Est, ouest |
| Salle traversante | Nord, sud |
| Salle latérale | Ouest, sud |
| Salle carrefour | Nord, sud, est, ouest |
| Carrefour de la clairière | Nord, sud, est, ouest |

**Jonction en T reportée au prochain lot** (limite de 10 générations atteinte ce tour : voir `source/secretgarden_reseau_v1/GENERATION_LOG.md`). Les deux essais non conformes ne sont pas conservés comme pièces ; le plein-cadre en croix est devenu la salle carrefour après vérification de ses 4 ouvertures d'herbe.

## Méthode

Référence `secretgarden.png` (408×408, SHA-256 dans `manifest.json`) → 6 générations guidées sur magenta → inspection des ouvertures (0px exigé sauf une variante) → détourage → partitions et calques → vérification.

Les matières (herbe claire, canopées, rochers, fleurs) sont des **images générées guidées par la référence**, pas des cartes natives pixel-identiques. Les bruts sont conservés dans `bruts/`.

## Calques

Chaque dossier de pièce contient :

1. `01_sol_chemin.png`
2. `02_vegetation_fond.png`
3. `03_massif_gauche.png`
4. `04_massif_droit.png`
5. `05_vegetation_premier_plan.png`
6. Un `06_acces_N/S/E/W.png` **par accès**, indépendant.

Puis `composition.png`, `terrain_detoure.png` et `schema.png`. **46 calques alignés au total**, tous en 512×512 placés en (0,0).

Les cinq calques de terrain sont des partitions de surfaces visibles : leur recomposition redonne exactement le terrain détouré. Ils ne reconstruisent pas le dessous de la végétation.

## Entrées / sorties

**16 ports de 64px**, centrés sur les bords. Coordonnées dans `manifest.json` et sur les schémas.

Leur bande de raccord utilise l'extrait natif `secretgarden.png` (190,240)-(222,272), agrandi ×2 sans lissage, opaque sur 24px au bord puis atténué vers l'intérieur. Le patch non agrandi est dans `materiaux/sol_raccord_natif.png`. La bande opaque couvre les retraits (~21px) du carrefour de la clairière ; continuité vérifiée sur chaque port.

**La bande commune ne garantit pas l'emboîtement de toute la silhouette végétale sans retouche.** Il ne s'agit pas de transitions PMDO codées ni d'un test de navigation/collision.

## Vérifications et reproduction

`verification.json` : référence SHA-256 inchangée, six compositions exactement recomposées, 46 calques 512×512, patch égal à l'extrait natif, 16 bandes opaques. Scripts : `source/secretgarden_reseau_v1/{build,gallery,verify}.py` (Pillow, numpy).

**Rendus statiques, pas d'animation ni de validation PMDO.** Aucun nouveau `.rsground` livré.
