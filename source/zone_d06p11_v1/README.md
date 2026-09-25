# Zone D06P11 V1 — textures ROM de d06p11a, nouveau layout
- Source : `pret/pmd-sky/files/MAP_BG/d06p11a` (.bma/.bpc/.bpl/.bpa), rendu par couche via skytemple-files (`rom_layers.py`, attend le MAP_BG dans `/tmp/pret`).
- Layout : grille cible (roche/sable/grotte/mer) ; grotte et falaise+mer copiées en blocs entiers ; le reste synthétisé tuile 8×8 par tuile à partir des tuiles ROM (contexte 5×5 + cohérence + 3 passes de raffinement). 0 pixel inventé. Collision = celle des tuiles source, îlots isolés bloqués.
- Calques : `00_base`, `01_mer_bpa` (10 frames, FrameLength 10), `02_scintillement_palette` (7 frames, FrameLength 5), `03_haut` (couche haute BMA).
- Roche : LUT de couleurs sur les tuiles de roche uniquement (teinte ramenée vers le sable, 30 % de ton sable). Sable, mer, ciel intacts.
- Limites : quelques raccords visibles (bord gauche du bloc grotte, bouts de corniches) ; non testé en jeu.
