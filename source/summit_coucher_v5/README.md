# Sommet au coucher du soleil — multicalque V5

Référence : `112438.png` (commit 055ff8d5, rip SparkuG23). La planche contient 12 frames de soleil, la carte composée, le terrain seul et le ciel orange. Pixels 100 % planche, aucun générateur.

- Calques : `00_ciel` (bloc orange, dernière ligne prolongée) · `01_soleil` (12 frames, ordre de la planche, 100 ms : cadence choisie ; positions retrouvées sur la carte composée, y=13 puis 14 pour les frames 9-11) · `02_terrain` (terrain seul, posé à y=37).
- Contrôle : recomposée sans élargissement avec la frame 8, la pile reproduit la carte de la planche à 99,9 %.
- Layout : sommet élargi de 64 px, avec deux bandes de 32 px dupliquées (x 24-56 et 184-216) de part et d'autre du chemin. Le chemin reste droit (sud→nord) et centré. Canevas 304×296 (2 lignes natives dupliquées pour la grille 8 px).
- Limites : la planche ne contient pas d'éclairs, seul le soleil est animé. Des mesas répétées sont visibles au raccord des bandes. Collisions 8 px indicatives, rien n'a été testé en jeu.
