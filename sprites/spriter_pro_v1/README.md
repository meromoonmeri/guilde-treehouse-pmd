# Spriter Pro v1 — six cartes canoniques Métano

Pack produit par le studio `source/spriter_pro/` : six compositions neuves
(04 à 09) assemblées **exclusivement** à partir des tuiles canoniques 8 × 8 px
de Métano (Palika / Halcyon). Aucune image générée, aucune berge tracée, aucune
recoloration, rotation, retournement ni mise à l’échelle des textures.

Galerie : **`apercu_spriter_pro_v1.html`** (sec / eau animée 4 phases, zoom 1×–3×,
grille, export PNG). Planche réduite : `apercu_comparatif.png` (présentation,
pas un asset de jeu).

## Les six cartes

| Dossier | Composition | Chutes | Bassins |
|---|---|---:|---:|
| `04_lac_suspendu/` | Plateau nord haut, grande chute centrale, deux bassins en plaine | 1 | 2 |
| `05_double_cirque/` | Deux parois superposées, deux doubles chutes, bassins intermédiaires | 4 | 2 |
| `06_deux_torrents/` | Trois gradins, deux torrents à triple chute | 6 | 0 |
| `07_grande_face/` | Paroi de 43 rangées de face, chute unique, bassins au pied | 1 | 2 |
| `08_etangs_altitude/` | Deux étages percés de chutes jumelles, étangs au-dessus des couronnes | 4 | 2 |
| `09_trois_chutes/` | Palier médian, trois chutes réparties, lac de plateau | 3 | 1 |

Toutes les cartes font **2048 × 1536 px**, soit 256 × 192 cellules de 8 px
(49 152 cases par calque).

## Contenu de chaque dossier de carte

- `sans_eau_sans_chemins.png` : rendu sec natif (herbe + falaises).
- `herbe.png` / `falaises_bordures.png` : calques secs séparés.
- `berges_eau.png` : réservoirs, bassins et chenaux (calque de la version humide).
- `eau_frame_1..4.png` : quatre calques d’eau animée, RGBA transparents.
- `avec_eau_frame_1..4.png` : quatre rendus complets en résolution native.
- `sec.tmj` / `anime.tmj` : cartes Tiled 2 et 4 calques, animations configurées.
- `layout.json` : parois, torrents, bassins, chutes et calques.

Au niveau du pack : `Metano_Spriter_Pro_8px.png/.tsj/.tile` (atlas commun, nom
indépendant pour l’import), `provenance.json` (référence de **chaque** entrée
d’atlas et de chaque Frame), `verification.json` (contrôle indépendant).

## Reproduction et contrôle

```bash
pip install -r source/requirements.txt   # Pillow suffit pour ce pack
python source/build_spriter_pro.py       # reconstruit le pack + l'aperçu
python source/verify_spriter_pro.py      # contrôle indépendant -> verification.json
```

Ajouter une carte = déclarer parois/torrents/bassins dans
`source/spriter_pro/layouts.py`, relancer build puis verify. Les contraintes
(alignement 8 px, chutes ≥ 17 rangées sur front plat, bandes sans recouvrement,
bassins en plaine) sont refusées avant toute pose.

## Ce qui est vérifié

1. SHA-256 et blobs Git des sept feuilles natives (Halcyon, commit
   `da6c2130d641507447e6386a5e47a296e8cb4c71`) ;
2. chaque entrée utilisée de l’atlas comparée octet à octet à sa tuile source,
   aller-retour d’alpha prémultiplié inclus ;
3. white-lists par calque : herbe = Base x 0..15 / y 80..95 ; falaises = colonnes
   natives autorisées (sans escaliers/grotte/eau) ; berges = bandes source du
   réservoir (103..144) et du chenal (123..133) ; eau = animations natives
   (quatre feuilles de rivière ou feuille de chute) ;
4. recomposition des PNG depuis les `.tmj`, zéro différence, quatre frames
   d’eau distinctes.

**Non vérifié :** lancement dans PMDO, collisions, transitions, continuité
artistique de chaque nouveau raccord, cadence autonome des grandes chutes
(10 ticks retenus ; celle de la rivière est vérifiée dans la carte originale).

## Import

- Tiled : ouvrir `sec.tmj` / `anime.tmj` en gardant atlas et dossiers ensemble.
- PMDO : ajouter `Metano_Spriter_Pro_8px.tile` dans `Content/Tile/`, réindexer,
  Ground à **TexSize = 1**. Les `.tmj` restent des cartes Tiled ; collisions et
  transitions à configurer.

Attribution : tuiles de [Palikadude/Halcyon](https://github.com/Palikadude/Halcyon)
et artistes crédités du projet. Ce pack prolonge `sprites/metano_pixel_perfect/`
(layouts 01–03) sans le modifier.
