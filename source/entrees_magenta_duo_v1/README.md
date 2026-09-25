# Entrées donjon — fond duo canonique, layout légèrement modifié, multicouche

**Reprise 25 septembre 2026 — cible PMDO 0.8.12**

Demande : zone entrée donjon avec fond duo issu de map canonique, modifier légèrement les layouts, pipeline générateur magenta → échantillonnage texture canonique → multicouche → animation selon composition, livraison 3 formats (PNG/TSX/ORA + PMDO Ground + aperçu HTML).

## Canonique & duo

- **Sources** : `Mystifying_Forest_entrance_TDS.png` (600×504), `Dark_Crater_entrance_TDS.png` (360×456), `Steam_Cave_entrance_TDS.png` (504×440) — hashes dans `references/config.json`.
- **Duo** : chaque entrée expose 2 fonds issus de la même map canonique mais à profondeurs distinctes :
  - Forêt : canopée lointaine (fond 1) + parois mousses proches (fond 2)
  - Volcan : paroi externe (fond 1) + champ de lave (fond 2, animé)
  - Vapeur : ciel brumeux lointain (fond 1) + falaise suintante proche (fond 2, vapeur animée)
- **Layout** : léger décalage du chemin sud→nord, entrée au nord recentrée/élargie, masses latérales rééquilibrées. Pas de copie pixel-exacte ; pas de nouvelle texture inventée pour le terrain de jour — échantillonnage canonique via magenta.

## Pipeline magenta multicouche (méthode layouts_magenta_v1 conservée)

1. **Génération guide** : terrain sur magenta #FF00FF + sol sur magenta, 3 entrées ×2 =6 bruts `bruts/*.png`
2. **Key magenta** : `palette.key()` — détection r>g*1.45 & b>g*1.45, frange 1px, alpha exact
3. **Détourage & séparation** : sol reconstitué / structure par masques géométriques, objets par seuils couleur, ombres contact (flou + alpha 23%), raccord 8px
4. **Palettes cohérentes** : `palette.tint()` — 2 variantes par entrée (6 scènes), teintes HS adaptees au biome, pas de recoloration arbitraire
5. **Animation selon map** :
   - Forêt : statique (1 frame, comme source)
   - Volcan : 6 phases lave, 120ms, cycle 720ms
   - Vapeur : 8 phases vapeur, 130ms, cycle 1040ms
6. **Calques** : 00_fond_lointain_duo, 01_fond_proche_duo, 02_sol, 03_ombres, 04-06 structure/entrée, 07_raccord, 01_animation (si présent)
7. **Vérif** : recomposition opaque, masques, durées, ORA, TSX 8px
8. **Livraisons** :
   - PNG transparents + TSX 8px + ORA + manifest.json (comme `layouts_magenta_v1`)
   - Pack PMDO Ground (20 Ground si étendu, ici 3×2 palettes =6 Ground démo, TexSize 1)
   - Aperçu HTML autonome avec WebP/GIF + ZIP

## État

Scaffolding posé, config et palette prêtes. Bruts à générer (étape suivante), puis `build.py` → `verify.py` → `gallery.py` → `package.py` → `make_project_pmdo.py`.

```bash
python3 source/entrees_magenta_duo_v1/build.py
python3 source/entrees_magenta_duo_v1/verify.py
python3 source/entrees_magenta_duo_v1/gallery.py
python3 source/entrees_magenta_duo_v1/package.py
```

Aucun import PMDO exécuté ici ; vérification fichier uniquement.
