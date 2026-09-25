# Zone D06P11 V9
Dérivé V8, layout identique.
- **Falaise + rochers régénérés** (`generation/falaise_style_d06p11a.png`) : générateur guidé par le terrain V8 + la ROM d06p11a (`generation/ref_rom_d06p11a.png`) → colonnes arrondies, ombrage doux, bande de pied humide sombre. Ramené sur la palette ROM V2. **Génération, pas des pixels ROM exacts.**
- **Écume de contour façon PMD Sky** (réf. `arenapmdskybeach.png`) : lavis clair collé à la roche, ligne blanche qui respire le long du pied, anneau tramé qui s'éloigne et s'efface. Procédural, 16 phases × 6 f (100 ms), boucle exacte. Remplace les sprites d'écume V8.
- **Soleil blanc façon Sky** (réf. `Extra_Backgrounds.png`, `generation/ref_soleil_blanc_sky_x4.png`) : disque blanc + halo tramé en damier, 6 phases de pulsation. Teinté au crépuscule uniquement.
- Collision : grille V8 reprise (1356 cases) ; mer, ciel, nuages, lune repris.
- Non testé en jeu. `.venv/bin/python source/zone_d06p11_v9/build.py`
