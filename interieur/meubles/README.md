# Meubles et décor du café — tilesheet

`meubles_cafe_tilesheet.png` — **512 × 704 px = 64 × 88 cellules** de 8 px,
fond **strictement transparent** (alpha binaire, 0 pixel semi-transparent).
`meubles_cafe_tilesheet.json` donne pour chaque objet son nom, sa position et
sa taille en cellules.

## D'où viennent les meubles

Les meubles ne sont pas dessinés : ils sont **extraits des vrais tilesets du
jeu**, ce qui garantit une qualité d'asset et non de génération.

| Source | Fichier | Objets |
|---|---|---|
| `Minemaker0430/ExplorersOfSkyOrigins` | `SpindaCafe2.tile` | 17 — les deux stands Spinda, guirlandes, jarres, tables, plantes |
| `Palikadude/Halcyon` | `Metano_Town_Cafe_Objects*.tile` | 15 — comptoir, étagère à baies, tables-souches, banc, tapis, caisses |
| généré au même format | `decor_cafe_genere.png` | 21 — mobilier de café supplémentaire |

Les `.tile` sont un format RogueEssence : en-tête `<tile 4o><count 4o>`, puis
`count` entrées de 16 octets `<clé 8o><offset 8o>`, la clé encodant `(y<<32)|x`
et chaque bloc de données étant préfixé de sa longueur sur 8 octets. Les PNG de
8 × 8 sont recomposés sur la grille.

## Qualité mesurée

Étalon : le calque d'objets du Spinda café d'EOS Origins — 86 couleurs,
6,1 couleurs par tuile, 100 % des tuiles sous 16 couleurs.

| Mesure | Tilesheet |
|---|---|
| Objets | **53** |
| Couleurs | 863 |
| Couleurs par tuile 8 × 8 | **8,1** en moyenne |
| Tuiles tenant en 16 couleurs | **93,3 %** |
| Pixels semi-transparents | **0** |

Les 21 objets générés sont passés par `aplatir_comme_palika.py`
(36 657 → 494 couleurs) pour retrouver de vrais aplats, sans quoi ils auraient
été détruits à l'import — voir la section « Import dans l'éditeur PMDO » du
README parent.

## Découpage

Chaque objet est isolé par **composante connexe** sur le masque alpha, recadré
au pixel près, puis aligné sur la grille de 8 px : chaque case du sheet occupe
un nombre entier de cellules PMDO, donc les objets se posent sans décalage.

Dans le calque EOS, les deux stands et les guirlandes ne forment qu'une seule
composante — les fanions les relient. Ces zones sont tranchées explicitement
dans le script pour rester réutilisables séparément.

```bash
python3 ../../tileset_pmd/construire_tilesheet_meubles.py
```
