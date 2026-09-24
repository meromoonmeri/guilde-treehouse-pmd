# Falaises proches Métano V2 — 100% pixels natifs Halcyon

Deux variantes 768×512 (cap gauche, terrasse droite) **reconstruites en tuiles
natives Métano Town**, mer et nuages **réutilisés** d'anciens lots, nuit Abyss exacte.

## Sources canoniques (liens directs)

Tuiles d'origine, repo `Palikadude/Halcyon`, vendues octet pour octet dans
`source/falaises_proches_metano_v2/natifs_halcyon/` (preuves : `provenance_halcyon.json`) :

| Fichier | Commit épinglé | Blob | Lien |
|---|---|---|---|
| `Content/Tile/Metano_Town_Base.tile` | `252aacb0` (2022-12-15) | `19b29549…` | https://github.com/Palikadude/Halcyon/blob/252aacb0d609cb2b43ca24d3134148352debae27/Content/Tile/Metano_Town_Base.tile |
| `Content/Tile/Metano_Town_Cliffs.tile` | `e51d00b1` (2021-07-14) | `6d342b97…` | https://github.com/Palikadude/Halcyon/blob/e51d00b1b0a9250a34d5a1d3dde89257e9fbd100/Content/Tile/Metano_Town_Cliffs.tile |
| `Content/Tile/Metano_Town_Fringe.tile` | `e51d00b1` (2021-07-14) | `28d3c9cf…` | https://github.com/Palikadude/Halcyon/blob/e51d00b1b0a9250a34d5a1d3dde89257e9fbd100/Content/Tile/Metano_Town_Fringe.tile |

Historiques : [Base](https://github.com/Palikadude/Halcyon/commits/master/Content/Tile/Metano_Town_Base.tile),
[Cliffs](https://github.com/Palikadude/Halcyon/commits/master/Content/Tile/Metano_Town_Cliffs.tile),
[Fringe](https://github.com/Palikadude/Halcyon/commits/master/Content/Tile/Metano_Town_Fringe.tile).
(Référence PMDO introuvable sous `Palikadude/PMDO` — 404 ; les tuiles vivent dans Halcyon.)

**Halcyon vs Abyss V4** (`55860b9a`, tuiles déjà en repo) : décodage des deux
jeux et comparaison tuile par tuile — **Cliffs et Fringe pixel-identiques
(0 différence)**, Base = 2 tuiles dont Abyss a retouché le joint (4 px au
raccord `(62,151)|(63,151)`). La V2 utilise les **originaux Halcyon**.

Actifs réutilisés (aucune régénération) :
- **Mer** : crop `(272,370)-(1040,582)` des 64+64 phases P de l'océan V2
  (`renders/caps_terrasses_v3/ocean/`) — indices figés, palettes conservées.
- **Nuages** : `sprites/cote_v2/COTEV2_NUAGES_WRAP.png` (2200×344, y=8,
  12 px/s, période 2200, raccord L==R vérifié).
- **Ciels** : copies V1 (`01/02`), inchangés.

## Méthode : magenta / échantillonnage / assemblage

1. **Magenta (V1, guide approuvé)** : les falaises V1 ont été générées sur fond
   magenta puis détourées ; leurs alpha constituent les **masques approuvés**.
   La V2 conserve ces alpha **à l'octet** (vérifié) : seule la matière change.
2. **Échantillonnage (modules natifs)** : décodage du format `.tile` Halcyon
   (tuiles 8×8), puis découpe de **rectangles cohérents** (référence MANUEL §9,
   `cote_v4_abyss/prepare.py`) — Herbe 128×128, Face/Retour 64×48,
   Couronne/Pied 64×16. Aucune rotation, aucun miroir, aucun rééchantillonnage.
3. **Assemblage (tampons)** : les masques V1 sont classés herbe/roche ; chaque
   module est **tamponné sur grille 8 px** et **clippé au pixel** par le masque
   (145 tampons cap + 212 terrasse). Ordre : herbe, faces, retours, couronnes,
   pieds. Les verts sont exclus des couronnes (pas de marche verte).
   `placements.json` rejoue les calques à l'identique (vérifié).

Nuit : **1 passe** du filtre Abyss exact (`cote_v4_abyss/night.py`), prouvé
égal au `tools/tile_night.py` d'Abyss sur toutes les couleurs source.

## Contenu

- `commun/` : ciels (01/02), mer jour/nuit (03/04, phase 00), nuages jour/nuit
  (05/06), `ocean/` (128 phases P + palettes).
- `cap_gauche/`, `terrasse_droite/` : 5 calques natifs + nuits, `TERRAIN`,
  `TERRAIN_NUIT`, `placements.json`, compositions jour/nuit.
- `manifest.json`, `verification.json` (33 contrôles PASS), `PLANCHE.png`.
- Aperçu : `apercu_falaises_proches_metano_v2.html` (calques, jour/nuit, mer
  64 phases, wrap animé, export PNG).

Reste-à-faire V4 jardin : 5 zones × 4 layouts (20 générations) — inchangé.
