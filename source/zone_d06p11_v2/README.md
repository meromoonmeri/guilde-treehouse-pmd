# Zone D06P11 V2 — promontoire
Chemin central sud → nord, esplanade devant la grotte, mer en contrebas des deux côtés, horizon à perte de vue (y=168), nuages rasant l'horizon.
- Textures : tuiles ROM d06p11a + miroirs horizontaux (bords de falaise côté gauche). Bloc grotte copié tel quel. 0 pixel inventé.
- Calques : `00_ciel` (couleurs de rangée ROM), `01_nuages` (nuages ROM extraits, bande 768 px, placement modulo = wrap parfait, −4 px/s, boucle 192 s), `02_mer_bpa` (10 f × FrameLength 10), `03_mer_palette` (7 f × 5), `04_terrain`.
- Mer : bande ROM pure (x 504–552) tuilée en miroir aller-retour, sans couture.
- Limites : bords de falaise encore un peu en escalier ; nuages petits (seul nuage de la ROM) ; non testé en jeu. Nécessite `/tmp/pret/files/MAP_BG`.
