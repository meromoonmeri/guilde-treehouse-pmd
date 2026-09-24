couloir_t: DEFERRED — 2 generations (v2 stem touched S edge, v3 came out full-bleed cross).
v3 reassigned as salle_carrefour (4 grass openings verified). Gap cross kept as carrefour_clairiere
(gaps ~21px @512, bridged by native connector strip, covered by opaque-band test).
Next turn (image limit resets): generate 1 true T (N/E/W, bottom closed) -> 7th piece.
Generation log: 6 initial + 3 retries + 1 T-retry = 10/10 this turn.

## V3 — multicalque sol/chemin/arbres/rochers/bordure jungle (24 septembre 2026)
7 bordures régénérées style Southern Jungle (lianes, grosses feuilles), réf
Southern_Jungle_entrance_S.png + brut de chaque pièce, fenêtres aux accès.
Anciennes bordures jardin conservées dans renders/.../bordures/ (archives).
Terrains inchangés. Nouveau schéma : 01_sol (rives), 02_chemin (bande centrale
géométrique, érosion 15px), 03_arbres (cimes claires + troncs, toutes profondeurs),
04_buissons (verts sombres), 05_rochers, 06_fleurs (+4 phases), 07_bordure_jungle,
08_acces. V2 (fond/cimes/premier plan/troncs séparés) dans l'historique git.

## V4 — layouts séparés sol/chemin/fleurs/rochers (24 septembre 2026, 2 zones)
Passage progressif : chaque élément généré seul sur magenta (mêmes noms de couches).
Ce tour (10/10) : couloir_ns + salle_carrefour (4+4), +reprise chemin carrefour
(était beige dirt -> herbe), +reprise fleurs carrefour (guirlandes denses ->
bouquets clairsemés). Assemblage : chemin⊆sol, végétation V3 rognée hors nouveau
sol, rochers/fleurs⊆(sol|végétation). Bordure jungle + accès V3 inchangés.
Restent : ew, t, traversee, laterale, clairiere (20 générations).
Note sandbox : 5e réinitialisation vue sur le projet ; historique réintégré
(fetch + reset --hard sur origin ce22a6eb), stash redondant jeté, layouts
sauvegardés/restaurés depuis /tmp, .venv reconstruite.
